"""
pdf_report.py — Producer's PDF spray record.

Stamps every record with field_id, engine version, guide version, and a
timestamp for audit traceability. No analytics, no transmission — built
in the running session and downloaded to the producer's device.
"""

from __future__ import annotations
from io import BytesIO
from typing import Dict, Any

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)

from engine import Result, Status, ENGINE_VERSION, GUIDE_VERSION
from labels import APP_NAME, forage_label, legume_label, livestock_label, rup_label, weed_label


def _styles():
    base = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle(
        "Title", parent=base["Title"], fontSize=18, leading=22,
        textColor=colors.HexColor("#0C2340"), alignment=TA_LEFT,
    )
    s["h1"] = ParagraphStyle(
        "H1", parent=base["Heading1"], fontSize=13, leading=16,
        textColor=colors.HexColor("#0C2340"), spaceBefore=12, spaceAfter=4, keepWithNext=1,
    )
    s["h2"] = ParagraphStyle(
        "H2", parent=base["Heading2"], fontSize=11, leading=14,
        textColor=colors.HexColor("#E87722"), spaceBefore=8, spaceAfter=2, keepWithNext=1,
    )
    s["body"] = ParagraphStyle(
        "Body", parent=base["Normal"], fontSize=10, leading=13, alignment=TA_JUSTIFY,
    )
    s["meta"] = ParagraphStyle(
        "Meta", parent=base["Normal"], fontSize=8.5, leading=11,
        textColor=colors.HexColor("#616161"),
    )
    s["banner_ok"] = ParagraphStyle(
        "BannerOK", parent=base["Normal"], fontSize=12, leading=15,
        textColor=colors.white, backColor=colors.HexColor("#2F6B3F"),
        borderPadding=8, alignment=TA_LEFT,
    )
    s["banner_warn"] = ParagraphStyle(
        "BannerWarn", parent=base["Normal"], fontSize=12, leading=15,
        textColor=colors.HexColor("#5D4037"), backColor=colors.HexColor("#FFF59D"),
        borderPadding=8, alignment=TA_LEFT,
    )
    s["banner_bad"] = ParagraphStyle(
        "BannerBad", parent=base["Normal"], fontSize=12, leading=15,
        textColor=colors.white, backColor=colors.HexColor("#C62828"),
        borderPadding=8, alignment=TA_LEFT,
    )
    s["callout"] = ParagraphStyle(
        "Callout", parent=base["Normal"], fontSize=9.5, leading=12,
        textColor=colors.HexColor("#B71C1C"),
        backColor=colors.HexColor("#FFEBEE"),
        borderColor=colors.HexColor("#B71C1C"),
        borderWidth=0.6, borderPadding=6,
    )
    return s


def _banner(result: Result, s):
    if result.status == Status.RECOMMEND:
        return Paragraph(f"<b>STATUS: RECOMMEND</b> — A product was approved for your conditions.", s["banner_ok"])
    if result.status == Status.RECOMMEND_WITH_WARNINGS:
        return Paragraph(f"<b>STATUS: RECOMMEND WITH WARNINGS</b> — Approved with cautions.", s["banner_warn"])
    if result.status == Status.NO_SINGLE_PRODUCT:
        return Paragraph(f"<b>STATUS: NO SINGLE PRODUCT</b> — No single product covers all weeds at G/E.", s["banner_warn"])
    if result.status == Status.NO_LEGAL_RECOMMENDATION:
        return Paragraph(f"<b>STATUS: NO LEGAL RECOMMENDATION</b> — All products rejected by hard gates.", s["banner_bad"])
    if result.status == Status.MANUAL_REVIEW:
        return Paragraph(f"<b>STATUS: MANUAL REVIEW</b> — Data missing; contact county Extension.", s["banner_warn"])
    if result.status == Status.INVALID_INPUT:
        return Paragraph(f"<b>STATUS: INVALID INPUT</b> — Correct inputs and resubmit.", s["banner_bad"])
    return Paragraph(f"<b>STATUS: {result.status}</b>", s["banner_warn"])


def _meta_table(result: Result, ui, s):
    rows = [
        ["Field ID",         result.field_id or "—"],
        ["Generated",        result.timestamp or "—"],
        ["Engine version",   result.engine_version],
        ["Guide version",    result.guide_version],
        ["Forage type",      forage_label(ui.forage) if ui.forage else "—"],
        ["Priority weeds",   ", ".join(weed_label(weed) for weed in ui.weeds) if ui.weeds else "—"],
        ["Livestock",        livestock_label(ui.livestock)],
        ["Operator hold (d)", str(ui.hold_days) if ui.hold_days is not None else "—"],
        ["Days since mow",   str(ui.days_since_mow) if ui.days_since_mow is not None else "—"],
        ["Days to next cut", str(ui.next_cut_days) if ui.next_cut_days is not None else "—"],
        ["Legumes present",  "Yes (" + ", ".join(legume_label(legume) for legume in ui.legumes) + ")" if ui.legumes_present else "No"],
        ["Slaughter ≤30d",   "Yes" if ui.slaughter_30d else "No"],
        ["Hay leaves farm",  "Yes" if ui.hay_off_farm else "No"],
        ["Manure leaves farm","Yes" if ui.manure_off else "No"],
        ["Sensitive crops nearby", "Yes" if ui.sensitive_crops_nearby else "No"],
        ["RUP applicator",   rup_label(ui.rup_status)],
        ["Farm",             ui.farm_name or "—"],
        ["Operator",         ui.operator_name or "—"],
        ["Location",         ui.location or "—"],
    ]
    t = Table(rows, colWidths=[1.7 * inch, 4.7 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7F3EF")),
    ]))
    return t


def _product_block(label: str, product: Dict[str, Any], s):
    flow = []
    flow.append(Paragraph(f"<b>{label}: {product.get('trade_name','—')}</b>", s["h2"]))
    rows = [
        ["Active ingredient", product.get("active_ingredient", "—")],
        ["Application type",  product.get("application_type", "—")],
        ["Rate per acre",     product.get("rate_per_acre", "—")],
        ["Timing",            product.get("timing_constraints", "—")],
        ["Hay PHI (days)",    product.get("hay_phi_days", "—")],
        ["Beef grazing (days)", product.get("beef_grazing_days", "—")],
        ["Lactating dairy (days)", product.get("lactating_dairy_days", "—")],
        ["Slaughter wait (days)", product.get("slaughter_withdrawal_days", "—")],
        ["RUP",               "Yes" if str(product.get("RUP_flag", "")).lower() in {"true", "1", "yes"} else "No"],
        ["Guide ref",         product.get("guide_page_ref", "—")],
    ]
    # Append efficacy ratings if present
    ratings = product.get("_ratings") or {}
    if ratings:
        rows.append(["Efficacy on selected weeds",
                     ", ".join(f"{weed_label(w)}: {r}" for w, r in ratings.items())])
    t = Table(rows, colWidths=[1.7 * inch, 4.7 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7F3EF")),
    ]))
    flow.append(t)
    if product.get("comments_structured"):
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(f"<i>Comments:</i> {product.get('comments_structured')}", s["body"]))
    return KeepTogether(flow)


def _rejection_table(items, title, s):
    if not items:
        return None
    rows = [["Product", "Gate", "Reason"]]
    for product, reason, gate in items:
        rows.append([product.get("trade_name", "—"), gate, reason])
    t = Table(rows, colWidths=[1.7 * inch, 1.0 * inch, 3.7 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0C2340")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BDBDBD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F3EF")]),
    ]))
    flow = [Paragraph(title, s["h2"]), t]
    return KeepTogether(flow)


def _footer(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(colors.HexColor("#757575"))
    canv.drawString(0.75 * inch, 0.5 * inch,
                    f"{APP_NAME} — Engine v{ENGINE_VERSION} — Source: {GUIDE_VERSION}")
    canv.drawRightString(LETTER[0] - 0.75 * inch, 0.5 * inch, f"Page {canv.getPageNumber()}")
    canv.restoreState()


def build(result: Result, ui, narrative: str = "") -> bytes:
    """Build the PDF and return raw bytes (suitable for Streamlit download)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.85 * inch,
        title=f"{APP_NAME} Spray Record — {result.field_id}",
        author=APP_NAME,
        subject="Producer spray record (IPM-0028A 2026)",
    )
    s = _styles()
    story = []

    # Header
    story.append(Paragraph(f"{APP_NAME} — Spray Record", s["title"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#E87722")))
    story.append(Spacer(1, 6))
    story.append(_banner(result, s))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Screening aid only.</b> The product label is the law. Always confirm "
        "recommendations with your county Extension office before applying any herbicide.",
        s["callout"],
    ))
    story.append(Spacer(1, 6))

    # Field & input metadata
    story.append(Paragraph("Field &amp; Input Summary", s["h1"]))
    story.append(_meta_table(result, ui, s))
    story.append(Spacer(1, 6))

    # Narrative summary
    if narrative:
        story.append(Paragraph("Recommendation Narrative", s["h1"]))
        story.append(Paragraph(narrative.replace("\n", "<br/>"), s["body"]))

    # Recommendations
    if result.best:
        story.append(Paragraph("Primary Recommendation", s["h1"]))
        story.append(_product_block("Recommended", result.best, s))
    if result.backup:
        story.append(Paragraph("Backup Option", s["h1"]))
        story.append(_product_block("Backup", result.backup, s))

    if result.partial_options and not result.best:
        story.append(Paragraph("Top Partial Options", s["h1"]))
        for i, p in enumerate(result.partial_options, 1):
            story.append(_product_block(f"Option {i}", p, s))
            story.append(Spacer(1, 4))

    # Why others failed
    if result.rejected:
        story.append(Spacer(1, 4))
        rt = _rejection_table(result.rejected, "Why Other Products Failed", s)
        if rt: story.append(rt)

    if result.review:
        story.append(Spacer(1, 4))
        rt = _rejection_table(result.review, "Manual Review Required (Data Missing)", s)
        if rt: story.append(rt)

    # Disclaimer
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#BDBDBD")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Generated {result.timestamp or ''} from {GUIDE_VERSION}. Engine v{ENGINE_VERSION}. "
        "This record is a screening aid based on a public ACES publication. The product label "
        "is the law. Trade names identify products only and do not constitute endorsement by ACES "
        "or Auburn University. Read the full label before purchase or application.",
        s["meta"],
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
