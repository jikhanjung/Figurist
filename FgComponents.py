from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QPushButton, QTreeView, QSizePolicy, QHeaderView
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QSize, QMargins, QObject, QEvent
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem, QListView, QStackedWidget, QAbstractItemView
import time

class FigureTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figures = []
        self.headers = ['Figure', 'Taxon', 'File']
        self.icon_cache = {}
        self.view_mode = 'table'  # Add this line

    def rowCount(self, parent=QModelIndex()):
        return len(self.figures)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self.figures)):
            return None

        figure = self.figures[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:
                return figure.get_figure_name()
            elif column == 1:
                return figure.related_taxa[0].taxon.name if figure.related_taxa else ''
            elif column == 2:
                return figure.file_name
        elif role == Qt.DecorationRole and column == 0:
            if figure in self.icon_cache:
                return self.icon_cache[figure]
            else:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                icon = QIcon(figure.get_file_path())
                QApplication.restoreOverrideCursor()
                self.icon_cache[figure] = icon
                return icon
            path = figure.get_file_path()
            print("load file to icon 1", time.time(), path)
            icon = QIcon(path)
            print("load file to icon 2", time.time())
            return icon #QIcon(figure.get_file_path())
        elif role == Qt.UserRole:
            return figure

        return None

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self.figures)):
            return None

        figure = self.figures[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if self.view_mode == 'table':
                if column == 0:
                    return figure.figure_number
                elif column == 1:
                    return figure.related_taxa[0].taxon.name if figure.related_taxa else ''
                elif column == 2:
                    return figure.file_name
            else:  # icon mode
                return f"{figure.figure_number} {figure.related_taxa[0].taxon.name if figure.related_taxa else ''}"
        elif role == Qt.DecorationRole and column == 0:
            if figure in self.icon_cache:
                return self.icon_cache[figure]
            else:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                icon = QIcon(figure.get_file_path())
                QApplication.restoreOverrideCursor()
                self.icon_cache[figure] = icon
                return icon
        elif role == Qt.UserRole:
            return figure

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def setFigures(self, figures):
        self.beginResetModel()
        self.figures = figures
        self.endResetModel()

    def setViewMode(self, mode):
        self.view_mode = mode
        self.layoutChanged.emit()

class FgFigureView(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Table View for list mode
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.tableView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)        
        
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
        self.model = FigureTableModel(self)
        
        self.tableView.setModel(self.model)
        self.listView.setModel(self.model)
        self.tableView.resizeColumnsToContents()

    def set_icon_mode(self, icon_mode=True):
        if icon_mode:
            self.setCurrentWidget(self.listView)
            self.listView.setGridSize(QSize(150, 150))
        else:
            self.setCurrentWidget(self.tableView)

    def set_icon_mode(self, icon_mode=True):
        if icon_mode:
            self.setCurrentWidget(self.listView)
            self.listView.setGridSize(QSize(150, 150))
            self.model.setViewMode('icon')
        else:
            self.setCurrentWidget(self.tableView)
            self.model.setViewMode('table')
        self.model.layoutChanged.emit()
        
    def load_figures(self, figures):
        if not isinstance(self.model, FigureTableModel):
            self.model = FigureTableModel(self)
            self.tableView.setModel(self.model)
            self.listView.setModel(self.model)
        self.model.setFigures(figures)
        return
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Figure', 'Taxon', 'File'])
        
        for figure in figures:
            items = [
                QStandardItem(QIcon(figure.get_file_path()), figure.get_figure_name()),
                QStandardItem(figure.related_taxa[0].taxon.name if figure.related_taxa else ''),
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
    
class TreeViewClickFilter(QObject):
    def __init__(self, tree_view):
        super().__init__(tree_view)
        self.tree_view = tree_view

    def eventFilter(self, obj, event):
        if obj == self.tree_view and event.type() == QEvent.MouseButtonPress:
            print("mouse button press", self.tree_view)
            index = self.tree_view.indexAt(event.pos())
            if not index.isValid():
                # Click is outside any item
                self.tree_view.clearSelection()
                return True
        return super().eventFilter(obj, event)    
    
class ClickableTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            # Click is outside any item
            self.clearSelection()
            # Optionally, clear the current index as well
            self.setCurrentIndex(self.rootIndex())
        super().mousePressEvent(event)    