import sys
from PyQt5.QtCore import Qt, QMimeData, QModelIndex, QByteArray, QEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QAbstractItemView 
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class DragDropModel(QStandardItemModel):
    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-qabstractitemmodeldatalist"]
    
    def mimeData(self, indexes):
        mimedata = QMimeData()
        # Ensure we're dragging a valid row
        if indexes and indexes[0].isValid():
            # Encode the row number as a byte array
            row_data = QByteArray(str(indexes[0].row()).encode())
            mimedata.setData("application/x-qabstractitemmodeldatalist", row_data)
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        print("drop data:", data, "action", action, "row", row, "column", column, "parent:", parent)
        if action == Qt.IgnoreAction:
            return True
        if row == -1:
            row = self.rowCount(parent)
        print("drop :", row)
        # Check for illegal moves
        source_row = data.data("source_row")
        if not source_row or row == int(source_row.data().decode()):
            return False

        self.beginMoveRows(QModelIndex(), int(source_row.data().decode()), int(source_row.data().decode()), QModelIndex(), row)
        self.endMoveRows()
        return True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.table_view = QTableView()
        self.model = DragDropModel()
        self.table_view.setModel(self.model)
        self.setCentralWidget(self.table_view)
        self.table_view.setDragDropMode(QAbstractItemView.InternalMove)  # Enable drag and drop
        self.table_view.setDragEnabled(True)
        #self.figureView.setDragEnabled(True)
        self.table_view.setAcceptDrops(True)
        self.table_view.setDropIndicatorShown(True)
        self.table_view.installEventFilter(self)  # Install the event filter

        # Sample data (replace with your actual data)
        for i in range(5):
            self.model.appendRow([QStandardItem(f"Item {i+1}")])
            
    def eventFilter(self, obj, event):
        if obj is self.table_view and event.type() == QEvent.Drop:
            dropEvent = event  # Access the QDropEvent
            print(f"Drop event position: {dropEvent.pos()}")
            print(f"Drop row index: {self.table_view.indexAt(dropEvent.pos()).row()}")  
        return super().eventFilter(obj, event)  # Pass the event along

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
