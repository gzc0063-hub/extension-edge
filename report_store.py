"""Optional persistent storage for usage analytics and PDF report backups.

The app runs without this module being configured. When Supabase settings are
present in Streamlit secrets, each completed recommendation stores one metadata
row and one PDF file backup.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st

from engine import Result
from labels import forage_label, livestock_label, weed_label


@dataclass(frozen=True)
class ReportStorageConfig:
    url: str
    service_role_key: str
    table: str = "recommendation_reports"
    bucket: str = "extension-edge-reports"


def _secret_section() -> dict[str, Any]:
    try:
        section = st.secrets.get("report_storage", {})
    except Exception:
        return {}
    return dict(section) if section else {}


def _normalize_url(raw_url: str) -> str | None:
    url = str(raw_url or "").strip().rstrip("/")
    if not url:
        return None
    if "://" not in url and "." in url:
        url = f"https://{url}"
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def get_config() -> ReportStorageConfig | None:
    section = _secret_section()
    raw_url = str(section.get("url", ""))
    url = _normalize_url(raw_url)
    key = str(section.get("service_role_key", ""))
    if not raw_url and not key:
        return None
    if not url:
        raise ValueError(
            "Report storage URL is invalid. In Streamlit secrets, use the Supabase Project URL, "
            "for example: https://your-project-ref.supabase.co"
        )
    if not key:
        raise ValueError("Report storage service_role_key is missing in Streamlit secrets.")
    return ReportStorageConfig(
        url=url,
        service_role_key=key,
        table=str(section.get("table", "recommendation_reports")),
        bucket=str(section.get("bucket", "extension-edge-reports")),
    )


def is_configured() -> bool:
    try:
        return get_config() is not None
    except ValueError:
        return False


def _headers(config: ReportStorageConfig, content_type: str = "application/json") -> dict[str, str]:
    return {
        "apikey": config.service_role_key,
        "Authorization": f"Bearer {config.service_role_key}",
        "Content-Type": content_type,
    }


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean_json(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_clean_json(child) for child in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return None if math.isnan(value) else value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        return _clean_json(value.item())
    return str(value)


def _result_payload(result: Result) -> dict[str, Any]:
    return _clean_json({
        "status": result.status,
        "best": result.best,
        "backup": result.backup,
        "partial_options": result.partial_options,
        "rejected_count": len(result.rejected),
        "review_count": len(result.review),
        "warnings": result.warnings,
        "primary_reason": result.primary_reason,
        "what_could_change": result.what_could_change,
    })


def _input_payload(ui) -> dict[str, Any]:
    return _clean_json({
        "field_id": ui.field_id,
        "forage": ui.forage,
        "forage_label": forage_label(ui.forage),
        "weeds": ui.weeds,
        "weed_labels": [weed_label(weed) for weed in ui.weeds],
        "livestock": ui.livestock,
        "livestock_label": livestock_label(ui.livestock),
        "hold_days": ui.hold_days,
        "legumes_present": ui.legumes_present,
        "legumes": ui.legumes,
        "next_cut_days": ui.next_cut_days,
        "days_since_mow": ui.days_since_mow,
        "slaughter_30d": ui.slaughter_30d,
        "hay_off_farm": ui.hay_off_farm,
        "manure_off": ui.manure_off,
        "sensitive_crops_nearby": ui.sensitive_crops_nearby,
        "rup_status": ui.rup_status,
        "county": ui.location,
        "farm_name": ui.farm_name,
        "operator_name": ui.operator_name,
    })


def save_report(result: Result, ui, narrative: str, pdf_bytes: bytes) -> tuple[bool, str]:
    """Store report metadata and PDF backup.

    Returns (saved, message). If storage is not configured, returns a successful
    no-op so the public app does not bother growers with admin setup details.
    """
    try:
        config = get_config()
    except ValueError as exc:
        return False, str(exc)
    if config is None:
        return True, "Report storage not configured; skipped remote backup."

    safe_field_id = (result.field_id or "unknown").replace("/", "-")
    generated = (result.timestamp or "").replace(":", "-")
    pdf_path = f"{safe_field_id}/{generated or 'report'}.pdf"

    upload_url = f"{config.url}/storage/v1/object/{config.bucket}/{pdf_path}"
    upload_headers = _headers(config, "application/pdf")
    upload_headers["x-upsert"] = "true"
    try:
        upload = requests.post(upload_url, headers=upload_headers, data=pdf_bytes, timeout=20)
    except requests.RequestException as exc:
        return False, f"PDF backup request failed: {exc}"
    if upload.status_code >= 300:
        return False, f"PDF backup failed ({upload.status_code}): {upload.text[:180]}"

    row = {
        "field_id": result.field_id,
        "generated_at": result.timestamp,
        "county": ui.location or "Not provided",
        "status": result.status,
        "forage": forage_label(ui.forage),
        "weeds": [weed_label(weed) for weed in ui.weeds],
        "livestock": livestock_label(ui.livestock),
        "best_product": (result.best or {}).get("trade_name"),
        "backup_product": (result.backup or {}).get("trade_name"),
        "engine_version": result.engine_version,
        "guide_version": result.guide_version,
        "pdf_path": pdf_path,
        "narrative": narrative,
        "inputs": _input_payload(ui),
        "result": _result_payload(result),
    }

    insert_url = f"{config.url}/rest/v1/{config.table}"
    insert_headers = _headers(config)
    insert_headers["Prefer"] = "return=minimal"
    try:
        insert = requests.post(insert_url, headers=insert_headers, data=json.dumps(_clean_json(row)), timeout=20)
    except requests.RequestException as exc:
        return False, f"Metadata save request failed: {exc}"
    if insert.status_code >= 300:
        return False, f"Metadata save failed ({insert.status_code}): {insert.text[:180]}"

    return True, f"Saved report backup at {pdf_path}."
