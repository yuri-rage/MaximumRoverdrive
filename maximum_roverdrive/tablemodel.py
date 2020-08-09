from collections import namedtuple
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor


class TableModel(QAbstractTableModel):
    dataChangedThreaded = pyqtSignal(QModelIndex, QModelIndex)
    layoutChangedThreaded = pyqtSignal()

    def __init__(self, data=None, dataParameters=None):
        super(TableModel, self).__init__()
        if data is None or dataParameters is None:
            pass
        else:
            self._data = data
            self._dataParameters = dataParameters
            self.dataChangedThreaded.connect(self._dataChangedThreaded)
            self.layoutChangedThreaded.connect(self._layoutChangedThreaded)

    def updateDataParameters(self, msg, multiplier, low, high):
        MsgParams = namedtuple('MsgParams', 'multiplier low high')
        self._dataParameters.update({msg: MsgParams(multiplier, low, high)})

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.BackgroundRole and index.column() == 1:
            msg = self._data[index.row()][0]
            if msg == 'NO DATA':
                return QBrush(Qt.darkMagenta)
            try:
                val = float(self._data[index.row()][index.column()])
            except ValueError:
                val = self._data[index.row()][index.column()]
            if val == 'NO DATA':
                return QBrush(Qt.darkMagenta)
            elif val < self._dataParameters[msg].low or val > self._dataParameters[msg].high:
                return QBrush(Qt.darkRed)
            else:
                return QBrush(QColor(38, 39, 40))

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            msg = self._data[index.row()][0]
            try:
                val = float(value) * self._dataParameters[msg].multiplier
                self._data[index.row()][index.column()] = val
            except ValueError:
                self._data[index.row()][index.column()] = value
            self.dataChangedThreaded.emit(index, index)  # workaround for threaded updates

    def removeRow(self, row, parent=QModelIndex):
        self._data.pop(row)
        self.layoutChangedThreaded.emit()            # workaround for threaded updates

    def appendRow(self, data):
        self._data.append(data)
        self.layoutChangedThreaded.emit()            # workaround for threaded updates

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0])

    @pyqtSlot(QModelIndex, QModelIndex)
    def _dataChangedThreaded(self, topLeft, bottomRight):
        self.dataChanged.emit(topLeft, bottomRight)

    @pyqtSlot()
    def _layoutChangedThreaded(self):
        self.layoutChanged.emit()
