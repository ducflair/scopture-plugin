#!/usr/bin/env python3
"""Generate the provider-neutral Scopture offer testing guide for a release."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        Image,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
    )
except ImportError as error:
    raise SystemExit(
        "The PDF generator requires ReportLab. Install it with "
        "`python3 -m pip install -r requirements-release.txt`."
    ) from error

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATH = REPO_ROOT / "assets" / "offer-testing-guide" / "scopture-model-viewer.jpg"
TEST_SUITE_PATH = REPO_ROOT / "test-prompts.json"

PAGE_W, PAGE_H = A4
MARGIN_L = MARGIN_R = 15 * mm
MARGIN_TOP = 18 * mm
MARGIN_BOTTOM = 15 * mm
NAVY = colors.HexColor("#17263D")
INK = colors.HexColor("#263447")
MUTED = colors.HexColor("#65758A")
ACCENT = colors.HexColor("#D95B52")
PALE = colors.HexColor("#F3F6FA")
PALE_RED = colors.HexColor("#FFF2F0")
PALE_BLUE = colors.HexColor("#ECF3FC")
LINE = colors.HexColor("#D9E1EA")

STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="CoverTitle", parent=STYLES["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=NAVY, alignment=TA_LEFT, spaceAfter=5))
STYLES.add(ParagraphStyle(name="CoverSub", parent=STYLES["Normal"], fontName="Helvetica", fontSize=11, leading=15, textColor=MUTED, spaceAfter=8))
STYLES.add(ParagraphStyle(name="Kicker", parent=STYLES["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=ACCENT, tracking=1.2, spaceAfter=5))
STYLES.add(ParagraphStyle(name="H1x", parent=STYLES["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY, spaceBefore=0, spaceAfter=8))
STYLES.add(ParagraphStyle(name="H2x", parent=STYLES["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=NAVY, spaceBefore=7, spaceAfter=4))
STYLES.add(ParagraphStyle(name="Bodyx", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=9, leading=13, textColor=INK, spaceAfter=6))
STYLES.add(ParagraphStyle(name="Smallx", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10, textColor=INK, spaceAfter=2))
STYLES.add(ParagraphStyle(name="Captionx", parent=STYLES["BodyText"], fontName="Helvetica-Oblique", fontSize=7.5, leading=10, textColor=MUTED, spaceBefore=4, spaceAfter=6))
STYLES.add(ParagraphStyle(name="CellHead", parent=STYLES["BodyText"], fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.white))
STYLES.add(ParagraphStyle(name="Cell", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9.1, textColor=INK))
STYLES.add(ParagraphStyle(name="CellStrong", parent=STYLES["BodyText"], fontName="Helvetica-Bold", fontSize=7.2, leading=9.1, textColor=NAVY))
STYLES.add(ParagraphStyle(name="CardTitle", parent=STYLES["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=NAVY, spaceAfter=3))
STYLES.add(ParagraphStyle(name="CardBody", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=8.2, leading=11, textColor=INK, spaceAfter=0))
STYLES.add(ParagraphStyle(name="Flow", parent=STYLES["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=NAVY, alignment=TA_CENTER))


def paragraph(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(text, STYLES[style])


def card(title: str, body: str, background=PALE) -> Table:
    content = [paragraph(title, "CardTitle"), paragraph(body, "CardBody")]
    table = Table([[content]], colWidths=[PAGE_W - MARGIN_L - MARGIN_R])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT if background == PALE_RED else colors.HexColor("#6D8FB7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def case_table(cases: list[dict], widths=(38, 182, 290)) -> Table:
    data = [[paragraph("ID", "CellHead"), paragraph("Prompt", "CellHead"), paragraph("Expected result and declared effect", "CellHead")]]
    for case in cases:
        effect = case.get("side_effects", "not recorded").replace("_", " ")
        expected = escape(case.get("expected_output", "No expected result is documented."))
        expected += f'<br/><font color="#65758A">Effect: {escape(effect)}</font>'
        data.append([
            paragraph(escape(case["id"].split("-", 1)[0]), "CellStrong"),
            paragraph(escape(case["prompt"]), "Cell"),
            paragraph(expected, "Cell"),
        ])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]))
    return table


def on_page(canvas, doc, release_date: str, version: str) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(MARGIN_L, PAGE_H - 10 * mm, "SCOPTURE")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 10 * mm, "OFFER TESTING GUIDE")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN_L, PAGE_H - 12 * mm, PAGE_W - MARGIN_R, PAGE_H - 12 * mm)
    canvas.line(MARGIN_L, 11 * mm, PAGE_W - MARGIN_R, 11 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN_L, 7.5 * mm, f"{release_date}  |  Plugin v{version}  |  Page {doc.page}")
    canvas.restoreState()


def source_version() -> str:
    manifest = json.loads((REPO_ROOT / "common" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return str(manifest["version"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Scopture offer testing guide PDF.")
    parser.add_argument("--version", default=source_version(), help="Plugin release version (defaults to the source manifest)")
    parser.add_argument("--out-dir", default="dist", help="Directory for the generated PDF")
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    if not re.fullmatch(r"[0-9A-Za-z.+-]+", version):
        parser.error("version must contain only letters, digits, dots, plus signs, or hyphens")
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"Documentation screenshot not found: {IMAGE_PATH}")

    suite = json.loads(TEST_SUITE_PATH.read_text(encoding="utf-8"))
    cases = suite.get("test_cases", [])
    positive_cases = [case for case in cases if case.get("kind") == "positive"]
    negative_cases = [case for case in cases if case.get("kind") == "negative"]
    inspect_cases = [
        case for case in positive_cases
        if case.get("side_effects", "none") in {"none", "changes_live_view"}
    ]
    change_cases = [case for case in positive_cases if case not in inspect_cases]
    if not positive_cases or not negative_cases:
        raise ValueError("The evaluation prompt suite must contain positive and negative cases")

    release_date = datetime.now(ZoneInfo("Europe/Lisbon")).strftime("%d %B %Y").lstrip("0")
    out_dir = (REPO_ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"offer-testing-guide-scopture-{version}.pdf"

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        title="Scopture Plugin Offer Testing Guide",
        author="Ducflair",
        subject="Connection setup, reproducible checks, and expected behavior",
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    frame = Frame(MARGIN_L, MARGIN_BOTTOM, PAGE_W - MARGIN_L - MARGIN_R, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=lambda canvas, current: on_page(canvas, current, release_date, version))])

    story = []
    # Page 1: purpose and public documentation screenshot.
    story.extend([
        Spacer(1, 5 * mm),
        paragraph("GENERAL OFFER TESTING INFORMATION", "Kicker"),
        paragraph("Scopture plugin<br/>offer testing guide", "CoverTitle"),
        paragraph("Connection setup • demo access • reproducible checks • expected behavior", "CoverSub"),
        HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceBefore=1, spaceAfter=9),
        paragraph(
            f"This guide helps reviewers connect Scopture to a compatible AI assistant and validate representative workflows against an authorized test workspace. It includes {len(positive_cases)} functional prompts and {len(negative_cases)} scope and safety prompts, drawn from the release evaluation suite.",
            "Bodyx",
        ),
    ])
    image_width = PAGE_W - MARGIN_L - MARGIN_R
    image = Image(str(IMAGE_PATH))
    image_height = image_width * image.imageHeight / image.imageWidth
    story.append(Image(str(IMAGE_PATH), width=image_width, height=image_height, hAlign="CENTER"))
    story.append(paragraph(
        'Documentation illustration: Scopture’s model viewer displaying an engineering assembly with linked-file and inspection controls (OreSat 0.5). Sourced from the public <link href="https://site.scopture.com/docs" color="#2773A5">Scopture Docs</link> homepage. This is product imagery, not a record of a completed test run.',
        "Captionx",
    ))
    story.append(card(
        "What this guide covers",
        "Scopture keeps drawings, interactive models, project intent, review issues, decisions, and revision history together. Its remote MCP connector lets a compatible assistant inspect and, when authorized, change accessible cloud drawings. Local <font name=\"Courier\">.duc</font> files remain on the device and are outside this remote connection.",
        PALE_BLUE,
    ))
    story.append(Spacer(1, 5))
    story.append(paragraph(
        "The prompts below are reproducible evaluation steps. Expected outcomes describe what to inspect; they are not assertions that a live reviewer run has already passed.",
        "Smallx",
    ))
    story.append(Spacer(1, 5))
    story.append(paragraph(
        'Setup references: <link href="https://site.scopture.com/docs/automation/ai-providers" color="#2773A5">AI Providers</link> • '
        '<link href="https://site.scopture.com/docs/automation/mcp-tool" color="#2773A5">MCP Tool</link> • '
        '<link href="https://site.scopture.com/docs/get-started/design-review" color="#2773A5">Run a Design Review</link> • '
        '<link href="https://site.scopture.com/docs" color="#2773A5">Scopture Docs</link>',
        "Smallx",
    ))
    story.append(PageBreak())

    # Page 2: provider-neutral connection and access guidance.
    story.extend([
        paragraph("01 / CONNECT", "Kicker"),
        paragraph("Set up the evaluation account", "H1x"),
        paragraph("The remote connector uses the authenticated Scopture identity and its drawing permissions. Provider menus and administrator requirements vary by client and organization.", "Bodyx"),
        paragraph("Connect Scopture", "H2x"),
        paragraph(
            "1. In a compatible assistant, open its MCP or custom connector settings and add a remote server named <b>Scopture</b>.<br/>"
            "2. Enter <font name=\"Courier\">https://api.scopture.com/mcp</font>; choose <b>Streamable HTTP</b> and <b>OAuth</b> when prompted.<br/>"
            "3. Complete Scopture sign-in and authorize the requested access, then enable Scopture for the conversation.<br/>"
            "4. If the client or organization requires it, ask an administrator to approve and make the connector available.",
            "Bodyx",
        ),
        paragraph("Demo test account access", "H2x"),
        paragraph(
            "If this evaluation requires account access, the demo review account invitation or credentials and sign-in steps should be included with the review materials. If you did not receive access, or need help entering the demo testing account, contact <link href=\"mailto:support@scopture.com\" color=\"#2773A5\">support@scopture.com</link> to request the credentials and sign-in instructions.",
            "Bodyx",
        ),
        paragraph("Prerequisites", "H2x"),
        paragraph(
            "• Use a Scopture test account with access to at least one cloud drawing.<br/>"
            "• Read, Write, and Execute capabilities are separate; the user also needs access to the target drawing.<br/>"
            "• Cloud Python execution requires an entitled paid organization plan.<br/>"
            "• Use a disposable drawing for create, update, issue-message, dismissal, charter-change, and restore prompts.",
            "Bodyx",
        ),
    ])
    flow = Table([[
        paragraph("AI assistant<br/><font size=\"7\">MCP connection</font>", "Flow"),
        paragraph("→", "Flow"),
        paragraph("Scopture MCP<br/><font size=\"7\">Streamable HTTP • OAuth</font>", "Flow"),
        paragraph("→", "Flow"),
        paragraph("Authorized cloud drawings<br/><font size=\"7\">user permissions apply</font>", "Flow"),
    ]], colWidths=[100, 28, 130, 28, 132], hAlign="LEFT")
    flow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([flow, Spacer(1, 5), paragraph("First-run smoke checks", "H2x")])
    smoke_ids = {"P01-current-drawing", "P02-accessible-drawings", "P04-current-screenshot", "P12-python-run"}
    smoke_cases = [case for case in positive_cases if case.get("id") in smoke_ids]
    story.append(case_table(smoke_cases, widths=(40, 190, 280)))
    story.append(Spacer(1, 6))
    story.append(card(
        "Test data and cleanup",
        "Replace angle-bracketed IDs with real test-account IDs; never send placeholder text to MCP. Read cases may use an authorized fixture. Run write, dismissal, charter, and restore cases only on disposable data. Drawing deletion is not exposed by the connector; remove temporary drawings in the Scopture application when cleanup is needed.",
        PALE_RED,
    ))
    story.append(PageBreak())

    # Page 3: prompt-driven inspection and compute checks.
    story.extend([
        paragraph("02 / INSPECT & ANALYZE", "Kicker"),
        paragraph("Read, inspect, and compute", "H1x"),
        paragraph("Run these prompts against drawings the test account can access. Compare semantic results rather than literal values because drawing records and timestamps vary between accounts.", "Bodyx"),
        case_table(inspect_cases),
        Spacer(1, 7),
        card(
            "General pass rule",
            "Every reported fact should trace to a tool result or be clearly labeled unavailable. Use the exact IDs returned or supplied for the authorized account. A successful tool response alone is not visual verification when the task asks whether geometry or placement looks right.",
            PALE_BLUE,
        ),
        Spacer(1, 5),
        paragraph("Remote MCP operates on cloud drawings. For local files, use the Scopture desktop CLI. Tool descriptions and input schemas remain the authoritative reference for individual operations.", "Smallx"),
        PageBreak(),
    ])

    # Page 4: writes, exports, and recovery.
    story.extend([
        paragraph("03 / CHANGE & RECOVER", "Kicker"),
        paragraph("Write scenarios and recovery", "H1x"),
        paragraph("Run cases that create or change records only in a disposable test drawing or workspace. Read the current state first, then verify each change from the returned record or a follow-up read.", "Bodyx"),
        case_table(change_cases),
        Spacer(1, 8),
        card(
            "Mutation verification sequence",
            "1. Read the target’s current state.<br/>2. Perform only the requested change on disposable data.<br/>3. Read the affected drawing, issue, charter, or version history again.<br/>4. Capture a screenshot when geometry or placement matters.<br/>5. Record returned IDs and outcomes in the reviewer’s run notes.",
            PALE_BLUE,
        ),
        Spacer(1, 6),
        paragraph("A recoverable version history does not replace a narrowly scoped operation. Restore only a specific version chosen for the test.", "Smallx"),
        PageBreak(),
    ])

    # Page 5: negative prompts and official documentation links.
    story.extend([
        paragraph("04 / BOUNDARIES", "Kicker"),
        paragraph("Safety and scope checks", "H1x"),
        paragraph("These prompts verify that the connector is used only for relevant requests and that access, project data, and user intent stay in bounds.", "Bodyx"),
        case_table(negative_cases, widths=(38, 182, 290)),
        Spacer(1, 7),
        card(
            "Boundary-case acceptance",
            "No unauthorized access, local-file confusion, credential disclosure, hidden instruction following, unsupported deletion, ambiguous write, write-through-read-only query, or partial execution of a compound request. When the assistant refuses or asks for clarification, confirm that no project state changed.",
            PALE_RED,
        ),
        Spacer(1, 7),
    ])

    doc.build(story)
    print(f"Created {output_path} ({output_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
