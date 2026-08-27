"""
Generate Project_Summary.pdf — a faculty-ready summary of the
Smart Wi-Fi Bandwidth Sharing (Game Theory) project.

Run:  python generate_summary_pdf.py
"""

import csv
import os
import traceback
from datetime import date

from fpdf import FPDF, FontFace
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV = os.path.join(BASE_DIR, "data", "experiment_results.csv")
OUTPUT_PDF = os.path.join(BASE_DIR, "Project_Summary.pdf")

NAVY = (26, 26, 46)
TEAL = (0, 150, 136)
BODY_CLR = (35, 35, 45)
MUTED = (100, 100, 110)
BOX_FILL = (236, 240, 248)

FAM = "helvetica"  # replaced by Unicode Arial if available


# ------------------------------------------------------------------
# Fonts
# ------------------------------------------------------------------

def register_fonts(pdf):
    """Register Windows Arial (full Unicode) with fallback to helvetica."""
    global FAM
    fonts_dir = r"C:\Windows\Fonts"
    styles = {"": "arial.ttf", "B": "arialbd.ttf", "I": "ariali.ttf", "BI": "arialbi.ttf"}
    all_found = all(
        os.path.isfile(os.path.join(fonts_dir, fname)) for fname in styles.values()
    )
    if all_found:
        for style, fname in styles.items():
            pdf.add_font("Main", style, os.path.join(fonts_dir, fname))
        FAM = "Main"


# ------------------------------------------------------------------
# PDF helpers
# ------------------------------------------------------------------

class SummaryPDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font(FAM, "I", 8)
        self.set_text_color(*MUTED)
        self.cell(
            0, 8,
            "Smart Wi-Fi Bandwidth Sharing using Game Theory   |   Page %d" % self.page_no(),
            align="C",
        )


def section_title(pdf, num, title):
    pdf.ln(2)
    if pdf.get_y() > 250:
        pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(FAM, "B", 12)
    pdf.cell(0, 8, "  %d.  %s" % (num, title), new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3.5)
    pdf.set_text_color(*BODY_CLR)


def body(pdf, text, size=10.5, style=""):
    pdf.set_font(FAM, style, size)
    pdf.multi_cell(0, 5.6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.6)


def bullet(pdf, text, size=10.5):
    pdf.set_font(FAM, "", size)
    pdf.set_x(pdf.l_margin + 2)
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 2, 5.6, "•  " + text,
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.8)


def formula_box(pdf, lines):
    pdf.set_fill_color(*BOX_FILL)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.35)
    pdf.set_text_color(15, 15, 60)
    x, y = pdf.get_x(), pdf.get_y()
    w = pdf.w - pdf.l_margin - pdf.r_margin
    h = 7.2 * len(lines) + 5
    if y + h > pdf.page_break_trigger:
        pdf.add_page()
        x, y = pdf.get_x(), pdf.get_y()
    pdf.rect(x, y, w, h, style="DF")
    pdf.set_font(FAM, "B", 11)
    pdf.set_xy(x + 4, y + 2.5)
    for line in lines:
        pdf.cell(w - 8, 7.2, line, align="C", new_x="LEFT", new_y="NEXT")
    pdf.set_xy(x, y + h + 3.5)
    pdf.set_text_color(*BODY_CLR)


def styled_table(pdf, headers, rows, col_widths, aligns, font_size=9.5):
    pdf.set_font(FAM, "", font_size)
    head_style = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=NAVY)
    with pdf.table(
        col_widths=col_widths,
        text_align=aligns,
        line_height=5.6,
        padding=1.6,
        headings_style=head_style,
    ) as table:
        hr = table.row()
        for h in headers:
            hr.cell(h)
        for r in rows:
            row = table.row()
            for v in r:
                row.cell(str(v))


def add_image_centered(pdf, path, width_mm, caption):
    if not os.path.isfile(path):
        return
    with Image.open(path) as im:
        w_px, h_px = im.size
    height = width_mm * h_px / w_px
    if pdf.get_y() + height + 14 > pdf.page_break_trigger:
        pdf.add_page()
    y = pdf.get_y()
    pdf.image(path, x=(pdf.w - width_mm) / 2, y=y, w=width_mm)
    pdf.set_y(y + height + 2)
    pdf.set_font(FAM, "I", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, caption, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_text_color(*BODY_CLR)


def qa(pdf, question, answer):
    pdf.set_font(FAM, "B", 10.5)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 5.6, "Q. " + question, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FAM, "", 10.5)
    pdf.set_text_color(*BODY_CLR)
    pdf.set_x(pdf.l_margin + 3)
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 3, 5.6, answer,
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2.2)


# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------

def load_results():
    rows = []
    if os.path.isfile(RESULTS_CSV):
        with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for r in reader:
                if len(r) >= 7:
                    rows.append(r)
    return rows


# ------------------------------------------------------------------
# Build PDF
# ------------------------------------------------------------------

def build():
    pdf = SummaryPDF(orientation="P", unit="mm", format="A4")
    register_fonts(pdf)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 15, 15)
    pdf.set_title("Smart Wi-Fi Bandwidth Sharing using Game Theory — Project Summary")
    pdf.set_author("Sujeetha & Bindu")
    pdf.set_text_color(*BODY_CLR)

    results = load_results()
    today = date.today().strftime("%d %B %Y")

    # ================= COVER =================
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 92, style="F")
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 92, 210, 3, style="F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_y(26)
    pdf.set_font(FAM, "B", 25)
    pdf.cell(0, 12, "Smart Wi-Fi Bandwidth Sharing", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 12, "using Game Theory", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FAM, "", 13)
    pdf.set_y(64)
    pdf.cell(0, 8, "Project Summary  —  Faculty Review Document", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*BODY_CLR)
    pdf.set_y(106)
    pdf.set_font(FAM, "B", 12)
    pdf.cell(0, 7, "Team:  Sujeetha   ·   Bindu", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FAM, "", 10.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 7, "Python  ·  Flask  ·  React  ·  Chart.js  ·  SQLite / MySQL", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Generated: " + today, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*BODY_CLR)
    pdf.set_y(140)
    pdf.set_font(FAM, "B", 12)
    pdf.cell(0, 7, "What's inside", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    contents = [
        "Objective & Problem Statement",
        "Game Theory Model — Players, Strategies, Utility",
        "Nash Equilibrium Algorithm (Best-Response Dynamics)",
        "Fairness — Jain's Fairness Index",
        "System Architecture & Technology Stack",
        "Experimental Results — Table & Graphs",
        "Key Findings & Conclusion",
        "Viva Questions & Answers",
        "How to Run the Demo  ·  Limitations & Future Work",
    ]
    for i, item in enumerate(contents, 1):
        bullet(pdf, "%d.  %s" % (i, item), size=10.5)

    # ================= 1. OBJECTIVE =================
    pdf.add_page()
    section_title(pdf, 1, "Objective")
    body(pdf,
         "This project builds a smart Wi-Fi bandwidth sharing system that treats every connected "
         "user as a player in a non-cooperative congestion game. Instead of splitting bandwidth "
         "equally (which wastes it) or proportionally (which becomes unfair under load), the system "
         "computes a Nash Equilibrium allocation that is simultaneously efficient and fair, and "
         "presents everything on a live web dashboard.")
    bullet(pdf, "Model Wi-Fi users as rational players competing for limited bandwidth")
    bullet(pdf, "Allocate bandwidth using best-response dynamics until a Nash Equilibrium is reached")
    bullet(pdf, "Quantify fairness with Jain's Fairness Index")
    bullet(pdf, "Compare against Equal-Allocation and Proportional-Allocation baselines")
    bullet(pdf, "Deliver a real-time dashboard (Flask + React) for allocations, fairness and analytics")

    # ================= 2. PROBLEM =================
    section_title(pdf, 2, "Problem Statement")
    body(pdf,
         "A single Wi-Fi router has limited bandwidth (e.g., 100 Mbps) shared by many users doing "
         "different activities — browsing, online classes, gaming, streaming and downloads. When "
         "demand exceeds capacity, naive policies fail:")
    bullet(pdf, "Equal splitting wastes bandwidth when demand is low and starves heavy users "
                "(e.g., a live class) when demand is high.")
    bullet(pdf, "Proportional splitting favours heavy requesters, but fairness and user "
                "satisfaction collapse under congestion.")
    body(pdf,
         "The challenge is to allocate bandwidth so that (a) no user can gain by demanding more "
         "(stability), (b) total benefit is high (efficiency), and (c) the distribution is fair "
         "(fairness). Game theory provides a principled way to achieve all three at once.")

    # ================= 3. GAME MODEL =================
    section_title(pdf, 3, "Game Theory Model")
    styled_table(
        pdf,
        ["Concept", "In this project"],
        [
            ["Players", "Each Wi-Fi user (User 1 … User n)"],
            ["Resource", "Total available bandwidth, e.g., 100 Mbps"],
            ["Strategy", "The bandwidth amount a user chooses (0 up to their request)"],
            ["Payoff (Utility)", "Benefit of received bandwidth  −  congestion cost"],
            ["Game type", "Non-cooperative congestion game — my payoff falls as total usage rises"],
        ],
        col_widths=(42, 138),
        aligns=("LEFT", "LEFT"),
    )
    pdf.ln(2)

    # ================= 4. UTILITY =================
    section_title(pdf, 4, "Utility Function (as implemented)")
    formula_box(pdf, [
        "Ui  =  wi · ln(1 + bi)   −   p · bi · ( Σb / B )",
        "Benefit = wi · ln(1 + bi)          Congestion cost = p · bi · (total usage / total bandwidth)",
        "wi = activity weight,  bi = allocated bandwidth,  p = 0.5 (congestion penalty),  B = total bandwidth",
    ])
    pdf.ln(1)
    bullet(pdf, "ln(1 + b) gives diminishing returns — the first few Mbps are the most valuable, "
                "so extra Mbps add less benefit. This discourages hogging.")
    bullet(pdf, "The congestion cost grows as the network gets crowded, so users automatically "
                "demand less under load — the system self-regulates.")
    pdf.ln(1)
    styled_table(
        pdf,
        ["Activity", "Weight (wi)", "Why"],
        [
            ["browsing", "1.0", "Lightest bandwidth need"],
            ["downloading", "1.1", "Tolerant of delay"],
            ["gaming", "1.3", "Needs low latency"],
            ["streaming", "1.4", "Needs steady throughput"],
            ["online_class", "1.5", "Highest priority — real-time and interactive"],
        ],
        col_widths=(45, 30, 105),
        aligns=("LEFT", "CENTER", "LEFT"),
    )

    # ================= 5. NASH =================
    section_title(pdf, 5, "Nash Equilibrium — Best-Response Algorithm")
    body(pdf,
         "A Nash Equilibrium is a set of strategies in which no player can improve their own "
         "utility by unilaterally changing their bandwidth. The system finds an approximate Nash "
         "Equilibrium with iterative best-response dynamics:")
    bullet(pdf, "Step 1 — Start with every user allocated 0 Mbps.")
    bullet(pdf, "Step 2 — Each user computes their Best Response: scan candidate bandwidths in "
                "0.5 Mbps steps (0 up to min(request, remaining bandwidth)) and keep the value "
                "that maximizes their utility given everyone else's current allocations.")
    bullet(pdf, "Step 3 — Repeat for up to 100 rounds; stop when the total change across all "
                "users in a round is below 0.5 Mbps (the state is stable ≈ Nash Equilibrium).")
    bullet(pdf, "Step 4 — Final allocations and utilities are stored and served to the dashboard "
                "through the REST API.")

    # ================= 6. FAIRNESS =================
    section_title(pdf, 6, "Fairness — Jain's Fairness Index")
    formula_box(pdf, [
        "J  =  ( Σxi )²  /  ( n · Σxi² )",
        "xi = bandwidth allocated to user i,   n = number of users",
        "J = 0  →  very unfair          J = 1  →  perfect fairness",
    ])
    pdf.ln(1)
    styled_table(
        pdf,
        ["J value", "Status"],
        [
            ["J ≥ 0.90", "Excellent"],
            ["0.75 – 0.90", "Good"],
            ["0.50 – 0.75", "Moderate"],
            ["J < 0.50", "Poor"],
        ],
        col_widths=(60, 120),
        aligns=("CENTER", "LEFT"),
    )

    # ================= 7. ARCHITECTURE =================
    section_title(pdf, 7, "System Architecture & Technology Stack")
    bullet(pdf, "Backend — Python + Flask REST API (blueprints: auth, bandwidth, network, data); "
                "game_theory engine package (utility, congestion_game, nash_equilibrium, fairness); "
                "service layer (allocation, fairness, evaluation, dataset).")
    bullet(pdf, "Database — SQLite for user accounts + SQL schema (MySQL-ready).")
    bullet(pdf, "Frontend — React (Vite) single-page app: Dashboard, Analytics, Network, Reports, "
                "Users and Dataset pages with Chart.js visualizations.")
    bullet(pdf, "Serving — waitress production WSGI server on port 5000; auto-detected Wi-Fi IP "
                "with QR-code access for phones; one-click START_APP.bat launcher.")
    bullet(pdf, "Dataset — real usage dataset (Cleaned_Dataset.csv) processed into user profiles "
                "for simulation and experiments.")
    pdf.ln(1)
    body(pdf, "Project flow:", style="B")
    body(pdf,
         "User  →  Bandwidth Request  →  Game Theory Engine  →  Best-Response Iterations  →  "
         "Nash Equilibrium  →  Bandwidth Allocation  →  Fairness & Utility Evaluation  →  Dashboard")

    # ================= 8. EXPERIMENTS =================
    section_title(pdf, 8, "Experimental Setup & Results")
    body(pdf,
         "Setup: total bandwidth 100 Mbps; 5 / 10 / 20 / 30 / 50 users with random activities and "
         "requests. Three strategies compared — Equal Allocation, Proportional Allocation and "
         "Game Theory (Nash Equilibrium). Metrics: utilization %, Jain fairness, average utility.")
    pdf.ln(1)
    if results:
        styled_table(
            pdf,
            ["Users", "Strategy", "Allocated (Mbps)", "Utilization %", "Jain Fairness", "Avg Utility"],
            [[r[0], r[1], r[3], r[4], r[5], r[6]] for r in results],
            col_widths=(18, 48, 30, 28, 28, 28),
            aligns=("CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER"),
            font_size=9,
        )

    # ================= 9. GRAPHS =================
    pdf.add_page()
    section_title(pdf, 9, "Results — Graphs")
    add_image_centered(pdf, os.path.join(BASE_DIR, "data", "fairness_vs_users.png"),
                       150, "Jain's Fairness Index vs number of users — Game Theory stays high at every load")
    add_image_centered(pdf, os.path.join(BASE_DIR, "data", "utility_vs_users.png"),
                       150, "Average utility vs number of users — Game Theory keeps users satisfied")
    add_image_centered(pdf, os.path.join(BASE_DIR, "data", "utilization_vs_users.png"),
                       150, "Bandwidth utilization vs number of users")

    # ================= 10. FINDINGS =================
    section_title(pdf, 10, "Key Findings & Conclusion")
    bullet(pdf, "Fairness — Game Theory keeps Jain's index between 0.89 and 0.96 at every load "
                "level, while Proportional drops to about 0.80–0.85 under load.")
    bullet(pdf, "User satisfaction — at 10 users the average utility is +1.11 for Game Theory but "
                "−2.26 for Proportional and −0.82 for Equal: baseline users are congested and "
                "dissatisfied, game-theory users are not.")
    bullet(pdf, "No wasteful over-allocation — at 5 users Game Theory allocates 28.5 Mbps vs "
                "43.5 Mbps for the baselines: giving more than the log-benefit peak only adds "
                "congestion cost without real benefit.")
    bullet(pdf, "Scales gracefully — at 50 users it still achieves 89% utilization with 0.926 "
                "fairness and the highest average utility (0.498).")
    bullet(pdf, "Fairness alone is not enough — Equal allocation scores J = 1.0 at 50 users only "
                "because everyone is equally capped; its utility (0.373) is still below Game "
                "Theory (0.498). Game Theory balances fairness AND utility.")
    pdf.ln(1)
    body(pdf,
         "Conclusion: Nash-equilibrium-based bandwidth allocation is stable, fair and efficient "
         "across all load levels, making it a better default policy for shared Wi-Fi networks "
         "than equal or proportional splitting.", style="B")

    # ================= 11. VIVA Q&A =================
    pdf.add_page()
    section_title(pdf, 11, "Viva Questions & Answers")
    qa(pdf, "Why use Game Theory for Wi-Fi bandwidth sharing?",
       "Users behave selfishly — each wants more bandwidth. Game theory models this competition "
       "mathematically and finds a stable allocation (Nash Equilibrium) where no user benefits by "
       "deviating, balancing individual interest with network efficiency and fairness.")
    qa(pdf, "What type of game is modeled here?",
       "A non-cooperative congestion game: the payoff (utility) of each player decreases as total "
       "usage (congestion) increases, because the congestion cost term grows with Σb/B.")
    qa(pdf, "Who are the players, what are the strategies and payoffs?",
       "Player = each Wi-Fi user; Strategy = the amount of bandwidth the user chooses (0 up to "
       "their request); Payoff = utility = activity-weighted log benefit minus congestion cost.")
    qa(pdf, "Why log(1 + b) in the utility function?",
       "It gives diminishing returns — the first Mbps are the most valuable and extra Mbps add "
       "less benefit. This naturally discourages any single user from hogging bandwidth.")
    qa(pdf, "What is the congestion cost and why include it?",
       "Cost = p · b · (total usage / total bandwidth) with p = 0.5. The more crowded the network, "
       "the higher the penalty on each user's usage — so users automatically reduce demand under "
       "load and the system self-regulates.")
    qa(pdf, "What is a Best Response?",
       "Given the current allocations of all other players, it is the bandwidth value that "
       "maximizes a user's own utility. The code searches candidates in 0.5 Mbps steps up to "
       "min(request, remaining bandwidth).")
    qa(pdf, "What is Nash Equilibrium and how is it found here?",
       "A state where no player can improve their utility by unilaterally changing strategy. It "
       "is approximated by iterative best-response dynamics: every user repeatedly plays their "
       "best response until allocations change by less than 0.5 Mbps in a round (max 100 rounds).")
    qa(pdf, "Why Jain's Fairness Index and what does its value mean?",
       "It is the standard normalized measure of allocation equality: J = (Σxi)²/(n·Σxi²), "
       "ranging 0 (very unfair) to 1 (perfect fairness). Our system reports ≥ 0.90 (Excellent) "
       "at almost all loads.")
    qa(pdf, "What did the experiments show compared to Equal/Proportional allocation?",
       "Game Theory maintained fairness 0.89–0.96 at all loads and kept average utility positive "
       "(e.g., +1.11 at 10 users vs −2.26 for Proportional), while avoiding wasteful "
       "over-allocation at low load and scaling to 50 users with 89% utilization.")
    qa(pdf, "Why does Game Theory allocate LESS bandwidth at low load — isn't that bad?",
       "No — because of diminishing returns (log benefit), extra Mbps beyond the benefit peak add "
       "more congestion cost than benefit. Allocating only 28.5 Mbps instead of 43.5 Mbps keeps "
       "utility highest and leaves headroom for new users.")
    qa(pdf, "What is the tech stack and how does data flow?",
       "Python/Flask REST API + game-theory engine in the backend, React + Chart.js dashboard in "
       "the frontend, SQLite/MySQL for storage. Flow: user request → game engine → best-response "
       "iterations → Nash Equilibrium → allocation + fairness evaluation → dashboard.")
    qa(pdf, "What are the limitations and future improvements?",
       "Current: discrete 0.5 Mbps search step and static activity weights. Future: dynamic "
       "priority weights, pricing/monetary mechanisms, integration with real routers (e.g., "
       "OpenWrt), and ML-based demand prediction.")

    # ================= 12. RUN =================
    section_title(pdf, 12, "How to Run the Demo")
    bullet(pdf, "Double-click START_APP.bat (first run installs dependencies and builds the frontend).")
    bullet(pdf, "On the PC open  http://localhost:5000 ; on phones/laptops on the same Wi-Fi open "
                "http://<wifi-ip>:5000 or scan the QR code shown by the launcher.")
    bullet(pdf, "The Dashboard shows live allocation, fairness gauge and charts; Analytics shows "
                "the strategy comparisons; Users/Dataset pages show the processed dataset.")
    pdf.ln(1)
    body(pdf, "Limitations & Future Work", style="B")
    bullet(pdf, "Discrete 0.5 Mbps search step; static activity weights; simulation-based evaluation.")
    bullet(pdf, "Future: dynamic weights, pricing mechanisms, real-router integration (OpenWrt), "
                "ML-based demand prediction.")

    pdf.output(OUTPUT_PDF)
    return OUTPUT_PDF


if __name__ == "__main__":
    try:
        path = build()
        size_kb = os.path.getsize(path) / 1024
        print("PDF generated successfully:")
        print("  " + path)
        print("  Size: %.1f KB" % size_kb)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)