"""
Design system — dark and light themes with Poppins font support.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Palette tokens
# ---------------------------------------------------------------------------

DARK = {
    "bg":           "#07091A",
    "surface":      "#0C0F24",
    "card":         "#111530",
    "card_hover":   "#181C3A",
    "card_sel":     "#1D2245",
    "border":       "#1E2340",
    "border_hover": "#343968",
    "accent":       "#6C5CE7",
    "accent_hover": "#7D6EF0",
    "accent_dim":   "#251F5E",
    "accent_text":  "#A29BFE",
    "cyan":         "#00CEC9",
    "green":        "#00B894",
    "orange":       "#FDCB6E",
    "red":          "#FF6B6B",
    "text":         "#E2E5FF",
    "text2":        "#8890BE",
    "text3":        "#525880",
    "toolbar":      "#0A0D20",
    "input":        "#0E1126",
    "scrollhandle": "#2C3160",
    "tooltip_bg":   "#181C3A",
}

LIGHT = {
    "bg":           "#F2F3FC",
    "surface":      "#FFFFFF",
    "card":         "#FFFFFF",
    "card_hover":   "#EEEFFF",
    "card_sel":     "#E6E7FF",
    "border":       "#DCDEFF",
    "border_hover": "#ADADF5",
    "accent":       "#6C5CE7",
    "accent_hover": "#5A4BD0",
    "accent_dim":   "#ECEAFF",
    "accent_text":  "#5248C8",
    "cyan":         "#00B2AE",
    "green":        "#00967A",
    "orange":       "#D06030",
    "red":          "#C0392B",
    "text":         "#16173A",
    "text2":        "#606490",
    "text3":        "#9498C0",
    "toolbar":      "#FFFFFF",
    "input":        "#EDEEFF",
    "scrollhandle": "#C4C7EE",
    "tooltip_bg":   "#16173A",
}


def _build_qss(p: dict, font_family: str = "Poppins") -> str:
    ff = f'"{font_family}", "Segoe UI", Arial, sans-serif'
    return f"""
/* ===== BASE ============================================================= */
QWidget {{
    background-color: {p["bg"]};
    color: {p["text"]};
    font-family: {ff};
    font-size: 13px;
    selection-background-color: {p["accent"]};
    selection-color: #FFFFFF;
    border: none;
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {p["bg"]};
}}

/* ===== APP TOOLBAR (search + controls, no in-app branding) ============= */
#appToolBar {{
    background-color: {p["toolbar"]};
    border-bottom: 1px solid {p["border"]};
    min-height: 52px;
    max-height: 52px;
}}

#toolbarSep {{
    background-color: {p["border"]};
    max-width: 1px;
    min-width: 1px;
    margin: 10px 2px;
}}

/* ===== SIDEBAR ========================================================== */
#sidebar {{
    background-color: {p["surface"]};
    border-right: 1px solid {p["border"]};
    min-width: 256px;
    max-width: 256px;
}}

#sidebarSection {{
    font-size: 10px;
    font-weight: 700;
    color: {p["text3"]};
    letter-spacing: 0.8px;
    padding: 2px 4px;
}}

/* ===== NAVIGATION ITEMS ================================================= */
#navItem {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    color: {p["text2"]};
    min-height: 34px;
}}

#navItem:hover {{
    background-color: {p["card_hover"]};
    color: {p["text"]};
}}

#navItem:pressed {{
    background-color: {p["accent_dim"]};
    color: {p["accent_text"]};
}}

#navItemActive {{
    background-color: {p["accent_dim"]};
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    color: {p["accent_text"]};
    min-height: 34px;
}}

#navItemActive:hover {{
    background-color: {p["card_sel"]};
}}

/* ===== STAT CARDS ======================================================= */
#statCard {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    border-radius: 10px;
    padding: 10px 12px;
}}

#statCard:hover {{
    border-color: {p["border_hover"]};
    background-color: {p["card_hover"]};
}}

#statValue {{
    font-size: 20px;
    font-weight: 700;
    color: {p["accent_text"]};
}}

#statLabel {{
    font-size: 10px;
    font-weight: 500;
    color: {p["text2"]};
    letter-spacing: 0.2px;
}}

/* ===== SEARCH BAR ======================================================= */
#searchContainer {{
    background-color: {p["card"]};
    border: 1.5px solid {p["border_hover"]};
    border-radius: 10px;
}}

#searchContainer:hover {{
    border-color: {p["accent"]};
}}

#searchContainer:focus-within {{
    border-color: {p["accent"]};
    background-color: {p["card_hover"]};
}}

#searchInput {{
    background: transparent;
    border: none;
    font-size: 13px;
    color: {p["text"]};
    padding: 0 2px;
    selection-background-color: {p["accent"]};
}}

#searchInput::placeholder {{
    color: {p["text3"]};
}}

#searchClear {{
    background: transparent;
    border: none;
    color: {p["text3"]};
    border-radius: 8px;
    padding: 2px 4px;
    min-width: 18px;
}}

#searchClear:hover {{
    color: {p["text"]};
    background-color: {p["border"]};
}}

/* ===== FILTER PILLS ===================================================== */
#filterPill {{
    background-color: transparent;
    border: 1px solid {p["border"]};
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 500;
    color: {p["text2"]};
}}

#filterPill:hover {{
    border-color: {p["accent"]};
    color: {p["accent_text"]};
    background-color: {p["accent_dim"]};
}}

#filterPillActive {{
    background-color: {p["accent"]};
    border: 1px solid {p["accent"]};
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
    color: #FFFFFF;
}}

/* ===== FOLDER LIST ====================================================== */
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}

QListWidget::item {{
    background: transparent;
    border-radius: 7px;
    padding: 5px 8px;
    margin: 1px 0;
    color: {p["text2"]};
    font-size: 12px;
    font-weight: 500;
}}

QListWidget::item:hover {{
    background-color: {p["card_hover"]};
    color: {p["text"]};
}}

QListWidget::item:selected {{
    background-color: {p["accent_dim"]};
    color: {p["accent_text"]};
    font-weight: 600;
}}

/* ===== RESULT CARDS ===================================================== */
#resultCard {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    border-radius: 12px;
}}

#resultCard:hover {{
    border-color: {p["accent"]};
    background-color: {p["card_hover"]};
}}

#resultCardSelected {{
    background-color: {p["card_sel"]};
    border: 1.5px solid {p["accent"]};
    border-radius: 12px;
}}

#resultThumb {{
    background-color: {p["surface"]};
    border-radius: 10px 10px 0 0;
    border-bottom: 1px solid {p["border"]};
}}

#resultTitle {{
    font-size: 12px;
    font-weight: 600;
    color: {p["text"]};
}}

#resultMeta {{
    font-size: 11px;
    color: {p["text2"]};
}}

#resultSnippet {{
    font-size: 11px;
    color: {p["text3"]};
}}

/* ===== BADGES =========================================================== */
#badgeAccent {{
    background-color: {p["accent"]};
    color: #FFFFFF;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}}

#badgeCount {{
    background-color: {p["accent_dim"]};
    color: {p["accent_text"]};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}

/* ===== PREVIEW PANEL ==================================================== */
#previewPanel {{
    background-color: {p["surface"]};
    border-left: 1px solid {p["border"]};
    min-width: 300px;
    max-width: 340px;
}}

#previewImageArea {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    border-radius: 10px;
}}

#previewTitle {{
    font-size: 13px;
    font-weight: 700;
    color: {p["text"]};
    letter-spacing: 0.1px;
}}

#metaKey {{
    font-size: 11px;
    color: {p["text2"]};
    font-weight: 500;
}}

#metaValue {{
    font-size: 11px;
    color: {p["text"]};
    font-weight: 400;
}}

#ocrBox {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    border-radius: 8px;
    color: {p["text2"]};
    font-size: 12px;
    line-height: 1.5;
    padding: 8px 10px;
}}

/* ===== RESULTS HEADER =================================================== */
#resultsHeader {{
    background-color: {p["surface"]};
    border-bottom: 1px solid {p["border"]};
}}

#resultsTitle {{
    font-size: 14px;
    font-weight: 700;
    color: {p["text"]};
}}

/* ===== EMPTY STATE ====================================================== */
#emptyTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {p["text3"]};
}}

#emptySubtitle {{
    font-size: 12px;
    color: {p["text3"]};
}}

/* ===== BUTTONS ========================================================== */
QPushButton {{
    background-color: {p["card"]};
    color: {p["text2"]};
    border: 1px solid {p["border"]};
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {p["card_hover"]};
    border-color: {p["border_hover"]};
    color: {p["text"]};
}}

QPushButton:pressed {{
    background-color: {p["accent_dim"]};
    border-color: {p["accent"]};
    color: {p["accent_text"]};
}}

QPushButton#primaryBtn {{
    background-color: {p["accent"]};
    color: #FFFFFF;
    border: 1px solid {p["accent"]};
    font-weight: 600;
}}

QPushButton#primaryBtn:hover {{
    background-color: {p["accent_hover"]};
    border-color: {p["accent_hover"]};
}}

QPushButton#primaryBtn:pressed {{
    background-color: {p["accent"]};
}}

QPushButton#ghostBtn {{
    background-color: transparent;
    color: {p["text2"]};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 12px;
}}

QPushButton#ghostBtn:hover {{
    background-color: {p["card_hover"]};
    border-color: {p["border"]};
    color: {p["text"]};
}}

QPushButton#dangerBtn {{
    background-color: transparent;
    color: {p["red"]};
    border: 1px solid rgba(255,107,107,0.25);
    border-radius: 8px;
}}

QPushButton#dangerBtn:hover {{
    background-color: rgba(255,107,107,0.1);
    border-color: {p["red"]};
}}

QPushButton#iconBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px;
    color: {p["text2"]};
}}

QPushButton#iconBtn:hover {{
    background-color: {p["card_hover"]};
    color: {p["text"]};
}}

QPushButton#addBtn {{
    background-color: transparent;
    color: {p["accent_text"]};
    border: 1px dashed {p["border_hover"]};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
}}

QPushButton#addBtn:hover {{
    background-color: {p["accent_dim"]};
    border-color: {p["accent"]};
    border-style: solid;
}}

/* ===== INPUT FIELDS ===================================================== */
QLineEdit, QSpinBox {{
    background-color: {p["input"]};
    color: {p["text"]};
    border: 1.5px solid {p["border"]};
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: {p["accent"]};
}}

QLineEdit:focus, QSpinBox:focus {{
    border-color: {p["accent"]};
    background-color: {p["card"]};
}}

QLineEdit:hover {{
    border-color: {p["border_hover"]};
}}

QComboBox {{
    background-color: {p["input"]};
    color: {p["text"]};
    border: 1.5px solid {p["border"]};
    border-radius: 8px;
    padding: 7px 12px;
    padding-right: 28px;
    font-size: 13px;
}}

QComboBox:focus {{
    border-color: {p["accent"]};
    background-color: {p["card"]};
}}

QComboBox:hover {{
    border-color: {p["border_hover"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {p["card"]};
    border: 1px solid {p["border_hover"]};
    border-radius: 8px;
    selection-background-color: {p["accent_dim"]};
    selection-color: {p["accent_text"]};
    padding: 4px;
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    border-radius: 6px;
    min-height: 28px;
}}

/* ===== TEXT EDIT ======================================================== */
QTextEdit {{
    background-color: {p["card"]};
    color: {p["text2"]};
    border: 1px solid {p["border"]};
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    selection-background-color: {p["accent"]};
}}

/* ===== SCROLL BARS ====================================================== */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 4px 1px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical {{
    background: {p["scrollhandle"]};
    border-radius: 3px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: {p["accent"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
    margin: 1px 4px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal {{
    background: {p["scrollhandle"]};
    border-radius: 3px;
    min-width: 28px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {p["accent"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
    width: 0;
}}

/* ===== TABS ============================================================= */
QTabWidget::pane {{
    border: 1px solid {p["border"]};
    border-radius: 0 8px 8px 8px;
    background: {p["surface"]};
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {p["text2"]};
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    color: {p["accent_text"]};
    border-bottom: 2px solid {p["accent"]};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    color: {p["text"]};
    border-bottom: 2px solid {p["border_hover"]};
}}

/* ===== CHECKBOXES ======================================================= */
QCheckBox {{
    color: {p["text"]};
    spacing: 8px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1.5px solid {p["border_hover"]};
    border-radius: 5px;
    background: {p["input"]};
}}

QCheckBox::indicator:checked {{
    background-color: {p["accent"]};
    border-color: {p["accent"]};
}}

QCheckBox::indicator:hover {{
    border-color: {p["accent"]};
}}

/* ===== SLIDERS ========================================================== */
QSlider::groove:horizontal {{
    height: 4px;
    background: {p["border"]};
    border-radius: 2px;
    margin: 8px 0;
}}

QSlider::sub-page:horizontal {{
    background: {p["accent"]};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {p["accent"]};
    border: 2px solid {p["surface"]};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}}

QSlider::handle:horizontal:hover {{
    background: {p["accent_hover"]};
}}

/* ===== PROGRESS BAR ===================================================== */
QProgressBar {{
    background-color: {p["border"]};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["accent"]}, stop:1 {p["cyan"]});
    border-radius: 3px;
}}

/* ===== STATUS BAR ======================================================= */
QStatusBar {{
    background-color: {p["toolbar"]};
    border-top: 1px solid {p["border"]};
    color: {p["text2"]};
    font-size: 11px;
    padding: 0 6px;
}}

QStatusBar::item {{
    border: none;
}}

/* ===== TOOLTIPS ========================================================= */
QToolTip {{
    background-color: {p["tooltip_bg"]};
    color: {p["text"]};
    border: 1px solid {p["border_hover"]};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
}}

/* ===== MENU BAR ========================================================= */
QMenuBar {{
    background-color: {p["toolbar"]};
    color: {p["text2"]};
    border-bottom: 1px solid {p["border"]};
    font-size: 12px;
    padding: 1px 0;
}}

QMenuBar::item {{
    padding: 5px 10px;
    border-radius: 5px;
    background: transparent;
}}

QMenuBar::item:selected, QMenuBar::item:pressed {{
    background-color: {p["card_hover"]};
    color: {p["text"]};
}}

QMenu {{
    background-color: {p["card"]};
    border: 1px solid {p["border_hover"]};
    border-radius: 10px;
    padding: 5px 4px;
    color: {p["text"]};
}}

QMenu::item {{
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 13px;
}}

QMenu::item:selected {{
    background-color: {p["accent_dim"]};
    color: {p["accent_text"]};
}}

QMenu::separator {{
    height: 1px;
    background: {p["border"]};
    margin: 4px 8px;
}}

/* ===== FRAMES / SEPARATORS ============================================== */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    background-color: {p["border"]};
    max-height: 1px;
    border: none;
}}

/* ===== LABELS =========================================================== */
QLabel {{
    background: transparent;
    color: {p["text"]};
}}

QLabel#sectionTitle {{
    font-size: 13px;
    font-weight: 700;
    color: {p["text"]};
}}

QLabel#helpText {{
    font-size: 11px;
    color: {p["text2"]};
}}

QLabel#fieldLabel {{
    font-size: 12px;
    color: {p["text2"]};
    font-weight: 500;
}}

/* ===== SCROLL AREA ====================================================== */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ===== SPLITTER ========================================================= */
QSplitter::handle {{
    background-color: {p["border"]};
    width: 1px;
    height: 1px;
}}

QSplitter::handle:hover {{
    background-color: {p["accent"]};
}}

/* ===== SETTINGS DIALOG ================================================== */
#settingsSectionHeader {{
    font-size: 11px;
    font-weight: 700;
    color: {p["text3"]};
    letter-spacing: 0.7px;
    padding: 0;
}}

#privacyBadge {{
    font-size: 12px;
    font-weight: 600;
    color: {p["green"]};
}}
"""


def get_stylesheet(theme: str, font_family: str | None = None) -> str:
    if font_family is None:
        from app.ui.fonts import family
        font_family = family() or "Segoe UI"
    palette = LIGHT if theme == "light" else DARK
    return _build_qss(palette, font_family)


def get_palette(theme: str) -> dict:
    return LIGHT if theme == "light" else DARK
