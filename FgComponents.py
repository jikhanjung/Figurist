from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTreeView, QSizePolicy, QHeaderView, QLabel, QInputDialog, QSpinBox, QComboBox
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QSize, QMargins, QObject, QEvent, QMimeData, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QStandardItemModel, QPixmap, QStandardItem, QPen, QFont, QMouseEvent, QWheelEvent, QPainter, QDrag, QImage, QColor
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem, QListView, QStackedWidget, QAbstractItemView
import time, math
from PyQt5.QtCore import QByteArray
from FgModel import FgCollection, FgReference, FgTreeOfLife
import ollama
from abc import ABC, abstractmethod
from openai import OpenAI, OpenAIError # Import the error class directly
import operator
from functools import reduce
import fitz
import os
from pyzotero import zotero
import httpx
import urllib.parse
import logging
from types import SimpleNamespace
import re
import requests
import ssl
from peewee import *

logger = logging.getLogger(__name__)

#os.environ['SSL_CERT_FILE'] = certifi.where()
#ssl_context = ssl.create_default_context(cafile=os.environ['SSL_CERT_FILE'])
#ollama.set_base_url('http://172.16.116.98:11434')

CLOSE_TO = { 'left': 1, 'right': 2, 'top': 4, 'bottom': 8 }

class SubFigure:
    def __init__(self, pixmap = None, rect = None, index = "", taxon_name = "", caption = "", comments = "", page_number = -1):
        self.pixmap = pixmap
        self.rect = rect
        self.index = index
        self.taxon_name = taxon_name
        self.caption = caption
        self.comments = comments
        self.page_number = page_number

class FigureTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figures = []
        self.headers = ['Prefix 1', 'No.1', '-', 'Prefix 2', 'No.2', 'Figure Number', 'Taxon', 'Caption', 'Comments']
        self.column_list = ['part1_prefix', 'part1_number', 'part_separator', 'part2_prefix', 'part2_number', 'figure_number', 'taxon_name', 'caption', 'comments']
        self.icon_cache = {}
        self.mode = 'table'
        self.edited_cells = set()  # To keep track of edited cells
        self._uneditable_columns = [5]

    def set_columns_uneditable(self, columns):
        self._uneditable_columns = columns

    def rowCount(self, parent=QModelIndex()):
        return len(self.figures)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self.figures)):
            return None

        figure = self.figures[index.row()]
        column = index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if self.mode in ['table', 'edit']:
                if hasattr(figure, self.column_list[column]):
                    return getattr(figure, self.column_list[column])
            else:  # icon mode
                return f"{figure.figure_number} {figure.taxon_name or ''}"
        elif role == Qt.BackgroundRole:
            if index.column() in self._uneditable_columns:
                return QColor(192, 192, 192)
            elif (index.row(), index.column()) in self.edited_cells:
                return QColor(255, 255, 0)  # Yellow color for edited cells
        elif role == Qt.DecorationRole and column == 0 and self.mode == 'icon':
            if figure in self.icon_cache and figure.modified_at == self.icon_cache[figure][0]:
                return self.icon_cache[figure][1]
            else:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                thumbnail_path = figure.get_or_create_thumbnail()
                if thumbnail_path:
                    icon = QIcon(thumbnail_path)
                else:
                    icon = QIcon()  # Empty icon if thumbnail creation failed
                QApplication.restoreOverrideCursor()
                self.icon_cache[figure] = [figure.modified_at, icon]
                return icon
        elif role == Qt.UserRole:
            return figure

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            figure = self.figures[row]

            if hasattr(figure, self.column_list[col]):
                if value != getattr(figure, self.column_list[col]):
                    setattr(figure, self.column_list[col], value)
                    #if col < 5:
                    #    figure.update_figure_number()
                    self.edited_cells.add((row, col))
                    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.BackgroundRole])
                    return True
        return False

    def flags(self, index):
        if self.mode == 'edit' and index.column() not in self._uneditable_columns:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def setFigures(self, figures):
        self.beginResetModel()
        sorted_figures = sorted(figures, key=lambda fig: fig.get_sort_key())
        self.figures = sorted_figures
        self.edited_cells = set()  # To keep track of edited cells
        self.endResetModel()

    def setMode(self, mode):
        self.mode = mode
        self.layoutChanged.emit()

    def save_changes(self):
        for row, col in self.edited_cells:
            figure = self.figures[row]
            if hasattr(figure, self.column_list[col]):
                setattr(figure, self.column_list[col], self.data(self.index(row, col), Qt.EditRole))
            if col < 5:
                figure.update_figure_number()
            figure.save()
        self.edited_cells.clear()

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
        self.model = FigureTableModel(self)
        
        self.tableView.setModel(self.model)
        self.listView.setModel(self.model)

    def adjust_column_widths(self):
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for i in range(5):  # First 5 columns
            self.tableView.horizontalHeader().resizeSection(i, 50)  # Adjust this value as needed
        self.tableView.horizontalHeader().resizeSection(5, 100)  # Adjust this value as needed
        #self.tableView.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # Figure Number
        self.tableView.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)  # Taxon
        self.tableView.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)  # Caption
        self.tableView.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)  # Comments

    def set_mode(self, mode):
        self.mode = mode
        if mode == 'icon':
            self.setCurrentWidget(self.listView)
            self.listView.setGridSize(QSize(150, 150))
            self.model.setMode('icon')
        elif mode == 'table':
            self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.setCurrentWidget(self.tableView)
            self.model.setMode('table')
        elif mode == 'edit':
            # make it editable, and selection is cell-based
            self.tableView.setSelectionBehavior(QAbstractItemView.SelectItems)
            self.setCurrentWidget(self.tableView)
            self.model.setMode('edit')
        self.model.layoutChanged.emit()
        self.adjust_column_widths()

    def save_changes(self):
        self.model.save_changes()
        self.tableView.viewport().update()

    def load_figures(self, figures):
        if not isinstance(self.model, FigureTableModel):
            self.model = FigureTableModel(self)
            self.tableView.setModel(self.model)
            self.listView.setModel(self.model)
        self.model.setFigures(figures)
        self.adjust_column_widths()

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

class FigureLabel(QLabel):
    def __init__(self, parent=None):
        super(FigureLabel, self).__init__(parent)
        self.parent = parent
        self.setMinimumSize(300,200)
        self.read_only = False
        self.edit_mode = "NONE"
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.scale = 1.0
        self.prev_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.mouse_down_x = 0
        self.mouse_down_y = 0
        self.mouse_curr_x = 0
        self.mouse_curr_y = 0
        self.curr_rect = None
        self.temp_rect = None
        self.subfigure_list = []
        self.curr_subfigure_index = -1
        self.rect = QRect()
        self.setMouseTracking(True)
        self.page_number = -1
        self.image_canvas_ratio = 1.0

    def setReadOnly(self, read_only):
        self.read_only = read_only

    def _2canx(self, coord):
        return round((float(coord) / self.image_canvas_ratio) * self.scale) + self.pan_x + self.temp_pan_x
    def _2cany(self, coord):
        return round((float(coord) / self.image_canvas_ratio) * self.scale) + self.pan_y + self.temp_pan_y
    def _2imgx(self, coord):
        return round(((float(coord) - self.pan_x) / self.scale) * self.image_canvas_ratio)
    def _2imgy(self, coord):
        return round(((float(coord) - self.pan_y) / self.scale) * self.image_canvas_ratio)

    def get_distance_to_line(self, curr_pos, line_start, line_end):
        x1 = line_start[0]
        y1 = line_start[1]
        x2 = line_end[0]
        y2 = line_end[1]
        max_x = max(x1,x2)
        min_x = min(x1,x2)
        max_y = max(y1,y2)
        min_y = min(y1,y2)
        if curr_pos[0] > max_x or curr_pos[0] < min_x or curr_pos[1] > max_y or curr_pos[1] < min_y:
            return -1
        x0 = curr_pos[0]
        y0 = curr_pos[1]
        numerator = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1)
        denominator = math.sqrt(math.pow(y2-y1,2) + math.pow(x2-x1,2))
        return numerator/denominator

    def get_distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def set_edit_mode(self, mode):
        self.edit_mode = mode

    def check_subfigure(self, curr_pos):
        close_to = 0
        margin = 10
        idx = -1
        for i, subfigure in enumerate(self.subfigure_list):
            close_to = 0
            pixmap, rect = subfigure.pixmap, subfigure.rect
            x = self._2canx(rect.x())
            y = self._2cany(rect.y())
            w = round(rect.width() / self.image_canvas_ratio * self.scale)
            h = round(rect.height() / self.image_canvas_ratio * self.scale)
            rect = QRect(x - margin, y - margin, w + 2 * margin , h + 2 * margin)
            if rect.contains(curr_pos[0], curr_pos[1]):
                if x - margin < curr_pos[0] < x + margin:
                    close_to += CLOSE_TO['left']
                elif x + w - margin < curr_pos[0] < x + w + margin:
                    close_to += CLOSE_TO['right']
                if y - margin < curr_pos[1] < y + margin:
                    close_to += CLOSE_TO['top']
                elif y + h - margin < curr_pos[1] < y + h + margin:
                    close_to += CLOSE_TO['bottom']
                idx = i
                break
        # set cursor
        if idx > -1:
            if close_to & CLOSE_TO['left'] and close_to & CLOSE_TO['top'] or close_to & CLOSE_TO['right'] and close_to & CLOSE_TO['bottom']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif close_to & CLOSE_TO['left'] and close_to & CLOSE_TO['bottom'] or close_to & CLOSE_TO['right'] and close_to & CLOSE_TO['top']:
                self.setCursor(Qt.SizeBDiagCursor)
            elif close_to & CLOSE_TO['left'] or close_to & CLOSE_TO['right']:
                self.setCursor(Qt.SizeHorCursor)
            elif close_to & CLOSE_TO['top'] or close_to & CLOSE_TO['bottom']:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.setCursor(Qt.OpenHandCursor)
            return i, close_to
        else:
            self.setCursor(Qt.ArrowCursor)

        return -1, close_to

    def mouseMoveEvent(self, event):
        #print("mouse move event")
        me = QMouseEvent(event)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
        #print("mouse move", curr_pos)
        if self.edit_mode == "CAPTURE_TEXT":
            pass
        elif self.edit_mode == "CAPTURE_TEXT_DRAG":
            diff_x = self.mouse_curr_x - self.down_x
            diff_x = round(((float(diff_x)) / self.scale) * self.image_canvas_ratio)
            diff_y = self.mouse_curr_y - self.down_y
            diff_y = round(((float(diff_y)) / self.scale) * self.image_canvas_ratio)
            self.temp_rect = QRect(self._2imgx(self.down_x), self._2imgy(self.down_y), diff_x, diff_y)
        elif self.edit_mode == "NEW_SUBFIGURE_DRAG":
            diff_x = self.mouse_curr_x - self.down_x
            diff_x = round(((float(diff_x)) / self.scale) * self.image_canvas_ratio)
            diff_y = self.mouse_curr_y - self.down_y
            diff_y = round(((float(diff_y)) / self.scale) * self.image_canvas_ratio)
            self.temp_rect = QRect(self._2imgx(self.down_x), self._2imgy(self.down_y), diff_x, diff_y)
        elif self.edit_mode == "PAN":
            self.temp_pan_x = self.mouse_curr_x - self.mouse_down_x
            self.temp_pan_y = self.mouse_curr_y - self.mouse_down_y
        elif self.edit_mode == "ADJUSTING_SUBFIGURE":#in ["RESIZE_LEFT", "RESIZE_RIGHT", "RESIZE_TOP", "RESIZE_BOTTOM", "MOVE"]:
            idx, close_to = self.check_subfigure(curr_pos)
            self.adjusting_side = close_to
            if idx == -1:
                self.set_edit_mode("NONE")
                self.temp_rect = None
                self.curr_subfigure_index = -1
                if hasattr(self.parent, 'clear_selection'):
                    self.parent.clear_selection()
            else:
                if hasattr(self.parent, 'select_row'):
                    self.parent.select_row(idx)
                    self.curr_subfigure_index = idx
                    self.set_edit_mode("ADJUSTING_SUBFIGURE")
        elif self.edit_mode == "ADJUSTING_SUBFIGURE_DRAG":
            #print("ADJUSTING_SUBFIGURE_DRAG", self.curr_subfigure_index)
            diff_x = self.mouse_curr_x - self.mouse_down_x
            diff_y = self.mouse_curr_y - self.mouse_down_y
            #print("diff_x, diff_y", diff_x, diff_y)
            diff_x = round(((float(diff_x)) / self.scale) * self.image_canvas_ratio)
            diff_y = round(((float(diff_y)) / self.scale) * self.image_canvas_ratio)
            #print("diff_x, diff_y", diff_x, diff_y)

            # copy the current subfigure

            self.temp_rect = QRect(self.subfigure_list[self.curr_subfigure_index].rect)
            #print("temp_rect before", self.temp_rect)
            #self.temp_rect = self.subfigure_list[self.curr_subfigure_index][1]
            if self.adjusting_side & CLOSE_TO['left']:
                self.temp_rect.setLeft(self.temp_rect.left() + diff_x)
            if self.adjusting_side & CLOSE_TO['right']:
                self.temp_rect.setRight(self.temp_rect.right() + diff_x)
            if self.adjusting_side & CLOSE_TO['top']:
                self.temp_rect.setTop(self.temp_rect.top() + diff_y)
            if self.adjusting_side & CLOSE_TO['bottom']:
                self.temp_rect.setBottom(self.temp_rect.bottom() + diff_y)
            if self.adjusting_side == 0:
                # set cursor to closehand cursor
                self.temp_rect.setLeft(self.temp_rect.left() + diff_x)
                self.temp_rect.setRight(self.temp_rect.right() + diff_x)
                self.temp_rect.setTop(self.temp_rect.top() + diff_y)
                self.temp_rect.setBottom(self.temp_rect.bottom() + diff_y)
            #print("temp_rect", self.temp_rect)
        else:
            idx, close_to = self.check_subfigure(curr_pos)
            if idx == -1:
                self.set_edit_mode("NONE")
                if hasattr(self.parent, 'clear_selection'):
                    self.parent.clear_selection()
            else:
                self.adjusting_side = close_to
                self.curr_subfigure_index = idx
                self.set_edit_mode("ADJUSTING_SUBFIGURE")
                if hasattr(self.parent, 'select_row'):
                    self.parent.select_row(idx)
        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        #print("mouse press event")
        me = QMouseEvent(event)
        if self.edit_mode == "DOUBLE_CLICK":
            return
        if me.button() == Qt.LeftButton:
            if self.read_only:
                return
            #if self.object_dialog is None:
            self.mouse_down_x = me.x()
            self.mouse_down_y = me.y()
            #    return
            if self.edit_mode == "NONE":
                self.down_x = me.x()
                self.down_y = me.y()
                self.edit_mode = "NEW_SUBFIGURE_DRAG"
                self.temp_rect = QRect(self._2imgx(self.down_x), self._2imgy(self.down_y), 1, 1)
            elif self.edit_mode == "CAPTURE_TEXT":
                self.down_x = me.x()
                self.down_y = me.y()
                self.edit_mode = "CAPTURE_TEXT_DRAG"
                self.temp_rect = QRect(self._2imgx(self.down_x), self._2imgy(self.down_y), 1, 1)                
            elif self.edit_mode == "ADJUSTING_SUBFIGURE": #in ["RESIZE_LEFT", "RESIZE_RIGHT", "RESIZE_TOP", "RESIZE_BOTTOM", "MOVE"]:
                self.temp_rect = self.subfigure_list[self.curr_subfigure_index].rect
                self.set_edit_mode("ADJUSTING_SUBFIGURE_DRAG")
                if self.adjusting_side == 0:
                    # set cursor to closehand cursor
                    self.setCursor(Qt.ClosedHandCursor)
        elif me.button() == Qt.RightButton:
            self.set_edit_mode("PAN")
            #self.temp_pan_x = self.pan_x
            #self.temp_pan_y = self.pan_y
            self.mouse_down_x = me.x()
            self.mouse_down_y = me.y()
        else:
            pass

    #def set_text_capture_callback(self, callback):
    #    self.text_capture_callback = callback


    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        def adjust_rect( rect ):

            left = rect.left()
            right = rect.right()
            if left > right:
                rect.setLeft(right)
                rect.setRight(left)
            top = rect.top()
            bottom = rect.bottom()
            if top > bottom:
                rect.setTop(bottom)
                rect.setBottom(top)
            return rect
        me = QMouseEvent(ev)
        # restore cursor
        self.setCursor(Qt.ArrowCursor)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
        if self.temp_rect is not None:
            self.temp_rect = adjust_rect(self.temp_rect)
        if self.edit_mode == "PAN":
            if self.temp_pan_x == 0 and self.temp_pan_y == 0:
                # signal to parent to show context menu
                print("show context menu")
                self.set_edit_mode("NONE")
                if hasattr(self.parent, 'show_figure_label_menu'):
                    self.parent.show_figure_label_menu(curr_pos)
                return
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
        elif self.edit_mode == "CAPTURE_TEXT_DRAG":
            if hasattr(self.parent, 'capture_text'):
                self.parent.capture_text(self.temp_rect)

            #self.text_capture_callback(self.temp_rect)
            self.temp_rect = None
            #text = self.get_text_from_rect(self.temp_rect)
            #print("captured text", text)
            #self.text_pixmap = self.orig_pixmap.copy(self.temp_rect)

        elif self.edit_mode == "ADJUSTING_SUBFIGURE_DRAG": #in ["NEW_SUBFIGURE_DRAG", "RESIZE_LEFT_DRAG", "RESIZE_RIGHT_DRAG", "RESIZE_TOP_DRAG", "RESIZE_BOTTOM_DRAG", "MOVE_DRAG"]:
            #print("curr_subfigure_index", self.curr_subfigure_index, self.temp_rect)
            # adjust temp_rect so that width and height are positive
            subfigure = self.subfigure_list[self.curr_subfigure_index]
            subfigure.rect = self.temp_rect
            subfigure.pixmap = self.orig_pixmap.copy(self.temp_rect)
            #self.subfigure_list[self.curr_subfigure_index] = subfigure
            #self.subfigure_list[self.curr_subfigure_index] = SubFigure(pixmap = self.orig_pixmap.copy(self.temp_rect), rect = self.temp_rect)
            self.temp_rect = None
            self.curr_subfigure_index = -1
        elif self.edit_mode == "NEW_SUBFIGURE_DRAG":
            #print("new subfigure", self.temp_rect)
            #self.temp_rect = QRect(self.down_x, self.down_y, self.mouse_curr_x-self.down_x, self.mouse_curr_y-self.down_y)
            # check size of the new subfigure
            abs_width = abs(self.temp_rect.width())
            abs_height = abs(self.temp_rect.height())
            min_width_height = 50
            #print("width, height", abs_width, abs_height)
            if abs_width < min_width_height or abs_height < min_width_height:
                self.temp_rect = None
            else:
                self.subfigure_list.append(SubFigure(pixmap=self.orig_pixmap.copy(self.temp_rect), rect=self.temp_rect, page_number = self.page_number))
                self.temp_rect = None
            if hasattr(self.parent, 'set_figure_pixmap'):
                self.parent.set_figure_pixmap(self.orig_pixmap)
        self.set_edit_mode("NONE")
        idx, close_to = self.check_subfigure(curr_pos)
        self.adjusting_side = close_to
        if idx > -1:
            self.curr_subfigure_index = idx
            self.set_edit_mode("ADJUSTING_SUBFIGURE")
        if hasattr(self.parent, 'load_subfigure_list'):
            self.parent.load_subfigure_list(self.subfigure_list)
        self.repaint()

    def set_page_number(self, page_number):
        self.page_number = page_number

    def wheelEvent(self, event):
        #if self.orig_pixmap is None:
        #    return
        we = QWheelEvent(event)
        scale_delta_ratio = 0
        if we.angleDelta().y() > 0:
            scale_delta_ratio = 0.1
        else:
            scale_delta_ratio = -0.1
        if self.scale <= 0.8 and scale_delta_ratio < 0:
            return

        self.prev_scale = self.scale
        #new_scale = self.scale + scale_delta
        #scale_proportion = new_scale / prev_scale       
        self.adjust_scale(scale_delta_ratio)
        #new_scale = self.scale + scale_delta
        scale_proportion = self.scale / self.prev_scale
        #print("1 pan_x, pan_y", self.pan_x, self.pan_y, "we.pos().x(), we.pos().y()", we.pos().x(), we.pos().y(), "scale_prop", scale_proportion, "scale", self.scale, "prev_scale", self.prev_scale, "scale_delta", scale_delta)       

        self.pan_x = round( we.pos().x() - (we.pos().x() - self.pan_x) * scale_proportion )
        self.pan_y = round( we.pos().y() - (we.pos().y() - self.pan_y) * scale_proportion )
        #print("2 pan_x, pan_y", self.pan_x, self.pan_y, "we.pos().x(), we.pos().y()", we.pos().x(), we.pos().y(), "scale_prop", scale_proportion, "scale", self.scale, "prev_scale", self.prev_scale, "scale_delta", scale_delta)       

        QLabel.wheelEvent(self, event)
        self.repaint()
        event.accept()

    def adjust_scale(self, scale_delta_ratio, recurse = True):
        #prev_scale = self.scale
        #prev_scale = self.scale
        #print("set scale", scale, self.parent, self.parent.sync_zoom)

        if self.scale > 1:
            scale_delta = math.floor(self.scale) * scale_delta_ratio
        else:
            scale_delta = scale_delta_ratio

        self.scale += scale_delta
        self.scale = round(self.scale * 10) / 10

        if self.orig_pixmap is not None:
            self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio), int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio))


        self.repaint()

    def paintEvent(self, event):
        # fill background with dark gray
        #print("paint event edge", self.edge_list)
        if hasattr(self.parent, 'statusBar'):
        #if self.parent.has_attr("statusBar"):
            self.parent.statusBar.setText( "{} {} {} {}".format(self.edit_mode, self.mouse_curr_x, self.mouse_curr_y, self.curr_subfigure_index))

        painter = QPainter(self)
        if self.curr_pixmap is not None:
            #print("paintEvent", self.curr_pixmap.width(), self.curr_pixmap.height())
            painter.drawPixmap(self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap)

        for idx, subfigure in enumerate(self.subfigure_list):
            if idx == self.curr_subfigure_index:
                continue
            if subfigure.page_number != self.page_number:
                continue
            pixmap, rect = subfigure.pixmap, subfigure.rect
            rect = self.rect_to_canvas(rect)
            color = Qt.blue
            painter.setPen(QPen(color, 2, Qt.DashLine))
            painter.drawRect(rect)
            # draw text in the middle of the rectangle with white background, calculated to fit the text, with a bit large font
            painter.setPen(QPen(color))
            painter.setFont(QFont("Arial", 12))
            text = "{}".format(idx+1)
            text_rect = painter.fontMetrics().boundingRect(text)
            text_rect.setWidth(text_rect.width() + 10)
            text_rect.setHeight(text_rect.height() + 10)
            text_rect.moveCenter(rect.center())
            painter.fillRect(text_rect, Qt.white)
            painter.drawText(text_rect, Qt.AlignCenter, text)


        color = Qt.red
        if self.temp_rect is not None or self.curr_subfigure_index > -1:
            rect = None
            if self.temp_rect is not None:
                #print("paintEvent temp rect:", self.temp_rect)
                rect = self.rect_to_canvas(self.temp_rect)
                painter.setPen(QPen(color, 2, Qt.DashLine))
                painter.drawRect(rect)
                if self.curr_subfigure_index > -1:
                    idx = self.curr_subfigure_index+1
                else:
                    idx = len(self.subfigure_list)+1
            elif self.curr_subfigure_index > -1:
                subfigure = self.subfigure_list[self.curr_subfigure_index]
                if subfigure.page_number == self.page_number:
                    pixmap, rect = subfigure.pixmap, subfigure.rect
                    rect = self.rect_to_canvas(rect)
                    painter.setPen(QPen(color, 2, Qt.DashLine))
                    painter.drawRect(rect)
                    idx = self.curr_subfigure_index+1
            if rect is not None:
                text = "{}".format(idx)
                if self.edit_mode == "CAPTURE_TEXT_DRAG":
                    text = "Text"
                painter.setPen(QPen(color))
                painter.setFont(QFont("Arial", 12))
                text_rect = painter.fontMetrics().boundingRect(text)
                text_rect.setWidth(text_rect.width() + 10)
                text_rect.setHeight(text_rect.height() + 10)
                text_rect.moveCenter(rect.center())
                painter.fillRect(text_rect, Qt.white)
                painter.drawText(text_rect, Qt.AlignCenter, text)




    def rect_to_canvas(self, rect):
        x = self._2canx(rect.x())
        y = self._2cany(rect.y())
        w = round(rect.width() / self.image_canvas_ratio * self.scale)
        h = round(rect.height() / self.image_canvas_ratio * self.scale)
        return QRect(x, y, w, h)
    
    def adjust_pixmap(self):
        #print("objectviewer calculate resize", self, self.object, self.landmark_list)
        if self.orig_pixmap is not None:
            self.orig_width = self.orig_pixmap.width()
            self.orig_height = self.orig_pixmap.height()
            #print("orig_width, orig_height", self.orig_width, self.orig_height)
            image_wh_ratio = self.orig_width / self.orig_height
            label_wh_ratio = self.width() / self.height()
            #print("image_wh_ratio, label_wh_ratio", image_wh_ratio, label_wh_ratio)
            if image_wh_ratio > label_wh_ratio:
                self.image_canvas_ratio = self.orig_width / self.width()
            else:
                self.image_canvas_ratio = self.orig_height / self.height()
            #print("image_canvas_ratio", self.image_canvas_ratio)
            new_width = int(self.orig_width*self.scale/self.image_canvas_ratio)
            new_height = int(self.orig_height*self.scale/self.image_canvas_ratio)
            #print("new_width, new_height", new_width, new_height)

            self.curr_pixmap = self.orig_pixmap.scaled(new_width,new_height, Qt.KeepAspectRatio)


    def resizeEvent(self, event):
        self.adjust_pixmap()
        QLabel.resizeEvent(self, event)


    def set_figure(self, file_name):
        #self.figure = figure
        self.orig_pixmap = QPixmap(file_name)
        self.curr_subfigure_index = -1
        self.adjust_pixmap()
        self.repaint()
    
    def set_pixmap(self, pixmap):
        self.orig_pixmap = pixmap
        self.curr_subfigure_index = -1
        self.adjust_pixmap()
        self.repaint()

    def set_subfigure_list(self, subfigure_list):
        self.subfigure_list = subfigure_list
        if len(subfigure_list) > 0:
            #print("set_subfigure_list", subfigure_list[0])
            pass
        self.curr_subfigure_index = -1
        #self.subfigure_rect = subfigure_rect
        #self.orig_pixmap = QPixmap(subfigure.get_file_path())
        #self.adjust_pixmap()
        self.repaint()

    def set_current_subfigure(self, subfigure_index):
        self.curr_subfigure_index = subfigure_index
        self.repaint()

    def mouseDoubleClickEvent(self, event):
        #print("mouse double click event")
        me = QMouseEvent(event)
        self.mouse_curr_x = me.x()
        self.mouse_curr_y = me.y()
        curr_pos = [self.mouse_curr_x, self.mouse_curr_y]
        
        if self.edit_mode == "ADJUSTING_SUBFIGURE":
            self.show_figure_index_dialog(self.curr_subfigure_index)

        self.set_edit_mode("DOUBLE_CLICK")
        #idx, close_to = self.check_subfigure(curr_pos)
        #self.adjusting_side = close_to
        #if idx > -1:
        #    self.curr_subfigure_index = idx
        #    self.set_edit_mode("ADJUSTING_SUBFIGURE")

        self.repaint()
        super().mouseDoubleClickEvent(event)

    def show_figure_index_dialog(self, old_index):
        #current_max_index = max([int(subfig[1].data(Qt.UserRole)) for subfig in self.subfigure_list] + [0])
        new_index, ok = QInputDialog.getInt(self, "Edit Figure Index", 
                                            "Enter the index for current figure:",
                                            self.curr_subfigure_index+1, 1, len(self.subfigure_list), 1)
        if ok:
            new_index -= 1
            if new_index == old_index:
                return
            # pop old index subfigure and put it at the new index
            old_subfigure = self.subfigure_list.pop(old_index)
            #print("old_subfigure", old_subfigure)
            self.subfigure_list.insert(new_index, old_subfigure)
            #for i, subfigure in enumerate(self.subfigure_list):
            #    subfigure.index = str(i+1)
            self.curr_subfigure_index = new_index
            # refresh parent's subfigure list
            self.parent.load_subfigure_list(self.subfigure_list)

    def clear(self):
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.repaint()

class DraggableTreeView(QTreeView):
    emptyAreaClicked = pyqtSignal()
    itemExpanded = pyqtSignal(object)  # New signal
    itemCollapsed = pyqtSignal(object)  # New signal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_position = None
        self.setMouseTracking(True)

        self.expanded.connect(self._onItemExpanded)
        self.collapsed.connect(self._onItemCollapsed)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        index = self.indexAt(event.pos())
        if not index.isValid():
            self.emptyAreaClicked.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.drag_start_position:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        if isinstance(self.model().itemFromIndex(self.selectedIndexes()[0]).data(), FgCollection):
            return

        drag = QDrag(self)
        mime_data = self.model().mimeData(self.selectedIndexes())
        #print("mime_data", mime_data)
        drag.setMimeData(mime_data)
        
        if event.modifiers() & Qt.ShiftModifier:
            drag.exec_(Qt.CopyAction)
        else:
            drag.exec_(Qt.MoveAction)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeColumnToContents(0)
        available_width = self.viewport().width()
        other_columns_width = sum(self.columnWidth(i) for i in range(1, self.model().columnCount()))
        self.setColumnWidth(0, max(0, available_width - other_columns_width))       

    def _onItemExpanded(self, index):
        item = self.model().itemFromIndex(index)
        self.itemExpanded.emit(item)

    def _onItemCollapsed(self, index):
        item = self.model().itemFromIndex(index)
        self.itemCollapsed.emit(item)

    def expandItem(self, item):
        index = self.model().indexFromItem(item)
        self.expand(index)

    def collapseItem(self, item):
        index = self.model().indexFromItem(item)
        self.collapse(index)

class LLMBackend(ABC):
    @abstractmethod
    def chat(self, messages):
        pass


class OpenAIBackend:
    def __init__(self, model='gpt-3.5-turbo', api_key=None):
        self.model = model
        self.api_key = api_key
        self.ssl_verification_disabled = False
        self.client = self._create_client()

    def _create_client(self):
        if self.ssl_verification_disabled:
            http_client = httpx.Client(verify=False)
        else:
            http_client = httpx.Client()
        
        return OpenAI(api_key=self.api_key, http_client=http_client)

    def chat(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except ssl.SSLError:
            logger.warning("SSL error occurred. Disabling SSL verification for future requests.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.chat(messages)  # Retry with new client
        except OpenAIError as e:
            logger.error(f"An error occurred: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

class OllamaBackend_old(LLMBackend):
    def __init__(self, model='llama3'):
        self.model = model
    def chat(self, messages):
        response = ollama.chat(model=self.model, messages=messages)
        return response['message']['content']

class OllamaBackend(LLMBackend):
    def __init__(self, model='llama3.1', server_ip="localhost", server_port="11434"):
        self.model = model
        self.client = ollama.Client(host="http://{}:{}".format(server_ip, server_port))
    
    def chat(self, messages):
        response = self.client.chat(model=self.model, messages=messages)
        return response['message']['content']

class LLMChat:
    def __init__(self, backend='ollama', model='llama3.1', api_key=None, server_ip=None, server_port=None):
        if backend == 'ollama' and ( server_ip is None or server_port is None ):
            raise ValueError("For Ollama, Server IP and port must be provided.")

        if backend == 'ollama':
            self.backend = OllamaBackend(model, server_ip, server_port)
        elif backend == 'openai':
            self.backend = OpenAIBackend(model, api_key)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def process_caption(self, caption, prompt = None):
        if prompt is None:
            prompt = CAPTION_PROCESSING_PROMPT_1 + "\n" + CAPTION_PROCESSING_PROMPT_2 + "\n"

        messages = [
            {"role": "system", "content": "You are a helpful assistant that processes scientific figure captions."},
            {"role": "user", "content": prompt + "Please process following caption in a similar way to the examples shown above:\n\n" + caption},
        ]
        return self.backend.chat(messages)

class RequestsLikeResponse:
    def __init__(self, httpx_response):
        self.httpx_response = httpx_response
        self.status_code = httpx_response.status_code
        self.headers = httpx_response.headers
        self.encoding = httpx_response.encoding
        self.url = str(httpx_response.url)
        self.text = httpx_response.text
        self.content = httpx_response.content
        self.request = SimpleNamespace(method=httpx_response.request.method)
        self.links = self._parse_links(httpx_response.headers.get('Link', ''))

    def json(self):
        return self.httpx_response.json()

    def raise_for_status(self):
        self.httpx_response.raise_for_status()

    def _parse_links(self, link_header):
        links = {}
        if link_header:
            link_pattern = re.compile(r'<([^>]+)>;\s*rel="([^"]+)"')
            matches = link_pattern.findall(link_header)
            for url, rel in matches:
                links[rel] = {'url': url}
        return links

class ZoteroBackend(zotero.Zotero):
    def __init__(self, library_id, library_type, api_key):
        super().__init__(library_id, library_type, api_key)
        #self.httpx_client = httpx.Client(verify=False)
        self.httpx_client = httpx.Client(verify=False, follow_redirects=True)
        self.ssl_verification_disabled = False

    def _retrieve_data(self, request=None, params=None):
        """
        Use normal HTTPS connection until an SSL error occurs, then fall back to httpx with SSL verification disabled
        """
        full_url = zotero.build_url(self.endpoint, request)
        self.self_link = request
        self._check_backoff()

        headers = self.default_headers()

        if not self.ssl_verification_disabled:
            try:
                # Try the normal pyzotero approach
                self.request = requests.get(
                    url=full_url,
                    headers=headers,
                    params=params,
                    allow_redirects=True
                )
                self.request.raise_for_status()
                return self.request
            except requests.exceptions.SSLError:
                logger.warning("SSL error occurred. Disabling SSL verification for future requests.")
                self.ssl_verification_disabled = True
            except requests.exceptions.RequestException as exc:
                logger.error(f"Request error: {exc}")
                error_handler(self, self.request, exc)

        # If SSL verification is disabled or an SSL error occurred, use httpx
        try:
            encoded_url = urllib.parse.quote(full_url, safe=':/?&=')
            httpx_response = self.httpx_client.get(
                url=encoded_url,
                headers=headers,
                params=params
            )
            self.request = RequestsLikeResponse(httpx_response)
            self.request.raise_for_status()
        except httpx.RequestError as exc:
            logger.error(f"Request error: {exc}")
            raise zotero.ze.HTTPError(str(exc))
        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP status error: {exc}")
            error_handler(self, self.request, exc)

        backoff = self.request.headers.get("backoff") or self.request.headers.get("retry-after")
        if backoff:
            self._set_backoff(backoff)

        return self.request

def error_handler(zot, response, exc):
    error_codes = {
        400: zotero.ze.UnsupportedParams,
        401: zotero.ze.UserNotAuthorised,
        403: zotero.ze.UserNotAuthorised,
        404: zotero.ze.ResourceNotFound,
        409: zotero.ze.Conflict,
        412: zotero.ze.PreConditionFailed,
        413: zotero.ze.RequestEntityTooLarge,
        428: zotero.ze.PreConditionRequired,
        429: zotero.ze.TooManyRequests,
    }

    def err_msg(response):
        return "\nCode: %s\nURL: %s\nMethod: %s\nResponse: %s" % (
            response.status_code,
            response.url,
            response.request.method,
            response.text,
        )

    logger.error(f"Error response: {err_msg(response)}")

    if error_codes.get(response.status_code):
        if response.status_code == 429:
            delay = response.headers.get("backoff") or response.headers.get("retry-after")
            if not delay:
                raise zotero.ze.TooManyRetries(
                    "You are being rate-limited and no backoff or retry duration has been received from the server. Try again later"
                )
            else:
                zot._set_backoff(delay)
        else:
            raise error_codes.get(response.status_code)(err_msg(response))
    else:
        raise zotero.ze.HTTPError(err_msg(response))
    
class PDFViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page_number = 1
        self.initUI()

    def initUI(self):
        self.pdfcontrol_widget = QWidget()
        self.pdfcontrol_layout = QHBoxLayout()#
        self.pdfcontrol_widget.setLayout(self.pdfcontrol_layout)
        #self.refcontrol_layout.addWidget(self.loadButton)
        self.pdf_prev_button = QPushButton("<")
        self.pdf_next_button = QPushButton(">")
        self.pdf_begin_button = QPushButton("<<")
        self.pdf_end_button = QPushButton(">>")
        self.pdf_prev_button.clicked.connect(self.on_pdf_prev_clicked)
        self.pdf_next_button.clicked.connect(self.on_pdf_next_clicked)
        self.pdf_begin_button.clicked.connect(self.on_pdf_begin_clicked)
        self.pdf_end_button.clicked.connect(self.on_pdf_end_clicked)        
        for button in [self.pdf_prev_button, self.pdf_next_button, self.pdf_begin_button, self.pdf_end_button]:
            button.setMinimumWidth(30)
            #button.setMaximumWidth(30)
        self.page_spinner = QSpinBox()        
        self.page_spinner.setRange(1, 1000)
        self.page_spinner.setValue(1)
        self.page_spinner.setSingleStep(1)
        self.page_spinner.setSuffix(" / ")
        self.page_spinner.setWrapping(True)
        self.pdfcontrol_layout.addWidget(self.pdf_begin_button)
        self.pdfcontrol_layout.addWidget(self.pdf_prev_button)
        self.pdfcontrol_layout.addWidget(self.page_spinner)
        self.pdfcontrol_layout.addWidget(self.pdf_next_button)
        self.pdfcontrol_layout.addWidget(self.pdf_end_button)
        #self.pdfcontrol_widget.hide()
        self.page_spinner.valueChanged.connect(self.on_page_changed)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.pdf_label = FigureLabel()
        self.pdf_label.setReadOnly(True)
        self.layout.addWidget(self.pdfcontrol_widget,0)
        self.layout.addWidget(self.pdf_label,1)

    def set_pdf(self, file_name):
        self.pdf_document = fitz.open(file_name)
        self.page_number = 1        
        self.page_spinner.setRange(1, self.pdf_document.page_count)
        self.page_spinner.setValue(1)
        self.page_spinner.setSingleStep(1)
        self.page_spinner.setSuffix(" / " + str(self.pdf_document.page_count))
        self.on_page_changed( self.page_number)
        #self.page_spinner.setWrapping(True)

    def on_page_changed(self, page_number):
        #print("Page changed:", page_number)
        if self.pdf_document is None:
            return
        self.page_number = page_number
        self.current_page = self.pdf_document[page_number-1]
        pix = self.current_page.get_pixmap(dpi=600, alpha=False, annots=True, matrix=fitz.Matrix(2, 2))
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)  # QImage
        self.original_figure_image = QPixmap.fromImage(img)  # QPixmap
        #print("pixmap size:", self.original_figure_image .size())
        self.pdf_label.set_pixmap(self.original_figure_image )
        self.pdf_label.set_page_number(page_number)
        #self.detectButton.setEnabled(True)
        #self.tempModel.clear()
        #self.subfigure_list = []
        #self.lblFigure.set_subfigure_list(self.subfigure_list)
        self.update()        

    def on_pdf_prev_clicked(self):
        #print("PDF prev clicked")
        current_page = self.page_spinner.value()
        if current_page > 1:
            self.page_spinner.setValue(current_page-1)
    
    def on_pdf_next_clicked(self):
        #print("PDF next clicked")
        current_page = self.page_spinner.value()
        if current_page < self.pdf_document.page_count:
            self.page_spinner.setValue(current_page+1)
    
    def on_pdf_begin_clicked(self):
        #print("PDF begin clicked")
        self.page_spinner.setValue(1)
    
    def on_pdf_end_clicked(self):
        #print("PDF end clicked")
        self.page_spinner.setValue(self.pdf_document.page_count)
    
    def clear(self):
        #print("clear pdf")
        self.pdf_label.clear()
        self.page_number = -1
        self.pdf_document = None
        self.page_spinner.setRange(1, 1)
        self.page_spinner.setValue(1)
        self.page_spinner.setSingleStep(1)
        self.page_spinner.setSuffix("")

        self.update()

class SearchableComboBox(QComboBox):
    entrySelected = pyqtSignal(object)  # Signal to emit when an entry is selected

    def __init__(self, parent=None):
        super(SearchableComboBox, self).__init__(parent)
        
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(10)
        
        completer = self.completer()
        completer.setCompletionMode(completer.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.model = QStandardItemModel()
        self.setModel(self.model)

        self.current_entry = None
        self._skip_search = False

        self.lineEdit().textEdited.connect(self.on_text_changed)
        self.activated.connect(self.on_item_selected)

    @pyqtSlot(str)
    def on_text_changed(self, text):
        if len(text) == 0:
            self.setEntry(None)
            
        if self._skip_search or len(text) < 2:
            return
        
        self._skip_search = True
        self.model.clear()
        
        if text:
            results = self.search_fg_tree_of_life(text)
            for result in results:
                item = QStandardItem(f"{result.rank} {result.name}")
                item.setData(result, Qt.UserRole)
                self.model.appendRow(item)
        
        self.setCurrentIndex(-1)
        self.setEditText(text)
        #
        self._skip_search = False

    def search_fg_tree_of_life(self, search_term):
        search_term = search_term.lower()
        fields_to_search = [
            FgTreeOfLife.name,
        ]
        
        query = FgTreeOfLife.select()
        conditions = [fn.Lower(field).contains(search_term) for field in fields_to_search]
        query = query.where(reduce(operator.or_, conditions))
        return query.limit(50)  # Limit results to prevent performance issues
    
    def setEntry(self, entry):
        if entry is None:
            self.current_entry = None
            self.setCurrentText('')            
            return
        self._skip_search = True
        self.setCurrentText(f"{entry.rank} {entry.name}")
        self.current_entry = entry
        self._skip_search = False

    @pyqtSlot(int)
    def on_item_selected(self, index):
        if index >= 0:
            item = self.model.item(index)
            self.current_entry = item.data(Qt.UserRole)
            self.entrySelected.emit(self.current_entry)

    def getCurrentEntry(self):
        return self.current_entry