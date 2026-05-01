"""
explainer.py — Deterministic template-based text generator.

Replaces the previous AI-based ai_explainer.py. Pure string substitution.
Same inputs always produce the same output. No external API.
"""

from __future__ import annotations
from typing import Dict, Any
from engine import Result, Status
from labels import forage_label, weed_label


def _trade(p: Dict[str, Any]) -> str:
    return p.get("trade_name", "—") if p else "—"


def _ai(p: Dict[str, Any]) -> str:
    return p.get("active_ingredient", "—") if p else "—"


def _rate(p: Dict[str, Any]) -> str:
    return p.get("rate_per_acre", "—") if p else "—"


def _timing(p: Dict[str, Any]) -> str:
    return p.get("timing_constraints", "—") if p else "—"


def _weed_list(ui) -> str:
    return ", ".join(weed_label(weed) for weed in ui.weeds)


def _format_rejection_summary(result: Result, max_items: int = 5) -> str:
    if not result.rejected:
        return "no rejections"
    bullets = []
    for product, reason, gate in result.rejected[:max_items]:
        bullets.append(f"  • {product.get('trade_name','—')} ({gate}): {reason}")
    if len(result.rejected) > max_items:
        bullets.append(f"  • …and {len(result.rejected) - max_items} more")
    return "\n".join(bullets)


def _format_review_list(result: Result, max_items: int = 5) -> str:
    if not result.review:
        return ""
    bullets = []
    for product, reason, gate in result.review[:max_items]:
        bullets.append(f"  • {product.get('trade_name','—')} ({gate}): {reason}")
    if len(result.review) > max_items:
        bullets.append(f"  • …and {len(result.review) - max_items} more")
    return "\n".join(bullets)


def render(result: Result, ui) -> str:
    """Return the human-readable narrative string for a Result."""
    fid = result.field_id or "(no-id)"

    if result.status == Status.INVALID_INPUT:
        bullets = "\n".join(f"  • {e}" for e in result.errors) or "  • (no detail)"
        return (
            f"Field {fid}: Input validation failed.\n"
            f"{bullets}\n"
            f"Correct the inputs above and resubmit."
        )

    if result.status == Status.RECOMMEND:
        weeds = _weed_list(ui)
        backup_line = f"Backup: {_trade(result.backup)}." if result.backup else "No backup product available with full coverage."
        warn_line = (
            f"{len(result.warnings)} warning(s): {'; '.join(result.warnings)}"
            if result.warnings else "No additional warnings."
        )
        return (
            f"Field {fid}: For {forage_label(ui.forage)} with {weeds}, the recommended product is "
            f"{_trade(result.best)} ({_ai(result.best)}) at {_rate(result.best)}. "
            f"Timing: {_timing(result.best)}. {backup_line} {warn_line} "
            f"Read the full label before purchase or application."
        )

    if result.status == Status.RECOMMEND_WITH_WARNINGS:
        warning_list = "; ".join(result.warnings) if result.warnings else "(see product comments)"
        backup_line = f"Backup: {_trade(result.backup)}." if result.backup else ""
        return (
            f"Field {fid}: {_trade(result.best)} is the top match but has "
            f"{len(result.warnings)} active warnings: {warning_list}. {backup_line} "
            f"Read the full label before purchase or application."
        )

    if result.status == Status.NO_SINGLE_PRODUCT:
        top3 = ", ".join(_trade(p) for p in result.partial_options) or "(none)"
        return (
            f"Field {fid}: No single product provides Good-or-Excellent control of all "
            f"selected weeds. Top partial options: {top3}. The guide states: 'pick your "
            f"battles in mixed stands.' Contact your county Extension office for a "
            f"site-specific strategy."
        )

    if result.status == Status.NO_LEGAL_RECOMMENDATION:
        primary = result.primary_reason or "All candidate products were rejected by hard gates."
        change_lines = "\n".join(f"  • {c}" for c in result.what_could_change) \
            if result.what_could_change else "  • Contact county Extension for site-specific options."
        rejection_summary = _format_rejection_summary(result)
        return (
            f"Field {fid}: No legal recommendation under your conditions.\n"
            f"Reason: {primary}\n"
            f"{len(result.rejected)} product(s) rejected:\n"
            f"{rejection_summary}\n"
            f"To unlock options:\n"
            f"{change_lines}\n"
            f"Contact your county Extension office at www.aces.edu/counties."
        )

    if result.status == Status.MANUAL_REVIEW:
        items = _format_review_list(result)
        return (
            f"Field {fid}: {len(result.review)} product(s) require manual review — "
            f"data missing in IPM-0028A:\n"
            f"{items}\n"
            f"Contact your county Extension office before applying."
        )

    return f"Field {fid}: Unrecognized status '{result.status}'."
