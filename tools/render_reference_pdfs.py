from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def paragraph_for(line: str, styles):
    stripped = line.strip()
    if not stripped:
        return Spacer(1, 8)
    if stripped.startswith("# "):
        return Paragraph(escape(stripped[2:]), styles["Title"])
    if stripped.startswith("## "):
        return Paragraph(escape(stripped[3:]), styles["Heading2"])
    if stripped.startswith("### "):
        return Paragraph(escape(stripped[4:]), styles["Heading3"])
    if stripped.startswith("- "):
        return Paragraph("• " + escape(stripped[2:]), styles["BodyText"])
    return Paragraph(escape(stripped), styles["BodyText"])


def render(markdown_path: Path) -> None:
    styles = getSampleStyleSheet()
    styles["BodyText"].leading = 12
    story = [paragraph_for(line, styles) for line in markdown_path.read_text(encoding="utf-8").splitlines()]
    pdf_path = markdown_path.with_suffix(".pdf")
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
        title=markdown_path.stem.replace("_", " ").title(),
    )
    doc.build(story)
    print(pdf_path)


def main() -> int:
    for name in [
        "DR_RUSSELL_REVIEW_BRIEF.md",
        "WEB_DEVELOPER_HANDOFF.md",
        "MAINTENANCE_GUIDE.md",
    ]:
        render(DOCS / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
