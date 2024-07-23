from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QSize, QMargins
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem, QListView, QStackedWidget, QAbstractItemView


class FgFigureView(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Table View for list mode
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # List View for icon mode
        self.listView = QListView(self)
        self.listView.setViewMode(QListView.IconMode)
        self.listView.setResizeMode(QListView.Adjust)
        self.listView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listView.setWrapping(True)
        self.listView.setSpacing(10)
        self.listView.setIconSize(QSize(128, 128))
        
        self.addWidget(self.tableView)
        self.addWidget(self.listView)
        
        # Single model for both views
        self.model = QStandardItemModel(self)
        
        self.tableView.setModel(self.model)
        self.listView.setModel(self.model)

    def set_icon_mode(self, icon_mode=True):
        if icon_mode:
            self.setCurrentWidget(self.listView)
            self.listView.setGridSize(QSize(150, 150))
        else:
            self.setCurrentWidget(self.tableView)

    def load_figures(self, figures):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Figure', 'Taxon', 'File'])
        
        for figure in figures:
            items = [
                QStandardItem(QIcon(figure.get_file_path()), figure.get_figure_name()),
                QStandardItem(figure.taxon.name if figure.taxon else ''),
                QStandardItem(figure.file_name)
            ]
            for item in items:
                item.setData(figure, Qt.UserRole)
            self.model.appendRow(items)

        # Adjust table columns
        self.tableView.resizeColumnsToContents()
        
        # Set list view to only show the first column
        self.listView.setModelColumn(0)

    def selectedIndexes(self):
        return self.currentWidget().selectedIndexes()

    def get_data(self, index):
        return index.data(Qt.UserRole)