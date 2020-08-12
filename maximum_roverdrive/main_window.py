from PyQt5.QtCore import Qt, QDir
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, \
    QComboBox, QPushButton, QTableView, QLineEdit, QFrame, QFileDialog


class MainWindow(QMainWindow):
    """ handle the bulk of the ugliness of window/widget geometry
        QMainWindow affords a built-in status bar, otherwise this could just be a QWidget
        written by 'hand' instead of by Qt Designer as an exercise in understanding PyQt5 """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.central_widget = QWidget()
        self.central_layout = QHBoxLayout(self.central_widget)

        # define the pymavlink widgets (left pane)
        self.layout_mav_monitor = QVBoxLayout(self.central_widget)
        self.combo_port = QComboBox(self.central_widget)
        self.button_connect = QPushButton('Connect', self.central_widget)
        self.button_msg_remove = QPushButton('Remove Selected Message', self.central_widget)
        self.table_messages = QTableView(self.central_widget)
        self.frame_msg_request = QFrame(self.central_widget)
        self.form_msg_request = QFormLayout(self.central_widget)
        self.form_msg_request.setLabelAlignment(Qt.AlignRight)
        self.button_msg_refresh = QPushButton('  Refresh Messages  ', self.central_widget)
        self.combo_msg_select = QComboBox(self.central_widget)
        self.combo_attr_select = QComboBox(self.central_widget)
        self.text_multiplier = QLineEdit('1.0', self.central_widget)
        self.text_low = QLineEdit('0.0', self.central_widget)
        self.text_high = QLineEdit('1000.0', self.central_widget)
        self.button_msg_add = QPushButton('Add', self.central_widget)

        # define the utilities widgets (right pane)
        self.layout_utilities = QVBoxLayout(self.central_widget)
        self.text_mission_file = QLineEdit('Filename', self.central_widget)
        self.button_mission_file = QPushButton('  Select File to Convert  ', self.central_widget)
        self.button_convert_file = QPushButton('Convert File', self.central_widget)
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
        self.layout_utilities.addWidget(self.button_mission_file)
        self.layout_utilities.addWidget(self.text_mission_file)
        self.layout_utilities.addWidget(self.button_convert_file)
        # TODO: finish utilities layout and functionality

    def initialize(self):  # allows for instantiating method to populate list/text items before painting
        """ must be called after class instantiation for window to be displayed """
        self.__init_ui__()  # populate the layouts

        # set up the main window
        self.setMinimumWidth(300)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Maximum Roverdrive')

        # put the central widget together
        self.central_layout.addLayout(self.layout_mav_monitor)
        self.central_layout.addLayout(self.layout_utilities)
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
        self.button_mission_file.clicked.connect(self.folder_picker)  # not abstract
        # TODO: create connections for utilities widgets

    def folder_picker(self):
        filename = QFileDialog.getOpenFileName(self, caption='Select Waypoint/Poly File',
                                               filter="Mission Files (*.waypoints *.poly);;All files (*.*)",
                                               options=QFileDialog.DontUseNativeDialog)
        if filename:
            filename = QDir.toNativeSeparators(filename[0])
            self.text_mission_file.setText(filename)
            return filename
        return None
