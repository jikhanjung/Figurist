from PyQt5.QtWidgets import QMainWindow, QHeaderView, QApplication, QAbstractItemView, \
                            QMessageBox, QTreeView, QTableView, QSplitter, QAction, QMenu, \
                            QStatusBar, QInputDialog, QToolBar, QWidget, QPlainTextEdit, QVBoxLayout, QHBoxLayout, \
                            QPushButton, QRadioButton, QLabel
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QSize, QTranslator, QItemSelectionModel, QObject, QEvent

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
from peewee_migrate import Router

from FgLogger import setup_logger
logger = setup_logger(fg.PROGRAM_NAME)

ICON = {'new_reference': 'icons/new_reference.png', 'about': 'icons/about.png', 'exit': 'icons/exit.png' } 

class FiguristMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(fg.resource_path('icons/Figurist.png')))
        self.setWindowTitle("{} v{}".format(self.tr("Figurist"), fg.PROGRAM_VERSION))
        self.setGeometry(100, 100, 800, 600)
        
        self.initUI()
        self.prepare_database()


    def initUI(self):
        ''' initialize UI '''
        self.figureView = QTableView()
        self.literatureView = QTreeView()
        self.taxaView = QTreeView()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.taxaView)
        self.splitter.addWidget(self.figureView)
        self.splitter.setSizes([300, 800])

        self.setCentralWidget(self.splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

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

        self.toolbar.addAction(self.actionNewReference)
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

    def on_action_about_triggered(self):
        text = fg.PROGRAM_NAME + " v" + fg.PROGRAM_VERSION + "\n\n"
        text += "This software is distributed under the terms of the MIT License.\n\n"
        text += "© 2024 Jikhan Jung\n"

        QMessageBox.about(self, "About", text)

        license_text = """
Figurist
Copyright 2023-2024 Jikhan Jung

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


    def on_action_new_reference_triggered(self):
        print("New Reference")

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

    #app.settings = 
    #app.preferences = QSettings("Modan", "Modan2")

    #WindowClass의 인스턴스 생성
    myWindow = FiguristMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()
    #myWindow.activateWindow()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()