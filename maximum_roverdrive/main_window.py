from os import getcwd
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QDir
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QGridLayout,\
     QComboBox, QPushButton, QTableView, QLabel, QLineEdit, QTextEdit, QCheckBox, QFrame, QFileDialog, QMessageBox


class QLabelClickable(QLabel):
    clicked = pyqtSignal()

    def __init__(self, caption, parent=None):
        QLabel.__init__(self, caption, parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class QTextStatus(QTextEdit):
    status_text_changed = pyqtSignal(int, str)

    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)


class QWideComboBox(QComboBox):
    """ auto resizes the dropdown list to contents (plus a little margin) """
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)

    def showPopup(self):
        self.view().setMinimumWidth(self.view().sizeHintForColumn(0) + 12)
        QComboBox.showPopup(self)


class MainWindow(QMainWindow):
    """
    handle the bulk of the ugliness of window/widget geometry
    QMainWindow affords a built-in status bar, otherwise this could just be a QWidget
    written by 'hand' instead of by Qt Designer as an exercise in understanding PyQt5
    in hindsight, this should've been broken down into more functions or even classes...
    """

    def __init__(self):
        super(MainWindow, self).__init__()

        self.mission_folder = getcwd()

        # central widgets/layouts
        self.central_widget = QTabWidget()
        self.central_layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget()
        self.label_about = QLabelClickable('About Maximum Roverdrive', self.tabs)
        self.label_about.setObjectName('label_about')

        # monitor widgets (left tab)
        self.widget_mav_monitor = QWidget()
        self.layout_mav_monitor = QVBoxLayout(self.widget_mav_monitor)
        self.frame_connect = QFrame()
        self.layout_connect = QHBoxLayout(self.frame_connect)
        self.button_connect = QPushButton('Connect')
        self.combo_port = QComboBox()
        self.widget_add_remove_buttons = QWidget()
        self.layout_add_remove_buttons = QHBoxLayout(self.widget_add_remove_buttons)
        self.button_msg_add = QPushButton('Add Message')
        self.button_msg_remove = QPushButton('Remove Selected Message')
        self.table_messages = QTableView()
        self.frame_msg_request = QFrame()
        self.form_msg_request = QFormLayout()
        self.form_msg_request.setLabelAlignment(Qt.AlignRight)
        self.button_msg_refresh = QPushButton('Refresh Messages')
        self.combo_msg_select = QComboBox()
        self.combo_attr_select = QComboBox()
        self.text_multiplier = QLineEdit('1.0')
        self.text_low = QLineEdit('0.0')
        self.text_high = QLineEdit('1000.0')

        # utilities widgets (center tab)
        self.widget_utilities = QWidget()
        self.layout_utilities = QVBoxLayout(self.widget_utilities)
        self.frame_utilities_header = QFrame()
        self.grid_utilities_header = QGridLayout(self.frame_utilities_header)
        self.button_arm = QPushButton('ARM')
        self.button_disarm = QPushButton('DISARM')
        self.label_headlight_relay = QLabel('Light Relay')
        self.checkbox_auto_headlights = QCheckBox('   Enable\n Automatic\nHeadlights')
        self.checkbox_relay_active_low = QCheckBox('  Relays\nActive Low')
        self.combo_headlight_relay = QComboBox()
        self.frame_mav_command_start = QFrame()
        self.frame_mav_command_start.setObjectName('mav_command_start')
        self.grid_mav_command_start = QGridLayout(self.frame_mav_command_start)
        self.label_mav_command_start = QLabel('Command at <span style="color: #94d6a3; font-weight: bold;">'
                                              'Mission Start:</span>')
        self.combo_mav_command_start = QComboBox()
        self.labels_mav_command_start = [QLabel()] * 8
        self.texts_mav_command_start = [QComboBox()]
        self.texts_mav_command_start.extend([QLineEdit()] * 7)
        self.button_mav_command_start_send = QPushButton('Send Now')
        self.checkbox_mav_command_start = QCheckBox('On Mission Start')
        self.checkbox_mav_command_start_all = QCheckBox('At Each WP')
        self.frame_mav_command_end = QFrame()
        self.frame_mav_command_end.setObjectName('mav_command_end')
        self.grid_mav_command_end = QGridLayout(self.frame_mav_command_end)
        self.label_mav_command_end = QLabel('Command at <span style="color: #ffe383; font-weight: bold;">'
                                            'Mission End:</span>')
        self.combo_mav_command_end = QComboBox()
        self.labels_mav_command_end = [QLabel()] * 8
        self.texts_mav_command_end = [QComboBox()]
        self.texts_mav_command_end.extend([QLineEdit()] * 7)
        self.button_mav_command_end_send = QPushButton('Send Now')
        self.checkbox_mav_command_end = QCheckBox('On Mission End')
        self.checkbox_mav_command_end_all = QCheckBox('At Each WP')

        # status messages (right tab)
        self.widget_status = QWidget()
        self.layout_status = QVBoxLayout(self.widget_status)
        self.text_status = QTextStatus()

        # file widgets at bottom of central vertical layout
        self.frame_mission_file = QFrame()
        self.grid_mission_file = QGridLayout(self.frame_mission_file)
        self.button_mission_file = QPushButton('Select\nMission File')
        self.text_mission_file = QTextEdit()
        self.button_convert_file = QPushButton('Convert File')
        self.button_modify_file = QPushButton('Modify File')

    def __init_ui__(self):
        """ called by 'public' method self.initialize()  """
        # set up the monitor widget layout
        self.layout_connect.setContentsMargins(0, 0, 0, 0)
        self.frame_connect.setStyleSheet('QFrame { border: 0px; }')
        self.combo_port.setEditable(True)
        self.button_connect.setMaximumWidth(85)
        self.layout_connect.addWidget(self.combo_port)
        self.layout_connect.addWidget(self.button_connect)
        self.layout_mav_monitor.addWidget(self.frame_connect)
        self.table_messages.horizontalHeader().setStretchLastSection(True)
        self.table_messages.horizontalHeader().hide()
        self.table_messages.verticalHeader().hide()
        self.layout_mav_monitor.addWidget(self.table_messages)
        self.layout_add_remove_buttons.addWidget(self.button_msg_add)
        self.layout_add_remove_buttons.addWidget(self.button_msg_remove)
        self.layout_add_remove_buttons.setContentsMargins(5, 5, 5, 5)
        self.layout_mav_monitor.addWidget(self.widget_add_remove_buttons)
        self.combo_msg_select.addItem('Click refresh')
        self.form_msg_request.addRow(self.button_msg_refresh, self.combo_msg_select)
        self.form_msg_request.addRow('Message Content:', self.combo_attr_select)
        self.form_msg_request.addRow('Multiplier:', self.text_multiplier)
        self.form_msg_request.addRow('Low Threshold:', self.text_low)
        self.form_msg_request.addRow('High Threshold:', self.text_high)
        self.frame_msg_request.setLayout(self.form_msg_request)
        self.layout_mav_monitor.addWidget(self.frame_msg_request)

        # set up the utilities widget layout
        self.grid_utilities_header.setColumnStretch(0, 4)
        self.button_arm.setMinimumWidth(76)
        self.button_disarm.setMinimumWidth(76)
        self.grid_utilities_header.setRowStretch(1, 2)
        self.button_arm.setEnabled(False)
        self.button_disarm.setEnabled(False)
        self.button_mav_command_start_send.setEnabled(False)
        self.button_mav_command_end_send.setEnabled(False)
        self.grid_utilities_header.addWidget(self.button_arm, 0, 0)
        self.grid_utilities_header.addWidget(self.button_disarm, 1, 0)
        self.grid_utilities_header.addWidget(self.checkbox_relay_active_low, 0, 2, 2, 1)
        self.grid_utilities_header.addWidget(self.checkbox_auto_headlights, 0, 3, 2, 1)
        self.label_headlight_relay.setStyleSheet('QLabel { qproperty-alignment: AlignCenter; }')
        self.grid_utilities_header.addWidget(self.label_headlight_relay, 0, 4)
        self.combo_headlight_relay.addItems([str(x) for x in range(7)])
        self.combo_headlight_relay.setEditable(True)
        self.combo_headlight_relay.lineEdit().setReadOnly(True)
        self.combo_headlight_relay.lineEdit().setAlignment(Qt.AlignCenter)
        self.grid_utilities_header.addWidget(self.combo_headlight_relay, 1, 4)
        self.grid_utilities_header.setContentsMargins(5, 5, 5, 5)

        self.grid_mav_command_start.addWidget(self.label_mav_command_start, 0, 0, 1, 2)
        self.grid_mav_command_start.addWidget(self.combo_mav_command_start, 0, 2, 1, 2)
        for x in range(8):
            self.grid_mav_command_start.setColumnStretch(x, 2)
            y = 1 if x < 4 else 3
            self.labels_mav_command_start[x] = QLabel(f'Arg{x + 1}')
            self.labels_mav_command_start[x].setObjectName('label_arg')
            if x > 1:
                self.texts_mav_command_start[x] = QLineEdit()
            else:
                self.texts_mav_command_start[x] = QWideComboBox()
                self.texts_mav_command_start[x].setEditable(True)
                self.texts_mav_command_start[x].lineEdit().setAlignment(Qt.AlignCenter)
                self.texts_mav_command_start[x].SizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
            self.texts_mav_command_start[x].setObjectName('text_arg')
            self.texts_mav_command_start[x].setMinimumWidth(82)
            self.grid_mav_command_start.addWidget(self.labels_mav_command_start[x], y, x % 4)
            self.grid_mav_command_start.addWidget(self.texts_mav_command_start[x], y + 1, x % 4)

        self.grid_mav_command_start.addWidget(self.button_mav_command_start_send, 5, 3)
        self.grid_mav_command_start.addWidget(self.checkbox_mav_command_start, 5, 0, 1, 2)
        self.grid_mav_command_start.addWidget(self.checkbox_mav_command_start_all, 5, 2)

        self.grid_mav_command_end.addWidget(self.label_mav_command_end, 0, 0, 1, 2)
        self.grid_mav_command_end.addWidget(self.combo_mav_command_end, 0, 2, 1, 2)
        for x in range(8):
            self.grid_mav_command_end.setColumnStretch(x, 2)
            y = 1 if x < 4 else 3
            self.labels_mav_command_end[x] = QLabel(f'Arg{x + 1}')
            self.labels_mav_command_end[x].setObjectName('label_arg')
            if x > 1:
                self.texts_mav_command_end[x] = QLineEdit()
            else:
                self.texts_mav_command_end[x] = QWideComboBox()
                self.texts_mav_command_end[x].setEditable(True)
                self.texts_mav_command_end[x].lineEdit().setAlignment(Qt.AlignCenter)
                self.texts_mav_command_end[x].SizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
            self.texts_mav_command_end[x].setMinimumWidth(82)
            self.grid_mav_command_end.addWidget(self.labels_mav_command_end[x], y, x % 4)
            self.grid_mav_command_end.addWidget(self.texts_mav_command_end[x], y + 1, x % 4)
        self.grid_mav_command_end.addWidget(self.button_mav_command_end_send, 5, 3)
        self.grid_mav_command_end.addWidget(self.checkbox_mav_command_end, 5, 0, 1, 2)
        self.grid_mav_command_end.addWidget(self.checkbox_mav_command_end_all, 5, 2)

        self.layout_utilities.addWidget(self.frame_utilities_header)
        self.layout_utilities.addWidget(self.frame_mav_command_start)
        self.layout_utilities.addWidget(self.frame_mav_command_end)

        # set up the filename container at the bottom of the central vertical layout
        self.frame_mission_file.setStyleSheet('QFrame { border: 0px; }'
                                              'QTextEdit { border: 1px solid #515253; }'
                                              'QTextEdit:focus { border: 1px solid #53a0ed; }')
        self.button_mission_file.setContentsMargins(10, 10, 10, 10)
        self.text_mission_file.setFixedHeight(40)
        self.text_mission_file.setToolTip('Auto-filled when files change in the Mission file folder\n'
                                          'Override by clicking the button to choose a file')
        for x in range(4):
            self.grid_mission_file.setColumnStretch(x, 2)
        self.grid_mission_file.addWidget(self.button_mission_file, 0, 0)
        self.grid_mission_file.addWidget(self.text_mission_file, 0, 1, 1, 3)
        self.grid_mission_file.addWidget(self.button_convert_file, 1, 0, 1, 2)
        self.grid_mission_file.addWidget(self.button_modify_file, 1, 2, 1, 2)
        self.grid_mission_file.setContentsMargins(5, 0, 5, 5)

        # set up the status messages tab
        self.text_status.setReadOnly(True)
        self.layout_status.addWidget(self.text_status)
        self.layout_status.setContentsMargins(0, 0, 0, 0)

    def initialize(self):  # allows for instantiating method to populate list/text items before painting
        """ must be called after class instantiation for window to be displayed """
        self.__init_ui__()  # populate the layouts

        # set up the main window
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Maximum Roverdrive')

        # put the central widget together
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.layout_mav_monitor.setContentsMargins(5, 5, 5, 5)
        self.layout_utilities.setContentsMargins(5, 5, 5, 5)
        self.central_widget.setMinimumWidth(400)
        self.central_widget.setMinimumHeight(502)
        self.tabs.addTab(self.widget_mav_monitor, 'Monitor')
        self.tabs.addTab(self.widget_utilities, 'Utilities')
        self.tabs.addTab(self.widget_status, 'Messages')
        self.central_layout.addWidget(self.tabs)
        self.central_layout.addWidget(self.frame_mission_file)
        self.label_about.setCursor(QCursor(Qt.PointingHandCursor))
        self.label_about.move(240, 2)
        self.setCentralWidget(self.central_widget)

        self.__init_connections__()  # connect the ui signals

    def __init_connections__(self):
        """
            called by 'public' method self.initialize()
            instances of this class must define slots for the following connections:
         """
        self.combo_port.lineEdit().returnPressed.connect(self.mav_connect)
        self.button_connect.clicked.connect(self.mav_connect)
        self.button_msg_add.clicked.connect(self.add_msg)
        self.button_msg_remove.clicked.connect(self.remove_selected_msg)
        self.button_msg_refresh.clicked.connect(self.refresh_msg_select)
        self.combo_msg_select.currentIndexChanged.connect(self.refresh_attr_select)
        self.combo_attr_select.currentIndexChanged.connect(self.update_button_msg_add)

        self.button_arm.clicked.connect(self.arm)
        self.button_disarm.clicked.connect(self.disarm)
        self.checkbox_relay_active_low.clicked.connect(self.save_relay_state)
        self.checkbox_auto_headlights.clicked.connect(self.save_auto_headlights_state)
        self.combo_headlight_relay.currentTextChanged.connect(self.save_headlight_relay)
        self.button_mav_command_start_send.clicked.connect(self.mav_command_send)
        self.button_mav_command_end_send.clicked.connect(self.mav_command_send)

        self.combo_mav_command_start.currentIndexChanged.connect(self.update_combo_mav_command)
        self.combo_mav_command_end.currentIndexChanged.connect(self.update_combo_mav_command)
        self.button_convert_file.clicked.connect(self.convert_mission_file)
        self.button_modify_file.clicked.connect(self.modify_mission_file)

        # these are not abstract
        self.label_about.clicked.connect(self.about)
        self.button_mission_file.clicked.connect(self.mission_file_dialog)

    @pyqtSlot()
    def mission_file_dialog(self):
        filename = QFileDialog.getOpenFileName(self, caption='Select Waypoint/Poly File',
                                               directory=self.mission_folder,
                                               filter='Mission Files (*.waypoints *.poly);;All files (*.*)',
                                               options=QFileDialog.DontUseNativeDialog)
        if filename != ('', ''):
            filename = QDir.toNativeSeparators(filename[0])
            self.text_mission_file.setText(filename)
            return filename
        return None

    @pyqtSlot()
    def about(self):
        msg = QMessageBox(icon=QMessageBox.NoIcon)
        msg.setWindowFlag(Qt.WindowStaysOnTopHint)
        msg.setWindowTitle('About Maximum Roverdrive')
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setTextFormat(Qt.RichText)
        msg.setStyleSheet('QMessageBox { border-image: url(:/images/logo.png); }'
                          'QLabel { width: 443px; min-width: 443px; max-width: 443px;'
                          'height: 251px; min-height: 251px; max-height: 251px; '
                          'font-family: "Copperplate Gothic Bold", sans-serif; '
                          'font-size: 20px; font-weight: 500; }')
        msg.setText('© 2020, Yuri<br>'
                    '''<a style="font-family: 'Calibri, sans-serif'; font-size: 12px; font-weight: normal;"'''
                    'href="https://github.com/yuri-rage/MaximumRoverdrive">View on GitHub</a>'
                    '<br><br><br><br><br><br><br><br><br><br>')
        msg.exec()
