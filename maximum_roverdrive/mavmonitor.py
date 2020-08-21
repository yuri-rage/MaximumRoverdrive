from pymavlink import mavutil
from threading import Thread
from PyQt5.QtGui import QTextCursor
from maximum_roverdrive.tablemodel import TableModel
from maximum_roverdrive.astral_dusk import is_dark

_MAX_STATUSTEXT_MESSAGES = 256  # number of STATUSTEXT messages to display

_ACK_RESULTS = ['ACCEPTED', 'TEMP_REJECTED', 'DENIED', 'UNKNOWN (bad arguments?)', 'FAILED', 'IN_PROGRESS', 'CANCELLED']


class Location:
    lat = None
    lng = None
    alt = None


class MavMonitor:
    _location = Location()

    def __init__(self, window=None, cmd_list=None):
        if window is None or cmd_list is None:
            self._received_messages = {}
        else:
            self._window = window
            self._command_list = cmd_list
            self._window.text_status.status_text_changed.connect(self.__update_text_status_messages)
            self._connection = mavutil.mavlink_connection(window.combo_port.currentText())
            self._received_messages = {}
            self._model = TableModel()
            self._is_headlight_on = False
            self._keep_alive = False
            self._is_alive = False
            self.__init_table()

    def __get_msg(self, msg):
        msg_split = msg.split('.')
        try:
            return self._received_messages[msg_split[0]][msg_split[1]]
        except KeyError:
            return 'NO DATA'

    def __init_table(self):
        data = []
        for msg in self._window.cfg.messages:
            data.append([msg, 'NO DATA'])
        self._model = TableModel(data, self._window.cfg.messages)
        self._window.table_messages.setModel(self._model)
        self._window.table_messages.resizeColumnsToContents()

    def __update_table(self):
        for row in range(self._model.rowCount()):
            index = self._model.index(row, 0)
            msg = self._model.data(index)
            index = self._model.index(row, 1)
            value = self.__get_msg(msg)
            self._model.setData(index, value)

    def __update_text_status_messages(self, severity, msg):  # yet another PyQt5 thread workaround
        prepend = ''
        append = '<br>'
        if severity < 6:
            prepend = '<span style="color:'
            append = '</span><br>'
        if severity == 5:
            prepend = f'{prepend} #53a0ed;">'
        elif severity == 4:
            prepend = f'{prepend} yellow;">'
        elif severity == 3 or severity == 0:
            prepend = f'{prepend} red;">'
        elif 1 <= severity <= 2:
            prepend = f'{prepend} orange;">'
        cursor = QTextCursor(self._window.text_status.document())
        cursor.setPosition(0)
        self._window.text_status.setTextCursor(cursor)
        self._window.text_status.insertHtml(f'{prepend}{msg}{append}\n')
        if self._window.text_status.toPlainText().count('\n') >= _MAX_STATUSTEXT_MESSAGES:
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()

    def __update_thread(self):
        """ this became a bit of spaghetti code as I tested and added features
            if this project grows any legs, this method needs to be split into multiple sub-functions """
        self._is_alive = True
        while self._keep_alive:
            key = None
            msg_received = None
            try:
                msg_received = self.connection.recv_match(blocking=True, timeout=0.2).to_dict()
                key = msg_received['mavpackettype']
                del msg_received['mavpackettype']
                self._received_messages.update({key: msg_received})
            except AttributeError:
                pass
            self.__update_table()
            if key == 'GLOBAL_POSITION_INT':  # store location to avoid the delay in the pymavlink location() method
                self._location.lat = float(msg_received['lat']) / 10000000.0
                self._location.lng = float(msg_received['lon']) / 10000000.0
                self._location.alt = float(msg_received['alt']) / 1000.0
            if key == 'STATUSTEXT':  # since we're capturing all traffic, keep a status history
                self._window.text_status.status_text_changed.emit(int(msg_received['severity']), msg_received['text'])
            if key == 'COMMAND_ACK':
                try:
                    cmd = list(filter(lambda command: command[1] == msg_received['command'], self._command_list))[0][0]
                    cmd = cmd.replace('MAV_CMD_', '')
                except IndexError:
                    cmd = f'COMMAND #{msg_received["command"]}'
                result = msg_received['result']
                self._window.statusBar().showMessage(f'{cmd}: {_ACK_RESULTS[result]}')
            if self._window.checkbox_auto_headlights.isChecked():  # now check way too often if it's dark outside
                if is_dark(self._location.lat, self._location.lng, self._location.alt) != self._is_headlight_on:
                    try:
                        relay = float(self._window.combo_headlight_relay.lineEdit().text())
                        on = 0 if self._window.checkbox_relay_active_low.isChecked() else 1
                        if is_dark(self._location.lat, self._location.lng, self._location.alt):
                            self._connection.set_relay(relay, on)
                            self._window.text_status.status_text_changed.emit(5, 'Headlights: ON')
                            self._is_headlight_on = True
                        else:
                            self._connection.set_relay(relay, on ^ 1)
                            self._window.text_status.status_text_changed.emit(5, 'Headlights: OFF')
                            self._is_headlight_on = False
                    except ValueError:
                        pass  # likely to happen if relay value is not a number
        self._is_alive = False

    def start_updates(self):
        self._keep_alive = True
        Thread(target=self.__update_thread, daemon=True).start()

    def add_msg(self, msg, attr, multiplier=1.0, low=0.0, high=0.0):
        msg_fullname = msg + '.' + attr
        self._model.updateDataParameters(msg_fullname, multiplier, low, high)
        exists = False
        for row in range(self._model.rowCount()):
            index = self._model.index(row, 0)
            msg = self._model.data(index)
            if msg == msg_fullname:
                exists = True
        if not exists:
            self._model.appendRow([msg_fullname, 'NO DATA'])
            self._window.table_messages.resizeColumnsToContents()
        # TODO: replace the 'NO DATA' row created when the user removes all messages

    def remove_selected(self):
        if self._model.rowCount() > 1:
            row = self._window.table_messages.selectedIndexes()[0].row()
            self._model.removeRow(row)
        else:  # don't remove last row
            index = self._model.index(0, 0)
            self._model.setData(index, 'NO DATA')
        self._window.table_messages.resizeColumnsToContents()

    def disconnect(self):
        self._keep_alive = False
        while self._is_alive:  # wait for thread to stop
            pass
        self._connection.close()

    @property
    def connection(self):
        return self._connection  # expose the pymavlink connection

    @property
    def messages(self):
        return self._received_messages  # expose the message dictionary

    @property
    def location(self):
        return self._location
