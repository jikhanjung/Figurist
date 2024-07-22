from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QSize, QMargins
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem

class FigureItemDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_mode = False
        self.margins = QMargins(10, 10, 10, 10)
        self.spacing = 20  # Add this line  
        self.item_size = 200  # Base size without spacing

    def paint(self, painter, option, index):
        if isinstance(index.model(), QSortFilterProxyModel):
            index = index.model().mapToSource(index)
        if self.icon_mode:
            adjusted_option = QStyleOptionViewItem(option)
            self.initStyleOption(adjusted_option, index)
            
            # Draw selection background if item is selected
            if option.state & QStyle.State_Selected:
                painter.save()
                painter.setBrush(option.palette.highlight())
                painter.setPen(Qt.NoPen)
                painter.drawRect(option.rect)
                painter.restore()
            
            adjusted_rect = option.rect.marginsRemoved(self.margins)
            
            # Draw the icon
            icon = index.data(Qt.DecorationRole)
            if icon:
                icon_size = min(adjusted_rect.width(), adjusted_rect.height() - 30)
                icon_rect = QRect(adjusted_rect.x() + (adjusted_rect.width() - icon_size) // 2,
                                  adjusted_rect.y(),
                                  icon_size, icon_size)
                icon.paint(painter, icon_rect)

            # Draw the text
            text = index.data(Qt.DisplayRole)
            if text:
                text_rect = QRect(adjusted_rect.x(), icon_rect.bottom() + 5,
                                  adjusted_rect.width(), adjusted_rect.height() - icon_rect.height() - 5)
                text_color = option.palette.highlightedText().color() if option.state & QStyle.State_Selected else option.palette.text().color()
                painter.setPen(text_color)
                painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, text)
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if self.icon_mode:
            size.setHeight(size.height() + 60 + self.spacing)  # Add spacing to height
            size.setWidth(max(size.width(), 140) + self.spacing)  # Add spacing to width
        return size

    def set_icon_mode(self, icon_mode):
        self.icon_mode = icon_mode

    def setContentsMargins(self, margins):
        self.margins = margins

    def setWordWrap(self, wrap):
        self.word_wrap = wrap

    def set_spacing(self, spacing):
        self.spacing = spacing
        self.item_size = 200 + spacing  # Update item size when spacing changes

class FigureTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.icon_mode = False
        self.columns_in_icon_mode = 4  # Adjust this number as needed

    def rowCount(self, parent=None):
        if self.icon_mode:
            return (len(self._data) + self.columns_in_icon_mode - 1) // self.columns_in_icon_mode
        return len(self._data)

    def columnCount(self, parent=None):
        return self.columns_in_icon_mode if self.icon_mode else 3  # Adjust for list mode columns

    def data(self, index, role):
        if not index.isValid():
            return None

        if self.icon_mode:
            item_index = index.row() * self.columns_in_icon_mode + index.column()
            if item_index >= len(self._data):
                return None
            item = self._data[item_index]
        else:
            item = self._data[index.row()]

        if role == Qt.DisplayRole:
            text = item.figure_number
            if item.taxon:
                text = text + " " + item.taxon.name # + " " + text
            return text
            #if self.icon_mode:
            #    return item.figure_number #['name']
            #else:
            #    #if index.column() == 0:
            #    return item.figure_number #['name']
                #elif index.column() == 1:
                #    return item['type']
                #elif index.column() == 2:
                #    return item['size']

        if role == Qt.DecorationRole and (self.icon_mode or index.column() == 0):
            return QIcon(item.get_file_path()) #['icon'])

        if role == Qt.UserRole:
            return item
        
        return None

    def set_icon_mode(self, icon_mode):
        self.icon_mode = icon_mode
        self.layoutChanged.emit()

    def update_columns(self, view_width, item_width):
        if self.icon_mode:
            self.columns_in_icon_mode = max(1, view_width // item_width)
            self.layoutChanged.emit()

    def get_item_data(self, index):
        if not index.isValid():
            return None

        if self.icon_mode:
            item_index = index.row() * self.columns_in_icon_mode + index.column()
            if item_index < len(self._data):
                return self._data[item_index]
        else:
            if index.row() < len(self._data):
                return self._data[index.row()]
        return None
from PyQt5.QtCore import QSortFilterProxyModel, Qt

class FigureProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filtered_taxa = set()

    def filterAcceptsRow(self, source_row, source_parent):
        print("filterAcceptsRow", self.filtered_taxa)
        if not self.filtered_taxa:
            return True

        source_model = self.sourceModel()
        for column in range(source_model.columnCount()):
            index = source_model.index(source_row, column, source_parent)
            figure = source_model.data(index, Qt.UserRole)
            if figure and figure.taxon in self.filtered_taxa:
                return True
        return False        
        
        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)
        figure = source_model.data(index, Qt.UserRole)
        print("figure", figure, figure.taxon)
        return figure.taxon in self.filtered_taxa

    def set_filtered_taxa(self, taxa):
        self.filtered_taxa = set(taxa)
        self.invalidateFilter()

