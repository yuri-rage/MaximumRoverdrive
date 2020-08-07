from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication


class QAppMPLookAndFeel(QApplication):
    def __init__(self, args):
        super(QAppMPLookAndFeel, self).__init__(args)
        self.apply_style()

    def apply_style(self):
        self.setStyle('Fusion')
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(38, 39, 40))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(38, 39, 40))
        dark_palette.setColor(QPalette.AlternateBase, QColor(38, 39, 40))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, QColor(221, 221,221))
        dark_palette.setColor(QPalette.ButtonText, QColor(64, 87, 4))
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        self.setStyleSheet('QWidget { font-family: "Segue UI", sans-serif; font-size: 12px; }'
                           'QToolTip { color: white; background-color: #2a82da; border: 1px solid white; }'
                           'QTableView { font-family: "Consolas", fixed;  font-size: 14px; '
                           'border: 1px solid #515253; gridline-color: #515253; }'
                           'QPushButton { min-height: 21px; border: 0px; border-radius: 2px; '
                           'border-color: #405704; background: '
                           'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #97c224, stop: 1 #c8df8c); }'
                           'QPushButton:hover { background:'
                           'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #789b1b, stop: 1 #9bb065); }'
                           'QPushButton:pressed { background:'
                           'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #628014, stop: 1 #7b8f49); }')
