"""Scoped Fusion styling; native text controls retain normal IME behavior."""


def stylesheet(dark):
    colors = dict(bg="#101525", panel="#192137", raised="#222d47", text="#edf2ff", muted="#a4b3d1", line="#33415c", accent="#8c83ff", hover="#303c59", paper="#111a2e") if dark else dict(bg="#eef2f9", panel="#ffffff", raised="#f3f5fc", text="#162442", muted="#64748b", line="#dce3f0", accent="#6454df", hover="#e8e7fc", paper="#ffffff")
    return """
    QMainWindow, QDialog { background: %(bg)s; }
    QWidget { color: %(text)s; }
    QLabel { background: transparent; }
    QLabel#brand { font-size: 22px; font-weight: 700; color: %(accent)s; }
    QLabel#subtitle, QLabel#muted { color: %(muted)s; }
    QLabel#section { font-size: 12px; font-weight: 700; color: %(muted)s; }
    QFrame#card, QWidget#card { background: %(panel)s; border: 1px solid %(line)s; border-radius: 12px; }
    QPushButton, QToolButton { background: %(panel)s; border: 1px solid %(line)s; border-radius: 7px; padding: 8px 12px; font-weight: 600; }
    QPushButton:hover, QToolButton:hover { background: %(hover)s; border-color: %(accent)s; }
    QPushButton:pressed { background: %(raised)s; }
    QPushButton:disabled { color: %(muted)s; background: %(raised)s; }
    QPushButton#primary { background: %(accent)s; color: white; border: none; }
    QPushButton#primary:hover { background: #7969ee; }
    QPushButton#ai { background: #146c76; color: white; border: none; }
    QPushButton#ai:hover { background: #198795; }
    QComboBox, QSpinBox { background: %(panel)s; border: 1px solid %(line)s; padding: 6px 10px; border-radius: 6px; }
    QComboBox QAbstractItemView { background: %(panel)s; selection-background-color: %(hover)s; }
    QLineEdit { background: %(paper)s; border: 1px solid %(line)s; padding: 8px; border-radius: 6px; }
    QTextEdit, QPlainTextEdit { background: %(paper)s; border: 1px solid %(line)s; border-radius: 8px; padding: 12px; selection-background-color: #b8b1f0; selection-color: #182038; }
    QListWidget { background: %(panel)s; border: none; outline: none; border-radius: 8px; }
    QListWidget::item { padding: 8px; margin: 3px; border-radius: 6px; }
    QListWidget::item:selected { background: %(hover)s; color: %(accent)s; }
    QWidget#outputPanel { background: %(panel)s; }
    QTabWidget::pane { border: none; background: %(panel)s; }
    QTabBar::tab { background: %(raised)s; color: %(muted)s; padding: 10px 14px; margin-right: 4px; border-top-left-radius: 7px; border-top-right-radius: 7px; }
    QTabBar::tab:selected { background: %(panel)s; color: %(accent)s; border-bottom: 3px solid %(accent)s; }
    QSplitter::handle { background: %(line)s; width: 2px; }
    QGraphicsView { background: %(raised)s; border: none; border-radius: 8px; }
    QScrollArea { border: none; background: %(panel)s; }
    QStatusBar { color: %(muted)s; background: %(panel)s; padding: 4px; }
    QProgressBar { border: none; background: %(raised)s; border-radius: 4px; max-height: 6px; }
    QProgressBar::chunk { background: %(accent)s; border-radius: 4px; }
    QMenu { background: %(panel)s; border: 1px solid %(line)s; padding: 5px; }
    QMenu::item { padding: 7px 20px; }
    QMenu::item:selected { background: %(hover)s; }
    QCheckBox { spacing: 8px; padding: 5px; }
    QScrollBar:vertical { background: %(raised)s; width: 10px; }
    QScrollBar::handle:vertical { background: %(line)s; min-height: 25px; border-radius: 5px; }
    """ % colors
