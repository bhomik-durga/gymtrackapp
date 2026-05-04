"""
GymTracker
Colour theme: coolors.co/palette/dcdcdd-c5c3c6-46494c-4c5c68-1985a1
Stores data : ~/Desktop/gym_workouts.csv

Install : pip install pandas matplotlib reportlab
Run     : python gym_tracker.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime, date
import os, pathlib, re, tempfile, io

# ReportLab — PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage,
)
from reportlab.platypus.flowables import KeepTogether

# ──────────────────────────────────────────────────────────
#  DATA FILE
# ──────────────────────────────────────────────────────────
DATA_FILE = os.path.join(pathlib.Path.home(), "Desktop", "gym_workouts.csv")

# ──────────────────────────────────────────────────────────
#  COLOUR PALETTE  — coolors.co/palette/dcdcdd-c5c3c6-46494c-4c5c68-1985a1
# ──────────────────────────────────────────────────────────
BG        = "#DCDCDD"   # light silver        — page / root bg
SIDEBAR   = "#46494C"   # dark charcoal       — sidebar fill
SURFACE   = "#FFFFFF"   # white               — card surfaces
SURFACE2  = "#EEECED"   # very light silver   — alt rows / inset bg
BORDER    = "#C5C3C6"   # medium silver       — borders / dividers

TEXT      = "#2B2C2E"   # near-black          — primary text (light bg)
TEXT_SIDE = "#DCDCDD"   # pale silver         — text on dark sidebar
TEXT2     = "#4C5C68"   # slate               — muted / secondary text
TEXT_MUT  = "#8A9BAA"   # lighter slate       — placeholder / labels

ACCENT    = "#1985A1"   # teal blue           — primary action colour
ACCENT_DK = "#116B82"   # darker teal         — hover state
ACCENT_LT = "#D0EEF4"   # pale teal           — badge / selected tint

SLATE     = "#4C5C68"   # slate               — secondary button fill
SLATE_DK  = "#3A4A55"   # dark slate          — secondary hover

SUCCESS   = "#1985A1"   # teal  — save / ok messages
WARNING   = "#9B6B1A"   # amber — personal best
WARN_BG   = "#FEF4DC"   # light amber bg
DANGER    = "#9B2B2B"   # red   — delete / errors
DANGER_BG = "#FDEAEA"   # light red bg

# Chart colours — distinct, readable on white
CHART_COLS = [
    "#1985A1",  # teal
    "#E07B39",  # orange
    "#6B4FA0",  # purple
    "#2E8B57",  # green
    "#C0392B",  # red
    "#4C5C68",  # slate
    "#1A6B8A",  # dark teal
    "#8B6914",  # amber
]

FN = "Helvetica"
def fnt(size, weight="normal"):
    return (FN, size, weight)

# ──────────────────────────────────────────────────────────
DEFAULT_EXERCISES = [
    # CHEST
    "Machine Chest Press", "Flat Dumbbell Press", "Incline Press",
    "Chest Fly", "Bench Press",
    # SHOULDER
    "Dumbbell Press", "Overhead Press", "Machine Overhead Press",
    "Cable Lateral Raises", "Dumbbell Lateral Raises", "Face Pull",
    # TRICEP
    "Tricep Pushdown", "Tricep Overhead Extension", "Skull Crusher",
    # BACK
    "Pull Ups", "Pulldown", "Rowing", "T-Bar Row",
    # BICEP
    "Incline Bench Curl", "Hammer Curl", "Preacher Curl",
    # LEGS
    "Squats", "Leg Press", "Extension", "Hamstring Curl",
    # CORE
    "Push Ups", "Plank",
]

# ── Muscle-group mapping ───────────────────────────────────
MUSCLE_MAP = {
    "Machine Chest Press":      "Chest",
    "Flat Dumbbell Press":      "Chest",
    "Incline Press":            "Chest",
    "Chest Fly":                "Chest",
    "Bench Press":              "Chest",
    "Dumbbell Press":           "Shoulders",
    "Overhead Press":           "Shoulders",
    "Machine Overhead Press":   "Shoulders",
    "Cable Lateral Raises":     "Shoulders",
    "Dumbbell Lateral Raises":  "Shoulders",
    "Face Pull":                "Shoulders",
    "Tricep Pushdown":          "Triceps",
    "Tricep Overhead Extension":"Triceps",
    "Skull Crusher":            "Triceps",
    "Pull Ups":                 "Back",
    "Pulldown":                 "Back",
    "Rowing":                   "Back",
    "T-Bar Row":                "Back",
    "Incline Bench Curl":       "Biceps",
    "Hammer Curl":              "Biceps",
    "Preacher Curl":            "Biceps",
    "Squats":                   "Legs",
    "Leg Press":                "Legs",
    "Extension":                "Legs",
    "Hamstring Curl":           "Legs",
    "Push Ups":                 "Core",
    "Plank":                    "Core",
}

def epley_1rm(weight: float, reps: int) -> float:
    """Epley formula: 1RM = weight × (1 + reps / 30)"""
    if reps == 1:
        return float(weight)
    return weight * (1 + reps / 30)


# ══════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════
class WorkoutData:
    COLS = ["date", "exercise", "sets", "reps", "weight"]

    def __init__(self, path=DATA_FILE):
        self.path = path
        self._init_file()

    def _init_file(self):
        p = pathlib.Path(self.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            pd.DataFrame(columns=self.COLS).to_csv(self.path, index=False)

    def load(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.path)
            for col in self.COLS:
                if col not in df.columns:
                    df[col] = None
            df["date"]   = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
            df["sets"]   = pd.to_numeric(df["sets"],   errors="coerce").fillna(0).astype(int)
            df["reps"]   = pd.to_numeric(df["reps"],   errors="coerce").fillna(0).astype(int)
            df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0.0)
            df = df[df["date"].notna()]
            return df.sort_values("date", ascending=False).reset_index(drop=True)
        except Exception as e:
            print("LOAD ERROR:", e)
            return pd.DataFrame(columns=self.COLS)

    def add(self, date_str, exercise, sets, reps, weight) -> bool:
        try:
            new = pd.DataFrame([{
                "date":     pd.to_datetime(date_str).strftime("%Y-%m-%d"),
                "exercise": exercise,
                "sets":     sets,
                "reps":     reps,
                "weight":   weight,
            }])
            file_exists = os.path.exists(self.path)
            new.to_csv(self.path, mode="a", header=not file_exists, index=False)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def delete_row(self, date_str, exercise, sets, reps, weight):
        df = self.load()
        df = df[~(
            (df["date"].dt.strftime("%Y-%m-%d") == date_str) &
            (df["exercise"] == exercise) &
            (df["sets"]   == int(sets))  &
            (df["reps"]   == int(reps))  &
            (df["weight"] == float(weight))
        )]
        df.to_csv(self.path, index=False, date_format="%Y-%m-%d")

    def exercises(self):
        logged = self.load()["exercise"].dropna().unique().tolist()
        return sorted(set(DEFAULT_EXERCISES) | set(logged))

    def personal_bests(self):
        df = self.load()
        return {} if df.empty else df.groupby("exercise")["weight"].max().to_dict()

    def weekly_summary(self):
        df = self.load()
        if df.empty:
            return pd.DataFrame()
        df["volume"] = df["sets"] * df["reps"] * df["weight"]
        df["week"]   = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
        return df.groupby("week").agg(
            sessions=("exercise", "count"), volume=("volume", "sum")
        ).reset_index().tail(10)

    def between(self, start: date, end: date):
        df = self.load()
        if df.empty:
            return df
        return df[(df["date"].dt.date >= start) &
                  (df["date"].dt.date <= end)].reset_index(drop=True)

    def muscle_volume(self):
        """Return dict {muscle_group: total_volume} for the balance chart."""
        df = self.load()
        if df.empty:
            return {}
        df["volume"] = df["sets"] * df["reps"] * df["weight"]
        df["muscle"] = df["exercise"].map(MUSCLE_MAP).fillna("Other")
        return df.groupby("muscle")["volume"].sum().to_dict()

    def change_path(self, new_path):
        self.path = new_path
        self._init_file()


# ══════════════════════════════════════════════════════════
#  PDF EXPORT ENGINE
# ══════════════════════════════════════════════════════════

# Hex → reportlab Color
def _rl(hex_str):
    h = hex_str.lstrip("#")
    return colors.HexColor(f"#{h}")

class PdfExporter:
    """
    Builds a print-ready PDF workout report using ReportLab.

    Sections:
      1. Cover / header
      2. Personal Bests table
      3. Weekly Volume table
      4. Full workout log table (paginated)
      5. Progress chart image (matplotlib figure exported to PNG bytes)
    """

    # Palette matched to app colours
    C_TEAL     = _rl("#1985A1")
    C_SLATE    = _rl("#4C5C68")
    C_SILVER   = _rl("#DCDCDD")
    C_MID      = _rl("#C5C3C6")
    C_CHARCOAL = _rl("#46494C")
    C_WHITE    = colors.white
    C_BLACK    = _rl("#2B2C2E")
    C_AMBER_BG = _rl("#FEF4DC")
    C_AMBER    = _rl("#9B6B1A")

    PAGE_W, PAGE_H = A4

    def __init__(self, db: "WorkoutData"):
        self.db = db

    # ── Public entry point ──────────────────────────────
    def export(self, out_path: str, fig=None,
               date_from: date = None, date_to: date = None):
        """
        Generate the PDF at `out_path`.
        fig  — optional matplotlib Figure to embed as a chart image.
        """
        date_from = date_from or date(2000, 1, 1)
        date_to   = date_to   or date.today()

        df = self.db.between(date_from, date_to)
        df_all = df.copy()
        df_all["volume"] = df_all["sets"] * df_all["reps"] * df_all["weight"]

        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
            title="GymTracker Report",
            author="GymTracker",
        )

        styles = self._styles()
        story  = []

        # ── Cover banner ──────────────────────────────
        story += self._cover(styles, date_from, date_to, len(df_all))

        # ── Personal Bests ────────────────────────────
        pbs = self.db.personal_bests()
        if pbs:
            story += self._section_header("🏆  Personal Bests", styles)
            story.append(self._pb_table(pbs))
            story.append(Spacer(1, 0.5*cm))

        # ── Weekly Volume ─────────────────────────────
        weekly = self.db.weekly_summary()
        if not weekly.empty:
            story += self._section_header("📅  Weekly Volume (Last 10 Weeks)", styles)
            story.append(self._weekly_table(weekly, styles))
            story.append(Spacer(1, 0.5*cm))

        # ── Progress chart ────────────────────────────
        if fig is not None:
            story += self._section_header("📈  Progress Chart", styles)
            story.append(self._chart_image(fig))
            story.append(Spacer(1, 0.5*cm))

        # ── Full workout log ──────────────────────────
        if not df_all.empty:
            story.append(PageBreak())
            story += self._section_header("📋  Workout Log", styles)
            story.append(Paragraph(
                f"Showing {len(df_all)} entries from "
                f"{date_from.strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')}",
                styles["sub"]
            ))
            story.append(Spacer(1, 0.3*cm))
            story.append(self._log_table(df_all, styles))

        # ── Footer note ───────────────────────────────
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                 color=self.C_MID, spaceAfter=6))
        story.append(Paragraph(
            f"Generated by GymTracker  •  {datetime.now().strftime('%d %b %Y, %H:%M')}",
            styles["footer"]
        ))

        doc.build(story)

    # ── Styles ──────────────────────────────────────────
    def _styles(self):
        base = getSampleStyleSheet()
        def S(name, **kw):
            return ParagraphStyle(name, **kw)

        return {
            "title":   S("gt_title",
                          fontSize=26, leading=30, textColor=self.C_TEAL,
                          fontName="Helvetica-Bold", spaceAfter=4),
            "subtitle":S("gt_subtitle",
                          fontSize=11, textColor=self.C_SLATE,
                          fontName="Helvetica", spaceAfter=2),
            "section": S("gt_section",
                          fontSize=13, leading=16, textColor=self.C_CHARCOAL,
                          fontName="Helvetica-Bold",
                          spaceBefore=14, spaceAfter=6),
            "sub":     S("gt_sub",
                          fontSize=9, textColor=self.C_SLATE,
                          fontName="Helvetica", spaceAfter=4),
            "footer":  S("gt_footer",
                          fontSize=8, textColor=self.C_MID,
                          fontName="Helvetica", alignment=TA_CENTER),
            "cell":    S("gt_cell",
                          fontSize=9, fontName="Helvetica",
                          textColor=self.C_BLACK),
            "cell_bold":S("gt_cellb",
                           fontSize=9, fontName="Helvetica-Bold",
                           textColor=self.C_BLACK),
        }

    # ── Cover section ────────────────────────────────────
    def _cover(self, styles, d_from, d_to, count):
        elems = []

        # Teal banner rectangle via a 1-row table
        banner_data = [[Paragraph(
            '<font color="white"><b>💪  GymTracker — Workout Report</b></font>',
            ParagraphStyle("banner", fontSize=18, fontName="Helvetica-Bold",
                           textColor=colors.white)
        )]]
        banner = Table(banner_data,
                       colWidths=[self.PAGE_W - 4*cm],
                       rowHeights=[1.4*cm])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), self.C_TEAL),
            ("LEFTPADDING",  (0,0), (-1,-1), 16),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ROWBORDERPADDING", (0,0), (-1,-1), 0),
        ]))
        elems.append(banner)
        elems.append(Spacer(1, 0.4*cm))

        elems.append(Paragraph(
            f"Period: {d_from.strftime('%d %b %Y')}  →  {d_to.strftime('%d %b %Y')}",
            styles["subtitle"]
        ))
        elems.append(Paragraph(
            f"Total entries: {count}",
            styles["subtitle"]
        ))
        elems.append(Spacer(1, 0.6*cm))
        elems.append(HRFlowable(width="100%", thickness=1,
                                 color=self.C_TEAL, spaceAfter=10))
        return elems

    # ── Section header ───────────────────────────────────
    def _section_header(self, title, styles):
        return [
            Paragraph(title, styles["section"]),
            HRFlowable(width="100%", thickness=0.5,
                        color=self.C_MID, spaceAfter=6),
        ]

    # ── Personal Bests table ─────────────────────────────
    def _pb_table(self, pbs):
        rows = [["Exercise", "Best Weight (kg)"]]
        for ex, wgt in sorted(pbs.items()):
            rows.append([ex, f"{wgt:.1f}"])

        col_w = [11*cm, 5*cm]
        t = Table(rows, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",   (0,0), (-1,0), self.C_CHARCOAL),
            ("TEXTCOLOR",    (0,0), (-1,0), self.C_WHITE),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 9),
            ("BOTTOMPADDING",(0,0), (-1,0), 7),
            ("TOPPADDING",   (0,0), (-1,0), 7),
            # Data rows
            ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",     (0,1), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[self.C_WHITE, self.C_SILVER]),
            ("TOPPADDING",   (0,1), (-1,-1), 5),
            ("BOTTOMPADDING",(0,1), (-1,-1), 5),
            ("LEFTPADDING",  (0,0), (-1,-1), 8),
            # PB weight column: teal + bold
            ("TEXTCOLOR",    (1,1), (1,-1), self.C_TEAL),
            ("FONTNAME",     (1,1), (1,-1), "Helvetica-Bold"),
            ("ALIGN",        (1,0), (1,-1), "CENTER"),
            # Grid
            ("LINEBELOW",    (0,0), (-1,-1), 0.3, self.C_MID),
            ("BOX",          (0,0), (-1,-1), 0.5, self.C_MID),
        ]))
        return t

    # ── Weekly volume table ──────────────────────────────
    def _weekly_table(self, summary, styles):
        rows = [["Week", "Sessions", "Total Volume (kg)"]]
        for _, r in summary.iterrows():
            rows.append([
                r["week"].strftime("%d %b %Y"),
                str(int(r["sessions"])),
                f'{r["volume"]:,.0f}',
            ])

        col_w = [7*cm, 4*cm, 5*cm]
        t = Table(rows, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), self.C_SLATE),
            ("TEXTCOLOR",     (0,0), (-1,0), self.C_WHITE),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("BOTTOMPADDING", (0,0), (-1,0), 7),
            ("TOPPADDING",    (0,0), (-1,0), 7),
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,1), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[self.C_WHITE, self.C_SILVER]),
            ("TOPPADDING",    (0,1), (-1,-1), 5),
            ("BOTTOMPADDING", (0,1), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("ALIGN",         (1,0), (2,-1), "CENTER"),
            ("LINEBELOW",     (0,0), (-1,-1), 0.3, self.C_MID),
            ("BOX",           (0,0), (-1,-1), 0.5, self.C_MID),
        ]))
        return t

    # ── Full log table ───────────────────────────────────
    def _log_table(self, df, styles):
        pbs = self.db.personal_bests()
        headers = ["Date", "Exercise", "Sets", "Reps", "Weight (kg)", "Volume"]
        rows = [headers]

        for _, r in df.sort_values("date").iterrows():
            vol = int(r["sets"]) * int(r["reps"]) * r["weight"]
            rows.append([
                r["date"].strftime("%d %b %Y"),
                str(r["exercise"]),
                str(int(r["sets"])),
                str(int(r["reps"])),
                f'{r["weight"]:.1f}',
                f'{vol:.0f}',
            ])

        col_w = [3*cm, 5.5*cm, 1.8*cm, 1.8*cm, 2.6*cm, 2.3*cm]
        t = Table(rows, colWidths=col_w, repeatRows=1)

        style_cmds = [
            # Header
            ("BACKGROUND",    (0,0), (-1,0), self.C_CHARCOAL),
            ("TEXTCOLOR",     (0,0), (-1,0), self.C_WHITE),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("ALIGN",         (0,0), (-1,0), "CENTER"),
            ("TOPPADDING",    (0,0), (-1,0), 7),
            ("BOTTOMPADDING", (0,0), (-1,0), 7),
            # Data
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,1), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [self.C_WHITE, self.C_SILVER]),
            ("TOPPADDING",    (0,1), (-1,-1), 4),
            ("BOTTOMPADDING", (0,1), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("ALIGN",         (2,1), (-1,-1), "CENTER"),
            ("LINEBELOW",     (0,0), (-1,-1), 0.25, self.C_MID),
            ("BOX",           (0,0), (-1,-1), 0.5, self.C_MID),
        ]

        # Highlight PB rows in amber
        for i, (_, r) in enumerate(df.sort_values("date").iterrows(), start=1):
            if pbs.get(r["exercise"]) == r["weight"]:
                style_cmds += [
                    ("BACKGROUND", (0,i), (-1,i), self.C_AMBER_BG),
                    ("TEXTCOLOR",  (4,i), (4,i),  self.C_AMBER),
                    ("FONTNAME",   (4,i), (4,i),  "Helvetica-Bold"),
                ]

        t.setStyle(TableStyle(style_cmds))
        return t

    # ── Chart image ──────────────────────────────────────
    def _chart_image(self, fig):
        """Render matplotlib figure to PNG bytes and return ReportLab Image."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        buf.seek(0)
        img = RLImage(buf, width=16*cm, height=8*cm)
        img.hAlign = "CENTER"
        return img


# ══════════════════════════════════════════════════════════
#  REUSABLE WIDGETS
# ══════════════════════════════════════════════════════════

def Divider(parent, padx=0):
    f = tk.Frame(parent, bg=BORDER, height=1)
    if padx:
        f.pack(fill="x", padx=padx)
    return f


class FormField(tk.Frame):
    """Stacked micro-label + text entry."""
    def __init__(self, parent, label, var, width=20, bg=SURFACE, **kw):
        super().__init__(parent, bg=bg)
        tk.Label(self, text=label.upper(), font=fnt(8),
                 fg=TEXT_MUT, bg=bg).pack(anchor="w")
        tk.Frame(self, height=3, bg=bg).pack()
        self.entry = tk.Entry(
            self, textvariable=var, width=width,
            font=fnt(12), bg=SURFACE2, fg=TEXT,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            insertbackground=ACCENT,
            selectbackground=ACCENT_LT,
            selectforeground=TEXT,
        )
        self.entry.pack(fill="x", ipady=7)


class ComboField(tk.Frame):
    """Stacked micro-label + combobox."""
    def __init__(self, parent, label, var, values, width=24,
                 editable=False, bg=SURFACE, **kw):
        super().__init__(parent, bg=bg)
        tk.Label(self, text=label.upper(), font=fnt(8),
                 fg=TEXT_MUT, bg=bg).pack(anchor="w")
        tk.Frame(self, height=3, bg=bg).pack()
        state = "normal" if editable else "readonly"
        self.combo = ttk.Combobox(
            self, textvariable=var, values=values,
            width=width, font=fnt(12),
            style="App.TCombobox", state=state,
        )
        self.combo.pack(fill="x", ipady=4)


class Btn(tk.Button):
    """
    style=  "primary"   teal fill, white text      — main actions
            "secondary" slate fill, white text     — neutral actions
            "danger"    red-tinted bg, red text    — destructive
            "ghost"     page bg, muted text        — low-emphasis
    Back-compat: primary=False maps to "secondary".
    """
    _P = {
        "primary":   (ACCENT,     "#FFFFFF", ACCENT_DK, "#FFFFFF"),
        "secondary": (SLATE,      "#FFFFFF", SLATE_DK,  "#FFFFFF"),
        "danger":    (DANGER_BG,  DANGER,    "#F5CACA", DANGER),
        "ghost":     (BG,         TEXT2,     SURFACE2,  TEXT2),
    }
    def __init__(self, parent, text, cmd, primary=True, small=False,
                 style=None, **kw):
        if style is None:
            style = "primary" if primary else "secondary"
        bg, fg, abg, afg = self._P.get(style, self._P["primary"])
        sz = 10 if small else 12
        super().__init__(
            parent, text=text, command=cmd,
            font=fnt(sz, "bold"), bg=bg, fg=fg,
            activebackground=abg, activeforeground=afg,
            relief="flat", cursor="hand2",
            padx=16, pady=7 if small else 10, bd=0, **kw
        )


# ══════════════════════════════════════════════════════════
#  APPLICATION
# ══════════════════════════════════════════════════════════
class App:
    def __init__(self):
        self.db       = WorkoutData()
        self.exporter = PdfExporter(self.db)

        self.root = tk.Tk()
        self.root.title("GymTracker")
        self.root.geometry("1060x700")
        self.root.minsize(860, 580)
        self.root.configure(bg=BG)
        self._styles()
        self._build()
        self.refresh_history()

    # ── TTK styles ────────────────────────────────────────
    def _styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Treeview
        s.configure("App.Treeview",
                    background=SURFACE, foreground=TEXT,
                    fieldbackground=SURFACE, font=fnt(11),
                    rowheight=32, borderwidth=0, relief="flat")
        s.configure("App.Treeview.Heading",
                    background=SURFACE2, foreground=SLATE,
                    font=fnt(9, "bold"), relief="flat", padding=[8, 6])
        s.map("App.Treeview",
              background=[("selected", ACCENT_LT)],
              foreground=[("selected", ACCENT_DK)])

        # Scrollbar
        s.configure("App.Vertical.TScrollbar",
                    background=SURFACE2, troughcolor=BG,
                    arrowcolor=SLATE, bordercolor=BG, relief="flat")

        # Combobox
        s.configure("App.TCombobox",
                    fieldbackground=SURFACE2, background=SURFACE2,
                    foreground=TEXT, arrowcolor=SLATE,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    selectbackground=ACCENT_LT, selectforeground=TEXT)
        s.map("App.TCombobox",
              fieldbackground=[("readonly", SURFACE2)],
              foreground=[("readonly", TEXT)],
              arrowcolor=[("readonly", SLATE)])

    # ── Root layout ───────────────────────────────────────
    def _build(self):
        self._sidebar = tk.Frame(self.root, bg=SIDEBAR, width=205)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        self._content = tk.Frame(self.root, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_pages()
        self._show_page("log")

    # ── Sidebar ───────────────────────────────────────────
    def _build_sidebar(self):
        sb = self._sidebar

        # ── Logo ──
        logo = tk.Frame(sb, bg=SIDEBAR, pady=22)
        logo.pack(fill="x")
        tk.Label(logo, text="💪", font=fnt(26), bg=SIDEBAR).pack()
        tk.Label(logo, text="GymTracker", font=fnt(15, "bold"),
                 fg=TEXT_SIDE, bg=SIDEBAR).pack(pady=(4, 1))
        tk.Label(logo, text="Workout Logger", font=fnt(9),
                 fg=TEXT2, bg=SIDEBAR).pack()

        # Accent rule under logo
        tk.Frame(sb, bg=ACCENT, height=2).pack(fill="x", padx=20, pady=(10, 6))

        # ── Nav buttons ──
        self._navbtns = {}
        for label, icon, pid in [
            ("Log Workout", "＋", "log"),
            ("History",     "☰", "history"),
            ("Progress",    "↗", "progress"),
            ("Summary",     "◉", "summary"),
            ("1RM & Balance","⚖", "analytics"),
        ]:
            b = tk.Button(
                sb, text=f"   {icon}   {label}",
                font=fnt(11), anchor="w",
                bg=SIDEBAR, fg=TEXT2,
                relief="flat", bd=0, pady=12,
                activebackground=ACCENT_DK,
                activeforeground="#FFFFFF",
                cursor="hand2",
                command=lambda p=pid: self._show_page(p),
            )
            b.pack(fill="x", padx=8)
            self._navbtns[pid] = b

        tk.Frame(sb, bg="#5A5D60", height=1).pack(fill="x", padx=20, pady=14)

        # ── Data file ──
        tk.Label(sb, text="DATA FILE", font=fnt(8),
                 fg=TEXT2, bg=SIDEBAR).pack(padx=18, anchor="w")
        self._path_var = tk.StringVar(value=self._short(self.db.path))
        tk.Label(sb, textvariable=self._path_var,
                 font=fnt(9), fg=ACCENT_LT, bg=SIDEBAR,
                 wraplength=165, justify="left").pack(padx=18, pady=(3, 6), anchor="w")
        tk.Button(
            sb, text="Change location…", font=fnt(9),
            fg=TEXT2, bg=SIDEBAR, relief="flat", bd=0,
            activebackground=SIDEBAR, activeforeground=ACCENT_LT,
            cursor="hand2",
            command=self._change_path,
        ).pack(padx=18, anchor="w")

        # ── Export PDF button at the very bottom ──
        tk.Frame(sb, bg="#5A5D60", height=1).pack(fill="x", padx=20, pady=(20, 10))
        export_btn = tk.Button(
            sb, text="  🖨  Export PDF  ",
            font=fnt(11, "bold"),
            bg=ACCENT, fg="#FFFFFF",
            activebackground=ACCENT_DK, activeforeground="#FFFFFF",
            relief="flat", cursor="hand2", bd=0, pady=11,
            command=self._export_pdf,
        )
        export_btn.pack(fill="x", padx=12, pady=(0, 16))

    def _short(self, p):
        try:
            return str(pathlib.Path(p).relative_to(pathlib.Path.home()))
        except Exception:
            return p

    def _change_path(self):
        new = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="gym_workouts.csv",
            title="Choose where to save your workout data",
        )
        if new:
            self.db.change_path(new)
            self._path_var.set(self._short(new))
            self.refresh_history()

    def _show_page(self, pid):
        for p, frame in self._pages.items():
            frame.pack_forget()
        self._pages[pid].pack(fill="both", expand=True)
        for p, btn in self._navbtns.items():
            if p == pid:
                btn.config(bg=ACCENT, fg="#FFFFFF", font=fnt(11, "bold"))
            else:
                btn.config(bg=SIDEBAR, fg=TEXT2, font=fnt(11))

    # ── PDF Export ────────────────────────────────────────
    def _export_pdf(self):
        """Open save dialog → generate PDF → open it."""
        # Default filename: GymTracker_Report_YYYY-MM-DD.pdf
        default_name = f"GymTracker_Report_{date.today().strftime('%Y-%m-%d')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            initialdir=str(pathlib.Path.home() / "Desktop"),
            title="Save PDF Report",
        )
        if not out_path:
            return  # user cancelled

        # Collect date range from history filters (if available)
        try:    d_from = datetime.strptime(self._ff.get(), "%Y-%m-%d").date()
        except: d_from = date(2000, 1, 1)
        try:    d_to   = datetime.strptime(self._ft.get(), "%Y-%m-%d").date()
        except: d_to   = date.today()

        # Pass the current matplotlib figure so the chart is embedded
        fig = getattr(self, "_fig", None)

        try:
            self.exporter.export(out_path, fig=fig,
                                  date_from=d_from, date_to=d_to)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
            return

        # Ask if user wants to open the PDF right away
        if messagebox.askyesno("PDF Saved",
                                f"Report saved to:\n{out_path}\n\nOpen it now?"):
            import subprocess, sys
            try:
                if sys.platform == "win32":
                    os.startfile(out_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", out_path])
                else:
                    subprocess.Popen(["xdg-open", out_path])
            except Exception:
                pass  # silently ignore if OS open fails

    # ── Pages ─────────────────────────────────────────────
    def _build_pages(self):
        self._pages = {}
        for pid in ["log", "history", "progress", "summary", "analytics"]:
            self._pages[pid] = tk.Frame(self._content, bg=BG)
        self._page_log()
        self._page_history()
        self._page_progress()
        self._page_summary()
        self._page_analytics()

    # ═══════════════════════════════════════════
    #  LOG WORKOUT
    # ═══════════════════════════════════════════
    def _page_log(self):
        p = self._pages["log"]

        # Header
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 0))
        tk.Label(hdr, text="Log Workout", font=fnt(22, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")
        tk.Label(hdr, text=date.today().strftime("%A, %d %b %Y"),
                 font=fnt(10), fg=TEXT2, bg=BG).pack(side="right", pady=8)

        # Two-column body: form | today's session
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=40, pady=14)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        # ── LEFT: entry form ──
        card = tk.Frame(body, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        inner = tk.Frame(card, bg=SURFACE, padx=28, pady=24)
        inner.pack(fill="x")

        # Section label
        tk.Label(inner, text="NEW ENTRY", font=fnt(8, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(anchor="w", pady=(0, 14))

        # Exercise dropdown (editable for custom names)
        self._ex_var = tk.StringVar(value="Bench Press")
        ex_f = ComboField(inner, "Exercise", self._ex_var,
                          self.db.exercises(), width=30, editable=True)
        ex_f.pack(fill="x", pady=(0, 14))
        self._ex_combo = ex_f.combo

        # Date field
        self._date_v = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        FormField(inner, "Date (YYYY-MM-DD)", self._date_v, width=22).pack(fill="x", pady=(0, 14))

        # Sets / Reps / Weight in a row
        nums = tk.Frame(inner, bg=SURFACE)
        nums.pack(fill="x", pady=(0, 4))
        nums.columnconfigure((0, 1, 2), weight=1, uniform="num")
        self._sets_v   = tk.StringVar(value="3")
        self._reps_v   = tk.StringVar(value="10")
        self._weight_v = tk.StringVar(value="60")
        for col, (lbl, var) in enumerate([
            ("Sets",        self._sets_v),
            ("Reps",        self._reps_v),
            ("Weight (kg)", self._weight_v),
        ]):
            ff = FormField(nums, lbl, var, width=10)
            ff.grid(row=0, column=col, padx=(0, 10) if col < 2 else 0, sticky="ew")

        Divider(inner).pack(fill="x", pady=(18, 14))

        # Feedback + Save button
        fb_row = tk.Frame(inner, bg=SURFACE)
        fb_row.pack(fill="x")
        self._fb_var = tk.StringVar()
        self._fb_lbl = tk.Label(fb_row, textvariable=self._fb_var,
                                 font=fnt(10), fg=SUCCESS, bg=SURFACE,
                                 wraplength=280, justify="left")
        self._fb_lbl.pack(side="left", fill="x", expand=True)

        Btn(inner, "  ＋  Add to Session", self._save, style="primary").pack(
            fill="x", pady=(12, 0))

        # ── RIGHT: today's session panel ──
        sess = tk.Frame(body, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        sess.grid(row=0, column=1, sticky="nsew")

        s_head = tk.Frame(sess, bg=SURFACE, padx=20, pady=14)
        s_head.pack(fill="x")
        tk.Label(s_head, text="TODAY'S SESSION", font=fnt(9, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(side="left")
        self._sess_count = tk.StringVar(value="0 sets")
        tk.Label(s_head, textvariable=self._sess_count,
                 font=fnt(9), fg=TEXT2, bg=SURFACE).pack(side="right")

        Divider(sess).pack(fill="x", padx=20)

        self._sess_frame = tk.Frame(sess, bg=SURFACE)
        self._sess_frame.pack(fill="both", expand=True, padx=14, pady=10)

        self._sess_empty = tk.Label(
            self._sess_frame,
            text="No exercises logged yet today.\nAdd your first set above! 💪",
            font=fnt(10), fg=TEXT_MUT, bg=SURFACE, justify="center",
        )
        self._sess_empty.pack(expand=True, pady=30)

        Divider(sess).pack(fill="x", padx=20)
        vol_row = tk.Frame(sess, bg=SURFACE, padx=20, pady=12)
        vol_row.pack(fill="x")
        tk.Label(vol_row, text="TOTAL VOLUME", font=fnt(8),
                 fg=TEXT_MUT, bg=SURFACE).pack(side="left")
        self._sess_vol = tk.StringVar(value="— kg")
        tk.Label(vol_row, textvariable=self._sess_vol,
                 font=fnt(13, "bold"), fg=WARNING, bg=SURFACE).pack(side="right")

        self._refresh_session()

    def _refresh_session(self):
        today_str = self._date_v.get().strip() if hasattr(self, "_date_v") \
                    else date.today().strftime("%Y-%m-%d")
        try:
            today_d = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            today_d = date.today()

        df = self.db.between(today_d, today_d)

        for w in self._sess_frame.winfo_children():
            w.destroy()

        if df.empty:
            tk.Label(
                self._sess_frame,
                text="No exercises logged yet today.\nAdd your first set above! 💪",
                font=fnt(10), fg=TEXT_MUT, bg=SURFACE, justify="center",
            ).pack(expand=True, pady=30)
            self._sess_count.set("0 sets")
            self._sess_vol.set("— kg")
            return

        total_vol, total_sets = 0.0, 0
        for i, (ex_name, grp) in enumerate(df.groupby("exercise", sort=False)):
            row_bg = SURFACE if i % 2 == 0 else SURFACE2
            row = tk.Frame(self._sess_frame, bg=row_bg)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=ex_name, font=fnt(11, "bold"),
                     fg=TEXT, bg=row_bg, anchor="w").pack(side="left", padx=10, pady=8)

            badges = tk.Frame(row, bg=row_bg)
            badges.pack(side="right", padx=8, pady=6)
            for _, entry in grp.iterrows():
                total_vol  += entry["sets"] * entry["reps"] * entry["weight"]
                total_sets += int(entry["sets"])
                badge = f'{int(entry["sets"])}×{int(entry["reps"])} @ {entry["weight"]:.0f}kg'
                tk.Label(badges, text=badge, font=fnt(9, "bold"),
                         fg=ACCENT, bg=ACCENT_LT,
                         padx=8, pady=3).pack(side="left", padx=(0, 4))

        self._sess_count.set(f"{total_sets} sets · {len(df)} entries")
        self._sess_vol.set(f"{total_vol:,.0f} kg")

    def _save(self):
        ex     = self._ex_var.get().strip()
        dt     = self._date_v.get().strip()
        sets_s = self._sets_v.get().strip()
        reps_s = self._reps_v.get().strip()
        wgt_s  = self._weight_v.get().strip()

        errs = []
        if not ex: errs.append("Exercise is required.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", dt):
            errs.append("Date must be YYYY-MM-DD.")
        else:
            try: datetime.strptime(dt, "%Y-%m-%d")
            except ValueError: errs.append("Invalid date value.")
        try:    sets = int(sets_s);  assert sets > 0
        except: errs.append("Sets must be a positive integer."); sets = 0
        try:    reps = int(reps_s);  assert reps > 0
        except: errs.append("Reps must be a positive integer."); reps = 0
        try:    wgt = float(wgt_s);  assert wgt >= 0
        except: errs.append("Weight must be ≥ 0."); wgt = 0.0

        if errs:
            messagebox.showerror("Please fix these", "\n".join(errs))
            return

        pbs   = self.db.personal_bests()
        is_pb = (ex not in pbs) or (wgt > pbs.get(ex, 0))

        if self.db.add(dt, ex, sets, reps, wgt):
            if is_pb:
                self._fb_var.set(f"🏆  New personal best for {ex}! ({wgt} kg)")
                self._fb_lbl.config(fg=WARNING)
            else:
                self._fb_var.set(f"✓  Saved — {ex}   {sets}×{reps} @ {wgt} kg")
                self._fb_lbl.config(fg=SUCCESS)
            # Keep exercise + date; only reset numeric fields
            self._sets_v.set("3")
            self._reps_v.set("10")
            self._weight_v.set(wgt_s)
            self._ex_combo["values"] = self.db.exercises()
            self._refresh_session()
            self.refresh_history()
            self._plot()
            self._refresh_summary()
        else:
            messagebox.showerror("Error", f"Could not write to:\n{self.db.path}")

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a row to delete.")
            return
        values = self.tree.item(selected[0])["values"]
        d, exercise, sets, reps, weight, _ = values
        if not messagebox.askyesno("Confirm Delete",
                                    f"Delete  {exercise}  on  {d}?"):
            return
        self.db.delete_row(d, exercise, sets, reps, float(weight))
        self.refresh_history()
        self._plot()
        self._refresh_summary()

    # ═══════════════════════════════════════════
    #  HISTORY
    # ═══════════════════════════════════════════
    def _page_history(self):
        p = self._pages["history"]

        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 0))
        tk.Label(hdr, text="History", font=fnt(22, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")
        self._hist_cnt = tk.StringVar()
        tk.Label(hdr, textvariable=self._hist_cnt,
                 font=fnt(10), fg=TEXT2, bg=BG).pack(side="right", pady=8)

        # Filter bar
        fcard = tk.Frame(p, bg=SURFACE,
                         highlightthickness=1, highlightbackground=BORDER)
        fcard.pack(fill="x", padx=40, pady=14)
        fi = tk.Frame(fcard, bg=SURFACE, padx=20, pady=12)
        fi.pack(fill="x")

        tk.Label(fi, text="FILTER", font=fnt(8, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(side="left", padx=(0, 14))

        self._fex = tk.StringVar(value="All")
        self._fex_cb = ttk.Combobox(
            fi, textvariable=self._fex,
            values=["All"] + self.db.exercises(),
            width=22, font=fnt(11),
            style="App.TCombobox", state="readonly",
        )
        self._fex_cb.pack(side="left", padx=(0, 18), ipady=3)

        self._ff = tk.StringVar(value="2020-01-01")
        self._ft = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        for lbl, var in [("From", self._ff), ("To", self._ft)]:
            tk.Label(fi, text=lbl, font=fnt(9),
                     fg=TEXT2, bg=SURFACE).pack(side="left")
            tk.Entry(
                fi, textvariable=var, width=12,
                font=fnt(11), bg=SURFACE2, fg=TEXT,
                relief="flat", bd=0,
                highlightthickness=1,
                highlightbackground=BORDER,
                highlightcolor=ACCENT,
                insertbackground=ACCENT,
            ).pack(side="left", ipady=5, padx=(4, 14))

        Btn(fi, "Apply",          self.refresh_history,    style="primary",   small=True).pack(side="left", padx=(0, 6))
        Btn(fi, "Reset",          self._reset_filter,      style="secondary", small=True).pack(side="left", padx=(0, 6))
        Btn(fi, "Delete Selected", self._delete_selected,  style="danger",    small=True).pack(side="left")

        # Treeview
        tcard = tk.Frame(p, bg=SURFACE,
                         highlightthickness=1, highlightbackground=BORDER)
        tcard.pack(fill="both", expand=True, padx=40, pady=(0, 28))

        cols = ("date", "exercise", "sets", "reps", "weight", "volume")
        self.tree = ttk.Treeview(tcard, columns=cols, show="headings",
                                  style="App.Treeview", selectmode="browse")
        self.tree.tag_configure("alt", background=SURFACE2)
        self.tree.tag_configure("pb",  background=WARN_BG, foreground=WARNING)

        for c, h, w in [
            ("date",     "Date",        110),
            ("exercise", "Exercise",    210),
            ("sets",     "Sets",         60),
            ("reps",     "Reps",         60),
            ("weight",   "Weight (kg)", 110),
            ("volume",   "Volume",      100),
        ]:
            self.tree.heading(c, text=h, command=lambda _c=c: self._sort(_c))
            self.tree.column(c, width=w, anchor="center")

        vsb = ttk.Scrollbar(tcard, orient="vertical",
                             command=self.tree.yview,
                             style="App.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._sort_col, self._sort_asc = "date", False

    def _reset_filter(self):
        self._fex.set("All")
        self._ff.set("2020-01-01")
        self._ft.set(date.today().strftime("%Y-%m-%d"))
        self.refresh_history()

    def _sort(self, col):
        self._sort_asc = not self._sort_asc if self._sort_col == col else True
        self._sort_col = col
        self.refresh_history()

    def refresh_history(self, _=None):
        try:    start = datetime.strptime(self._ff.get(), "%Y-%m-%d").date()
        except: start = date(2020, 1, 1)
        try:    end   = datetime.strptime(self._ft.get(), "%Y-%m-%d").date()
        except: end   = date.today()

        df = self.db.between(start, end)
        if hasattr(self, "_fex") and self._fex.get() != "All":
            df = df[df["exercise"] == self._fex.get()]
        if self._sort_col in df.columns:
            df = df.sort_values(self._sort_col, ascending=self._sort_asc)

        df = df.copy()
        df["volume"] = (df["sets"] * df["reps"] * df["weight"]).round(1)
        pbs = self.db.personal_bests()

        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, (_, r) in enumerate(df.iterrows()):
            tag = "pb" if pbs.get(r["exercise"]) == r["weight"] \
                  else ("alt" if i % 2 else "")
            self.tree.insert("", "end", values=(
                r["date"].strftime("%Y-%m-%d"), r["exercise"],
                int(r["sets"]), int(r["reps"]),
                f'{r["weight"]:.1f}', f'{r["volume"]:.0f}',
            ), tags=(tag,))

        if hasattr(self, "_hist_cnt"):
            self._hist_cnt.set(f"{len(df)} entries")
        if hasattr(self, "_fex_cb"):
            self._fex_cb["values"] = ["All"] + self.db.exercises()

    # ═══════════════════════════════════════════
    #  PROGRESS
    # ═══════════════════════════════════════════
    def _page_progress(self):
        p = self._pages["progress"]

        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 0))
        tk.Label(hdr, text="Progress", font=fnt(22, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")

        ctrl = tk.Frame(p, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        ctrl.pack(fill="x", padx=40, pady=14)
        ci = tk.Frame(ctrl, bg=SURFACE, padx=20, pady=12)
        ci.pack(fill="x")

        self._pex = tk.StringVar()
        exs = self.db.exercises()
        if exs: self._pex.set(exs[0])

        tk.Label(ci, text="EXERCISE", font=fnt(8, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(side="left", padx=(0, 10))
        self._pex_cb = ttk.Combobox(
            ci, textvariable=self._pex, values=exs,
            width=28, font=fnt(11),
            style="App.TCombobox", state="readonly",
        )
        self._pex_cb.pack(side="left", padx=(0, 20), ipady=3)

        self._all_ex = tk.BooleanVar(value=False)
        tk.Checkbutton(
            ci, text="Overlay all exercises",
            variable=self._all_ex, command=self._plot,
            font=fnt(11), fg=TEXT2, bg=SURFACE,
            selectcolor=ACCENT_LT,
            activebackground=SURFACE,
            activeforeground=ACCENT,
            relief="flat", cursor="hand2",
        ).pack(side="left", padx=(0, 16))

        Btn(ci, "  Plot  ", self._plot, style="primary", small=True).pack(side="left")

        chart_card = tk.Frame(p, bg=SURFACE,
                              highlightthickness=1, highlightbackground=BORDER)
        chart_card.pack(fill="both", expand=True, padx=40, pady=(0, 28))

        self._fig = Figure(figsize=(8, 4.2), facecolor=SURFACE)
        self._ax  = self._fig.add_subplot(111)
        self._style_ax(self._ax)
        self._fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.15)

        self._canvas = FigureCanvasTkAgg(self._fig, master=chart_card)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=2, pady=2)

    def _style_ax(self, ax):
        ax.set_facecolor(SURFACE2)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.tick_params(colors=TEXT2, labelsize=9)
        ax.grid(True, color=BORDER, linestyle="--", lw=0.7, alpha=0.8)
        ax.xaxis.label.set_color(TEXT2)
        ax.yaxis.label.set_color(TEXT2)

    def _plot(self):
        self._ax.clear()
        self._style_ax(self._ax)
        df = self.db.load()

        if df.empty:
            self._ax.text(0.5, 0.5, "No data yet — log some workouts first!",
                          ha="center", va="center", color=TEXT2, fontsize=12,
                          transform=self._ax.transAxes)
            self._canvas.draw()
            return

        exercises = (df["exercise"].unique().tolist()
                     if self._all_ex.get() else [self._pex.get()])

        for i, ex in enumerate(exercises):
            sub = df[df["exercise"] == ex].sort_values("date")
            if sub.empty: continue
            c = CHART_COLS[i % len(CHART_COLS)]
            # Faint glow band
            self._ax.plot(sub["date"], sub["weight"], lw=6, color=c, alpha=0.10)
            # Main line
            self._ax.plot(sub["date"], sub["weight"],
                          marker="o", ms=5, lw=2, color=c, label=ex,
                          markerfacecolor=SURFACE, markeredgewidth=2, markeredgecolor=c)
            pk = sub.loc[sub["weight"].idxmax()]
            self._ax.annotate(f'{pk["weight"]:.0f}kg',
                              xy=(pk["date"], pk["weight"]),
                              xytext=(5, 8), textcoords="offset points",
                              color=c, fontsize=8, fontweight="bold")

        title = "All Exercises" if self._all_ex.get() else self._pex.get()
        self._ax.set_title(title, fontsize=13, fontweight="bold",
                           color=TEXT, pad=10, fontfamily=FN)
        self._ax.set_xlabel("Date", fontsize=9)
        self._ax.set_ylabel("Weight (kg)", fontsize=9)
        self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        self._ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        if len(exercises) > 1:
            self._ax.legend(fontsize=8, framealpha=0.95,
                            edgecolor=BORDER, facecolor=SURFACE,
                            labelcolor=TEXT)
        self._fig.autofmt_xdate(rotation=25)
        self._canvas.draw()
        self._pex_cb["values"] = self.db.exercises()

    # ═══════════════════════════════════════════
    #  SUMMARY
    # ═══════════════════════════════════════════
    def _page_summary(self):
        p = self._pages["summary"]

        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 0))
        tk.Label(hdr, text="Summary", font=fnt(22, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")
        Btn(hdr, "🖨  Export PDF", self._export_pdf,
            style="primary", small=True).pack(side="right", pady=6, padx=(8, 0))
        Btn(hdr, "↻  Refresh", self._refresh_summary,
            style="secondary", small=True).pack(side="right", pady=6)

        cols_frame = tk.Frame(p, bg=BG)
        cols_frame.pack(fill="both", expand=True, padx=40, pady=18)
        cols_frame.columnconfigure(0, weight=2)
        cols_frame.columnconfigure(1, weight=3)

        # Personal Bests card
        pb_card = tk.Frame(cols_frame, bg=SURFACE,
                           highlightthickness=1, highlightbackground=BORDER)
        pb_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(pb_card, text="Personal Bests", font=fnt(14, "bold"),
                 fg=TEXT, bg=SURFACE).pack(anchor="w", padx=20, pady=(18, 2))
        tk.Label(pb_card, text="Heaviest lift per exercise",
                 font=fnt(9), fg=TEXT2, bg=SURFACE).pack(anchor="w", padx=20, pady=(0, 10))
        Divider(pb_card).pack(fill="x", padx=20)
        self._pb_frame = tk.Frame(pb_card, bg=SURFACE)
        self._pb_frame.pack(fill="both", expand=True, padx=14, pady=10)

        # Weekly Volume card
        wk_card = tk.Frame(cols_frame, bg=SURFACE,
                           highlightthickness=1, highlightbackground=BORDER)
        wk_card.grid(row=0, column=1, sticky="nsew")

        tk.Label(wk_card, text="Weekly Volume", font=fnt(14, "bold"),
                 fg=TEXT, bg=SURFACE).pack(anchor="w", padx=20, pady=(18, 2))
        tk.Label(wk_card, text="Last 10 weeks — sets × reps × weight",
                 font=fnt(9), fg=TEXT2, bg=SURFACE).pack(anchor="w", padx=20, pady=(0, 10))
        Divider(wk_card).pack(fill="x", padx=20)

        self.wtree = ttk.Treeview(wk_card,
                                   columns=("week", "sessions", "volume"),
                                   show="headings", style="App.Treeview", height=10)
        for c, h, w in [
            ("week",     "Week",         130),
            ("sessions", "Sessions",      90),
            ("volume",   "Volume (kg)",  140),
        ]:
            self.wtree.heading(c, text=h)
            self.wtree.column(c, width=w, anchor="center")
        self.wtree.pack(fill="both", expand=True, padx=20, pady=12)

        self._refresh_summary()

    def _refresh_summary(self):
        for w in self._pb_frame.winfo_children():
            w.destroy()

        pbs = self.db.personal_bests()
        if pbs:
            for i, (ex, wgt) in enumerate(sorted(pbs.items())):
                row_bg = SURFACE if i % 2 == 0 else SURFACE2
                row = tk.Frame(self._pb_frame, bg=row_bg)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=ex, font=fnt(11), fg=TEXT,
                         bg=row_bg, anchor="w").pack(side="left", padx=10, pady=6)
                tk.Label(row, text=f"{wgt:.1f} kg",
                         font=fnt(10, "bold"), fg=WARNING,
                         bg=WARN_BG, padx=10, pady=3).pack(side="right", padx=10)
        else:
            tk.Label(self._pb_frame, text="No workouts yet.",
                     font=fnt(11), fg=TEXT2, bg=SURFACE).pack(pady=20)

        for row in self.wtree.get_children():
            self.wtree.delete(row)
        summary = self.db.weekly_summary()
        if not summary.empty:
            for _, r in summary.iterrows():
                self.wtree.insert("", "end", values=(
                    r["week"].strftime("%b %d, %Y"),
                    int(r["sessions"]),
                    f'{r["volume"]:,.0f}',
                ))

    # ═══════════════════════════════════════════
    #  1RM ESTIMATOR  &  MUSCLE BALANCE
    # ═══════════════════════════════════════════
    def _page_analytics(self):
        p = self._pages["analytics"]

        # ── Header ──
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 0))
        tk.Label(hdr, text="1RM & Balance", font=fnt(22, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")
        Btn(hdr, "↻  Refresh", self._refresh_analytics,
            style="secondary", small=True).pack(side="right", pady=6)

        # ── Two-column body ──
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=40, pady=18)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # ────────────────────────────────────────
        #  LEFT: 1-Rep Max estimator
        # ────────────────────────────────────────
        orm_card = tk.Frame(body, bg=SURFACE,
                            highlightthickness=1, highlightbackground=BORDER)
        orm_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(orm_card, text="1-Rep Max Estimator",
                 font=fnt(14, "bold"), fg=TEXT, bg=SURFACE).pack(
                     anchor="w", padx=20, pady=(18, 2))
        tk.Label(orm_card,
                 text="Epley formula: weight × (1 + reps ÷ 30)",
                 font=fnt(9), fg=TEXT2, bg=SURFACE).pack(anchor="w", padx=20, pady=(0, 10))
        Divider(orm_card).pack(fill="x", padx=20)

        # Manual-entry sub-card
        inp = tk.Frame(orm_card, bg=SURFACE2, padx=20, pady=14)
        inp.pack(fill="x", padx=20, pady=14)

        tk.Label(inp, text="CALCULATE FROM A SET", font=fnt(8, "bold"),
                 fg=ACCENT, bg=SURFACE2).pack(anchor="w", pady=(0, 10))

        row_f = tk.Frame(inp, bg=SURFACE2)
        row_f.pack(fill="x")
        row_f.columnconfigure((0, 1, 2), weight=1, uniform="orm")

        self._orm_weight = tk.StringVar(value="80")
        self._orm_reps   = tk.StringVar(value="8")
        for col, (lbl, var) in enumerate([
            ("Weight (kg)", self._orm_weight),
            ("Reps",        self._orm_reps),
        ]):
            ff = FormField(row_f, lbl, var, width=10, bg=SURFACE2)
            ff.grid(row=0, column=col, padx=(0, 10) if col == 0 else 0, sticky="ew")

        Btn(inp, "  Calculate  ", self._calc_orm, style="primary", small=True).pack(
            anchor="w", pady=(14, 0))

        # Result label
        self._orm_result_var = tk.StringVar(value="")
        self._orm_result_lbl = tk.Label(
            orm_card, textvariable=self._orm_result_var,
            font=fnt(20, "bold"), fg=ACCENT, bg=SURFACE,
            anchor="center",
        )
        self._orm_result_lbl.pack(pady=(4, 0))
        tk.Label(orm_card, text="estimated 1-Rep Max",
                 font=fnt(9), fg=TEXT2, bg=SURFACE).pack(pady=(0, 4))

        Divider(orm_card).pack(fill="x", padx=20, pady=(8, 0))

        # Per-exercise 1RM table from best recorded sets
        tk.Label(orm_card, text="ESTIMATED 1RM PER EXERCISE",
                 font=fnt(8, "bold"), fg=ACCENT, bg=SURFACE).pack(
                     anchor="w", padx=20, pady=(10, 6))

        self._orm_frame = tk.Frame(orm_card, bg=SURFACE)
        self._orm_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # ────────────────────────────────────────
        #  RIGHT: Muscle-group balance chart
        # ────────────────────────────────────────
        bal_card = tk.Frame(body, bg=SURFACE,
                            highlightthickness=1, highlightbackground=BORDER)
        bal_card.grid(row=0, column=1, sticky="nsew")

        tk.Label(bal_card, text="Muscle Group Balance",
                 font=fnt(14, "bold"), fg=TEXT, bg=SURFACE).pack(
                     anchor="w", padx=20, pady=(18, 2))
        tk.Label(bal_card,
                 text="Volume distribution (sets × reps × weight) across muscle groups",
                 font=fnt(9), fg=TEXT2, bg=SURFACE).pack(anchor="w", padx=20, pady=(0, 10))
        Divider(bal_card).pack(fill="x", padx=20)

        # Chart toggle
        toggle_row = tk.Frame(bal_card, bg=SURFACE, padx=20)
        toggle_row.pack(fill="x", pady=(10, 0))
        tk.Label(toggle_row, text="View:", font=fnt(10), fg=TEXT2, bg=SURFACE).pack(side="left")
        self._bal_mode = tk.StringVar(value="pie")
        for val, lbl in [("pie", "Pie"), ("bar", "Bar")]:
            tk.Radiobutton(
                toggle_row, text=lbl, variable=self._bal_mode, value=val,
                command=self._refresh_analytics,
                font=fnt(10), fg=TEXT2, bg=SURFACE,
                selectcolor=ACCENT_LT, activebackground=SURFACE,
                relief="flat", cursor="hand2",
            ).pack(side="left", padx=(10, 0))

        self._bal_fig = Figure(figsize=(5, 4.5), facecolor=SURFACE)
        self._bal_canvas = FigureCanvasTkAgg(self._bal_fig, master=bal_card)
        self._bal_canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=(6, 4))

        # First render
        self._refresh_analytics()

    def _calc_orm(self):
        """Calculate 1RM from the manual entry fields and display result."""
        try:
            w = float(self._orm_weight.get())
            r = int(self._orm_reps.get())
            assert w > 0 and r > 0
        except Exception:
            self._orm_result_var.set("—")
            messagebox.showerror("Invalid input", "Enter a positive weight and rep count.")
            return
        est = epley_1rm(w, r)
        self._orm_result_var.set(f"{est:.1f} kg")

    def _refresh_analytics(self):
        # ── 1RM table ──
        for w in self._orm_frame.winfo_children():
            w.destroy()

        df = self.db.load()
        if df.empty:
            tk.Label(self._orm_frame, text="No workouts yet.",
                     font=fnt(11), fg=TEXT2, bg=SURFACE).pack(pady=20)
        else:
            # Best set per exercise: highest Epley 1RM (max weight single set)
            df["est_1rm"] = df.apply(
                lambda r: epley_1rm(r["weight"], max(r["reps"], 1)), axis=1)
            best = df.groupby("exercise")["est_1rm"].max().sort_values(ascending=False)

            for i, (ex, est) in enumerate(best.items()):
                row_bg = SURFACE if i % 2 == 0 else SURFACE2
                row = tk.Frame(self._orm_frame, bg=row_bg)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=ex, font=fnt(11), fg=TEXT,
                         bg=row_bg, anchor="w").pack(side="left", padx=10, pady=6)
                tk.Label(row, text=f"~{est:.1f} kg",
                         font=fnt(10, "bold"), fg=ACCENT,
                         bg=ACCENT_LT, padx=8, pady=3).pack(side="right", padx=10)

        # ── Balance chart ──
        self._bal_fig.clear()
        mv = self.db.muscle_volume()

        if not mv:
            ax = self._bal_fig.add_subplot(111)
            ax.set_facecolor(SURFACE)
            ax.text(0.5, 0.5, "No data yet — log some workouts first!",
                    ha="center", va="center", color=TEXT2, fontsize=11,
                    transform=ax.transAxes)
            ax.axis("off")
            self._bal_canvas.draw()
            return

        labels = list(mv.keys())
        values = list(mv.values())
        colours = [CHART_COLS[i % len(CHART_COLS)] for i in range(len(labels))]

        mode = self._bal_mode.get()
        if mode == "pie":
            ax = self._bal_fig.add_subplot(111)
            ax.set_facecolor(SURFACE)
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, colors=colours,
                autopct="%1.0f%%", startangle=140,
                pctdistance=0.78,
                wedgeprops={"edgecolor": SURFACE, "linewidth": 2},
            )
            for t in texts:
                t.set_color(TEXT); t.set_fontsize(9)
            for at in autotexts:
                at.set_color("#FFFFFF"); at.set_fontsize(8); at.set_fontweight("bold")
            ax.set_title("Volume by Muscle Group", fontsize=12,
                         fontweight="bold", color=TEXT, pad=10)
        else:
            ax = self._bal_fig.add_subplot(111)
            ax.set_facecolor(SURFACE2)
            for sp in ax.spines.values():
                sp.set_color(BORDER)
            ax.tick_params(colors=TEXT2, labelsize=8)
            ax.grid(axis="x", color=BORDER, linestyle="--", lw=0.7, alpha=0.8)
            # Sort descending
            pairs = sorted(zip(values, labels), reverse=True)
            vals, labs = zip(*pairs)
            bars = ax.barh(labs, vals,
                           color=[CHART_COLS[i % len(CHART_COLS)] for i in range(len(labs))],
                           edgecolor=SURFACE, linewidth=1.5, height=0.6)
            total = sum(vals)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_width() + total * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f"{v:,.0f} kg  ({v/total*100:.0f}%)",
                        va="center", ha="left", fontsize=8, color=TEXT2)
            ax.set_xlabel("Volume (kg)", fontsize=9, color=TEXT2)
            ax.set_title("Volume by Muscle Group", fontsize=12,
                         fontweight="bold", color=TEXT, pad=10)
            ax.invert_yaxis()
            self._bal_fig.subplots_adjust(left=0.22, right=0.75, top=0.88, bottom=0.12)

        self._bal_canvas.draw()

    # ── Launch ────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().run()