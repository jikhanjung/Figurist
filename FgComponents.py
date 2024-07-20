from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QSize, QMargins
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_mode = False
        self.margins = QMargins(0, 0, 0, 0)

    def paint(self, painter, option, index):
        if self.icon_mode:
            adjusted_option = option
            adjusted_option.rect = option.rect.marginsRemoved(self.margins)
            self.initStyleOption(adjusted_option, index)
            
            # Draw the icon
            icon = index.data(Qt.DecorationRole)
            if icon:
                icon_size = min(adjusted_option.rect.width(), adjusted_option.rect.height()) - 20
                icon_rect = QRect(adjusted_option.rect.x() + (adjusted_option.rect.width() - icon_size) // 2,
                                  adjusted_option.rect.y() + 10,
                                  icon_size, icon_size)
                icon.paint(painter, icon_rect)

            # Draw the text
            text = index.data(Qt.DisplayRole)
            if text:
                text_rect = QRect(adjusted_option.rect.x(), adjusted_option.rect.bottom() - 30,
                                  adjusted_option.rect.width(), 30)
                painter.drawText(text_rect, Qt.AlignCenter, text)
        else:
            super().paint(painter, option, index)
    def sizeHint(self, option, index):
        if self.icon_mode:
            return option.rect.size()
        return super().sizeHint(option, index)

    def set_icon_mode(self, icon_mode):
        self.icon_mode = icon_mode

    def setContentsMargins(self, margins):
        self.margins = margins

    def setWordWrap(self, wrap):
        self.word_wrap = wrap

class CustomTableModel(QAbstractTableModel):
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
            if self.icon_mode:
                return item['name']
            else:
                if index.column() == 0:
                    return item['name']
                elif index.column() == 1:
                    return item['type']
                elif index.column() == 2:
                    return item['size']

        if role == Qt.DecorationRole and (self.icon_mode or index.column() == 0):
            return QIcon(item['icon'])

        return None

    def set_icon_mode(self, icon_mode):
        self.icon_mode = icon_mode
        self.layoutChanged.emit()

