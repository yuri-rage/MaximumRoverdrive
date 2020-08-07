from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, pyqtSlot


class TableModel(QAbstractTableModel):
    dataChangedThreaded = pyqtSignal(QModelIndex, QModelIndex)
    layoutChangedThreaded = pyqtSignal()

    def __init__(self, data=None):
        super(TableModel, self).__init__()
        if data is None:
            pass
        else:
            self._data = data
            self.dataChangedThreaded.connect(self._dataChangedThreaded)
            self.layoutChangedThreaded.connect(self._layoutChangedThreaded)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def setData(self, index, value, role=Qt.EditRole):
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
