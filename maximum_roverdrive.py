"""
    companion app to Mission Planner or other MAVLink GCS software
    monitors user selected MAVLink messages in a GUI
    converts between waypoint and polygon mission files
    TODO: sends custom commands via MAVLink

    -- Yuri -- Aug 2020
 """

import sys
from sys import argv, float_info
from os import getcwd, path
from maximum_roverdrive.config_io import ConfigIO
from maximum_roverdrive.mavmonitor import MavMonitor
from maximum_roverdrive.qappmplookandfeel import QAppMPLookAndFeel
from maximum_roverdrive.main_window import MainWindow
from maximum_roverdrive.waypointconverter import WaypointConverter
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QAction


class MaximumRoverdrive(MainWindow):
    mission_file_changed = pyqtSignal(str)

    def __init__(self):
        super(MaximumRoverdrive, self).__init__()
        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)
        self.cfg = ConfigIO()
        self.mavlink = MavMonitor()
        self.init_ui()
        self.ev_observer = Observer()
        self.mission_folder = self.cfg.mission_folder
        self.mission_file_changed.connect(self.update_text_mission_file)
        self.init_watchdog()

    def init_ui(self):
        self.combo_port.addItems(self.cfg.ports)
        self.statusBar().showMessage('Disconnected')
        self.initialize()

    def init_watchdog(self):
        ev_handler = PatternMatchingEventHandler(['*.waypoints', '*.poly'], ignore_directories=True)
        ev_handler.on_any_event = self.on_any_file_event
        if self.mission_folder is None:
            self.mission_folder = getcwd()
        self.ev_observer.schedule(ev_handler, self.mission_folder, recursive=False)
        self.ev_observer.start()
        pass

    def kill_watchdog(self):
        try:
            self.ev_observer.stop()
            self.ev_observer.join()
            self.ev_observer = Observer()
        except RuntimeError:
            pass

    def on_any_file_event(self, event):
        self.mission_file_changed.emit(event.src_path)  # ensure that widgets are updated outside of thread

    @pyqtSlot(str)
    def update_text_mission_file(self, filename):
        if path.exists(filename):
            self.text_mission_file.setText(filename)

    @pyqtSlot()
    def convert_mission_file(self):
        self.kill_watchdog()
        filename = self.text_mission_file.toPlainText()
        if filename is None or not path.exists(filename):
            self.statusBar().showMessage(f'{"File" if filename == "" or filename is None else filename} not found...')
            return
        lat = self.cfg.home_lat
        lng = self.cfg.home_lng
        alt = self.cfg.default_altitude
        result = WaypointConverter(filename, lat, lng, alt)
        if result.error is None:
            mission_folder = path.dirname(filename)
            if mission_folder != self.mission_folder:
                self.mission_folder = mission_folder
                self.cfg.mission_folder = mission_folder
            self.statusBar().showMessage(f'Created {path.basename(result.output_filename)}')
        else:
            self.statusBar().showMessage(f'Could not convert {path.basename(filename)}')
        self.init_watchdog()

    @pyqtSlot()
    def refresh_msg_select(self):
        if self.mavlink.messages:
            self.combo_msg_select.clear()
            sorted_msgs = sorted(self.mavlink.messages)
            self.combo_msg_select.addItems(sorted_msgs)

    @pyqtSlot()
    def refresh_attr_select(self):
        if self.mavlink.messages:
            msg = self.combo_msg_select.currentText()
            if len(msg) > 0:
                self.combo_attr_select.clear()
                self.combo_attr_select.addItems(self.mavlink.messages[msg].keys())

    @pyqtSlot()
    def update_button_msg_add(self):
        self.button_msg_add.setText('Add ' + self.combo_msg_select.currentText()
                                    + '.' + self.combo_attr_select.currentText())

    @pyqtSlot()
    def add_msg(self):
        msg = self.combo_msg_select.currentText()
        attr = self.combo_attr_select.currentText()
        try:
            multiplier = float(self.text_multiplier.text())
        except ValueError:
            multiplier = 1.0
        try:
            low = float(self.text_low.text())
        except ValueError:
            low = float_info.max * -1.0
        try:
            high = float(self.text_high.text())
        except ValueError:
            high = float_info.max
        self.cfg.add_msg(msg, attr, multiplier, low, high)
        self.mavlink.add_msg(msg, attr, multiplier, low, high)
        self.text_multiplier.setText(str(multiplier))
        self.text_low.setText(str(low))
        self.text_high.setText(str(high))

    @pyqtSlot()
    def remove_selected_msg(self):
        row = self.table_messages.selectedIndexes()[0].row()
        index = self.table_messages.model().index(row, 0)
        msg = self.table_messages.model().data(index)
        msg_split = msg.split('.')
        try:
            self.cfg.del_msg(msg_split[0], msg_split[1])
        except IndexError:
            pass
        self.mavlink.remove_selected()

    @pyqtSlot()
    def mav_connect(self):
        if self.button_connect.text() == 'Connect':
            self.cfg.add_port(self.combo_port.currentText())
            self.mavlink = MavMonitor(self.combo_port.currentText(), self.table_messages, self.cfg.messages)
            self.statusBar().showMessage('Awaiting heartbeat...')
            self.mavlink.connection.wait_heartbeat()
            self.statusBar().showMessage('Connected -- SYSTEM: {s}  //  COMPONENT: {c}'.format(
                s=self.mavlink.connection.target_system, c=self.mavlink.connection.target_component + 1))
            self.button_connect.setText('Disconnect')
            self.combo_port.setEnabled(False)
            self.mavlink.start_updates()
        else:
            self.mav_disconnect()


    @pyqtSlot(bool)
    def closeEvent(self, event):
        if self.button_connect.text() == "Disconnect":
            self.mav_disconnect()

    def mav_disconnect(self):
        self.mavlink.disconnect()
        self.button_connect.setText('Connect')
        self.combo_port.setEnabled(True)
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
    window.kill_watchdog()


if __name__ == '__main__':
    main()
