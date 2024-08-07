from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QPushButton, QTreeView, QSizePolicy, QHeaderView, QLabel, QInputDialog
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QSize, QMargins, QObject, QEvent, QMimeData, pyqtSignal
from PyQt5.QtGui import QIcon, QStandardItemModel, QPixmap, QStandardItem, QPen, QFont, QMouseEvent, QWheelEvent, QPainter, QDrag
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem, QListView, QStackedWidget, QAbstractItemView
import time, math
from PyQt5.QtCore import QByteArray
from FgModel import FgCollection, FgReference
import ollama, openai
from abc import ABC, abstractmethod

CLOSE_TO = { 'left': 1, 'right': 2, 'top': 4, 'bottom': 8 }

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
            pixmap, rect = subfigure
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

            self.temp_rect = QRect(self.subfigure_list[self.curr_subfigure_index][1])
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
                self.temp_rect = self.subfigure_list[self.curr_subfigure_index][1]
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

    def set_text_capture_callback(self, callback):
        self.text_capture_callback = callback


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
                if hasattr(self.parent, 'show_figure_label_menu'):
                    self.set_edit_mode("NONE")
                    self.parent.show_figure_label_menu(curr_pos)
                return
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
        elif self.edit_mode == "CAPTURE_TEXT_DRAG":
            self.text_capture_callback(self.temp_rect)
            self.temp_rect = None
            #text = self.get_text_from_rect(self.temp_rect)
            #print("captured text", text)
            #self.text_pixmap = self.orig_pixmap.copy(self.temp_rect)

        elif self.edit_mode == "ADJUSTING_SUBFIGURE_DRAG": #in ["NEW_SUBFIGURE_DRAG", "RESIZE_LEFT_DRAG", "RESIZE_RIGHT_DRAG", "RESIZE_TOP_DRAG", "RESIZE_BOTTOM_DRAG", "MOVE_DRAG"]:
            #print("curr_subfigure_index", self.curr_subfigure_index, self.temp_rect)
            # adjust temp_rect so that width and height are positive
            self.subfigure_list[self.curr_subfigure_index] = (self.orig_pixmap.copy(self.temp_rect), self.temp_rect)
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
                self.subfigure_list.append((self.orig_pixmap.copy(self.temp_rect), self.temp_rect))
                self.temp_rect = None
        self.set_edit_mode("NONE")
        idx, close_to = self.check_subfigure(curr_pos)
        self.adjusting_side = close_to
        if idx > -1:
            self.curr_subfigure_index = idx
            self.set_edit_mode("ADJUSTING_SUBFIGURE")
        if hasattr(self.parent, 'load_subfigure_list'):
            self.parent.load_subfigure_list(self.subfigure_list)
        self.repaint()

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
            pixmap, rect = subfigure
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
                pixmap, rect = self.subfigure_list[self.curr_subfigure_index]
                rect = self.rect_to_canvas(rect)
                painter.setPen(QPen(color, 2, Qt.DashLine))
                painter.drawRect(rect)
                idx = self.curr_subfigure_index+1

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
            self.subfigure_list.insert(new_index, old_subfigure)
            self.curr_subfigure_index = new_index
            # refresh parent's subfigure list
            self.parent.load_subfigure_list(self.subfigure_list)

class DraggableTreeView(QTreeView):
    emptyAreaClicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_position = None
        self.setMouseTracking(True)

    def _mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            # Click is outside any item
            self.emptyAreaClicked.emit()
        super().mousePressEvent(event)
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
        print("mime_data", mime_data)
        drag.setMimeData(mime_data)
        
        if event.modifiers() & Qt.ShiftModifier:
            drag.exec_(Qt.CopyAction)
        else:
            drag.exec_(Qt.MoveAction)

    def _mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.drag_start_position:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        
        selected_indexes = self.selectedIndexes()
        items_data = []
        for index in selected_indexes:
            item = self.model().itemFromIndex(index)
            if isinstance(item.data(), FgCollection):
                items_data.append(('collection', item.data().id))
            elif isinstance(item.data(), FgReference):
                items_data.append(('reference', item.data().id))
        
        mime_data.setData("application/x-figurist-items", QByteArray(str(items_data).encode()))
        #mime_data.setData("application/x-figurist-items", QByteArray(str(items_data).encode()))
        drag.setMimeData(mime_data)
        #print("mime_data", mime_data)
        
        if event.modifiers() & Qt.ShiftModifier:
            drag.exec_(Qt.CopyAction)
        else:
            drag.exec_(Qt.MoveAction)            


class LLMBackend(ABC):
    @abstractmethod
    def chat(self, messages):
        pass

class OpenAIBackend(LLMBackend):
    def __init__(self, model='gpt-3.5-turbo', api_key=None):
        self.model = model
        if api_key:
            openai.api_key = api_key
        elif not openai.api_key:
            raise ValueError("OpenAI API key must be provided or set as an environment variable.")

    def chat(self, messages):
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message['content']
        except openai.error.OpenAIError as e:
            print(f"An error occurred: {e}")
            return None

class OllamaBackend(LLMBackend):
    def __init__(self, model='llama3'):
        self.model = model

    def chat(self, messages):
        response = ollama.chat(model=self.model, messages=messages)
        return response['message']['content']

class LLMChat:
    def __init__(self, backend='ollama', model='llama3', api_key=None):
        if backend == 'ollama':
            self.backend = OllamaBackend(model)
        elif backend == 'openai':
            self.backend = OpenAIBackend(model, api_key)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def process_caption(self, caption):
        content = '''
Please process following caption so that:
each subfigure caption is in one line and separated by a newline character;
each subfigure caption should contain a scientific name enclosed in underlined brackets;
each subfigure caption should contains specimen information if available;
each subfigure caption should contain a scale bar information if available.

For example:
Figure 3.
Pojetaia runnegari Jell, 1980 from the Shackleton Limestone. (1–4)
Specimen SMNH Mo185039 in (1) lateral view, (2) dorsal view, (3) magniﬁca-
tion of the central margin, showing laminar crystalline imprints, (4) magniﬁca-
tion of the cardinal teeth shown in (2). (5, 6) Specimen SMNH Mo185040,
(5) lateral view, (6) magniﬁcation of lateral surface, showing laminar crystalline
imprints. (7) Specimen SMNH Mo185041 in lateral view. (8) Specimen SMNH
Mo185042 in lateral view. (9) Specimen SMNH Mo185043. (5, 6, 8) imaged
under low vacuum settings. (1, 2, 6–9) Scale bars = 200 µm; (3–5) scale bars
= 100 µm.

Paragraph above should be converted to:
1. _Pojetaia runnegari_ SMNH Mo185039, lateral view (200 µm scale bar).
2. _Pojetaia runnegari_ SMNH Mo185039, dorsal view (200 µm scale bar).
3. _Pojetaia runnegari_ SMNH Mo185039, magnification of central margin, showing laminar crystalline imprints (100 µm scale bar).
4. _Pojetaia runnegari_ SMNH Mo185039, magnification of cardinal teeth (100 µm scale bar).
5. _Pojetaia runnegari_ SMNH Mo185040, lateral view (100 µm scale bar).
6. _Pojetaia runnegari_ SMNH Mo185040, magnification of lateral surface, showing laminar crystalline imprints (200 µm scale bar).
7. _Pojetaia runnegari_ SMNH Mo185041, lateral view (200 µm scale bar).
8. _Pojetaia runnegari_ SMNH Mo185042, lateral view (200 µm scale bar).
9. _Pojetaia runnegari_ SMNH Mo185043 (200 µm scale bar).

'''
        messages = [
            {"role": "system", "content": "You are a helpful assistant that processes scientific figure captions."},
            {"role": "user", "content": content + caption},
        ]
        return self.backend.chat(messages)