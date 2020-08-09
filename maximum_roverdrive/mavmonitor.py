from pymavlink import mavutil
from maximum_roverdrive.tablemodel import TableModel
from threading import Thread


class MavMonitor:

    def __init__(self, port=None, tableView=None, cfg_messages=None):
        if port is None or tableView is None or cfg_messages is None:
            pass
        else:
            self._tableView = tableView
            self._connection = mavutil.mavlink_connection(port)
            self._messages = cfg_messages
            self._tableView = tableView
            self._model = TableModel()
            self._keepalive = False
            self._isalive = False
            self.__init_table()

    @staticmethod
    def __msg_name(msg, attr):
        return msg + '.' + attr

    def __get_msg(self, msg):
        msg_split = msg.split('.')
        try:
            return getattr(self._connection.messages[msg_split[0]], msg_split[1])
        except KeyError:
            return 'NO DATA'

    def __init_table(self):
        data = []
        for msg in self._messages:
            data.append([msg, 'NO DATA'])
        self._model = TableModel(data, self._messages)
        self._tableView.setModel(self._model)
        self._tableView.resizeColumnsToContents()

    def __update_table(self):
        for row in range(self._model.rowCount()):
            index = self._model.index(row, 0)
            msg = self._model.data(index)
            index = self._model.index(row, 1)
            value = self.__get_msg(msg)
            self._model.setData(index, value)

    def __update_thread(self):
        self._isalive = True
        while self._keepalive:
            msg_types = []
            for row in range(self._model.rowCount()):
                index = self._model.index(row, 0)
                msg_types.append(self._model.data(index).split('.')[0])
            # TODO: wait for any message and update a static dictionary with current data
            self._connection.recv_match(type=msg_types, blocking=True, timeout=0.2)
            self.__update_table()
        self._isalive = False

    def start_updates(self):
        self._keepalive = True
        Thread(target=self.__update_thread, daemon=True).start()

    def add_msg(self, msg, attr, multiplier=1.0, low=0.0, high=0.0):
        self._model.updateDataParameters(msg + '.' + attr, multiplier, low, high)
        self._model.appendRow([msg + '.' + attr, 'NO DATA'])
        self._tableView.resizeColumnsToContents()

    def remove_selected(self):
        if self._model.rowCount() > 1:
            row = self._tableView.selectedIndexes()[0].row()
            self._model.removeRow(row)
        else:  # don't remove last row
            index = self._model.index(0, 0)
            self._model.setData(index, 'NO DATA')

    def disconnect(self):
        self._keepalive = False
        while self._isalive:  # wait for thread to stop
            pass
        self._connection.close()

    @property
    def connection(self):
        return self._connection  # expose the pymavlink connection
