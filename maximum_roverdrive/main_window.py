from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox, QPushButton, QTableView, QLineEdit


class MainWindow(QMainWindow):
    """ handle the bulk of the ugliness of window/widget geometry
        QMainWindow affords a built-in status bar, otherwise this could just be a QWidget """

    def __init__(self):
        super(MainWindow, self).__init__()
        self._widget = QWidget()
        self._layout = QVBoxLayout()
        self._con_text = QComboBox()
        self._con_button = QPushButton('Connect')
        self._remove_button = QPushButton('Remove Selected Message')
        self._tableView = QTableView()
        self._refresh_button = QPushButton('Refresh Available Messages')
        self._msg_select_cb = QComboBox()
        self._attr_select_cb = QComboBox()
        self._multiplier_text = QLineEdit('1.0')
        self._low_text = QLineEdit('0.0')
        self._high_text = QLineEdit('1000.0')
        self._add_button = QPushButton('Add')

    def __init_ui__(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Maximum Roverdrive')
        self._msg_select_cb.addItem('Click refresh')
        self._con_text.setEditable(True)
        self._layout.addWidget(self._con_text)
        self._layout.addWidget(self._con_button)
        self._layout.addWidget(self._remove_button)
        self._tableView.horizontalHeader().setStretchLastSection(True)
        self._tableView.horizontalHeader().hide()
        self._tableView.verticalHeader().hide()
        self._layout.addWidget(self._tableView)
        self._layout.addWidget(self._refresh_button)
        self._layout.addWidget(self._msg_select_cb)
        self._layout.addWidget(self._attr_select_cb)
        self._layout.addWidget(self._multiplier_text)
        self._layout.addWidget(self._low_text)
        self._layout.addWidget(self._high_text)
        self._layout.addWidget(self._add_button)
        self.__init_connections__()
        self._widget.setLayout(self._layout)
        self.setCentralWidget(self._widget)
        # TODO: add multiplier, low, and high labels
        # TODO: make the layout nicer

    def __init_connections__(self):
        """ instances of this class must define slots for:
            mav_connect
            add_msg
            remove_selected_msg
            refresh_msg_select
            refresh_attr_select
            update_add_button """
        self.con_text.lineEdit().returnPressed.connect(self.mav_connect)
        self.con_button.clicked.connect(self.mav_connect)
        self.add_button.clicked.connect(self.add_msg)
        self.remove_button.clicked.connect(self.remove_selected_msg)
        self.refresh_button.clicked.connect(self.refresh_msg_select)
        self.msg_select_cb.currentIndexChanged.connect(self.refresh_attr_select)
        self.attr_select_cb.currentIndexChanged.connect(self.update_add_button)
        
    # I bet there's a better way to do this than defining every UI element as a property...
    # ...but I'm just not gonna worry about that right now...

    @property
    def layout(self):
        return self._layout

    @property
    def con_text(self):
        return self._con_text

    @property
    def con_button(self):
        return self._con_button

    @property
    def remove_button(self):
        return self._remove_button

    @property
    def tableView(self):
        return self._tableView

    @property
    def refresh_button(self):
        return self._refresh_button

    @property
    def msg_select_cb(self):
        return self._msg_select_cb

    @property
    def attr_select_cb(self):
        return self._attr_select_cb

    @property
    def multiplier_text(self):
        return self._multiplier_text

    @property
    def low_text(self):
        return self._low_text

    @property
    def high_text(self):
        return self._high_text
    
    @property
    def add_button(self):
        return self._add_button

