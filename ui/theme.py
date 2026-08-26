"""
Windows 11 Fluent Dark Theme stylesheet for AetherClean.
"""

DARK_THEME_QSS = """
/* Global Window & Fonts */
QWidget {
    background-color: #202020;
    color: #FFFFFF;
    font-family: "Segoe UI Variable Text", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* Main Window */
QMainWindow {
    background-color: #1a1a1a;
}

/* Headers & Titles */
QLabel#headerTitle {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#headerSubtitle {
    font-size: 12px;
    color: #9E9E9E;
}

QLabel#sectionTitle {
    font-size: 15px;
    font-weight: 600;
    color: #E0E0E0;
}

/* Cards & Containers */
QFrame.CardFrame {
    background-color: #2b2b2b;
    border: 1px solid #383838;
    border-radius: 8px;
    padding: 12px;
}

QFrame#detailCard {
    background-color: #262626;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
}

/* Buttons */
QPushButton {
    background-color: #333333;
    color: #FFFFFF;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3f3f3f;
    border-color: #555555;
}

QPushButton:pressed {
    background-color: #252525;
}

QPushButton:disabled {
    background-color: #252525;
    color: #666666;
    border-color: #303030;
}

/* Accent Action Buttons (Scan, Clean) */
QPushButton#primaryButton {
    background-color: #0078D4;
    color: #FFFFFF;
    border: 1px solid #1E88E5;
    font-weight: 600;
    font-size: 14px;
    padding: 8px 20px;
}

QPushButton#primaryButton:hover {
    background-color: #1084D9;
    border-color: #42A5F5;
}

QPushButton#primaryButton:pressed {
    background-color: #006CBE;
}

QPushButton#dangerButton {
    background-color: #C62828;
    color: #FFFFFF;
    border: 1px solid #D32F2F;
    font-weight: 600;
}

QPushButton#dangerButton:hover {
    background-color: #D32F2F;
}

QPushButton#secondaryButton {
    background-color: #383838;
    border: 1px solid #4a4a4a;
}

QPushButton#secondaryButton:hover {
    background-color: #454545;
}

/* Tree & List Views */
QTreeWidget, QListWidget, QTableWidget {
    background-color: #252525;
    border: 1px solid #383838;
    border-radius: 8px;
    color: #FFFFFF;
    outline: none;
    padding: 4px;
}

QTreeWidget::item {
    padding: 6px 4px;
    border-radius: 4px;
    margin: 1px 0px;
}

QTreeWidget::item:hover {
    background-color: #323232;
}

QTreeWidget::item:selected {
    background-color: #005A9E;
    color: #FFFFFF;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    image: none;
}

QHeaderView::section {
    background-color: #2a2a2a;
    color: #B0B0B0;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #383838;
    font-weight: 600;
}

/* Progress Bar */
QProgressBar {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-weight: 600;
    height: 16px;
}

QProgressBar::chunk {
    background-color: #0078D4;
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #202020;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #444444;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a5a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #202020;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background-color: #444444;
    min-width: 24px;
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #FFFFFF;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #555555;
    border-radius: 4px;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #0078D4;
    border-color: #0078D4;
}

QCheckBox::indicator:hover {
    border-color: #777777;
}

/* Radio Buttons */
QRadioButton {
    spacing: 8px;
    color: #E0E0E0;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #555555;
    background-color: #2d2d2d;
}

QRadioButton::indicator:checked {
    background-color: #0078D4;
    border-color: #0078D4;
}

/* Tooltips */
QToolTip {
    background-color: #2d2d2d;
    color: #FFFFFF;
    border: 1px solid #4a4a4a;
    padding: 6px;
    border-radius: 4px;
}

/* Badges */
QLabel.BadgeSafe {
    background-color: #1b4332;
    color: #74c69d;
    border: 1px solid #2d6a4f;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.BadgeMedium {
    background-color: #5c4300;
    color: #ffd166;
    border: 1px solid #8c6400;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.BadgeHigh {
    background-color: #4a151b;
    color: #ff758f;
    border: 1px solid #781c26;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11px;
}
"""
