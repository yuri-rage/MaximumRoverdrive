from os import getcwd
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QDir
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, \
     QComboBox, QPushButton, QTableView, QLabel, QLineEdit, QTextEdit, QCheckBox, \
     QFrame, QFileDialog, QMessageBox


class QLabelClickable(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class MainWindow(QMainWindow):
    """ handle the bulk of the ugliness of window/widget geometry
        QMainWindow affords a built-in status bar, otherwise this could just be a QWidget
        written by 'hand' instead of by Qt Designer as an exercise in understanding PyQt5 """

    def __init__(self):
        super(MainWindow, self).__init__()

        self.mission_folder = getcwd()

        # containing widgets/layouts
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout(self.central_widget)
        self.widget_horizontal = QWidget()
        self.layout_horizontal = QHBoxLayout(self.widget_horizontal)

        # pymavlink widgets (left pane)
        self.widget_mav_monitor = QWidget()
        self.layout_mav_monitor = QVBoxLayout(self.widget_mav_monitor)
        self.combo_port = QComboBox()
        self.button_connect = QPushButton('Connect')
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
        self.button_msg_add = QPushButton('Add')

        # utilities widgets (right pane)
        self.widget_utilities = QWidget()
        self.layout_utilities = QVBoxLayout(self.widget_utilities)
        self.label_about = QLabelClickable('About')
        self.label_mission_command = QLabel('Command to execute:')
        self.combo_mission_command = QComboBox()
        self.checkbox_mission_start = QCheckBox('Mission Start/Stop:')
        self.checkbox_mission_all = QCheckBox('At Each Waypoint:')
        self.button_convert_file = QPushButton('Convert File')

        # file widgets at bottom of central vertical layout
        self.frame_mission_file = QFrame()
        self.form_mission_file = QFormLayout()
        self.button_mission_file = QPushButton('Select Waypoint/Poly\nFile to Convert')
        self.text_mission_file = QTextEdit()
        # TODO: finish utilities layout and functionality

    def __init_ui__(self):
        """ called by 'public' method self.initialize()  """
        # set up the pymavlink widget layout
        self.combo_port.setEditable(True)
        self.layout_mav_monitor.addWidget(self.combo_port)
        self.layout_mav_monitor.addWidget(self.button_connect)
        self.table_messages.horizontalHeader().setStretchLastSection(True)
        self.table_messages.horizontalHeader().hide()
        self.table_messages.verticalHeader().hide()
        self.layout_mav_monitor.addWidget(self.table_messages)
        self.layout_mav_monitor.addWidget(self.button_msg_remove)
        self.combo_msg_select.addItem('Click refresh')
        self.form_msg_request.addRow(self.button_msg_refresh, self.combo_msg_select)
        self.form_msg_request.addRow('Message Content:', self.combo_attr_select)
        self.form_msg_request.addRow('Multiplier:', self.text_multiplier)
        self.form_msg_request.addRow('Low Threshold:', self.text_low)
        self.form_msg_request.addRow('High Threshold:', self.text_high)
        self.form_msg_request.addRow(self.button_msg_add)
        self.frame_msg_request.setLayout(self.form_msg_request)
        self.layout_mav_monitor.addWidget(self.frame_msg_request)

        # set up the utilities widget layout
        self.label_about.setObjectName('label_about')
        self.label_about.setCursor(QCursor(Qt.PointingHandCursor))
        self.layout_utilities.addWidget(self.label_about)
        self.layout_utilities.addWidget(self.label_mission_command)
        self.layout_utilities.addWidget(self.combo_mission_command)
        self.layout_utilities.addWidget(self.checkbox_mission_start)
        self.layout_utilities.addWidget(self.checkbox_mission_all)
        self.layout_utilities.addWidget(self.button_convert_file)

        # set up the filename container at the bottom of the central vertical layout
        self.frame_mission_file.setStyleSheet('QFrame { border: 0px; }'
                                              'QTextEdit { border: 1px solid #515253; }'
                                              'QTextEdit:focus { border: 1px solid #53a0ed; }')
        # self.button_mission_file.setFixedHeight(40)
        self.button_mission_file.setContentsMargins(10, 10, 10, 10)
        self.text_mission_file.setFixedHeight(40)
        self.form_mission_file.addRow(self.button_mission_file, self.text_mission_file)
        self.frame_mission_file.setLayout(self.form_mission_file)

        # TODO: finish utilities layout and functionality

    def initialize(self):  # allows for instantiating method to populate list/text items before painting
        """ must be called after class instantiation for window to be displayed """
        self.__init_ui__()  # populate the layouts

        # set up the main window
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Maximum Roverdrive')

        # put the central widget together
        self.central_layout.setContentsMargins(5, 10, 5, 10)
        self.layout_horizontal.setContentsMargins(0, 0, 0, 0)
        self.layout_mav_monitor.setContentsMargins(0, 0, 0, 0)
        self.layout_utilities.setContentsMargins(0, 0, 0, 0)
        self.widget_mav_monitor.setMinimumWidth(350)
        self.widget_utilities.setMinimumWidth(180)
        self.layout_horizontal.addWidget(self.widget_mav_monitor)
        self.layout_horizontal.addWidget(self.widget_utilities)
        self.central_layout.addWidget(self.widget_horizontal)
        self.central_layout.addWidget(self.frame_mission_file)
        self.setCentralWidget(self.central_widget)

        self.__init_connections__()  # connect the ui signals
        # TODO: finish layout design/tweaks

    def __init_connections__(self):
        """ called by 'public' method self.initialize()
            instances of this class must define slots for:
            mav_connect
            add_msg
            remove_selected_msg
            refresh_msg_select
            refresh_attr_select
            update_button_msg_add """
        self.combo_port.lineEdit().returnPressed.connect(self.mav_connect)
        self.button_connect.clicked.connect(self.mav_connect)
        self.button_msg_add.clicked.connect(self.add_msg)
        self.button_msg_remove.clicked.connect(self.remove_selected_msg)
        self.button_msg_refresh.clicked.connect(self.refresh_msg_select)
        self.combo_msg_select.currentIndexChanged.connect(self.refresh_attr_select)
        self.combo_attr_select.currentIndexChanged.connect(self.update_button_msg_add)
        self.button_convert_file.clicked.connect(self.convert_mission_file)
        self.button_mission_file.clicked.connect(self.mission_file_dialog)  # not abstract
        self.label_about.clicked.connect(self.about)  # not abstract
        # TODO: create connections for utilities widgets

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
        msg.setStyleSheet('QMessageBox { border-image: url(:/images/logo.png); }'
                          'QLabel { width: 443px; min-width: 443px; max-width: 443px;'
                          'height: 251px; min-height: 251px; max-height: 251px; '
                          'font-family: "Copperplate Gothic Bold", sans-serif; '
                          'font-size: 20px; font-weight: 500; }')
        msg.setText('© 2020, Yuri\n\n\n\n\n\n\n\n\n\n')
        msg.exec()

