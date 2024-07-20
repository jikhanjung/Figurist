from PyQt5.QtWidgets import QMainWindow, QHeaderView, QApplication, QAbstractItemView, \
                            QMessageBox, QTreeView, QTableView, QSplitter, QAction, QMenu, \
                            QStatusBar, QInputDialog, QToolBar, QWidget, QPlainTextEdit, QVBoxLayout, QHBoxLayout, \
                            QPushButton, QRadioButton, QLabel
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QSize, QTranslator, QItemSelectionModel, QObject, QEvent, QMargins
from PyQt5.QtWidgets import QHeaderView

from PyQt5.QtCore import pyqtSlot
import re,os,sys
from pathlib import Path
from peewee import *
from PIL.ExifTags import TAGS
import shutil
import copy
from datetime import datetime
import FgUtils as fg
from FgModel import *
from FgDialogs import *
from peewee_migrate import Router

from FgComponents import CustomTableModel, CustomItemDelegate
from FgLogger import setup_logger
logger = setup_logger(fg.PROGRAM_NAME)

ICON = {'new_reference': 'icons/new_reference.png', 'about': 'icons/about.png', 'exit': 'icons/exit.png', 'preferences': 'icons/preferences.png' } 

class FiguristMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(fg.resource_path('icons/Figurist.png')))
        self.setWindowTitle("{} v{}".format(self.tr("Figurist"), fg.PROGRAM_VERSION))
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

        self.prepare_database()
        self.reset_treeView()
        self.load_references()

    def initUI(self):
        ''' initialize UI '''
        self.figureView = QTableView()
        self.referenceView = QTreeView()
        #self.taxaView = QTreeView()

        self.icon_mode = False
        self.toggle_button = QPushButton("Toggle View")
        self.toggle_button.clicked.connect(self.toggle_view)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        self.right_layout.addWidget(self.figureView)
        self.right_layout.addWidget(self.toggle_button)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.referenceView)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([300, 800])


        self.setCentralWidget(self.splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)


        self.referenceView.doubleClicked.connect(self.on_referenceView_doubleClicked)
        self.figureView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.figureView.customContextMenuRequested.connect(self.open_figureView_menu)

        #self.model = CustomTableModel(self.data)
        #self.delegate = CustomItemDelegate()
        #self.figureView.setItemDelegate(self.delegate)


        ''' toolbar and actions'''
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setIconSize(QSize(32,32))

        self.actionNewReference = QAction(QIcon(fg.resource_path(ICON['new_reference'])), self.tr("New Reference\tCtrl+N"), self)
        self.actionNewReference.triggered.connect(self.on_action_new_reference_triggered)
        self.actionNewReference.setShortcut(QKeySequence("Ctrl+N"))
        self.actionExit = QAction(QIcon(fg.resource_path(ICON['exit'])), self.tr("Exit\tCtrl+W"), self)
        self.actionExit.triggered.connect(self.on_action_exit_triggered)
        self.actionExit.setShortcut(QKeySequence("Ctrl+W"))
        self.actionAbout = QAction(QIcon(fg.resource_path(ICON['about'])), self.tr("About\tF1"), self)
        self.actionAbout.triggered.connect(self.on_action_about_triggered)
        self.actionAbout.setShortcut(QKeySequence("F1"))
        self.actionPreferences = QAction(QIcon(fg.resource_path(ICON['preferences'])),self.tr("Preferences"), self)
        self.actionPreferences.triggered.connect(self.on_action_preferences_triggered)

        self.toolbar.addAction(self.actionNewReference)
        self.toolbar.addAction(self.actionPreferences)
        self.toolbar.addAction(self.actionAbout)
        self.addToolBar(self.toolbar)



        ''' menu '''
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu(self.tr("File"))
        self.file_menu.addAction(self.actionExit)
        self.help_menu = self.main_menu.addMenu(self.tr("Help"))
        self.help_menu.addAction(self.actionAbout)

        self.m_app = QApplication.instance()
        self.read_settings()

        self.figureView.setDragEnabled(True)
        self.figureView.setAcceptDrops(True)
        #print("tableview accept drops:", self.tableView.acceptDrops())
        self.figureView.setDropIndicatorShown(True)
        self.figureView.dropEvent = self.figureView_drop_event
        self.figureView.dragEnterEvent = self.figureView_drag_enter_event
        self.figureView.dragMoveEvent = self.figureView_drag_move_event

    def toggle_view(self):
        self.icon_mode = not self.icon_mode
        self.figure_model.set_icon_mode(self.icon_mode)
        self.delegate.set_icon_mode(self.icon_mode)
        
        if self.icon_mode:
            #print("icon mode")
            self.figureView.setGridStyle(Qt.NoPen)
            self.figureView.setIconSize(QSize(128, 128))
            self.figureView.setShowGrid(False)
            self.figureView.horizontalHeader().hide()
            self.figureView.verticalHeader().hide()
            
            # Set row and column sizes for icon mode
            self.figureView.verticalHeader().setDefaultSectionSize(240)
            self.figureView.horizontalHeader().setDefaultSectionSize(240)
            
            # Set resize mode to Fixed for both directions
            self.figureView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.figureView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            
            # Enable text wrapping for item delegate
            self.delegate.setWordWrap(True)
        else:
            #print("list mode")
            self.figureView.setGridStyle(Qt.SolidLine)
            self.figureView.setIconSize(QSize(16, 16))
            self.figureView.setShowGrid(True)
            self.figureView.horizontalHeader().show()
            self.figureView.verticalHeader().show()
            
            # Reset row and column sizes for list mode
            self.figureView.verticalHeader().setDefaultSectionSize(30)  # Adjust as needed
            self.figureView.horizontalHeader().setDefaultSectionSize(100)  # Adjust as needed
            
            # Set resize modes for columns in list mode
            self.figureView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            for i in range(1, self.figure_model.columnCount()):
                self.figureView.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
            
            # Disable text wrapping for item delegate
            self.delegate.setWordWrap(False)

        self.figure_model.layoutChanged.emit()
        self.figureView.reset()

    def update_language(self, language):
        #print("main update language:", language)
        #translators = self.m_app.findChildren(QTranslator)
        #for translator in translators:
        #    print("Translator:", translator)
        
        if self.m_app.translator is not None:
            self.m_app.removeTranslator(self.m_app.translator)
            #print("removed translator")
            self.m_app.translator = None
        else:
            pass
            #print("no translator")

        translator = QTranslator()
        translator_path = fg.resource_path("translations/PTMGenerator2_{}.qm".format(language))
        #print("translator_path:", translator_path)
        if os.path.exists(translator_path):
            #print("Loading new translator:", translator_path)
            #pass
            translator.load(translator_path)
            #translator.load('PTMGenerator2_{}.qm'.format(language))
            self.m_app.installTranslator(translator)
            self.m_app.translator = translator
        else:
            pass
            #print("Translator not found:", translator_path)

        self.setWindowTitle("{} v{}".format(self.tr(fg.PROGRAM_NAME), fg.PROGRAM_VERSION))
        file_text = self.tr("File")
        #print("file_text:", file_text)
        self.file_menu.setTitle(file_text)
        self.help_menu.setTitle(self.tr("Help"))
        self.actionPreferences.setText(self.tr("Preferences"))
        self.actionAbout.setText(self.tr("About"))
        self.actionExit.setText(self.tr("Exit"))
        self.actionNewReference.setText(self.tr("New Reference\tCtrl+N"))

    def on_action_preferences_triggered(self):
        preferences = PreferencesDialog(self)
        preferences.exec()
        self.read_settings()


    def figureView_drag_enter_event(self, event):
        event.accept()

    def figureView_drag_move_event(self, event):
        event.accept()

    def on_referenceView_doubleClicked(self):
        self.dlg = ReferenceDialog(self)
        self.dlg.setModal(True)
        self.dlg.load_reference( self.selected_reference )
        ret = self.dlg.exec_()
        self.reset_treeView()
        self.load_references()

    def reset_tableView(self):
        #self.figure_model = CustomTableModel()
        #self.figureView.setHeaderHidden(True)
        pass

    def reset_treeView(self):
        self.reference_model = QStandardItemModel()
        self.referenceView.setModel(self.reference_model)
        self.referenceView.setHeaderHidden(True)
        self.reference_selection_model = self.referenceView.selectionModel()
        self.reference_selection_model.selectionChanged.connect(self.on_reference_selection_changed)
        header = self.referenceView.header()
        self.referenceView.setSelectionBehavior(QTreeView.SelectRows)

    def load_references(self):
        self.reference_model.clear()
        self.selected_reference = None
        ref_list = FgReference.filter(parent=None)

        ref_list = FgReference.select()
        for ref in ref_list:
            item1 = QStandardItem(ref.author + " (" + str(ref.year) + ")")
            item2 = QStandardItem(str(ref.id))
            item1.setData(ref)
            self.reference_model.appendRow([item1,item2])#,item2,item3] )
        self.referenceView.expandAll()
        self.referenceView.hideColumn(1)

    def on_figure_selection_changed(self, selected, deselected):
        pass

    def load_figure(self):
        self.reset_tableView()
        if self.selected_reference is None:
            return
        figure_list = FgFigure.select().where(FgFigure.reference == self.selected_reference)
        self.data = []
        for figure in figure_list:
            path = figure.get_file_path()
            print("figure path:", path)
            self.data.append( { 'name': figure.figure_number, 'type': figure.file_path, 'size': '', 'icon': figure.get_file_path() } )
            #item1 = QStandardItem(figure.figure_number)
            #item2 = QStandardItem(figure.file_path)
            #item1.setData(figure)
            #self.figure_model.appendRow([item1])
        self.figure_model = CustomTableModel(self.data)
        self.delegate = CustomItemDelegate()
        self.figureView.setModel(self.figure_model)
        self.figureView.setItemDelegate(self.delegate)
        #self.figureView.expandAll()
        self.figure_selection_model = self.figureView.selectionModel()
        self.figure_selection_model.selectionChanged.connect(self.on_figure_selection_changed)
        #header = self.figureView.header()
        self.figureView.setSelectionBehavior(QTreeView.SelectRows)


    def on_reference_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if len(indexes) == 0:
            return
        index = indexes[0]
        self.selected_reference = self.reference_model.itemFromIndex(index).data()
        #print("selected reference:", self.selected_reference)
        self.load_figure()

    def on_action_about_triggered(self):
        year_since = "2024"
        #year_current = datetime.now()
        now = datetime.datetime.now()
        year_current = now.strftime("%Y")
        #return now.strftime("%Y%m%d")

        if year_since == year_current:
            year_str = str(year_since)
        else:
            year_str = "{}-{}".format(year_since, year_current)

        text = fg.PROGRAM_NAME + " v" + fg.PROGRAM_VERSION + "\n\n"
        text += "This software is distributed under the terms of the MIT License.\n\n"
        #text += "© {year_str} Jikhan Jung\n"
        text += "© {} Jikhan Jung\n".format(year_str)

        QMessageBox.about(self, "About", text)

        license_text = """
Figurist
Copyright {} Jikhan Jung

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""".format(year_str)

    def figureView_drop_event(self, event):
        print("tabelview drop event", event.mimeData().text())
        if self.selected_reference is None:
            return
        
        if event.mimeData().text() == "":
            return
        file_name_list = event.mimeData().text().strip().split("\n")
        if len(file_name_list) == 0:
            return

        print("file name list: [", file_name_list, "]")

        QApplication.setOverrideCursor(Qt.WaitCursor)
        total_count = len(file_name_list)
        current_count = 0
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.setModal(True)
        label_text = self.tr("Importing figure files...")
        self.progress_dialog.lbl_text.setText(label_text)
        self.progress_dialog.pb_progress.setValue(0)
        self.progress_dialog.show()

        for file_name in file_name_list:
            current_count += 1
            self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
            self.progress_dialog.update()
            QApplication.processEvents()

            file_name = fg.process_dropped_file_name(file_name)

            ext = file_name.split('.')[-1].lower()
            if ext in fg.IMAGE_EXTENSION_LIST:
                figure = self.selected_reference.add_figure(Path(file_name))
                figure.save()

            elif os.path.isdir(file_name):
                self.statusBar.showMessage(self.tr("Cannot process directory..."),2000)

            else:
                self.statusBar.showMessage(self.tr("Nothing to import."),2000)

            self.load_figure()

        self.progress_dialog.close()

        reference = self.selected_reference
        self.load_references()
        self.reset_tableView()
        self.select_reference(reference)
        self.load_figure()
        QApplication.restoreOverrideCursor()


    def select_reference(self,reference,node=None):
        if reference is None:
            return
        if node is None:
            node = self.reference_model.invisibleRootItem()   

        for i in range(node.rowCount()):
            item = node.child(i,0)
            if item.data() == reference:
                self.referenceView.setCurrentIndex(item.index())
                break
            self.select_reference(reference,node.child(i,0))

    def on_action_new_reference_triggered(self):
        dialog = ReferenceDialog(self)
        dialog.exec_()
        self.reset_treeView()
        self.load_references()

        #print("New Reference")

    def on_action_exit_triggered(self):
        self.close()

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def read_settings(self):
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, fg.COMPANY_NAME, fg.PROGRAM_NAME)
        self.restoreGeometry(self.settings.value("geometry", self.saveGeometry()))
        self.restoreState(self.settings.value("windowState", self.saveState()))

    def write_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())    

    def prepare_database(self):
        migrations_path = fg.resource_path("migrations")
        logger.info("migrations path: %s", migrations_path)
        logger.info("database path: %s", database_path)
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")

        # backup database file to backup directory
        backup_path = os.path.join( fg.DB_BACKUP_DIRECTORY, DATABASE_FILENAME + '.' + date_str )
        if not os.path.exists(backup_path) and os.path.exists(database_path):
            shutil.copy2(database_path, backup_path)
            logger.info("backup database to %s", backup_path)
            # read backup directory and delete old backups
            backup_list = os.listdir(fg.DB_BACKUP_DIRECTORY)
            # filter out non-backup files
            backup_list = [f for f in backup_list if f.startswith(DATABASE_FILENAME)]
            backup_list.sort()
            if len(backup_list) > 10:
                for i in range(len(backup_list) - 10):
                    os.remove(os.path.join(fg.DB_BACKUP_DIRECTORY, backup_list[i]))                    
        
        #logger.info("database name: %s", mu.DEFAULT_DATABASE_NAME)
        #print("migrations path:", migrations_path)
        gDatabase.connect()
        router = Router(gDatabase, migrate_dir=migrations_path)

        # Auto-discover and run migrations
        router.run()        
        return

    def open_figureView_menu(self, position):
        indexes = self.figureView.selectedIndexes()
        if len(indexes) == 0:
            return

        level = 0
        figure_list = []
        for index in indexes:
            #level = max(level, index.row())
            item = self.figure_model.itemFromIndex(index)
            #print("item:", item)
            figure = item.data()
            if figure is None:
                continue
            #print("figure:", figure)
            figure_list.append(figure)

        self.selected_figures = figure_list

        action_delete_figure = QAction(self.tr("Delete figure(s)"))
        action_delete_figure.triggered.connect(self.on_action_delete_figure_triggered)

        menu = QMenu()
        menu.addAction(action_delete_figure)
        menu.exec_(self.figureView.viewport().mapToGlobal(position))

    def on_action_delete_figure_triggered(self):
        if self.selected_figures is None:
            return
        for figure in self.selected_figures:
            figure.delete_instance()
        self.load_figure()


if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    #with open('log.txt', 'w') as f:
    #    f.write("hello\n")
    #    # current directory
    #    f.write("current directory 1:" + os.getcwd() + "\n")
    #    f.write("current directory 2:" + os.path.abspath(".") + "\n")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(fg.resource_path('icons/Figurist.png')))
    app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,fg.COMPANY_NAME, fg.PROGRAM_NAME)

    translator = QTranslator()
    app.language = app.settings.value("language", "en")
    translator.load(fg.resource_path("translations/Figurist_{}.qm".format(app.language)))
    app.installTranslator(translator)
    app.translator = translator

    #app.settings = 
    #app.preferences = QSettings("Modan", "Modan2")

    #WindowClass의 인스턴스 생성
    myWindow = FiguristMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()
    #myWindow.activateWindow()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
    
''' 
How to make an exe file

pyinstaller --name "Figurist_v0.1.0_.exe" --onefile --noconsole --add-data "icons/*.png;icons" --add-data "translations/*.qm;translations" --add-data "migrations/*;migrations" --icon="icons/Figurist.png" Figurist.py
pyinstaller --onedir --noconsole --add-data "icons/*.png;icons" --add-data "translations/*.qm;translations" --add-data "migrations/*;migrations" --icon="icons/Figurist.png" --noconfirm Figurist.py
#--upx-dir=/path/to/upx

for MacOS
pyinstaller --onefile --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Figurist.png" Figurist.py
pyinstaller --onedir --noconsole --add-data "icons/*.png:icons" --add-data "translations/*.qm:translations" --add-data "migrations/*:migrations" --icon="icons/Figurist.png" --noconfirm Figurist.py

pylupdate5 Figurist.py -ts translations/Figurist_en.ts
pylupdate5 Figurist.py -ts translations/Figurist_ko.ts
pylupdate5 Figurist.py -ts translations/Figurist_ja.ts

linguist


'''