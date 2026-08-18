from pathlib import Path
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "FIFA_Auction_2026_Rulebook.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4

NAVY = HexColor("#071218")
NAVY_2 = HexColor("#0B1E25")
PANEL = HexColor("#102831")
PANEL_2 = HexColor("#0C222A")
GREEN = HexColor("#42F5A7")
GREEN_DARK = HexColor("#1BCB7B")
CYAN = HexColor("#2AD4FF")
MINT = HexColor("#B8FCE0")
TEXT = HexColor("#F4F8F7")
MUTED = HexColor("#A7BAC0")
LINE = HexColor("#24434C")
AMBER = HexColor("#FFC857")
RED = HexColor("#FF6B6B")


def register_fonts():
    candidates = [
        (
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
        ),
        (
            Path(r"C:\Windows\Fonts\calibri.ttf"),
            Path(r"C:\Windows\Fonts\calibrib.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("Body", str(regular)))
            pdfmetrics.registerFont(TTFont("BodyBold", str(bold)))
            return
    raise RuntimeError("A suitable TrueType font was not found")


register_fonts()

STYLE_BODY = ParagraphStyle(
    "body",
    fontName="Body",
    fontSize=9.4,
    leading=13.2,
    textColor=TEXT,
    spaceAfter=0,
)
STYLE_SMALL = ParagraphStyle(
    "small",
    parent=STYLE_BODY,
    fontSize=8.2,
    leading=11.1,
    textColor=MUTED,
)
STYLE_CARD = ParagraphStyle(
    "card",
    parent=STYLE_BODY,
    fontSize=9.1,
    leading=12.8,
)
STYLE_NOTE = ParagraphStyle(
    "note",
    parent=STYLE_BODY,
    fontSize=9.2,
    leading=13,
)
STYLE_CENTER = ParagraphStyle(
    "center",
    parent=STYLE_BODY,
    alignment=TA_CENTER,
)


def para(c, text, x, y_top, width, style=STYLE_BODY, max_height=200 * mm):
    p = Paragraph(text, style)
    w, h = p.wrap(width, max_height)
    p.drawOn(c, x, y_top - h)
    return h


def rounded_panel(c, x, y, w, h, fill=PANEL, stroke=LINE, radius=5 * mm):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def draw_pitch_motif(c):
    c.saveState()
    c.setStrokeColor(Color(0.16, 0.92, 0.58, alpha=0.11))
    c.setLineWidth(0.7)
    x, y, w, h = 20 * mm, 20 * mm, PAGE_W - 40 * mm, PAGE_H - 40 * mm
    c.roundRect(x, y, w, h, 6 * mm, fill=0, stroke=1)
    c.line(PAGE_W / 2, y, PAGE_W / 2, y + h)
    c.circle(PAGE_W / 2, y + h / 2, 22 * mm, fill=0, stroke=1)
    c.circle(PAGE_W / 2, y + h / 2, 1.3 * mm, fill=0, stroke=1)
    c.rect(x, y + h / 2 - 35 * mm, 20 * mm, 70 * mm, fill=0, stroke=1)
    c.rect(x + w - 20 * mm, y + h / 2 - 35 * mm, 20 * mm, 70 * mm, fill=0, stroke=1)
    c.restoreState()


def draw_bg(c, page_no, label):
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY_2)
    c.setStrokeColor(NAVY_2)
    c.wedge(PAGE_W - 100 * mm, PAGE_H - 92 * mm, PAGE_W + 32 * mm, PAGE_H + 32 * mm, 180, 90, fill=1, stroke=0)
    c.setFillColor(Color(0.06, 0.55, 0.35, alpha=0.10))
    c.circle(PAGE_W - 12 * mm, 34 * mm, 75 * mm, fill=1, stroke=0)
    draw_pitch_motif(c)

    c.setFillColor(GREEN)
    c.rect(0, PAGE_H - 4 * mm, PAGE_W, 4 * mm, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("BodyBold", 7.5)
    c.drawString(16 * mm, 10 * mm, "FIFA AUCTION 2026")
    c.setFillColor(LINE)
    c.rect(16 * mm, 15 * mm, PAGE_W - 32 * mm, 0.35, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Body", 7.5)
    c.drawCentredString(PAGE_W / 2, 10 * mm, label.upper())
    c.drawRightString(PAGE_W - 16 * mm, 10 * mm, f"{page_no:02d} / 03")


def section_heading(c, number, title, x, y):
    c.setFillColor(GREEN)
    c.setFont("BodyBold", 8)
    c.drawString(x, y, f"{number:02d}")
    c.setFillColor(TEXT)
    c.setFont("BodyBold", 15)
    c.drawString(x + 12 * mm, y - 1.1 * mm, title.upper())
    c.setFillColor(GREEN)
    c.rect(x, y - 4 * mm, 20 * mm, 0.8 * mm, fill=1, stroke=0)


def pill(c, text, x, y, w, fill, text_color=NAVY):
    c.setFillColor(fill)
    c.roundRect(x, y, w, 8 * mm, 4 * mm, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont("BodyBold", 7.5)
    c.drawCentredString(x + w / 2, y + 2.7 * mm, text)


def bullet_list(items):
    return "<br/>".join(f"<font color='#42F5A7'>&#8226;</font>&nbsp; {item}" for item in items)


def draw_cover(c):
    draw_bg(c, 1, "Official Rulebook")

    c.setFillColor(GREEN)
    c.setFont("BodyBold", 10)
    c.drawString(17 * mm, PAGE_H - 28 * mm, "THE OFFICIAL GUIDE TO BUILDING A CHAMPION")

    c.setFillColor(TEXT)
    c.setFont("BodyBold", 34)
    c.drawString(17 * mm, PAGE_H - 51 * mm, "FIFA AUCTION")
    c.setFillColor(GREEN)
    c.setFont("BodyBold", 45)
    c.drawString(17 * mm, PAGE_H - 70 * mm, "2026")
    c.setFillColor(TEXT)
    c.setFont("BodyBold", 20)
    c.drawString(17 * mm, PAGE_H - 83 * mm, "RULEBOOK")

    c.setStrokeColor(CYAN)
    c.setLineWidth(1.2)
    c.line(17 * mm, PAGE_H - 91 * mm, 86 * mm, PAGE_H - 91 * mm)
    para(
        c,
        "Build the strongest Best 8, manage a limited purse, create chemistry, and outscore every rival.",
        17 * mm,
        PAGE_H - 98 * mm,
        92 * mm,
        ParagraphStyle("intro", parent=STYLE_BODY, fontSize=11.5, leading=16, textColor=MINT),
    )

    # Decorative football
    bx, by, br = PAGE_W - 43 * mm, PAGE_H - 62 * mm, 23 * mm
    c.setFillColor(Color(0.16, 0.83, 0.66, alpha=0.10))
    c.setStrokeColor(GREEN)
    c.setLineWidth(1.4)
    c.circle(bx, by, br, fill=1, stroke=1)
    c.setFillColor(NAVY_2)
    c.setStrokeColor(GREEN)
    c.setLineWidth(0.8)
    c.circle(bx, by, 7 * mm, fill=1, stroke=1)
    for dx, dy in ((0, 15), (14, 4), (9, -13), (-9, -13), (-14, 4)):
        c.line(bx, by, bx + dx * mm, by + dy * mm)
        c.circle(bx + dx * mm, by + dy * mm, 2.3 * mm, fill=0, stroke=1)

    # Snapshot cards
    y = PAGE_H - 151 * mm
    gap = 5 * mm
    card_w = (PAGE_W - 34 * mm - 2 * gap) / 3
    stats = [
        ("€700M", "STARTING PURSE", GREEN),
        ("20", "TEAMS PER ROOM", CYAN),
        ("BEST 8", "SCORING LINEUP", AMBER),
    ]
    for i, (value, label, color) in enumerate(stats):
        x = 17 * mm + i * (card_w + gap)
        rounded_panel(c, x, y, card_w, 29 * mm, PANEL_2, LINE, 4 * mm)
        c.setFillColor(color)
        c.setFont("BodyBold", 18)
        c.drawCentredString(x + card_w / 2, y + 14 * mm, value)
        c.setFillColor(MUTED)
        c.setFont("BodyBold", 7.2)
        c.drawCentredString(x + card_w / 2, y + 6 * mm, label)

    section_heading(c, 1, "Competition Setup", 17 * mm, PAGE_H - 198 * mm)
    rounded_panel(c, 17 * mm, 36 * mm, PAGE_W - 34 * mm, 53 * mm, PANEL_2, LINE)
    para(
        c,
        bullet_list([
            "Each auction room contains <b>20 independent teams</b>.",
            "Every team receives a starting purse of <b>€700 million</b>.",
            "The player pool contains Goalkeepers, Defenders, Midfielders, and Attackers.",
            "A player's auction score is the total of the <b>three displayed attributes</b>.",
            "All purchases, bonuses, and rankings are calculated separately for each room.",
        ]),
        24 * mm,
        82 * mm,
        PAGE_W - 48 * mm,
        STYLE_CARD,
    )

    pill(c, "BUILD  •  BID  •  BALANCE  •  WIN", 53 * mm, 22 * mm, 104 * mm, GREEN)
    c.showPage()


def draw_auction_page(c):
    draw_bg(c, 2, "Auction and Bidding")
    c.setFillColor(TEXT)
    c.setFont("BodyBold", 25)
    c.drawString(17 * mm, PAGE_H - 28 * mm, "AUCTION & BIDDING")
    c.setFillColor(MUTED)
    c.setFont("Body", 9)
    c.drawString(17 * mm, PAGE_H - 37 * mm, "Every bid is a commitment. Track the purse before raising the paddle.")

    section_heading(c, 2, "Budget and Purchase Rules", 17 * mm, PAGE_H - 55 * mm)
    rounded_panel(c, 17 * mm, PAGE_H - 107 * mm, PAGE_W - 34 * mm, 40 * mm, PANEL_2, LINE)
    para(
        c,
        bullet_list([
            "Bidding begins from the player's announced <b>base price</b>.",
            "A team may not bid more than its <b>remaining purse</b>.",
            "A player becomes <b>SOLD</b> when the auctioneer closes the highest valid bid.",
            "A player receiving no valid bid is marked <b>UNSOLD</b> and may be returned to the pool by the organizers.",
        ]),
        24 * mm,
        PAGE_H - 74 * mm,
        PAGE_W - 48 * mm,
        STYLE_CARD,
    )

    section_heading(c, 3, "Bid Increments", 17 * mm, PAGE_H - 122 * mm)
    data = [
        ["CURRENT BID", "NEXT VALID INCREMENT"],
        ["€5M to below €20M", "+ €1M"],
        ["€20M to €50M", "+ €2.5M"],
        ["Above €50M", "+ €5M"],
    ]
    table = Table(data, colWidths=[91 * mm, 72 * mm], rowHeights=[10 * mm, 11 * mm, 11 * mm, 11 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("FONTNAME", (0, 0), (-1, 0), "BodyBold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Body"),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
        ("BACKGROUND", (0, 1), (-1, -1), PANEL_2),
        ("GRID", (0, 0), (-1, -1), 0.7, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    table.wrapOn(c, 163 * mm, 50 * mm)
    table.drawOn(c, 23 * mm, PAGE_H - 180 * mm)
    para(
        c,
        "<b>Boundary rule:</b> once the current bid reaches €20M, the €2.5M increment applies. The €5M increment applies only after the current bid moves above €50M.",
        23 * mm,
        PAGE_H - 184 * mm,
        163 * mm,
        STYLE_SMALL,
    )

    # Mystery and captain side-by-side
    left_x, right_x = 17 * mm, 107 * mm
    y, h, w = 32 * mm, 61 * mm, 86 * mm
    rounded_panel(c, left_x, y, w, h, PANEL, GREEN, 5 * mm)
    c.setFillColor(GREEN)
    c.setFont("BodyBold", 9)
    c.drawString(left_x + 7 * mm, y + h - 10 * mm, "MYSTERY PLAYER RULE")
    c.setFillColor(Color(0.25, 0.96, 0.65, alpha=0.13))
    c.circle(left_x + w - 14 * mm, y + h - 13 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont("BodyBold", 16)
    c.drawCentredString(left_x + w - 14 * mm, y + h - 16 * mm, "?")
    para(
        c,
        "The base price of every Mystery Player <b>may or may not be the same</b>. Mystery Players are auctioned normally, like any other football player. The player's identity and complete statistics remain hidden and are revealed <b>only after a team purchases the player</b>.",
        left_x + 7 * mm,
        y + h - 18 * mm,
        w - 14 * mm,
        STYLE_NOTE,
    )

    rounded_panel(c, right_x, y, w, h, PANEL, AMBER, 5 * mm)
    c.setFillColor(AMBER)
    c.setFont("BodyBold", 9)
    c.drawString(right_x + 7 * mm, y + h - 10 * mm, "CAPTAIN NOTE")
    c.setFont("BodyBold", 22)
    c.drawRightString(right_x + w - 7 * mm, y + h - 13 * mm, "2X")
    para(
        c,
        "Assign <b>one Captain</b> from your team's Best 8. The Captain's player score counts twice, meaning the team receives an additional bonus equal to the Captain's full three-attribute score.",
        right_x + 7 * mm,
        y + h - 20 * mm,
        w - 14 * mm,
        STYLE_NOTE,
    )
    c.showPage()


def formation_box(c, x, y, w, pos, count, color):
    rounded_panel(c, x, y, w, 26 * mm, PANEL_2, LINE, 4 * mm)
    c.setFillColor(color)
    c.setFont("BodyBold", 17)
    c.drawString(x + 6 * mm, y + 13 * mm, pos)
    c.setFillColor(TEXT)
    c.setFont("BodyBold", 16)
    c.drawRightString(x + w - 6 * mm, y + 13 * mm, str(count))
    c.setFillColor(MUTED)
    c.setFont("Body", 7.2)
    c.drawString(x + 6 * mm, y + 6 * mm, "REQUIRED IN BEST 8")


def draw_scoring_page(c):
    draw_bg(c, 3, "Formation and Scoring")
    c.setFillColor(TEXT)
    c.setFont("BodyBold", 25)
    c.drawString(17 * mm, PAGE_H - 28 * mm, "FORMATION & SCORING")
    c.setFillColor(MUTED)
    c.setFont("Body", 9)
    c.drawString(17 * mm, PAGE_H - 37 * mm, "Qualification comes first. Only the strongest valid lineup drives the result.")

    section_heading(c, 4, "Required Best 8", 17 * mm, PAGE_H - 55 * mm)
    gap = 4 * mm
    box_w = (PAGE_W - 34 * mm - 3 * gap) / 4
    y = PAGE_H - 98 * mm
    for i, (pos, count, color) in enumerate((("GK", 1, AMBER), ("DEF", 3, CYAN), ("MID", 2, GREEN), ("ATT", 2, RED))):
        formation_box(c, 17 * mm + i * (box_w + gap), y, box_w, pos, count, color)

    para(
        c,
        "A team qualifies with at least <b>1 Goalkeeper, 3 Defenders, 2 Midfielders, and 2 Attackers</b>. Extra purchases are allowed, but only the highest-scoring players filling these eight positional slots enter the Best 8. All other owned players remain on the bench.",
        17 * mm,
        PAGE_H - 104 * mm,
        PAGE_W - 34 * mm,
        STYLE_CARD,
    )

    section_heading(c, 5, "Score Calculation", 17 * mm, PAGE_H - 134 * mm)
    rounded_panel(c, 17 * mm, PAGE_H - 180 * mm, PAGE_W - 34 * mm, 34 * mm, PANEL, GREEN)
    c.setFillColor(MUTED)
    c.setFont("BodyBold", 7.5)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 157 * mm, "CHAMPIONSHIP FORMULA")
    c.setFillColor(TEXT)
    c.setFont("BodyBold", 13)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 169 * mm, "FINAL = BEST 8 + CAPTAIN + NATIONALITY + CLUB")

    # Bonus cards
    bonus_y, bonus_h = PAGE_H - 217 * mm, 32 * mm
    bonus_w = (PAGE_W - 39 * mm) / 2
    rounded_panel(c, 17 * mm, bonus_y, bonus_w, bonus_h, PANEL_2, CYAN)
    c.setFillColor(CYAN)
    c.setFont("BodyBold", 9)
    c.drawString(24 * mm, bonus_y + bonus_h - 10 * mm, "NATIONALITY CHEMISTRY")
    para(
        c,
        "When at least two Best 8 players share a nationality, that group earns <b>10 points per player</b>. Every qualifying nationality group stacks.",
        24 * mm,
        bonus_y + bonus_h - 15 * mm,
        bonus_w - 14 * mm,
        STYLE_SMALL,
    )

    rx = 22 * mm + bonus_w
    rounded_panel(c, rx, bonus_y, bonus_w, bonus_h, PANEL_2, GREEN)
    c.setFillColor(GREEN)
    c.setFont("BodyBold", 9)
    c.drawString(rx + 7 * mm, bonus_y + bonus_h - 10 * mm, "CLUB CHEMISTRY")
    para(
        c,
        "When at least two Best 8 players share a club, that group earns <b>5 points per player</b>. Every qualifying club group stacks.",
        rx + 7 * mm,
        bonus_y + bonus_h - 15 * mm,
        bonus_w - 14 * mm,
        STYLE_SMALL,
    )

    # Disqualification and conduct rules
    disq_y, disq_h = 20 * mm, 56 * mm
    rounded_panel(c, 17 * mm, disq_y, PAGE_W - 34 * mm, disq_h, PANEL_2, RED)
    c.setFillColor(RED)
    c.setFont("BodyBold", 10)
    c.drawString(24 * mm, disq_y + disq_h - 9 * mm, "DISQUALIFICATION & CONDUCT")

    disq_style = ParagraphStyle(
        "disq",
        parent=STYLE_SMALL,
        fontSize=6.5,
        leading=7.7,
        textColor=TEXT,
    )
    left_rules = bullet_list([
        "Any team that fails to form a squad of <b>8 players</b> will be disqualified.",
        "After forming its squad, each team must submit its <b>final Best 8</b>. Failure to submit will lead to disqualification.",
        "If anyone other than the <b>Team Leader</b> is found bidding more than three times, the team will be disqualified.",
        "Any team that does not follow the required <b>team composition</b> will be disqualified.",
    ])
    right_rules = bullet_list([
        "Physical or verbal indiscipline between teams or toward the organizing team will lead to disqualification.",
        "Any kind of <b>foul play</b> will not be tolerated.",
        "Inappropriate or disrespectful behavior may result in removal from the event.",
        "If a team's <b>purse money is exhausted</b> and it continues bidding, the team will be immediately disqualified.",
    ])
    column_top = disq_y + disq_h - 14 * mm
    para(c, left_rules, 24 * mm, column_top, 76 * mm, disq_style)
    para(c, right_rules, 109 * mm, column_top, 76 * mm, disq_style)

    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(24 * mm, disq_y + 10 * mm, PAGE_W - 24 * mm, disq_y + 10 * mm)
    c.setFillColor(AMBER)
    c.setFont("BodyBold", 6.5)
    c.drawString(24 * mm, disq_y + 5 * mm, "RULE UPDATE NOTE")
    c.setFillColor(MUTED)
    c.setFont("Body", 6.5)
    c.drawString(
        51 * mm,
        disq_y + 5 * mm,
        "Any modification will be communicated to all participants before the event begins.",
    )
    c.showPage()


def build():
    c = canvas.Canvas(str(OUTPUT), pagesize=A4, pageCompression=1)
    c.setTitle("FIFA Auction 2026 - Official Rulebook")
    c.setAuthor("FIFA Auction 2026 Organizing Team")
    c.setSubject("Auction, bidding, formation, scoring, and leaderboard rules")
    draw_cover(c)
    draw_auction_page(c)
    draw_scoring_page(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
