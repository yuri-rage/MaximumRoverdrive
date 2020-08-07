import sys
from maximum_roverdrive.config_io import ConfigIO
from maximum_roverdrive.mavmonitor import MavMonitor
from maximum_roverdrive.qappmplookandfeel import QAppMPLookAndFeel
from maximum_roverdrive.tablemodel import TableModel
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QPushButton, QTableView


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.cfg = ConfigIO()
        self.monitor = MavMonitor()
        self.model = TableModel()
        self.layout = QVBoxLayout()
        self.con_text = QComboBox()
        self.con_button = QPushButton('Connect')
        self.add_button = QPushButton('Add')
        self.remove_button = QPushButton('Remove')
        self.tableView = QTableView()
        self.status_label = QLabel('Disconnected')
        self.init_ui()

    def init_ui(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Maximum Roverdrive')
        self.con_text.addItems(self.cfg.ports)
        self.con_text.setEditable(True)
        self.con_text.lineEdit().returnPressed.connect(self.mav_connect)
        self.con_button.clicked.connect(self.mav_connect)
        self.add_button.clicked.connect(self.add_msg)
        self.remove_button.clicked.connect(self.remove_selected_msg)
        self.layout.addWidget(self.con_text)
        self.layout.addWidget(self.con_button)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.remove_button)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().hide()
        self.tableView.verticalHeader().hide()
        self.layout.addWidget(self.tableView)
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

    @pyqtSlot()
    def add_msg(self):
        self.monitor.add_msg('MISSION_CURRENT', 'seq')
        self.monitor.add_msg('NAV_CONTROLLER_OUTPUT', 'nav_bearing')
        # TODO: update config file sections
        # TODO: select from a list of available messages

    @pyqtSlot()
    def remove_selected_msg(self):
        self.monitor.remove_selected()
        # TODO: update config file sections

    @pyqtSlot()
    def mav_connect(self):
        if self.con_button.text() == 'Connect':
            self.cfg.add_port(self.con_text.currentText())
            self.monitor = MavMonitor(self.con_text.currentText(), self.tableView, self.cfg.messages)
            self.status_label.setText('Awaiting heartbeat...')
            self.monitor.connection.wait_heartbeat()
            self.status_label.setText('Connected -- SYSTEM: {s}  //  COMPONENT: {c}'.format(
                s=self.monitor.connection.target_system, c=self.monitor.connection.target_component + 1))
            self.con_button.setText('Disconnect')
            self.con_text.setEnabled(False)
            self.monitor.start_updates()
        else:
            self.mav_disconnect()

    def mav_disconnect(self):
        self.con_button.setText('Connect')
        self.con_text.setEnabled(True)
        self.monitor.disconnect()
        self.status_label.setText('Disconnected')


def main():
    app = QAppMPLookAndFeel(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
