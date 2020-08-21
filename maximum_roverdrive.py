"""
    companion app to Mission Planner or other MAVLink GCS software
    monitors user selected MAVLink messages in a GUI
    converts between waypoint and polygon mission files
    sends custom commands via MAVLink
    scrolls all received GCS messages by color coded severity
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
from maximum_roverdrive.main_window import MainWindow, QWideComboBox
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
        self.checkbox_relay_active_low.setChecked(not bool(self.cfg.relay_active_state))
        self.checkbox_auto_headlights.setChecked(bool(self.cfg.auto_headlights))
        self.combo_headlight_relay.lineEdit().setText(str(self.cfg.headlight_relay))
        commands = [cmd for cmd, cls in self.mav_commands]
        self.combo_mav_command_start.addItems(commands)
        self.combo_mav_command_end.addItems(commands)
        self.combo_mav_command_start.setCurrentText(
            self.cfg.get_most_recent('wp_start_preferences'))
        self.combo_mav_command_end.setCurrentText(
            self.cfg.get_most_recent('wp_end_preferences'))

    def update_mav_commands(self, combo):
        if combo == self.combo_mav_command_start:
            frame = self.frame_mav_command_start
            labels = self.labels_mav_command_start
            texts = self.texts_mav_command_start
            values = self.cfg.get_wp_preference('wp_start_preferences', combo.currentText()).split(',')
            self.checkbox_mav_command_start.setChecked(bool(int(values[8])))
            self.checkbox_mav_command_start_all.setChecked(bool(int(values[9])))
        elif combo == self.combo_mav_command_end:
            frame = self.frame_mav_command_end
            labels = self.labels_mav_command_end
            texts = self.texts_mav_command_end
            values = self.cfg.get_wp_preference('wp_end_preferences', combo.currentText()).split(',')
            self.checkbox_mav_command_end.setChecked(bool(int(values[8])))
            self.checkbox_mav_command_end_all.setChecked(bool(int(values[9])))
        else:
            return

        cls_name, cls = list(filter(lambda c: combo.currentText() in c, self.mav_commands))[0]
        params = list(signature(cls).parameters.keys())
        frame.setToolTip(cls().description())

        texts[0].clear()
        texts[1].clear()

        if cls_name == 'SET_MODE':
            try:
                texts[0].addItems(list(mav_commands.MODES))
            except TypeError:
                pass

        if cls_name == 'SET_RELAY':
            try:
                texts[0].addItems([str(x) for x in range(7)])
                texts[1].addItems(['ON', 'OFF'])
            except TypeError:
                pass

        for x in range(len(labels)):
            try:
                labels[x].setText(params[x].capitalize())
                texts[x].setEnabled(True)
                if isinstance(texts[x], QWideComboBox):
                    texts[x].lineEdit().setText(values[x])
                else:
                    texts[x].setText(values[x])
            except IndexError:
                labels[x].setText('')
                texts[x].setEnabled(False)
                if isinstance(texts[x], QWideComboBox):
                    texts[x].lineEdit().setText(values[x])
                else:
                    texts[x].setText(values[x])

        if cls_name == 'MavlinkCommandLong':
            texts[0].setEnabled(True)
            texts[0].addItems([cmd for cmd, val in mav_commands.MAV_CMD_LIST])
            texts[0].lineEdit().setText(values[0])
            for x in range(1, len(labels)):
                labels[x].setText(f'Arg{x}')
                texts[x].setEnabled(True)

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
            self.save_wp_command_preference('wp_start_preferences')
        elif self.sender() == self.button_mav_command_end_send:
            cmd = self.combo_mav_command_end.currentText()
            arg_texts = self.texts_mav_command_end
            self.save_wp_command_preference('wp_end_preferences')
        else:
            return
        self.mav_command(cmd, arg_texts, True)

    def mav_command(self, cmd, arg_texts, do_send=False):
        args = []
        on = 0 if self.checkbox_relay_active_low.isChecked() else 1
        for arg in arg_texts:
            if isinstance(arg, QWideComboBox):
                val = arg.lineEdit().text()
            else:
                val = arg.text()
            if val != '':
                try:
                    val = float(val)
                except ValueError:  # it's a string that doesn't convert to a float
                    if val == 'ON':
                        val = on
                    elif val == 'OFF':
                        val = on ^ 1
                args.append(val)

        cls = list(filter(lambda command: cmd in command, getmembers(mav_commands, isclass)))[0][1]

        if cmd == 'MavlinkCommandLong':
            cmd = args.pop(0)
            cmd = list(filter(lambda command: command[0] == cmd, mav_commands.MAV_CMD_LIST))[0][1]
            args = [cmd, args]

        if do_send:
            cls(*args).send()
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
            self.save_wp_command_preference('wp_start_preferences')
        if self.checkbox_mav_command_start_all.isChecked():
            cmd_start_add_all = True
        if self.checkbox_mav_command_end.isChecked() or self.checkbox_mav_command_end_all.isChecked():
            cmd_end = self.mav_command(self.combo_mav_command_end.currentText(), self.texts_mav_command_end)
            self.save_wp_command_preference('wp_end_preferences')
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
            self.button_arm.setEnabled(True)
            self.button_disarm.setEnabled(True)
            self.button_mav_command_start_send.setEnabled(True)
            self.button_mav_command_end_send.setEnabled(True)
            self.mavlink.start_updates()
        else:
            self.mav_disconnect()

    @pyqtSlot()
    def arm(self):
        mav_commands.ARM().send()

    @pyqtSlot()
    def disarm(self):
        mav_commands.DISARM().send()

    @pyqtSlot()
    def save_relay_state(self):
        self.cfg.relay_active_state = str(int(not self.checkbox_relay_active_low.isChecked()))

    @pyqtSlot()
    def save_auto_headlights_state(self):
        self.cfg.auto_headlights = str(int(self.checkbox_auto_headlights.isChecked()))

    @pyqtSlot()
    def save_headlight_relay(self):
        self.cfg.headlight_relay = self.combo_headlight_relay.currentText()

    def save_wp_command_preference(self, section):
        start = 'start' in section
        values = []
        texts = self.texts_mav_command_start if start else self.texts_mav_command_end
        cmd = self.combo_mav_command_start.currentText() if start else self.combo_mav_command_end.currentText()
        for text in texts:
            if isinstance(text, QWideComboBox):
                values.append(text.lineEdit().text())
            else:
                values.append(text.text())
        if start:
            values.append(str(int(self.checkbox_mav_command_start.isChecked())))
            values.append(str(int(self.checkbox_mav_command_start_all.isChecked())))
        else:
            values.append(str(int(self.checkbox_mav_command_end.isChecked())))
            values.append(str(int(self.checkbox_mav_command_end_all.isChecked())))
        self.cfg.save_wp_preference(section, cmd, ','.join(values))

    @pyqtSlot(bool)
    def closeEvent(self, event):
        if self.button_connect.text() == "Disconnect":
            self.mav_disconnect()

    def mav_disconnect(self):
        self.mavlink.disconnect()
        self.button_connect.setText('Connect')
        self.button_arm.setEnabled(False)
        self.button_disarm.setEnabled(False)
        self.button_mav_command_start_send.setEnabled(False)
        self.button_mav_command_end_send.setEnabled(False)
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
