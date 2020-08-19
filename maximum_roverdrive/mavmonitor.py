from pymavlink import mavutil
from maximum_roverdrive.tablemodel import TableModel
from threading import Thread
from PyQt5.QtGui import QTextCursor

_MAX_STATUSTEXT_MESSAGES = 256  # number of STATUSTEXT messages to display


class Location:
    lat = None
    lng = None
    alt = None


class MavMonitor:
    _location = Location()

    def __init__(self, port=None, tableView=None, text_status=None, cfg_messages=None):
        if port is None or tableView is None or text_status is None or cfg_messages is None:
            self._received_messages = {}
        else:
            self._tableView = tableView
            self._text_status_messages = text_status
            self._text_status_messages.status_text_changed.connect(self.__update_text_status_messages)
            self._connection = mavutil.mavlink_connection(port)
            self._requested_messages = cfg_messages
            self._received_messages = {}
            self._tableView = tableView
            self._model = TableModel()
            self._keepalive = False
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
        for msg in self._requested_messages:
            data.append([msg, 'NO DATA'])
        self._model = TableModel(data, self._requested_messages)
        self._tableView.setModel(self._model)
        self._tableView.resizeColumnsToContents()

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
        cursor = QTextCursor(self._text_status_messages.document())
        cursor.setPosition(0)
        self._text_status_messages.setTextCursor(cursor)
        self._text_status_messages.insertHtml(f'{prepend}{msg}{append}\n')
        if self._text_status_messages.toPlainText().count('\n') >= _MAX_STATUSTEXT_MESSAGES:
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()

    def __update_thread(self):
        self._is_alive = True
        while self._keepalive:
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
            if key == 'GLOBAL_POSITION_INT':  # avoids the delay in the pymavlink location() method
                self._location.lat = float(msg_received['lat']) / 10000000.0
                self._location.lng = float(msg_received['lon']) / 10000000.0
                self._location.alt = float(msg_received['alt']) / 1000.0
            if key == 'STATUSTEXT':  # since we're capturing all traffic, keep a status history
                self._text_status_messages.status_text_changed.emit(int(msg_received['severity']), msg_received['text'])
        self._is_alive = False

    def start_updates(self):
        self._keepalive = True
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
            self._tableView.resizeColumnsToContents()
        # TODO: replace the 'NO DATA' row created when the user removes all messages

    def remove_selected(self):
        if self._model.rowCount() > 1:
            row = self._tableView.selectedIndexes()[0].row()
            self._model.removeRow(row)
        else:  # don't remove last row
            index = self._model.index(0, 0)
            self._model.setData(index, 'NO DATA')
        self._tableView.resizeColumnsToContents()

    def disconnect(self):
        self._keepalive = False
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

    @property
    def statustext_buffer(self):
        return self._statustext_buffer
