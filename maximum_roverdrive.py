import sys
from sys import argv, float_info
from maximum_roverdrive.config_io import ConfigIO
from maximum_roverdrive.mavmonitor import MavMonitor
from maximum_roverdrive.qappmplookandfeel import QAppMPLookAndFeel
from maximum_roverdrive.main_window import MainWindow
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QAction


class MaximumRoverdrive(MainWindow):

    def __init__(self):
        super(MaximumRoverdrive, self).__init__()
        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)
        self.cfg = ConfigIO()
        self.mavlink = MavMonitor()
        self.init_ui()

    def init_ui(self):
        super(MaximumRoverdrive, self).__init_ui__()
        self.con_text.addItems(self.cfg.ports)
        self.statusBar().showMessage('Disconnected')


    @pyqtSlot()
    def refresh_msg_select(self):
        if self.mavlink.messages:
            self.msg_select_cb.clear()
            sorted_msgs = sorted(self.mavlink.messages)
            self.msg_select_cb.addItems(sorted_msgs)

    @pyqtSlot()
    def refresh_attr_select(self):
        if self.mavlink.messages:
            msg = self.msg_select_cb.currentText()
            if len(msg) > 0:
                self.attr_select_cb.clear()
                self.attr_select_cb.addItems(self.mavlink.messages[msg].keys())

    @pyqtSlot()
    def update_add_button(self):
        self.add_button.setText('Add ' + self.msg_select_cb.currentText() + '.' + self.attr_select_cb.currentText())

    @pyqtSlot()
    def add_msg(self):
        msg = self.msg_select_cb.currentText()
        attr = self.attr_select_cb.currentText()
        try:
            multiplier = float(self.multiplier_text.text())
        except ValueError:
            multiplier = 1.0
        try:
            low = float(self.low_text.text())
        except ValueError:
            low = float_info.max * -1.0
        try:
            high = float(self.high_text.text())
        except ValueError:
            high = float_info.max
        self.cfg.add_msg(msg, attr, multiplier, low, high)
        self.mavlink.add_msg(msg, attr, multiplier, low, high)
        self.multiplier_text.setText(str(multiplier))
        self.low_text.setText(str(low))
        self.high_text.setText(str(high))

    @pyqtSlot()
    def remove_selected_msg(self):
        row = self.tableView.selectedIndexes()[0].row()
        index = self.tableView.model().index(row, 0)
        msg = self.tableView.model().data(index)
        msg_split = msg.split('.')
        try:
            self.cfg.del_msg(msg_split[0], msg_split[1])
        except IndexError:
            pass
        self.mavlink.remove_selected()

    @pyqtSlot()
    def mav_connect(self):
        if self.con_button.text() == 'Connect':
            self.cfg.add_port(self.con_text.currentText())
            self.mavlink = MavMonitor(self.con_text.currentText(), self.tableView, self.cfg.messages)
            self.statusBar().showMessage('Awaiting heartbeat...')
            self.mavlink.connection.wait_heartbeat()
            self.statusBar().showMessage('Connected -- SYSTEM: {s}  //  COMPONENT: {c}'.format(
                s=self.mavlink.connection.target_system, c=self.mavlink.connection.target_component + 1))
            self.con_button.setText('Disconnect')
            self.con_text.setEnabled(False)
            self.mavlink.start_updates()
        else:
            self.mav_disconnect()

    @pyqtSlot(bool)
    def closeEvent(self, event):
        if self.con_button.text() == "Disconnect":
            self.mav_disconnect()

    def mav_disconnect(self):
        self.mavlink.disconnect()
        self.con_button.setText('Connect')
        self.con_text.setEnabled(True)
        self.statusBar().showMessage('Disconnected')


# force PyQt5 to provide traceback messages for debugging
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def main():
    sys.excepthook = except_hook
    app = QAppMPLookAndFeel(argv)
    window = MaximumRoverdrive()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
