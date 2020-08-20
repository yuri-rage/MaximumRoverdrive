"""
    companion app to Mission Planner or other MAVLink GCS software
    monitors user selected MAVLink messages in a GUI
    converts between waypoint and polygon mission files
    sends custom commands via MAVLink
    TODO: maybe a 3rd tab with scrolling STATUSTEXT messages?
    TODO: send waypoint missions?  can we use MAVftp for faster transfer?

    -- Yuri -- Aug 2020
 """

import sys
from sys import argv, float_info
from os import getcwd, path
from inspect import signature, getmembers, isclass
from maximum_roverdrive.config_io import ConfigIO
from maximum_roverdrive.mavmonitor import MavMonitor
from maximum_roverdrive import mav_commands
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
        self.mav_commands = getmembers(mav_commands, isclass)
        self.init_ui()
        self.ev_observer = Observer()
        self.mission_folder = self.cfg.mission_folder
        self.mission_file_changed.connect(self.update_text_mission_file)
        self.init_watchdog()

    def init_ui(self):
        self.combo_port.addItems(self.cfg.ports)
        self.statusBar().showMessage('Disconnected')
        self.initialize()
        self.update_mav_commands(self.combo_mav_command_start)
        self.update_mav_commands(self.combo_mav_command_end)

    def update_mav_commands(self, combo):
        if combo.count() == 0:
            combo.addItems([cmd for cmd, cls in self.mav_commands])

        if combo == self.combo_mav_command_start:
            frame = self.frame_mav_command_start
            labels = self.labels_mav_command_start
            texts = self.texts_mav_command_start
        elif combo == self.combo_mav_command_end:
            frame = self.frame_mav_command_end
            labels = self.labels_mav_command_end
            texts = self.texts_mav_command_end
        else:
            return

        cls_name, cls = list(filter(lambda c: combo.currentText() in c, self.mav_commands))[0]
        params = list(signature(cls).parameters.keys())
        frame.setToolTip(cls().description())

        texts[0].clear()
        texts[0].lineEdit().setText('')
        if cls_name == 'SET_MODE':
            try:
                texts[0].addItems(list(mav_commands.MODES))
            except TypeError:
                pass

        for x in range(len(labels)):
            try:
                labels[x].setText(params[x].capitalize())
                texts[x].setEnabled(True)
                if x > 0:
                    texts[x].setText('')
            except IndexError:
                labels[x].setText('')
                texts[x].setEnabled(False)
                if x > 0:
                    texts[x].setText('')

        if cls_name == 'MavlinkCommandLong':
            texts[0].setEnabled(True)
            texts[0].addItems([cmd for cmd, val in mav_commands.MAV_CMD_LIST])
            for x in range(1, len(labels)):
                labels[x].setText(f'Arg{x}')
                texts[x].setEnabled(True)
            return

    # TODO: actually send these commands now!
    # commands = getmembers(mav_commands, isclass)
    # command_names = [cmd for cmd, cls in getmembers(mav_commands, isclass)]
    # print(command_names)
    # for cmd in commands:
    #     print(cmd)
    # name, cmd = list(filter(lambda n: 'SET_HOME' in n, commands))[0]
    # print(name, cmd(34, -96, 0).to_waypoint_command_string(3))
    # sig = signature(cmd)
    # for p in sig.parameters:
    #     print(p.capitalize())

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

    @pyqtSlot()
    def update_combo_mav_command(self):
        self.update_mav_commands(self.sender())

    @pyqtSlot()
    def mav_command_send(self):
        if self.sender() == self.button_mav_command_start_send:
            cmd = self.combo_mav_command_start.currentText()
            arg_texts = self.texts_mav_command_start
        elif self.sender() == self.button_mav_command_end_send:
            cmd = self.combo_mav_command_end.currentText()
            arg_texts = self.texts_mav_command_end
        else:
            return
        self.mav_command(cmd, arg_texts, True)

    def mav_command(self, cmd, arg_texts, do_send=False):
        args = []
        for arg in arg_texts:
            try:
                if arg.text() != '':
                    try:
                        val = float(arg.text())
                    except ValueError:
                        val = arg.text()
                    args.append(val)
            except AttributeError:
                if arg.lineEdit().text() != '':
                    try:
                        val = float(arg.lineEdit().text())
                    except ValueError:
                        val = arg.lineEdit().text()
                    args.append(val)
        cls = list(filter(lambda command: cmd in command, getmembers(mav_commands, isclass)))[0][1]

        if cmd == 'MavlinkCommandLong':
            cmd = args.pop(0)
            cmd = list(filter(lambda command: command[0] == cmd, mav_commands.MAV_CMD_LIST))[0][1]
            args = [cmd, args]

        if do_send:
            cls(*args).send()
        # TODO: use this to craft file strings also - need a conditional to determine whether to send (or not...)
        # TODO: maybe store current position to pass to SET_HOME as we get it in the monitor
        return cls(*args).to_waypoint_command_string()

    @pyqtSlot(str)
    def update_text_mission_file(self, filename):
        if path.exists(filename):
            self.text_mission_file.setText(filename)

    @pyqtSlot(bool)
    def convert_mission_file(self, modify=False, 
                             cmd_start=None, cmd_start_add_all=False, cmd_end=None, cmd_end_add_all=False):
        filename = self.text_mission_file.toPlainText()
        if filename is None or not path.exists(filename):
            self.statusBar().showMessage(f'{"File" if filename == "" or filename is None else filename} not found...')
            return
        self.kill_watchdog()
        lat = self.mavlink.location.lat
        lng = self.mavlink.location.lng
        alt = self.mavlink.location.alt
        if not modify:
            result = WaypointConverter(filename, lat, lng, alt)
        else:

            result = WaypointConverter(filename, lat, lng, alt,
                                       True, cmd_start, cmd_start_add_all, cmd_end, cmd_end_add_all)
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
    def modify_mission_file(self):
        cmd_start = None
        cmd_start_add_all = False
        cmd_end = None
        cmd_end_add_all = False
        if self.checkbox_mav_command_start.isChecked() or self.checkbox_mav_command_start_all.isChecked():
            cmd_start = self.mav_command(self.combo_mav_command_start.currentText(), self.texts_mav_command_start)
        if self.checkbox_mav_command_start_all.isChecked():
            cmd_start_add_all = True
        if self.checkbox_mav_command_end.isChecked() or self.checkbox_mav_command_end_all.isChecked():
            cmd_end = self.mav_command(self.combo_mav_command_end.currentText(), self.texts_mav_command_end)
        if self.checkbox_mav_command_end_all.isChecked():
            cmd_end_add_all = True
        self.convert_mission_file(True, cmd_start, cmd_start_add_all, cmd_end, cmd_end_add_all)

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
            self.mavlink = MavMonitor(self, mav_commands.MAV_CMD_LIST)
            self.statusBar().showMessage('Awaiting heartbeat...')
            mav_commands.init(self.mavlink)  # this waits for heartbeat
            self.statusBar().showMessage(f'MAVLink {mav_commands.MAVLINK_VERSION} -- '
                                         f'SYSTEM: {self.mavlink.connection.target_system}  //  '
                                         f'COMPONENT: {self.mavlink.connection.target_component}')
            self.button_connect.setText('Disconnect')
            self.combo_port.setEnabled(False)
            self.mavlink.start_updates()
        else:
            self.mav_disconnect()

    @pyqtSlot()
    def arm(self):
        mav_commands.ARM().send()

    @pyqtSlot()
    def disarm(self):
        mav_commands.DISARM().send()

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
