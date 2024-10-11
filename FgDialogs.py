from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QColorDialog, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar, QMessageBox, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QSizePolicy, \
                            QTableWidget, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QListWidgetItem,\
                            QTabWidget, QListWidget, QSpinBox, QPlainTextEdit, QSlider, QScrollArea, QShortcut, QMenu, \
                            QInputDialog, QTextEdit
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem, QImage,\
                        QFont, QPainter, QBrush, QMouseEvent, QWheelEvent, QDoubleValidator, QIcon, QCursor,\
                        QFontMetrics, QIntValidator, QKeySequence
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSize, QPoint, QTranslator,\
                         pyqtSlot, pyqtSignal, QItemSelectionModel, QTimer, QEvent, QSettings
import re
from FgModel import *
import numpy as np
import cv2
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QModelIndex, QRect, QPoint, QSettings, QByteArray

from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import math
from FgComponents import *
import fitz
import os
import sys
import ollama
from decouple import config
import tempfile

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from pyzotero import zotero
import FgUtils as fg

class ReferenceDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Figurist - Reference Information"))
        self.parent = parent
        self.ref = None
        #print(self.parent.pos())
        #self.setGeometry(QRect(100, 100, 600, 400))
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        self.collection = None
        #self.move(self.parent.pos()+QPoint(100,100))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close) 

        self.initUI()
        #self.prepare_database()

    def read_settings(self):
        settings = QSettings()
        if settings.contains("geometry") and self.remember_geometry:
            self.setGeometry(settings.value("geometry"))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))

    def initUI(self):
        ''' initialize UI '''
        self.lblCollection = QLabel(self.tr("Collection"))
        self.edtCollection = QLineEdit()
        # read only
        self.edtCollection.setReadOnly(True)
        self.lblTitle = QLabel(self.tr("Title"))
        self.edtTitle = QLineEdit()
        self.lblAuthor = QLabel(self.tr("Author"))
        self.edtAuthor = QLineEdit()
        self.lblJournal = QLabel(self.tr("Journal"))
        self.edtJournal = QLineEdit()
        self.lblYear = QLabel(self.tr("Year"))
        self.edtYear = QLineEdit()
        self.lblVolume = QLabel(self.tr("Volume"))
        self.edtVolume = QLineEdit()
        self.lblIssue = QLabel(self.tr("Issue"))
        self.edtIssue = QLineEdit()
        self.lblPages = QLabel(self.tr("Pages"))
        self.edtPages = QLineEdit()
        self.lblDOI = QLabel(self.tr("DOI"))
        self.edtDOI = QLineEdit()
        self.lblURL = QLabel(self.tr("URL"))
        self.edtURL = QLineEdit()
        self.lblZoteroKey = QLabel(self.tr("Zotero Key"))
        self.edtZoteroKey = QLineEdit()
        self.btnSave = QPushButton(self.tr("Save"))
        self.btnSave.clicked.connect(self.on_btn_save_clicked)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)

        self.btn_widget = QWidget()
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.btnSave)
        self.btn_layout.addWidget(self.btnCancel)
        self.btn_widget.setLayout(self.btn_layout)

        #self.statusBar = QStatusBar()
        #self.setStatusBar(self.statusBar)
        self.all_layout = QVBoxLayout()

        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.lblCollection, self.edtCollection)
        self.form_layout.addRow(self.lblTitle, self.edtTitle)
        self.form_layout.addRow(self.lblAuthor, self.edtAuthor)
        self.form_layout.addRow(self.lblJournal, self.edtJournal)
        self.form_layout.addRow(self.lblYear, self.edtYear)
        self.form_layout.addRow(self.lblVolume, self.edtVolume)
        self.form_layout.addRow(self.lblIssue, self.edtIssue)
        self.form_layout.addRow(self.lblPages, self.edtPages)
        self.form_layout.addRow(self.lblDOI, self.edtDOI)
        self.form_layout.addRow(self.lblURL, self.edtURL)
        self.form_layout.addRow(self.lblZoteroKey, self.edtZoteroKey)
        #self.form_layout.addRow(self.btnSave, self.btnCancel)
        self.form_widget.setLayout(self.form_layout)
        #self.layout.addRow(self.btnSave, self.btnCancel)
        self.all_layout.addWidget(self.form_widget)
        self.all_layout.addWidget(self.btn_widget)
        self.setLayout(self.all_layout)

    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.ref is None:
            self.ref = FgReference()
        #self.ref = FgReference()
        self.ref.title = self.edtTitle.text()
        self.ref.author = self.edtAuthor.text()
        self.ref.journal = self.edtJournal.text()
        self.ref.year = self.edtYear.text()
        self.ref.volume = self.edtVolume.text()
        self.ref.issue = self.edtIssue.text()
        self.ref.pages = self.edtPages.text()
        self.ref.doi = self.edtDOI.text()
        self.ref.url = self.edtURL.text()
        self.ref.zotero_key = self.edtZoteroKey.text()
        self.ref.save()

        if self.collection is None:
            pass
        else:
            colref = FgCollectionReference.select().where(FgCollectionReference.collection == self.collection, FgCollectionReference.reference == self.ref)
            if colref.count() == 0:
                colref = FgCollectionReference()
                colref.collection = self.collection
                colref.reference = self.ref
                colref.save()

        self.accept()

    def on_btn_cancel_clicked(self):
        #print("Cancel clicked")
        self.reject()

    def set_reference(self, ref):
        self.ref = ref
        self.edtTitle.setText(ref.title)
        self.edtAuthor.setText(ref.author)
        self.edtJournal.setText(ref.journal)
        self.edtYear.setText(ref.year)
        self.edtVolume.setText(ref.volume)
        self.edtIssue.setText(ref.issue)
        self.edtPages.setText(ref.pages)
        self.edtDOI.setText(ref.doi)
        self.edtURL.setText(ref.url)
        self.edtZoteroKey.setText(ref.zotero_key)

    def set_collection(self, collection):
        self.collection = collection
        self.edtCollection.setText(collection.name)
           
class BrowseZoteroCollectionDialog(QDialog):
    collection_selected = pyqtSignal(dict)

    def __init__(self, parent, collection_name=""):
        super().__init__(parent)
        self.parent = parent
        self.zotero_backend = None
        self.selected_collection = None
        self.collection_name = collection_name
        self.initUI()
        if self.collection_name != "":
            self.load_zotero_collections(self.collection_name)

    def initUI(self):
        self.setWindowTitle("Browse Zotero Collections")
        self.setGeometry(100, 100, 400, 500)

        self.layout = QVBoxLayout()

        self.search_widget = QWidget()
        self.search_layout = QHBoxLayout()
        self.search_widget.setLayout(self.search_layout)

        self.edt_search = QLineEdit()
        self.edt_search.setPlaceholderText("Enter search word")
        self.edt_search.setText(self.collection_name)
        #self.edt_search.textChanged.connect(self.on_search)
        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.on_search)
        self.search_layout.addWidget(self.edt_search)
        self.search_layout.addWidget(self.btn_search)
        self.layout.addWidget(self.search_widget)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Zotero Collections")
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.layout.addWidget(self.tree_widget)

        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.on_select)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        #self.load_zotero_collections()

    def on_search(self):
        keyword = self.edt_search.text()
        self.load_zotero_collections(keyword)

    def load_zotero_collections(self, keyword=""):
        library_id = self.parent.m_app.settings.value("zotero_user_id", "")
        library_type = "user"  # or "group" if it's a group library
        api_key = self.parent.m_app.settings.value("zotero_api_key", "")
        
        if not library_id or not api_key:
            QMessageBox.warning(self, "Zotero Settings Missing", "Please set your Zotero user ID and API key in the preferences.")
            return

        # application wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.zotero_backend = ZoteroBackend(library_id, library_type, api_key)
            
            self.tree_widget.clear()
            collections = self.zotero_backend.collections(q=keyword)
            for collection in collections:
                self.add_collection_to_tree(collection, self.tree_widget.invisibleRootItem())
        except Exception as e:
            QMessageBox.warning(self, "Zotero Connection Error", f"Failed to connect to Zotero: {str(e)}")
        # application normal cursor
        QApplication.restoreOverrideCursor()
        
    def add_collection_to_tree(self, collection, parent_item):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, collection['data']['name'])
        item.setData(0, Qt.UserRole, collection['key'])

        subcollections = self.zotero_backend.collections_sub(collection['key'])
        for subcollection in subcollections:
            self.add_collection_to_tree(subcollection, item)

    def on_item_clicked(self, item, column):
        self.selected_collection = self.zotero_backend.collection(item.data(0, Qt.UserRole))

    def on_select(self):
        if self.selected_collection:
            #self.collection_selected.emit(self.selected_collection)
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a Zotero collection.")

    def get_selected_collection(self):
        return self.selected_collection

class CollectionDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Figurist - Collection Information"))
        self.parent = parent
        self.collection = None
        self.parent_collection = None
        #print(self.parent.pos())
        #self.setGeometry(QRect(100, 100, 600, 400))
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.move(self.parent.pos()+QPoint(100,100))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close) 
        self.zotero_backend = None

        self.initUI()
        #self.prepare_database()

    def read_settings(self):
        self.m_app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, fg.COMPANY_NAME, fg.PROGRAM_NAME)
        self.remember_geometry = fg.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/CollectionDialog", QRect(100, 100, 500, 250)))
            is_maximized = fg.value_to_bool(self.m_app.settings.value("IsMaximized/CollectionDialog", False))
            if is_maximized:
                self.showMaximized()
            else:
                self.showNormal()
        else:
            self.setGeometry(QRect(100, 100, 500, 250))
        self.language = self.m_app.settings.value("language", "en")
        self.prev_language = self.language
        #self.update_language(self.language)
        self.zotero_api_key = self.m_app.settings.value("zotero_api_key", "")
        self.zotero_user_id = self.m_app.settings.value("zotero_user_id", "")

    def initUI(self):
        ''' initialize UI '''
        self.lblParent = QLabel(self.tr("Parent Collection"))
        self.edtParent = QLineEdit()
        # read only
        self.edtParent.setReadOnly(True)
        self.lblCollectionName = QLabel(self.tr("Collection name"))
        self.edtCollectionName = QLineEdit()
        self.lblDescription = QLabel(self.tr("Description"))
        self.edtDescription = QTextEdit()
        self.lblZoteroKey = QLabel(self.tr("Zotero Key"))
        self.edtZoteroKey = QLineEdit()
        self.btnBrowseZotero = QPushButton(self.tr("Zotero"))
        self.btnBrowseZotero.clicked.connect(self.on_btn_browse_zotero_clicked)
        self.btnSave = QPushButton(self.tr("Save"))
        self.btnSave.clicked.connect(self.on_btn_save_clicked)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)
        self.collection_name_widget = QWidget()
        self.collection_name_layout = QHBoxLayout()
        self.collection_name_widget.setLayout(self.collection_name_layout)
        self.collection_name_layout.addWidget(self.edtCollectionName)
        self.collection_name_layout.addWidget(self.btnBrowseZotero)

        self.btn_widget = QWidget()
        self.btn_layout = QHBoxLayout()
        #self.btn_layout.addWidget(self.btnBrowseZotero)
        self.btn_layout.addWidget(self.btnSave)
        self.btn_layout.addWidget(self.btnCancel)
        self.btn_widget.setLayout(self.btn_layout)

        #self.statusBar = QStatusBar()
        #self.setStatusBar(self.statusBar)
        self.all_layout = QVBoxLayout()

        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.lblParent, self.edtParent)
        self.form_layout.addRow(self.lblCollectionName, self.collection_name_widget)
        self.form_layout.addRow(self.lblDescription, self.edtDescription)
        self.form_layout.addRow(self.lblZoteroKey, self.edtZoteroKey)
        #self.form_layout.addRow(self.btnSave, self.btnCancel)
        self.form_widget.setLayout(self.form_layout)
        #self.layout.addRow(self.btnSave, self.btnCancel)
        self.all_layout.addWidget(self.form_widget)
        self.all_layout.addWidget(self.btn_widget)
        self.setLayout(self.all_layout)

    def on_btn_browse_zotero_clicked(self):
        #print("Browse Zotero clicked")
        collection_name = self.edtCollectionName.text() or ""
        #if collection_name 
        self.zotero_dialog = BrowseZoteroCollectionDialog(self, collection_name)
        ret = self.zotero_dialog.exec_()
        if ret == QDialog.Accepted:
            collection = self.zotero_dialog.get_selected_collection()
            if collection:
                self.edtZoteroKey.setText(collection['key'])
                self.edtCollectionName.setText(collection['data']['name'])


    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.collection is None:
            self.collection = FgCollection()
            self.collection.zotero_version = 0
        #self.ref = FgReference()
        self.collection.name = self.edtCollectionName.text()
        self.collection.description = self.edtDescription.toPlainText()
        self.collection.zotero_key = self.edtZoteroKey.text()
        self.collection.zotero_library_id = self.zotero_user_id
        if self.parent_collection:
            self.collection.parent = self.parent_collection
        self.collection.save()
        try:
            if self.collection.zotero_key != "":
                # application wait cursor
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.synchronize_zotero_collection(self.collection, since=self.collection.zotero_version)
                # application normal cursor
                QApplication.restoreOverrideCursor()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Zotero Synchronization Error", f"Failed to synchronize with Zotero: {str(e)}")

        self.accept()

    def synchronize_zotero_collection(self, collection, update_this=True, since=0):
        library_id = self.zotero_user_id
        library_type = "user"
        api_key = self.zotero_api_key
        if not library_id or not api_key:
            QMessageBox.warning(self, "Zotero Settings Missing", "Please set your Zotero user ID and API key in the preferences.")
            return
        
        if self.zotero_backend is None:
            self.zotero_backend = ZoteroBackend(library_id, library_type, api_key)

        # first get the collection
        if update_this:
            zcoll = self.zotero_backend.collection(collection.zotero_key, since=since)
            #print("zcoll:", zcoll)
            collection.name = zcoll['data']['name']
            collection.zotero_version = zcoll['data']['version']
            collection.zotero_library_id = library_id
            #print("collection:", collection, collection.name, collection.zotero_version, collection.zotero_library_id)
            collection.save()
            #collection_description = collection['data'].get('description', "")        #

        # get items in the collection
        item_list = self.zotero_backend.collection_items(collection.zotero_key, since=since)
        attachment_list = []
        for item in item_list:
            item_key = item['key']
            #print("ref:", item_key)
            #print("item:", item)
            if item['data']['itemType'] == "attachment":
                attachment_list.append(item)
                continue
            item_type = item['data']['itemType']
            item_title = item['data']['title']
            item_url = item['data']['url']
            #item_abstract = item['data'].get('abstractNote', "")
            #item_authors = item['data'].get('creators', [])
            #item_author_list = []
            #for author in item_authors:
            #    item_author_list.append(author['lastName'])
            #item_authors_str = ", ".join(item_author_list)
            item_journal = item['data'].get('publicationTitle', "")
            item_volume = item['data'].get('volume', "")
            item_issue = item['data'].get('issue', "")
            item_pages = item['data'].get('pages', "")
            item_doi = item['data'].get('DOI', "")
            item_version = item['data']['version']
            #item_year = item['data'].get('date', "")
            item_authors_str = item['meta']['creatorSummary']
            item_year = item['meta']['parsedDate']
            if len(item_year) > 4:
                item_year = item_year[:4]
            #'meta': {'creatorSummary': 'Palmer and Rowell', 'parsedDate': '1995', 'numChildren': 1}
            # try read first and then if not exist, create. not get_or_create
            ref = FgReference.get_or_create(zotero_key=item_key, zotero_library_id=library_id)[0]
            #ref = FgReference.select().where(FgReference.zotero_key == item_key, FgReference.zotero_library_id == library_id)
            #if ref.count() == 0:
            #    ref = FgReference()
            #else:
            #    ref = ref[0]
            ref.title = item_title
            ref.author = item_authors_str
            ref.journal = item_journal
            ref.volume = item_volume
            ref.issue = item_issue
            ref.pages = item_pages
            ref.doi = item_doi
            ref.year = item_year
            ref.url = item_url
            ref.zotero_key = item_key
            ref.zotero_library_id = library_id
            ref.zotero_version = item_version
            ref.zotero_data = item
            ref.save()
            # add reference to collection
            colref, created = FgCollectionReference.get_or_create(collection=collection, reference=ref)
            colref.save()
            # add reference to parent collection
            #if collection.parent:
            #    colref, created = FgCollectionReference.get_or_create(collection=collection.parent, reference=item_reference)
            #    colref.save()
        # get attachments
        for attachment in attachment_list:
            #print("attachment data:", attachment['data'])
            # get key
            attachment_key = attachment['key']
            #print("att:", attachment_key)

            # check file type
            attachment_filetype = attachment['data']['contentType']
            if attachment_filetype != "application/pdf":
                continue
            attachment_filename = attachment['data']['filename']

            # check if parent item exists. it should exist, but just in case, check and pass if not exist
            if 'parentItem' not in attachment['data']:
                continue
            attachment_parent = attachment['data']['parentItem']
            ref = FgReference.select().where(FgReference.zotero_key == attachment_parent, FgReference.zotero_library_id == library_id)
            if ref.count() == 0:
                continue

            #att = FgAttachment.get_or_create(zotero_key=attachment_key, zotero_library_id=library_id)[0]
            att = FgAttachment.select().where(FgAttachment.zotero_key == attachment_key, FgAttachment.zotero_library_id == library_id)
            if att.count() == 0:
                att = FgAttachment()
            else:
                att = att[0]

            att.reference = ref
            att.zotero_key = attachment_key
            att.zotero_library_id = library_id
            att.zotero_version = attachment['data']['version']
            att.filename = attachment_filename
            att.title = attachment_filename
            att.filetype = attachment_filetype
            att.zotero_data = attachment
            att.save()

            attachment_file = self.zotero_backend.file(attachment_key)
            att.save_file(attachment_file)
            # add attachment to parent collection
            #if collection.parent:
            #    colref, created = FgCollectionAttachment.get_or_create(collection=collection.parent, attachment=attachment_reference)
            #    colref.save()  


        sub_collection_list = self.zotero_backend.collections_sub(collection.zotero_key, since=since)
        for sub_collection in sub_collection_list:
            #print("sub_collection:", sub_collection)
            sub_collection_name = sub_collection['data']['name']
            sub_collection_key = sub_collection['key']
            sub_collection_version = sub_collection['data']['version']
            sub_collection_library_id = library_id
            coll, created = FgCollection.get_or_create(zotero_key=sub_collection_key, parent=collection, zotero_library_id=library_id)
            coll.zotero_version = sub_collection_version
            coll.zotero_library_id = sub_collection_library_id
            coll.name = sub_collection_name
            #print("sub_collection:", coll, coll.name, coll.zotero_version, coll.zotero_library_id)
            coll.save()
            self.synchronize_zotero_collection(coll, update_this=False,since=since)

    def on_btn_cancel_clicked(self):
        #print("Cancel clicked")
        self.reject()

    def set_collection(self, collection):
        self.collection = collection
        if self.collection.parent:
            self.parent_collection = self.collection.parent
            self.edtParent.setText(self.parent_collection.name)
        self.edtCollectionName.setText(collection.name)
        self.edtDescription.setText(collection.description)
        self.edtZoteroKey.setText(collection.zotero_key)

    def set_parent_collection(self, parent_collection):
        self.parent_collection = parent_collection
        self.edtParent.setText(parent_collection.name)

class ProgressDialog(QDialog):
    def __init__(self,parent):
        super().__init__()
        #self.setupUi(self)
        #self.setGeometry(200, 250, 400, 250)
        self.setWindowTitle("Figurist - Progress Dialog")
        self.parent = parent
        self.setGeometry(QRect(100, 100, 320, 180))
        self.move(self.parent.pos()+QPoint(100,100))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50,50, 50, 50)

        self.lbl_text = QLabel(self)
        #self.lbl_text.setGeometry(50, 50, 320, 80)
        #self.pb_progress = QProgressBar(self)
        self.pb_progress = QProgressBar(self)
        #self.pb_progress.setGeometry(50, 150, 320, 40)
        self.pb_progress.setValue(0)
        self.stop_progress = False
        self.btnStop = QPushButton(self)
        #self.btnStop.setGeometry(175, 200, 50, 30)
        self.btnStop.setText("Stop")
        self.btnStop.clicked.connect(self.set_stop_progress)
        self.layout.addWidget(self.lbl_text)
        self.layout.addWidget(self.pb_progress)
        self.layout.addWidget(self.btnStop)
        self.setLayout(self.layout)

    def set_stop_progress(self):
        self.stop_progress = True

    def set_progress_text(self,text_format):
        self.text_format = text_format

    def set_max_value(self,max_value):
        self.max_value = max_value

    def set_curr_value(self,curr_value):
        self.curr_value = curr_value
        self.pb_progress.setValue(int((self.curr_value/float(self.max_value))*100))
        self.lbl_text.setText(self.text_format.format(self.curr_value, self.max_value))
        #self.lbl_text.setText(label_text)
        self.update()
        QApplication.processEvents()


class PreferencesDialog(QDialog):
    """
    A dialog window for managing preferences in the PTMGenerator application.

    Attributes:
        parent (QWidget): The parent widget of the dialog.
        m_app (QApplication): The instance of the QApplication.
        current_translator (QTranslator): The current translator for language localization.
        settings (QSettings): The settings object for storing and retrieving preferences.
        language_label (QLabel): The label for the language selection.
        language_combobox (QComboBox): The combobox for selecting the language.

        btnOkay (QPushButton): The button for accepting the preferences and closing the dialog.
        layout (QFormLayout): The layout for arranging the preferences widgets.
    """

    def __init__(self, parent=None):
        """
        Initializes a new instance of the PreferencesWindow class.

        Args:
            parent (QWidget): The parent widget of the dialog.
        """
        super().__init__(parent)
        self.initialize_variables(parent)
        self.setup_ui()

    def initialize_variables(self, parent):
        """
        Initializes the variables required for the PreferencesWindow.

        Args:
            parent (QWidget): The parent widget of the dialog.
        """
        self.parent = parent
        self.m_app = QApplication.instance()
        self.current_translator = None
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, fg.COMPANY_NAME, fg.PROGRAM_NAME)

    def setup_ui(self):
        """
        Sets up the user interface of the PreferencesWindow.
        """
        self.setWindowTitle(self.tr("Preferences"))
        self.setWindowIcon(QIcon(fg.resource_path('icons/Figurist.png')))

        self.language_label = QLabel(self.tr("Language"))
        self.language_combobox = QComboBox()
        self.language_combobox.addItem("English", "en")
        self.language_combobox.addItem("한국어", "ko")
        self.language_combobox.setCurrentIndex(self.language_combobox.findData(self.settings.value("language", "en")))


        self.lblZoteroUserID = QLabel(self.tr("Zotero User ID"))
        self.edtZoteroUserID = QLineEdit()
        self.lblZoteroAPIKey = QLabel(self.tr("Zotero API Key"))
        self.edtZoteroAPIKey = QLineEdit()

        # openai api key 
        self.lblOpenAIKey = QLabel(self.tr("OpenAI Key"))
        self.edtOpenAIKey = QLineEdit()
        # Ollama IP address
        self.lblOllamaIP = QLabel(self.tr("Ollama IP"))
        self.edtOllamaIP = QLineEdit()
        # Ollama port
        self.lblOllamaPort = QLabel(self.tr("Ollama Port"))
        self.edtOllamaPort = QLineEdit()
        
        self.btnOkay = QPushButton(self.tr("OK"))
        self.btnOkay.clicked.connect(self.Okay)

        self.layout = QFormLayout()

        self.layout.addRow(self.language_label, self.language_combobox)
        self.layout.addRow(self.lblZoteroUserID, self.edtZoteroUserID)
        self.layout.addRow(self.lblZoteroAPIKey, self.edtZoteroAPIKey)
        self.layout.addRow(self.lblOpenAIKey, self.edtOpenAIKey)
        self.layout.addRow(self.lblOllamaIP, self.edtOllamaIP)
        self.layout.addRow(self.lblOllamaPort, self.edtOllamaPort)
        self.layout.addRow(self.btnOkay)
        self.setLayout(self.layout)

        self.read_settings()

        self.language_combobox.currentIndexChanged.connect(self.language_combobox_currentIndexChanged)

        self.language_combobox.setCurrentIndex(self.language_combobox.findData(self.language))

    def Okay(self):
        """
        Performs the necessary actions when the 'Okay' button is clicked.
        Saves the settings, accepts the changes, and closes the dialog.
        """
        #self.settings.setValue("ptm_fitter", self.edtPtmFitter.text())               
        #self.parent.update_language(self.language)
        self.save_settings()
        self.accept()

    def read_settings(self):
        """
        Reads the application settings from the QSettings object and applies them to the preferences window.

        This method retrieves various settings values such as window geometry, serial port, PTM fitter, number of LEDs,
        retry count, and language. It then updates the preferences window with the retrieved values.

        Returns:
            None
        """
        self.m_app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, fg.COMPANY_NAME, fg.PROGRAM_NAME)
        self.remember_geometry = fg.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/PreferencesWindow", QRect(100, 100, 500, 250)))
            is_maximized = fg.value_to_bool(self.m_app.settings.value("IsMaximized/PreferencesWindow", False))
            if is_maximized:
                self.showMaximized()
            else:
                self.showNormal()
        else:
            self.setGeometry(QRect(100, 100, 500, 250))
        self.language = self.m_app.settings.value("language", "en")
        self.prev_language = self.language
        self.update_language(self.language)
        self.zotero_api_key = self.m_app.settings.value("zotero_api_key", "")
        self.edtZoteroAPIKey.setText(self.zotero_api_key)
        self.zotero_user_id = self.m_app.settings.value("zotero_user_id", "")
        self.edtZoteroUserID.setText(self.zotero_user_id)
        self.openai_key = self.m_app.settings.value("openai_key", "")
        self.edtOpenAIKey.setText(self.openai_key)
        self.ollama_ip = self.m_app.settings.value("ollama_ip", "")
        self.edtOllamaIP.setText(self.ollama_ip)
        self.ollama_port = self.m_app.settings.value("ollama_port", "11434")
        self.edtOllamaPort.setText(self.ollama_port)        

    def save_settings(self):
        """
        Saves the current settings of the application.

        This method saves the window geometry, maximized state, language selection,
        zotero key to the application settings.

        Returns:
            None
        """
        self.m_app.settings.setValue("WindowGeometry/PreferencesWindow", self.geometry())
        self.m_app.settings.setValue("IsMaximized/PreferencesWindow", self.isMaximized())
        self.m_app.settings.setValue("language", self.language_combobox.currentData())
        self.m_app.settings.setValue("zotero_api_key", self.edtZoteroAPIKey.text())
        self.m_app.settings.setValue("zotero_user_id", self.edtZoteroUserID.text())
        self.m_app.settings.setValue("openai_key", self.edtOpenAIKey.text())
        self.m_app.settings.setValue("ollama_ip", self.edtOllamaIP.text())
        self.m_app.settings.setValue("ollama_port", self.edtOllamaPort.text())


    def language_combobox_currentIndexChanged(self, index):
        """
        This method is called when the index of the language_combobox is changed.
        It updates the selected language and calls the update_language method.

        Parameters:
        - index: The new index of the language_combobox.

        Returns:
        None
        """
        self.language = self.language_combobox.currentData()
        #self.settings.setValue("language", self.language_combobox.currentData())
        #print("language:", self.language)
        #self.accept()
        self.update_language(self.language)

    def update_language(self, language):
        """
        Update the language of the application.

        Args:
            language (str): The language to be set.

        Returns:
            None
        """
        if self.m_app.translator is not None:
            self.m_app.removeTranslator(self.m_app.translator)
            #print("removed translator")
            self.m_app.translator = None
        else:
            pass
            #print("no translator")
        #print("pref update language:", language)
        #print("update language:", language)
        translator = QTranslator()
        #translator.load('PTMGenerator2_{}.qm'.format(language))
        filename = "translations/PTMGenerator2_{}.qm".format(language)
        #print("filename:", filename)
        if os.path.exists(fg.resource_path(filename)):
            #print('path exists:', resource_path(filename))
            #print("loading translator", resource_path(filename))
            ret = translator.load(fg.resource_path(filename))
            #print("load result:", ret)
            ret = self.m_app.installTranslator(translator)
            self.m_app.translator = translator
            #print("install result:", ret)
        else:
            #print("not exist:", resource_path(filename))
            pass

        #print("language_label before:", self.language_label.text())
        lang_text = self.tr("Language")
        #print("lang_text:", lang_text)
        self.language_label.setText(lang_text)
        #print("language_label after:", self.language_label.text())
        self.lblZoteroAPIKey.setText(self.tr("Zotero Key"))
        self.btnOkay.setText(self.tr("OK"))
        self.update()

class TaxonDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Figurist - Taxon Information"))
        self.parent = parent
        self.taxon = None
        self.reference = None
        #print(self.parent.pos())
        #self.setGeometry(QRect(100, 100, 600, 400))
        self.remember_geometry = True
        self.m_app = QApplication.instance()
        self.read_settings()
        #self.move(self.parent.pos()+QPoint(100,100))
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close) 

        self.initUI()
        #self.prepare_database()

    def read_settings(self):
        settings = QSettings()
        if settings.contains("geometry") and self.remember_geometry:
            self.setGeometry(settings.value("geometry"))
        else:
            self.setGeometry(QRect(100, 100, 600, 400))

    def initUI(self):
        ''' initialize UI '''
        self.lblReference = QLabel(self.tr("Reference"))
        self.edtReference = QLineEdit()
        self.lblFigure = QLabel(self.tr("Figure(s)"))
        # figure list in listbox
        self.lstFigure = QListWidget()
        self.lblTaxonName = QLabel(self.tr("Taxon Name"))
        self.edtTaxonName = QLineEdit()
        self.lblTaxonRank = QLabel(self.tr("Taxon Rank"))
        self.edtTaxonRank = QLineEdit()
        self.lblParentTaxon = QLabel(self.tr("Parent Taxon"))
        self.edtParentTaxon = QLineEdit()
        self.btnSave = QPushButton(self.tr("Save"))
        self.btnSave.clicked.connect(self.on_btn_save_clicked)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)

        self.btn_widget = QWidget()
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.btnSave)
        self.btn_layout.addWidget(self.btnCancel)
        self.btn_widget.setLayout(self.btn_layout)

        #self.statusBar = QStatusBar()
        #self.setStatusBar(self.statusBar)
        self.all_layout = QVBoxLayout()

        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.lblReference, self.edtReference)
        self.form_layout.addRow(self.lblFigure, self.lstFigure)
        self.form_layout.addRow(self.lblTaxonName, self.edtTaxonName)
        self.form_layout.addRow(self.lblTaxonRank, self.edtTaxonRank)
        self.form_layout.addRow(self.lblParentTaxon, self.edtParentTaxon)
        #self.form_layout.addRow(self.btnSave, self.btnCancel)
        self.form_widget.setLayout(self.form_layout)
        #self.layout.addRow(self.btnSave, self.btnCancel)
        self.all_layout.addWidget(self.form_widget)
        self.all_layout.addWidget(self.btn_widget)
        self.setLayout(self.all_layout)

    def set_reference(self, ref):
        self.reference = ref
        self.edtReference.setText(ref.get_abbr())

    def set_figures(self, figure_list):
        #self.figure_list = figure_list
        self.figure_list = []
        for figure in figure_list:
            if self.reference:
                item_text = figure.figure_number
            else:
                item_text = figure.reference.get_abbr() + " - " + figure.figure_number
            #item_text = "{}: {}".format(figure.figure_number, figure.caption)
            item = QListWidgetItem(item_text)
            self.lstFigure.addItem(item)
            self.figure_list.append(figure)

    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.taxon is None:
            self.taxon = FgTaxon()
        #self.taxon = FgTaxon() 
        taxon_name = self.edtTaxonName.text()
        # find if taxon name already exists
        taxon = FgTaxon.select().where(FgTaxon.name == taxon_name)
        if taxon.count() > 0:
            self.taxon = taxon[0]
        else:
            self.taxon.name = self.edtTaxonName.text()
            name_list = self.taxon.name.split(" ")
            self.taxon.parent = None
            self.taxon.rank = self.edtTaxonRank.text()
            if len(name_list) > 1:
                ''' this is a species '''
                genus, created = FgTaxon.get_or_create(name=name_list[0])
                print("genus:",genus)
                genus.rank = "Genus"
                genus.save()
                self.taxon.parent = genus
                self.taxon.rank = "Species"
            self.taxon.save()

        #for fig in self.figure_list:
        #    fig.taxon = self.taxon
        #    fig.save()

        self.update_taxon_reference(self.taxon, self.reference)
        
        # find if taxon-figure relationship already exists
        for figure in self.figure_list:
            self.update_taxon_figure(self.taxon, figure)

        self.accept()
    
    def on_btn_cancel_clicked(self):
        #print("Cancel clicked")
        self.reject()

    def update_taxon_figure(self, taxon, figure):
        taxfig = FgTaxonFigure.select().where(FgTaxonFigure.figure == figure, FgTaxonFigure.taxon == taxon)
        if taxfig.count() == 0:
            taxfig = FgTaxonFigure()
            taxfig.taxon = taxon
            taxfig.figure = figure
            taxfig.save()

    def update_taxon_reference(self, taxon, reference):
        # find if taxon-reference relationship already exists
        taxref = FgTaxonReference.select().where(FgTaxonReference.taxon == taxon, FgTaxonReference.reference == reference)
        if taxref.count() == 0:
            taxref = FgTaxonReference()
            taxref.taxon = taxon
            taxref.reference = reference
            taxref.save()


class FigureDialog(QDialog):
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Figurist - Figure Information"))
        self.parent = parent
        self.initUI()
        self.figure = None
        self.figure_changed = False
        self.read_settings()

    def read_settings(self):
        settings = QSettings()
        if settings.contains("geometry") and self.remember_geometry:
            self.setGeometry(settings.value("geometry"))
        else:
            self.setGeometry(QRect(100, 100, 1024,768))
    
    def initUI(self):
        ''' initialize UI '''
        self.lblFigure = FigureLabel(self)
        #self.lblFigure.setFixedSize(600,400)
        #self.lblFile = QLabel(self.tr("File"))
        #self.edtFile = QLineEdit()

        self.lblFigureNumber = QLabel(self.tr("Figure Number"))

        self.edt_part1_prefix = QLineEdit()
        self.edt_part1_number = QLineEdit()
        self.edt_part_separator = QComboBox()
        self.edt_part2_prefix = QLineEdit()
        self.edt_part2_number = QLineEdit()
        self.edtFigureNumber = QLineEdit()
        self.edt_part_separator.addItem("Dash(-)", "-")
        self.edt_part_separator.addItem("Dot(.)", ".")
        self.edt_part_separator.addItem("Space", " ")
        self.edt_part_separator.addItem("None", "")

        self.figure_number_widget = QWidget()
        self.figure_number_layout = QHBoxLayout()
        self.figure_number_widget.setLayout(self.figure_number_layout)
        self.figure_number_layout.addWidget(self.edt_part1_prefix)
        self.figure_number_layout.addWidget(self.edt_part1_number)
        self.figure_number_layout.addWidget(self.edt_part_separator)
        self.figure_number_layout.addWidget(self.edt_part2_prefix)
        self.figure_number_layout.addWidget(self.edt_part2_number)
        self.figure_number_layout.addWidget(self.edtFigureNumber)
        
        self.lblCaption = QLabel(self.tr("Caption"))
        self.edtCaption = QTextEdit()
        self.lblComments = QLabel(self.tr("Comments"))
        self.edtComments = QTextEdit()
        self.btnSave = QPushButton(self.tr("Save"))
        self.btnSave.clicked.connect(self.on_btn_save_clicked)
        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)

        self.btn_widget = QWidget()
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.btnSave)
        self.btn_layout.addWidget(self.btnCancel)
        self.btn_widget.setLayout(self.btn_layout)

        #self.scrollArea = QScrollArea()
        #self.scrollArea.setWidget(self.lblFigure)
        #self.scrollArea.setWidgetResizable(True)

        #self.statusBar = QStatusBar()
        #self.setStatusBar(self.statusBar)
        self.all_layout = QVBoxLayout()

        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        #self.form_layout.addRow(self.lblFile, self.edtFile)
        self.form_layout.addRow(self.lblFigureNumber, self.figure_number_widget)
        self.form_layout.addRow(self.lblCaption, self.edtCaption)
        self.form_layout.addRow(self.lblComments, self.edtComments)
        self.form_widget.setLayout(self.form_layout)
 
        self.all_layout.addWidget(self.lblFigure,1)
        self.all_layout.addWidget(self.form_widget)
        self.all_layout.addWidget(self.btn_widget)
        self.setLayout(self.all_layout)

    def show_figure_label_menu(self, pos):
        menu = QMenu()
        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(self.on_paste)
        menu.exec_(self.lblFigure.mapToGlobal(QPoint(*pos)))

    def on_paste(self):
        print("Paste clicked")
        # paste clipboard image to label
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        #print("mime data:", mime_data)
        if mime_data.hasImage():
            image = mime_data.imageData()
            #print("image:", image)
            self.lblFigure.set_pixmap(QPixmap(image))
            self.lblFigure.setReadOnly(True)
            self.figure_changed = True

    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.figure is None:
            self.figure = FgFigure()
        #self.figure = FgFigure()
        if self.figure_changed:
            self.figure.add_pixmap(self.lblFigure.orig_pixmap)
        
        #self.figure.file_name = self.edtFile.text()
        #self.figure.figure_number = self.edtFigureNumber.text()
        self.figure.part1_number = self.edt_part1_number.text()
        self.figure.part1_prefix = self.edt_part1_prefix.text()
        self.figure.part_separator = self.edt_part_separator.currentData()
        self.figure.part2_number = self.edt_part2_number.text()
        self.figure.part2_prefix = self.edt_part2_prefix.text()
        self.figure.update_figure_number()
        self.figure.caption = self.edtCaption.toPlainText()
        self.figure.comments = self.edtComments.toPlainText()
        self.figure.modified_at = datetime.datetime.now()
        self.figure.save()
        self.accept()

    def on_btn_cancel_clicked(self):
        #print("Cancel clicked")
        self.reject()

    def load_figure(self, figure):

        self.figure = figure
        #self.figure_image = QPixmap(figure.get_file_path())
        #self.lblFigure.setPixmap(self.figure_image)

        self.lblFigure.set_figure(self.figure.get_file_path())
        self.lblFigure.setReadOnly(True)#read_only = True
        #self.lblFigure.set_edit_mode("VIEW_ONLY")

        # scale image to fit label
        #self.figure_image = self.figure_image.scaled(600,400,Qt.KeepAspectRatio)

        #self.edtFile.setText(figure.file_name)
        self.edtFigureNumber.setText(figure.figure_number)
        self.edt_part1_number.setText(figure.part1_number)
        self.edt_part1_prefix.setText(figure.part1_prefix)
        # set combobox to current value
        index = self.edt_part_separator.findData(figure.part_separator)
        self.edt_part_separator.setCurrentIndex(index)
        self.edt_part2_number.setText(figure.part2_number)
        self.edt_part2_prefix.setText(figure.part2_prefix)
        self.edtCaption.setText(figure.caption)
        self.edtComments.setText(figure.comments)


class DragDropModel(QStandardItemModel):
    rows_moved = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_source_row = None

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled




    def mimeTypes(self):
        return ['application/vnd.row.list']

    def mimeData(self, indexes):
        mimedata = QMimeData()
        encoded_data = self.encodeData(indexes)
        mimedata.setData('application/vnd.row.list', encoded_data)
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        success = self.decodeData(row, column, parent, data)
        if success:
            self.rows_moved.emit(self.drag_source_row, row)
        return success

    def encodeData(self, indexes):
        rows = sorted(set(index.row() for index in indexes))
        self.drag_source_row = rows[0]
        return ','.join(str(row) for row in rows).encode()

    def decodeData(self, row, column, parent, data):
        print("decodeData", row, column, parent, data)
        encoded_data = data.data('application/vnd.row.list')
        source_row = int(encoded_data.data().decode())
        
        if row == -1:
            row = self.rowCount(parent)

        print(f"Moving row from {source_row} to {row}")

        # Don't move if source and destination are the same
        if source_row == row:
            return False

        # Adjust destination row if moving down
        if row > source_row:
            row -= 1

        self.beginMoveRows(QModelIndex(), source_row, source_row, QModelIndex(), row)

        # Store the entire row data
        row_data = [self.item(source_row, c).clone() for c in range(self.columnCount())]

        # Remove the original row
        self.removeRow(source_row)

        # Insert the row at the new position
        self.insertRow(row)
        for c, item in enumerate(row_data):
            self.setItem(row, c, item)

        self.endMoveRows()

        return True

class DragDropModel(QStandardItemModel):
    rows_moved = pyqtSignal(int, int)  # Signal to notify about row moves

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        if row == -1:  
            row = self.rowCount(parent)  # Drop at the end if no row is specified
        
        # Check for illegal moves (e.g., onto itself)
        source_row = data.data("source_row")
        if not source_row or row == source_row.row():
            return False
        
        self.beginMoveRows(QModelIndex(), source_row.row(), source_row.row(), QModelIndex(), row)
        self.endMoveRows()
        self.rows_moved.emit(source_row.row(), row)  # Emit signal
        return True

    def mimeTypes(self):
        return ["application/x-qabstractitemmodeldatalist"]

    def mimeData(self, indexes):
        mimedata = QMimeData()
        mimedata.setData("source_row", indexes[0])  # Pass the source row index
        return mimedata

    def mimeData(self, indexes):
        mimedata = QMimeData()
        # Encode the row number into a byte array
        encoded_data = QByteArray(str(indexes[0].row()).encode())
        mimedata.setData("source_row", encoded_data)
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        if row == -1:  
            row = self.rowCount(parent)  # Drop at the end if no row is specified
        
        # Decode the row number
        encoded_data = data.data("source_row")
        source_row = int(encoded_data.data().decode())
        
        # Check for illegal moves (e.g., onto itself)
        if row == source_row:
            return False
        
        self.beginMoveRows(QModelIndex(), source_row, source_row, QModelIndex(), row)
        self.endMoveRows()
        self.rows_moved.emit(source_row, row)  # Emit signal
        return True
    
    def dropMimeData(self, data, action, row, column, parent):
        print("Drop mime data")
        encoded_data = data.data("source_row")
        source_row = int(encoded_data.data().decode())
        if row == -1:
            row = self.rowCount(parent)

        # Check for valid drop
        valid_drop = (row != source_row) and (0 <= row <= self.rowCount())
        print(f"Valid drop: {valid_drop}")

        if valid_drop:
            action = Qt.MoveAction  # Allow the move
        else:
            action = Qt.IgnoreAction  # Indicate invalid drop, this will show the stop cursor

        if action == Qt.MoveAction:
            self.beginMoveRows(QModelIndex(), source_row, source_row, QModelIndex(), row)
            self.endMoveRows()
            self.rows_moved.emit(source_row, row)

        return True  # Indicate the drop was handled, even if invalid
    
    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled
            
class AddFiguresDialog(QDialog):
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Figurist - Figure Information"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.initUI()
        self.reference = None
        self.processed_caption_list = []
        self.m_app = QApplication.instance()
        self.subfigure_list = []
        self.figure_list = []
        #self.
        self.read_settings()


    def update_language(self, language):
        pass

    def on_rows_moved(self, source_row, destination_row):
        print(f"Row moved from {source_row} to {destination_row}")

        # Update subfigure_list order
        moved_item = self.subfigure_list.pop(source_row)
        self.subfigure_list.insert(destination_row, moved_item)

    def initUI(self):
        ''' initialize UI '''
        self.zoom_factor = 1.0
        self.lblFigure = FigureLabel(self)
        # set gray image
        self.figure_image = QPixmap(200,300)
        self.figure_image.fill(Qt.gray)
        self.lblFigure.setPixmap(self.figure_image)
    

        self.tempFigureView = QTableView()
        #self.figureView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tempFigureView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tempFigureView.setSortingEnabled(True)
        #self.figureView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tempFigureView.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        #self.figureView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.tempFigureView.setAlternatingRowColors(True)
        self.tempFigureView.setShowGrid(True)
        self.tempFigureView.setGridStyle(Qt.SolidLine)
        self.tempFigureView.setWordWrap(True)
        self.tempFigureView.setCornerButtonEnabled(False)
        #self.figureView.setDragDropMode(QAbstractItemView.InternalMove)  # Enable drag and drop
        #self.figureView.setDragEnabled(True)
        #self.figureView.setDragEnabled(True)
        #self.figureView.setAcceptDrops(True)
        #self.figureView.setDropIndicatorShown(True)
        self.tempFigureView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #self.figureView.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.mainFigureView = QTableView()
        self.mainFigureView.setAlternatingRowColors(True)
        self.mainFigureView.setShowGrid(True)
        self.mainFigureView.setGridStyle(Qt.SolidLine)

        self.lblType = QLabel(self.tr("Type"))
        self.comboType = QComboBox()
        self.comboType.addItem("Figure")
        self.comboType.addItem("Plate")
        self.comboType.addItem("Text-Figure")
        self.comboType.addItem("Table")
        self.edtNumber1 = QLineEdit()
        self.comboSubType = QComboBox()
        self.comboSubType.addItem("--None--")
        self.comboSubType.addItem("Figure")
        self.comboSubNumbering = QComboBox()
        self.comboSubNumbering.addItem("1, 2, 3, ...")
        self.comboSubNumbering.addItem("A, B, C, ...")
        self.comboSubNumbering.addItem("a, b, c, ...")
        self.prefix_widget = QWidget()
        self.prefix_layout = QHBoxLayout()
        self.prefix_layout.addWidget(self.lblType)
        self.prefix_layout.addWidget(self.comboType)
        self.prefix_layout.addWidget(self.edtNumber1)
        self.prefix_layout.addWidget(self.comboSubType)
        self.prefix_layout.addWidget(self.comboSubNumbering)
        self.prefix_widget.setLayout(self.prefix_layout)

        self.up_button = QPushButton("Up")
        self.down_button = QPushButton("Down")
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.up_button.clicked.connect(self.move_up)
        self.down_button.clicked.connect(self.move_down)
        self.add_button.clicked.connect(self.on_add_subfigure)
        self.edit_button.clicked.connect(self.on_edit_subfigure)
        self.delete_button.clicked.connect(self.on_delete_subfigure)

        self.figure_button_widget = QWidget()
        self.figure_button_layout = QHBoxLayout()
        self.figure_button_layout.addWidget(self.up_button)
        self.figure_button_layout.addWidget(self.down_button)
        self.figure_button_layout.addWidget(self.add_button)
        self.figure_button_layout.addWidget(self.edit_button)
        self.figure_button_layout.addWidget(self.delete_button)
        self.figure_button_widget.setLayout(self.figure_button_layout)


        #self.model = QStandardItemModel()
        #self.figureView.setModel(self.model)
        #self.model = DragDropModel(self)
        #self.figureView.setModel(self.model)
        #self.model.rows_moved.connect(self.update_subfigure_list)     

        #self.model = DragDropModel(self)
        self.tempModel = QStandardItemModel()
        self.tempFigureView.setModel(self.tempModel)
        self.tempModel.dataChanged.connect(self.on_data_changed)
        self.tempFigureView.selectionModel().selectionChanged.connect(self.on_temp_figure_selection_changed)
        self.tempFigureView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tempFigureView.customContextMenuRequested.connect(self.on_custom_context_menu)

        self.mainModel = QStandardItemModel()
        self.mainFigureView.setModel(self.mainModel)
        self.mainFigureView.selectionModel().selectionChanged.connect(self.on_main_figure_selection_changed)

        self.raw_caption_edit = QTextEdit()
        self.process_caption_widget = QWidget()
        self.process_caption_layout = QHBoxLayout()
        self.process_caption_widget.setLayout(self.process_caption_layout)

        self.process_caption_target = QComboBox()
        self.process_caption_target.addItem("OpenAI")
        self.process_caption_target.addItem("Ollama")
        # selection changed event
        self.process_caption_target.currentIndexChanged.connect(self.on_process_caption_target_changed)
        self.process_caption_button = QPushButton(self.tr("Process Caption"))
        self.process_caption_button.clicked.connect(self.on_process_caption_button_clicked)

        self.process_caption_layout.addWidget(self.process_caption_target)
        self.process_caption_layout.addWidget(self.process_caption_button)

        self.raw_caption_widget = QWidget()
        self.raw_caption_layout = QVBoxLayout()
        self.raw_caption_widget.setLayout(self.raw_caption_layout)

        self.raw_caption_layout.addWidget(self.raw_caption_edit)
        self.raw_caption_layout.addWidget(self.process_caption_widget)

        self.prompt_edit = QTextEdit()
        # set prompt text. read from file prompt.txt in unicode
        prompt_file = "json_prompt.txt"
        if os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_text = f.read()
                self.prompt_edit.setText(prompt_text)
        else:
            self.prompt_edit.setText("")

        self.processed_caption_widget = QWidget()
        self.processed_caption_layout = QVBoxLayout()
        self.processed_caption_widget.setLayout(self.processed_caption_layout)

        self.processed_caption_edit = QTextEdit()
        self.update_caption_button = QPushButton(self.tr("Update Caption"))
        self.update_caption_button.setEnabled(False)
        self.update_caption_button.clicked.connect(self.on_update_caption_button_clicked)
        self.processed_caption_layout.addWidget(self.processed_caption_edit)
        self.processed_caption_layout.addWidget(self.update_caption_button)


        self.caption_tab_widget = QTabWidget()
        self.caption_tab_widget.addTab(self.prompt_edit, "Prompt")
        self.caption_tab_widget.addTab(self.raw_caption_widget, "Raw caption")
        self.caption_tab_widget.addTab(self.processed_caption_widget, "Processed caption")
        self.caption_tab_widget.setCurrentIndex(1)


        # set header 
        self.tempModel.setHorizontalHeaderLabels(["File Name", "Figure Number", "Caption", "Comments"])

        self.loadButton = QPushButton(self.tr("Load"))
        self.loadButton.clicked.connect(self.on_btn_load_clicked)
        self.detectButton = QPushButton(self.tr("Detect"))
        self.detectButton.clicked.connect(self.on_btn_detect_clicked)
        self.captureButton = QPushButton(self.tr("Capture text"))
        self.captureButton.clicked.connect(self.on_btn_capture_clicked)

        self.reference_control_widget = QWidget()
        self.reference_control_layout = QHBoxLayout()
        self.reference_control_widget.setLayout(self.reference_control_layout)
        self.reference_control_layout.addWidget(self.loadButton)
        self.reference_control_layout.addWidget(self.detectButton)
        self.reference_control_layout.addWidget(self.captureButton)


        #self.detectButton.setEnabled(False)
        self.saveButton = QPushButton(self.tr("Save"))
        self.saveButton.clicked.connect(self.on_btn_save_clicked)
        self.clearButton = QPushButton(self.tr("Clear"))
        self.clearButton.clicked.connect(self.on_btn_clear_clicked)
        self.cancelButton = QPushButton(self.tr("Cancel"))
        self.cancelButton.clicked.connect(self.on_btn_cancel_clicked)

        self.lblReference = QLabel(self.tr("Reference"))
        self.edtReference = QLineEdit()
        # read only edtReference
        self.edtReference.setReadOnly(True)

        self.top_widget = QWidget()
        self.top_layout = QHBoxLayout()
        self.top_widget.setLayout(self.top_layout)
        self.top_layout.addWidget(self.lblReference)
        self.top_layout.addWidget(self.edtReference)


        self.save_clear_button_widget = QWidget()
        self.save_clear_button_layout = QHBoxLayout()
        self.save_clear_button_widget.setLayout(self.save_clear_button_layout)
        self.save_clear_button_layout.addWidget(self.saveButton)
        self.save_clear_button_layout.addWidget(self.clearButton)

        self.temp_figure_list_widget = QWidget()
        self.temp_figure_list_layout = QVBoxLayout()
        self.temp_figure_list_widget.setLayout(self.temp_figure_list_layout)
        self.temp_figure_list_layout.addWidget(self.prefix_widget)
        self.temp_figure_list_layout.addWidget(self.tempFigureView)
        self.temp_figure_list_layout.addWidget(self.caption_tab_widget)
        self.temp_figure_list_layout.addWidget(self.save_clear_button_widget)

        #self.temp_figure_list_layout.addWidget(self.saveButton)

        self.main_figure_label = FigureLabel()
        self.main_figure_label.setReadOnly(True)
        self.main_figure_splitter = QSplitter(Qt.Vertical)
        self.main_figure_splitter.addWidget(self.mainFigureView)
        self.main_figure_splitter.addWidget(self.main_figure_label)
        self.main_figure_splitter.setStretchFactor(0,3)
        self.main_figure_splitter.setStretchFactor(1,1)


        #self.main_figure_list_widget = QWidget()
        #self.main_figure_list_layout = QVBoxLayout()
        #self.main_figure_list_widget.setLayout(self.main_figure_list_layout)
        #self.main_figure_list_layout.addWidget(self.mainFigureView)
        #self.main_figure_list_layout.addWidget(self.main_figure_label)

        #self.figure_list_layout.addWidget(self.process_caption_button)
        #self.figure_layout.addWidget(self.figure_button_widget)

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
        self.pdfcontrol_widget.hide()

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)
        self.left_layout.addWidget(self.reference_control_widget)
        self.left_layout.addWidget(self.pdfcontrol_widget)
        self.left_layout.addWidget(self.lblFigure,1)

        # use splitter instead of middle_widget
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.temp_figure_list_widget)
        self.splitter.addWidget(self.main_figure_splitter)
        self.splitter.setStretchFactor(0,1)
        self.splitter.setStretchFactor(1,2)
        self.splitter.setStretchFactor(2,1)
        self.splitter.setSizes([200,500,200]) 
        
        self.bottom_widget = QWidget()
        self.bottom_layout = QHBoxLayout()
        self.bottom_widget.setLayout(self.bottom_layout)
        #self.bottom_layout.addWidget(self.loadButton)
        #self.bottom_layout.addWidget(self.detectButton)
        #self.bottom_layout.addWidget(self.saveButton)
        self.bottom_layout.addWidget(self.cancelButton)

        self.statusBar = QLineEdit()
        self.statusBar.setReadOnly(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(self.splitter,1)
        #self.layout.addWidget(self.bottom_widget)
        self.layout.addWidget(self.statusBar)
        self.setLayout(self.layout)

    def read_settings(self):
        self.m_app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, fg.COMPANY_NAME, fg.PROGRAM_NAME)
        self.remember_geometry = fg.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.remember_geometry is True:
            self.setGeometry(self.m_app.settings.value("WindowGeometry/AddFiguresWindow", QRect(100, 100, 1200, 800)))
            is_maximized = fg.value_to_bool(self.m_app.settings.value("IsMaximized/AddFiguresWindow", False))
            if is_maximized:
                self.showMaximized()
            else:
                self.showNormal()
        else:
            self.setGeometry(QRect(100, 100, 1200,800))
        self.zotero_key = self.m_app.settings.value("zotero_key", "")
        self.language = self.m_app.settings.value("language", "en")
        self.prev_language = self.language
        self.update_language(self.language)
        self.openapi_key = self.m_app.settings.value("openai_key", "")
        self.ollama_ip = self.m_app.settings.value("ollama_ip", "")
        self.ollama_port = self.m_app.settings.value("ollama_port", "11434")
        self.process_caption_target.clear()
        if self.openapi_key != "":
            print("OpenAI key exists")
            self.process_caption_target.addItem("OpenAI")
        if self.ollama_ip != "":
            print("Ollama IP exists")
            self.process_caption_target.addItem("Ollama http://{}:{}".format(self.ollama_ip,self.ollama_port))
        self.last_used_llm = self.m_app.settings.value("last_used_llm", "")
        print("last used lllm from preferences:", self.last_used_llm)
        if self.last_used_llm != "":
            print("last used llm:", self.last_used_llm)
            for i in range(self.process_caption_target.count()):
                print("item text:", self.process_caption_target.itemText(i))
                if self.process_caption_target.itemText(i).find(self.last_used_llm) >= 0:
                    print("has item:", self.last_used_llm, "index:", i)
                    self.process_caption_target.setCurrentIndex(i)
                    break
        else:
            print("last used llm not found")

    def write_settings(self):
        """
        Saves the current settings of the application.

        This method saves the window geometry, maximized state, language selection,
        zotero key to the application settings.

        Returns:
            None
        """
        self.m_app.remember_geometry = fg.value_to_bool(self.m_app.settings.value("WindowGeometry/RememberGeometry", True))
        if self.m_app.remember_geometry is True:
            #print("maximized:", self.isMaximized(), "geometry:", self.geometry())
            if self.isMaximized():
                self.m_app.settings.setValue("IsMaximized/AddFiguresWindow", True)
            else:
                self.m_app.settings.setValue("IsMaximized/AddFiguresWindow", False)
                self.m_app.settings.setValue("WindowGeometry/AddFiguresWindow", self.geometry())
                #print("save maximized false")
        # store last_used_llm
        self.m_app.settings.setValue("last_used_llm", self.last_used_llm)

    def on_update_caption_button_clicked(self):
        #print("Update caption")
        if len(self.processed_caption_list) > 0 and len(self.processed_caption_list) == len(self.subfigure_list):
            for i, caption_text in enumerate(self.processed_caption_list):
                #sub_index, taxon_name, caption = self.processed_caption_list[i].split("\t")
                sub_index, taxon_name, caption = "", "", ""
                parts = self.processed_caption_list[i].split("\t")
                if len(parts) > 0:
                    sub_index = parts.pop(0)
                    if len(parts) > 0:
                        taxon_name = parts.pop(0)
                        if len(parts) > 0:
                            caption = "\t".join(parts)

                subfigure = self.subfigure_list[i]
                type = self.comboType.currentText()
                main_idx = self.edtNumber1.text()
                subtype = self.comboSubType.currentText()
                if subtype == "--None--":
                    subtype = ""
                subfigure.index = sub_index #type + main_idx + "-" + subtype + sub_index
                subfigure.taxon_name = taxon_name
                subfigure.caption = caption
            self.load_subfigure_list(self.subfigure_list)
            self.lblFigure.set_subfigure_list(self.subfigure_list)
                #self.figureView.model().item(i, 0).setText(sub_index)
                #self.figureView.model().item(i, 1).setText(taxon_name)
                #self.figureView.model().item(i, 2).setText(caption)

    def on_del_subfigure(self):
        #print("Delete subfigure")
        indexes = self.tempFigureView.selectionModel().selectedIndexes()
        index = indexes[0]
        row = index.row()
        self.subfigure_list.pop(row)
        self.tempModel.removeRow(row)
        self.lblFigure.set_subfigure_list(self.subfigure_list)

    def show_figure_label_menu(self, pos):
        menu = QMenu()
        del_action = menu.addAction("Delete")
        del_action.triggered.connect(self.on_del_subfigure)
        menu.exec_(self.lblFigure.mapToGlobal(QPoint(*pos)))

    def on_btn_capture_clicked(self):
        #print("Capture text")
        self.lblFigure.set_edit_mode("CAPTURE_TEXT")
        def on_text_capture(rect):
            dpi = 600
            scale_factor = 72 / dpi
            clip = fitz.Rect(
                rect.left() * scale_factor,
                rect.top() * scale_factor,
                rect.right() * scale_factor,
                rect.bottom() * scale_factor
            )
            #print("clip:", clip)
            text = self.current_page.get_text("text", clip=clip)
            #print("text:", text)
            # if shift is clicked:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                text = self.raw_caption_edit.toPlainText() + "\n" + text

            self.raw_caption_edit.setText(text)
            self.update()
            # wait cursor

            #self.caption_edit.setText(processed_text)
            #print("text:", text)
            return text
        #self.lblFigure.set_text_capture_callback(on_text_capture)

    def capture_text(self, rect):
        dpi = 600
        scale_factor = 72 / dpi
        clip = fitz.Rect(
            rect.left() * scale_factor,
            rect.top() * scale_factor,
            rect.right() * scale_factor,
            rect.bottom() * scale_factor
        )
        #print("clip:", clip)
        text = self.current_page.get_text("text", clip=clip)
        if text is None or text == '':
            
            QMessageBox().information(self, "No text", "No text found in the selected area")
        #print("text:", text)
        # if shift is clicked:
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            text = self.raw_caption_edit.toPlainText() + "\n" + text

        self.raw_caption_edit.setText(text)
        self.update()
        # wait cursor

        #self.caption_edit.setText(processed_text)
        #print("text:", text)
        return text
    
    def on_process_caption_target_changed(self, index):
        #print("Process caption target changed")
        self.last_used_llm = self.process_caption_target.currentText()
        print("selection changed. last used llm:", self.last_used_llm)

    def on_process_caption_button_clicked(self):
        caption = self.raw_caption_edit.toPlainText()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        prompt = self.prompt_edit.toPlainText()
        processed_text = self.process_caption(caption, prompt)
        # restore cursor
        print("processed text:", processed_text)
        if processed_text is None:
            processed_text = "Caption processing failed"
        else:
            processed_text = self.further_process_caption(processed_text)
        QApplication.restoreOverrideCursor()
        self.processed_caption_edit.setText(processed_text)
        self.caption_tab_widget.setCurrentIndex(2)

    def further_process_caption(self, processed_text):
        if processed_text.find("----BEGIN----") < 0:
            return processed_text
        if processed_text.find("----END----") < 0:
            return processed_text
        
        # get text between begin and end line
        processed_text = processed_text.split("----BEGIN----",1)[1]
        processed_text = processed_text.split("----END----",1)[0]
        # trim white spaces
        caption_dict = json.loads(processed_text)
        title = caption_dict['title']
        figure_caption_list = caption_dict['subfigure_list']
        # find figure or plate number
        #title = re.(r"(\w+)\t(\d+)", title)
        figure_type, figure_number = title.split(" ")
        #print("figure type:", figure_type)
        #print("figure number:", figure_number)
        # if comboType has figure type, set it
        if self.comboType.findText(figure_type) >= 0:
            self.comboType.setCurrentText(figure_type)
        else:
            self.comboType.setCurrentText("Figure")
        #self.comboType.setCurrentText(figure_type)
        self.edtNumber1.setText(figure_number)
        self.processed_caption_list = figure_caption_list
            #self.load_subfigure_list(self.processed_caption_list)
        self.check_update_caption_button()
        return processed_text

    def check_update_caption_button(self):
        if len(self.processed_caption_list) > 0 and len(self.processed_caption_list) == len(self.subfigure_list):
            self.update_caption_button.setEnabled(True)
        else:
            self.update_caption_button.setEnabled(False)

    def process_caption(self, caption, prompt):
        backend = self.process_caption_target.currentText().lower()
        if 'ollama' in backend:
            #print("ollama", self.ollama_ip, self.ollama_port)
            llm_chat = LLMChat(backend='ollama', server_ip=self.ollama_ip, server_port=self.ollama_port, model='llama3.1')
            self.last_used_llm = "Ollama"
        elif backend == 'openai':

            #print("openai", self.openapi_key)
            api_key = self.openapi_key
            llm_chat = LLMChat(backend='openai', model='gpt-3.5-turbo', api_key=api_key)
            self.last_used_llm = "OpenAI"
        processed_caption = llm_chat.process_caption(caption, prompt)
        return processed_caption

    def paste_to_table(self):
        current_index = self.tempFigureView.currentIndex()
        if not current_index.isValid():
            return
        text = QApplication.clipboard().text()
        #print("text:", text)
        rows = text.split("\n")
        #print("rows:", rows)
        for row, row_text in enumerate(rows):
            #print("row_text:", row_text)
            columns = row_text.split("\t")
            row_num = current_index.row() + row
            for col, text in enumerate(columns):
                col_num = current_index.column() + col
                index = self.tempFigureView.model().index(row_num, col_num)
                self.tempFigureView.model().setData(index, text, Qt.EditRole)
        self.update_subfigure_info_from_table()
        #self.lblFigure.update_subfigure_list(self.subfigure_list)

    def update_subfigure_info_from_table(self):
        col_heading = ["index","taxon_name","caption","comments"]
        for i in range(self.tempModel.rowCount()):
            for j in range(self.tempModel.columnCount()):
                item = self.tempModel.item(i,j)
                #print(f"{col_heading[j]}: {item.text()}")
                if hasattr(self.subfigure_list[i], col_heading[j]):
                    setattr(self.subfigure_list[i], col_heading[j], item.text())
        self.lblFigure.set_subfigure_list(self.subfigure_list)

    def on_data_changed(self, topLeft, bottomRight, roles):
        #print("data changed")
        if Qt.EditRole in roles:
            row = topLeft.row()
            column = topLeft.column()
            new_value = self.tempModel.data(topLeft)
            #print(f"Data changed at row {row}, column {column}: {new_value}")
            
            if 0 <= row < len(self.subfigure_list):
                subfigure = self.subfigure_list[row]
                if column == 0:  # Figure Number column
                    subfigure.index = new_value
                elif column == 1:  # Taxon name column
                    subfigure.taxon_name = new_value
                elif column == 2:  # Caption column
                    subfigure.caption = new_value
                elif column == 3:  # Comments column
                    subfigure.comments = new_value

            self.lblFigure.set_subfigure_list(self.subfigure_list)
            self.lblFigure.update()

    def fill_selected_cells(self):
        selection_model = self.tempFigureView.selectionModel()
        if not selection_model.hasSelection():
            return

        value, ok = QInputDialog.getText(self, "Fill Cells", "Enter value to fill:")
        if not ok:
            return

        for index in selection_model.selectedIndexes():
            self.tempModel.setData(index, value, Qt.EditRole)

    def move_up(self):
        #print("Move up")
        row = -1
        indexes = self.tempFigureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            if row > 0:
                #self.model.moveRow(QModelIndex(), row, QModelIndex(), row-1)
                self.subfigure_list[row], self.subfigure_list[row-1] = self.subfigure_list[row-1], self.subfigure_list[row]
        self.load_subfigure_list(self.subfigure_list)
        if row > 0:
            self.tempFigureView.selectRow(row-1)
        # select row-1 row

    def select_row(self, row):
        self.tempFigureView.selectRow(row)

    def clear_selection(self):
        self.tempFigureView.clearSelection()
    
    def move_down(self):
        #print("Move down")
        indexes = self.tempFigureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            if row < len(self.subfigure_list) - 1:
                #self.model.moveRow(QModelIndex(), row, QModelIndex(), row+1)
                self.subfigure_list[row], self.subfigure_list[row+1] = self.subfigure_list[row+1], self.subfigure_list[row]

        self.load_subfigure_list(self.subfigure_list)
        # select row+1 row
        self.tempFigureView.selectRow(row+1)

    def on_add_subfigure(self):
        print("Add subfigure")
    
    def on_edit_subfigure(self):
        print("Edit subfigure")
        indexes = self.tempFigureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            subfigure = self.subfigure_list[row]

    def on_data_changed_old(self, top_left, bottom_right, roles):
        if Qt.EditRole in roles:
            row = top_left.row()
            col = top_left.column()
            new_value = self.tempModel.data(top_left)
            #print(f"Data changed at row {row}, column {col}: {new_value}")
            # Update your subfigure_list or perform any other necessary actions here

    def load_subfigure_list(self, subfigure_list):
        self.tempModel.clear()
        self.tempModel.setHorizontalHeaderLabels(["Index", "Taxon name", "Caption", "Comments"])
        self.subfigure_list = subfigure_list
        for i, subfigure in enumerate(self.subfigure_list):
            #name = QStandardItem("")

            index = QStandardItem(str(subfigure.index))
            taxon_name = QStandardItem(subfigure.taxon_name)
            caption = QStandardItem(subfigure.caption)
            comments = QStandardItem(subfigure.comments)
            
            #name.setData(cropped_pixmap, Qt.DecorationRole)
            #name.setData(rect, Qt.UserRole)
            for item in [ taxon_name, caption, comments]:
                item.setEditable(True)

            self.tempModel.appendRow([index, taxon_name, caption, comments])
        self.check_update_caption_button()

    def on_custom_context_menu(self, pos):
        menu = QMenu()
        paste_action = menu.addAction("Paste data")
        paste_action.triggered.connect(self.paste_to_table)
        fill_action = menu.addAction("Fill Cells")
        fill_action.triggered.connect(self.fill_selected_cells)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.on_delete_subfigure)
        menu.exec_(self.tempFigureView.viewport().mapToGlobal(pos))

    def on_delete_subfigure(self):
        #print("Delete figure")
        # get selected index
        indexes = self.tempFigureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            #print("row:", row)
            # get segment result
            #self.subfigure_list = segmentation_results
            cropped_pixmap, rect = self.subfigure_list[row].pixmap, self.subfigure_list[row].rect
            # remove item from model
            self.tempModel.removeRow(row)
            # remove item from subfigure_list
            self.subfigure_list.pop(row)
            # update figure image
        self.lblFigure.set_subfigure_list(self.subfigure_list)
        self.update()

    def on_temp_figure_selection_changed(self, selected, deselected):
        #print("selection changed")
        # get selected index
        indexes = selected.indexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            self.lblFigure.set_current_subfigure(row)
            pixmap = self.subfigure_list[row].pixmap
            self.main_figure_label.set_pixmap(pixmap)
            return

    def on_main_figure_selection_changed(self, selected, deselected):
        #print("selection changed")
        # get selected index
        indexes = selected.indexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            self.main_figure_label.set_figure(self.figure_list[row].get_file_path())
            return

    def on_btn_load_clicked(self):
        #print("Load clicked")
        # load image or pdf file
        
        #file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.bmp *.gif)")
        #file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        # let user select image or pdf file
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image or PDF File", "", "Image or PDF Files (*.png *.jpg *.bmp *.gif *.pdf)")

        # if image file is selected        
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            self.pdfcontrol_widget.hide()        
            self.lblFigure.set_figure(file_name)
            self.original_figure_image = QPixmap(file_name)
            self.detectButton.setEnabled(True)
            self.tempModel.clear()
            self.subfigure_list = []
            self.lblFigure.set_subfigure_list(self.subfigure_list)
            self.update()
        elif file_name.lower().endswith('.pdf'):
            self.pdfcontrol_widget.show()
            self.pdf_document = fitz.open(file_name)
            #print("page count:", self.pdf_document.page_count)
            self.page_spinner.setRange(1, self.pdf_document.page_count)
            self.page_spinner.setValue(1)
            self.page_spinner.setSingleStep(1)
            self.page_spinner.setSuffix(" / " + str(self.pdf_document.page_count))
            #self.page_spinner.setWrapping(True)
            self.page_spinner.valueChanged.connect(self.on_page_changed)
            self.on_page_changed(1)
        else:
            return

    def load_pdf_file(self, file_name):
        self.pdfcontrol_widget.show()
        self.pdf_document = fitz.open(file_name)
        #print("page count:", self.pdf_document.page_count)
        self.page_spinner.setRange(1, self.pdf_document.page_count)
        self.page_spinner.setValue(1)
        self.page_spinner.setSingleStep(1)
        self.page_spinner.setSuffix(" / " + str(self.pdf_document.page_count))
        #self.page_spinner.setWrapping(True)
        self.page_spinner.valueChanged.connect(self.on_page_changed)
        self.on_page_changed(1)

    def on_page_changed(self, page_number):
        #print("Page changed:", page_number)
        self.page_number = page_number
        self.current_page = self.pdf_document[page_number-1]
        pix = self.current_page.get_pixmap(dpi=600, alpha=False, annots=True, matrix=fitz.Matrix(2, 2))
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)  # QImage
        self.original_figure_image = QPixmap.fromImage(img)  # QPixmap
        #print("pixmap size:", self.original_figure_image .size())
        self.lblFigure.set_pixmap(self.original_figure_image )
        self.lblFigure.set_page_number(page_number)
        self.detectButton.setEnabled(True)
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

    def set_figure_pixmap(self, pixmap):
        self.figure_pixmap = pixmap

    def on_btn_detect_clicked(self):
        # get segmentation result from image
        # call segment_figures_qt function
        #self.figure_page_pixmap = self.original_figure_image
        self.set_figure_pixmap(self.original_figure_image)
        segmentation_results, annotated_pixmap = self.segment_figures_qt(self.original_figure_image)
        #self.annotated_pixmap = annotated_pixmap
        #scaled_pixmap = annotated_pixmap.scaled(self.lblFigure.width(), self.lblFigure.height(), Qt.KeepAspectRatio)
        #self.lblFigure.setPixmap(scaled_pixmap)
        #self.model.clear()

        #self.model.setHorizontalHeaderLabels(["File Name", "Figure Number", "Caption", "Comments"])
        self.subfigure_list = []
        for i, (cropped_pixmap, rect) in enumerate(segmentation_results):
            subfigure = SubFigure(pixmap=cropped_pixmap, rect=rect, page_number=self.page_number)
            #subfigure.index = i+1
            self.subfigure_list.append(subfigure)
        #self.subfigure_list = segmentation_results
        self.lblFigure.set_subfigure_list(self.subfigure_list)

        self.load_subfigure_list(self.subfigure_list)


        self.tempFigureView.resizeColumnsToContents()
        self.tempFigureView.resizeRowsToContents()
        self.check_update_caption_button()

    def update_subfigure_list(self, source_row, destination_row):
        #print(f"Updating subfigure_list: Moving from {source_row} to {destination_row}")

        
        # Reorder the subfigure_list to match the new model order
        moved_item = self.subfigure_list.pop(source_row)
        if destination_row == -1 or destination_row >= len(self.subfigure_list):
            self.subfigure_list.append(moved_item)
        else:
            self.subfigure_list.insert(destination_row, moved_item)

        # reload the figureView from self.subfigure_list
        self.tempModel.clear()
        self.tempModel.setHorizontalHeaderLabels(["File Name", "Figure Number", "Caption", "Comments"])
        for i, (cropped_pixmap, rect) in enumerate(self.subfigure_list):
            name = QStandardItem(f"Figure{i+1}")
            figure_number = QStandardItem(f"Figure{i+1}")
            caption = QStandardItem("Caption")
            comments = QStandardItem("Comments")
            
            name.setData(cropped_pixmap, Qt.DecorationRole)
            name.setData(rect, Qt.UserRole)
            self.tempModel.appendRow([name, figure_number, caption, comments])
        print(f"New subfigure_list order: {[item[1] for item in self.subfigure_list]}")

    def on_btn_clear_clicked(self):
        self.tempModel.clear()
        self.subfigure_list = []
        self.lblFigure.set_subfigure_list(self.subfigure_list)
        # clear caption
        self.raw_caption_edit.clear()
        self.processed_caption_edit.clear()
        self.edtNumber1.clear()

    def on_btn_save_clicked(self):

        if len(self.subfigure_list) == 0:
            return
        number1 = self.edtNumber1.text()
        if number1 == "":
            QMessageBox().information(self, "Figure Number", "Please enter figure number")
            self.edtNumber1.setFocus()
            return


        # wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)

        type = self.comboType.currentText()
        sub_type = self.comboSubType.currentText()
        if sub_type == "--None--":
            sub_type = ""
        sub_numbering = self.comboSubNumbering.currentText()
        separator = "-"
        if sub_numbering == "1, 2, 3, ...":
            sub_number_list = [str(i+1) for i in range(len(self.subfigure_list))]
        elif sub_numbering == "A, B, C, ...":
            sub_number_list = [chr(i+65) for i in range(len(self.subfigure_list))]
        elif sub_numbering == "a, b, c, ...":
            sub_number_list = [chr(i+97) for i in range(len(self.subfigure_list))]
        else:
            sub_number_list = ["" for i in range(len(self.subfigure_list))]
        
        if len(self.subfigure_list) == 1:
            print("Single figure")
            separator = ""
            parent_figure = FgFigure()
            parent_figure.file_name = f"{type}{number1}.png"
            parent_figure.figure_number = f"{type}{number1}"
            #figure.caption = self.model.item(0, 3).text()
            #figure.comments = self.model.item(0, 4).text()
            parent_figure.part1_prefix = type
            parent_figure.part1_number = number1
            parent_figure.part2_prefix = ""
            parent_figure.part2_number = ""
            parent_figure.part_separator = ""
            parent_figure.update_figure_number()
            parent_figure.caption = self.raw_caption_edit.toPlainText()

            parent_figure.reference = self.reference
            parent_figure.file_path = ""
            parent_figure.save()
            parent_figure.add_pixmap(self.subfigure_list[0].pixmap)
        

        elif len(self.subfigure_list) > 1:

            parent_figure = FgFigure()
            parent_figure.file_name = f"{type}{number1}.png"
            parent_figure.figure_number = f"{type}{number1}"
            #figure.caption = self.model.item(0, 3).text()
            #figure.comments = self.model.item(0, 4).text()
            parent_figure.part1_prefix = type
            parent_figure.part1_number = number1
            parent_figure.part2_prefix = ""
            parent_figure.part2_number = ""
            parent_figure.part_separator = ""
            parent_figure.update_figure_number()
            parent_figure.caption = self.raw_caption_edit.toPlainText()

            parent_figure.reference = self.reference
            parent_figure.file_path = ""
            parent_figure.save()
            # print time
            #print("Time:", datetime.datetime.now())

            if len(self.subfigure_list) == 1:
                # just one subfigure == whole figure
                parent_figure.add_pixmap(self.subfigure_list[0].pixmap)
            
            else:
                # composite whole figure from subfigures
                rect_page = {}
                #parent_rect = QRect()
                for i, figure_info in enumerate(self.subfigure_list):
                    #print("Time:", i, datetime.datetime.now())
                    cropped_pixmap, rect = figure_info.pixmap, figure_info.rect
                    if figure_info.page_number not in rect_page:
                        rect_page[figure_info.page_number] = QRect()
                    rect_page[figure_info.page_number] = rect_page[figure_info.page_number].united(rect)
                    #parent_rect = parent_rect.united(rect)
                    figure = FgFigure()
                    figure.reference = self.reference
                    figure.parent = parent_figure
                    sub_number = sub_number_list[i]
                    figure.file_name = f"{type}{number1}{separator}{sub_type}{sub_number}.png"
                    #figure.figure_number = f"{type}{number1}{separator}{sub_type}{sub_number}"
                    figure.file_path = ""
                    #print("figure number:", figure.figure_number)
                    figure.part1_prefix = type
                    figure.part1_number = number1
                    figure.part2_prefix = sub_type
                    figure.part2_number = sub_number
                    figure.part_separator = separator
                    figure.update_figure_number()
                    #figure.caption = 
                    figure.taxon_name = self.tempModel.item(i, 1).text()
                    figure.caption = self.tempModel.item(i, 2).text()
                    figure.comments = self.tempModel.item(i, 3).text()
                    figure.save()
                    #print("Time figure saved:", i, datetime.datetime.now())
                    taxon_name = self.tempModel.item(i, 1).text()
                    taxon = self.process_taxon_name(taxon_name, taxon_rank = "Species", reference_abbr = self.reference.get_abbr())
                    figure.add_pixmap(cropped_pixmap)
                    if taxon is not None:
                        self.update_taxon_figure(taxon, figure)
                        self.update_taxon_reference(taxon, self.reference)
                    #print("Time processing done:", i, datetime.datetime.now())
                    #print(f"Name: {name.text()}, Figure Number: {figure_number.text()}, Caption: {caption.text()}, Comments: {comments.text()}")

                # process parent pixmap
                pixmap_list = []
                for page_number, rect in rect_page.items():
                    # get page pixmap from pdf
                    pix = self.pdf_document[page_number-1].get_pixmap(dpi=600, alpha=False, annots=True, matrix=fitz.Matrix(2, 2))
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)  # QImage
                    parent_pixmap = QPixmap.fromImage(img)  # QPixmap
                    parent_pixmap = parent_pixmap.copy(rect)
                    pixmap_list.append(parent_pixmap)
                
                # join pixmap
                pixmap_width = max([pixmap.width() for pixmap in pixmap_list])
                pixmap_height = sum([pixmap.height() for pixmap in pixmap_list])
                parent_pixmap = QPixmap(pixmap_width, pixmap_height)
                painter = QPainter(parent_pixmap)
                y = 0
                for pixmap in pixmap_list:
                    painter.drawPixmap(0, y, pixmap)
                    y += pixmap.height()
                painter.end()
                parent_figure.add_pixmap(parent_pixmap)

        # restore cursor
        QApplication.restoreOverrideCursor()
        self.load_main_figure_list()
        # set tab to raw caption
        self.caption_tab_widget.setCurrentIndex(1)
        # clear 
        self.on_btn_clear_clicked()
        #self.accept()
    
    def update_taxon_figure(self, taxon, figure):
        taxfig = FgTaxonFigure.select().where(FgTaxonFigure.figure == figure, FgTaxonFigure.taxon == taxon)
        if taxfig.count() == 0:
            taxfig = FgTaxonFigure()
            taxfig.taxon = taxon
            taxfig.figure = figure
            taxfig.save()

    def update_taxon_reference(self, taxon, reference):
        # find if taxon-reference relationship already exists
        taxref = FgTaxonReference.select().where(FgTaxonReference.taxon == taxon, FgTaxonReference.reference == reference)
        if taxref.count() == 0:
            taxref = FgTaxonReference()
            taxref.taxon = taxon
            taxref.reference = reference
            taxref.save()


    def process_taxon_name(self, taxon_name, taxon_rank = "Species", reference_abbr = ""):
        taxon = FgTaxon.select().where(FgTaxon.name == taxon_name)
        if taxon.count() > 0:
            taxon = taxon[0]
        else:
            taxon = FgTaxon()
            taxon.name = taxon_name
            name_list = taxon.name.split(" ")
            taxon.parent = None
            #taxon.rank = self.edtTaxonRank.text()
            if len(name_list) > 1:
                ''' this is a species '''
                genus, created = FgTaxon.get_or_create(name=name_list[0])
                #print("genus:",genus)
                genus.rank = "Genus"
                genus.save()
                taxon.parent = genus
                taxon.rank = "Species"
            else:
                taxon.rank = taxon_rank
            taxon.save()
        return taxon

    def on_btn_cancel_clicked(self):
        #print("Cancel clicked")
        self.reject()

    def detect_figures(self):
        print("Detecting figures")
        #self.figureView.setModel

    def set_reference(self, ref):
        self.reference = ref
        self.setWindowTitle(self.tr("Figurist - Figure Information for ") + ref.get_abbr())
        self.edtReference.setText(ref.get_abbr())
        self.load_main_figure_list()
        if self.reference.attachments.count() > 0:
            attachment_path = self.reference.attachments[0].get_file_path()
            self.load_pdf_file(attachment_path)

    def load_main_figure_list(self):

        self.figure_list = [ f for f in self.reference.figures ]
        self.mainModel.clear()
        self.mainModel.setHorizontalHeaderLabels(["Figure Number", "Taxon Name", "Caption"])
        for i, figure in enumerate(self.figure_list):
            figure_number = QStandardItem(figure.figure_number)
            taxon_name = QStandardItem(figure.get_taxon_name())
            caption = QStandardItem(figure.caption)
            self.mainModel.appendRow([figure_number, taxon_name, caption])




    def check_overlap(self, box1, box2):
        x1, y1, w1, h1 = box1[:4]
        x2, y2, w2, h2 = box2[:4]
        
        if (x1 <= x2 <= x1 + w1 or x2 <= x1 <= x2 + w2) and (y1 <= y2 <= y1 + h1 or y2 <= y1 <= y2 + h2):
            return True
        return False

    def segment_figures_qt(self, qpixmap):
        img = qpixmap.toImage()
        
        # Convert QImage to numpy array
        width = img.width()
        height = img.height()
        ptr = img.constBits()
        ptr.setsize(height * width * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        # Convert RGBA to RGB
        img = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
        
        original_img = img.copy()

        # Calculate a scaling factor based on image size
        scale_factor = max(1, min(width, height) / 4000)
        
        # Resize the image for processing
        proc_width = int(width / scale_factor)
        proc_height = int(height / scale_factor)
        proc_img = cv2.resize(img, (proc_width, proc_height))

        # Convert black background to white
        gray = cv2.cvtColor(proc_img, cv2.COLOR_RGB2GRAY)
        _, black_mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
        proc_img[black_mask == 0] = [255, 255, 255]

        # Function to process the image and return bounding boxes
        def process_image(img):
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # Apply morphological operations
            kernel = np.ones((5,5), np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)

            # Apply threshold
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Calculate minimum and maximum contour area based on image size
            total_area = img.shape[0] * img.shape[1]
            min_contour_area = total_area * 0.005  # Minimum figure size (1% of image)
            max_contour_area = total_area * 0.8   # Maximum figure size (50% of image)
            
            # Get bounding boxes for all contours
            bounding_boxes = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_contour_area < area < max_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    bounding_boxes.append((x, y, w, h))
            
            return bounding_boxes

        # Process the image
        bounding_boxes = process_image(proc_img)

        # Adaptive threshold adjustment
        if len(bounding_boxes) < 10 or len(bounding_boxes) > 50:
            # Binary search to find optimal threshold
            low, high = 0.001, 0.05  # 0.1% to 5% of image area
            while high - low > 0.0001:
                mid = (low + high) / 2
                min_contour_area = proc_width * proc_height * mid
                bounding_boxes = process_image(proc_img)
                if len(bounding_boxes) < 10:
                    high = mid
                elif len(bounding_boxes) > 50:
                    low = mid
                else:
                    break

        # Scale bounding boxes back to original size
        bounding_boxes = [(int(x*scale_factor), int(y*scale_factor), 
                        int(w*scale_factor), int(h*scale_factor)) 
                        for x, y, w, h in bounding_boxes]

        # Remove overlapping boxes, keeping the larger ones
        valid_boxes = []
        for box in bounding_boxes:
            is_valid = True
            for valid_box in valid_boxes:
                if self.check_overlap(box, valid_box):
                    if box[2] * box[3] > valid_box[2] * valid_box[3]:
                        valid_boxes.remove(valid_box)
                    else:
                        is_valid = False
                    break
            if is_valid:
                valid_boxes.append(box)

        # Calculate average height of boxes
        if valid_boxes:
            avg_height = sum(box[3] for box in valid_boxes) / len(valid_boxes)

            # Assign row numbers based on y-coordinate and average height
            for i, box in enumerate(valid_boxes):
                box_y = box[1]
                row = int(box_y / (avg_height * 1.2))  # 1.2 is a factor to allow some variation
                valid_boxes[i] = box + (row,)  # Add row number as the 5th element of the tuple

            # Sort boxes first by row, then by x-coordinate
            valid_boxes.sort(key=lambda box: (box[4], box[0]))

        annotated_pixmap = qpixmap.copy()
        painter = QPainter(annotated_pixmap)
        painter.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine))

        # Process valid boxes
        result = []
        for i, (x, y, w, h, _) in enumerate(valid_boxes, start=1):
            # Add some padding
            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(original_img.shape[1] - x, w + 2*padding)
            h = min(original_img.shape[0] - y, h + 2*padding)

            # Crop the figure
            figure = original_img[y:y+h, x:x+w]

            # Convert cv2 image to QPixmap
            height, width, channel = figure.shape
            bytes_per_line = 3 * width
            q_img = QImage(figure.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            cropped_pixmap = QPixmap.fromImage(q_img)

            # Add the cropped pixmap and its coordinates to the result
            result.append((cropped_pixmap, QRect(x, y, w, h)))
            painter.drawRect(x, y, w, h)

        painter.end()
        return result, annotated_pixmap

    def closeEvent(self, event):
        self.write_settings()
        event.accept()


class ImportCollectionDialog(QDialog):
    def __init__(self, parent=None):
        super(ImportCollectionDialog, self).__init__(parent)
        self.m_app = parent
        self.setWindowTitle(self.tr("Import Collection"))
        self.resize(400, 300)
        self.read_settings()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.edtCollection = QLineEdit()
        self.edtCollection.setPlaceholderText(self.tr("Enter collection name"))
        self.layout.addWidget(self.edtCollection)

        self.btnBrowse = QPushButton(self.tr("Browse"))
        self.btnBrowse.clicked.connect(self.on_btn_browse_clicked)
        self.layout.addWidget(self.btnBrowse)

        self.btnImport = QPushButton(self.tr("Import"))
        self.btnImport.clicked.connect(self.on_btn_import_clicked)
        self.layout.addWidget(self.btnImport)

        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)
        self.layout.addWidget(self.btnCancel)

    def read_settings(self):
        pass

    def on_btn_browse_clicked(self):
        directory = QFileDialog.getExistingDirectory(self, self.tr("Select Collection Directory"))
        if directory:
            self.edtCollection.setText(directory)

    def on_btn_import_clicked(self):
        collection_path = self.edtCollection.text()
        if not collection_path:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Please enter a collection name"))
            return

        if not os.path.exists(collection_path):
            QMessageBox.critical(self, self.tr("Error"), self.tr("The specified directory does not exist"))
            return

        collection = FgCollection()
        # wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        with gDatabase.atomic():
            collection.import_collection(collection_path)
        # restore cursor
        QApplication.restoreOverrideCursor()
        self.accept()
        
    def on_btn_cancel_clicked(self):
        self.reject()

class TOLNodeDialog(QDialog):
    def __init__(self, node, parent=None):
        super(TOLNodeDialog, self).__init__(parent)
        self.m_app = parent
        self.node = node
        self.setWindowTitle(self.tr("Edit TOL Node"))
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        self.form_layout = QFormLayout()
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.lblName = QLabel(self.tr("Name"))
        self.edtName = QLineEdit()
        self.edtName.setText(self.node.name)
        self.form_layout.addRow(self.lblName, self.edtName)

        self.lblRank = QLabel(self.tr("Rank"))
        self.edtRank = QLineEdit()
        self.edtRank.setText(self.node.rank)
        self.form_layout.addRow(self.lblRank, self.edtRank)

        self.lblAuthor = QLabel(self.tr("Author"))
        self.edtAuthor = QLineEdit()
        self.edtAuthor.setText(self.node.author)
        self.form_layout.addRow(self.lblAuthor, self.edtAuthor)

        self.lblComments = QLabel(self.tr("Comments"))
        self.edtComments = QLineEdit()
        self.edtComments.setText(self.node.comments)
        self.form_layout.addRow(self.lblComments, self.edtComments)

        self.lblSource = QLabel(self.tr("Source"))
        self.edtSource = QLineEdit()
        self.edtSource.setText(self.node.source)
        self.form_layout.addRow(self.lblSource, self.edtSource)

        self.lblCommonName = QLabel(self.tr("Common Name"))
        self.edtCommonName = QLineEdit()
        self.edtCommonName.setText(self.node.common_name)
        self.form_layout.addRow(self.lblCommonName, self.edtCommonName)

        self.lblRedirectTo = QLabel(self.tr("Redirect To"))
        self.edtRedirectTo = SearchableComboBox()
        self.edtRedirectTo.setEntry(self.node.redirect_to)
        self.form_layout.addRow(self.lblRedirectTo, self.edtRedirectTo)

        self.lblRedirectReason = QLabel(self.tr("Redirect Reason"))
        self.edtRedirectReason = QLineEdit()
        self.edtRedirectReason.setText(self.node.redirect_reason)
        self.form_layout.addRow(self.lblRedirectReason, self.edtRedirectReason)

        self.button_layout = QHBoxLayout()
        self.btnSave = QPushButton(self.tr("Save"))
        self.btnSave.clicked.connect(self.on_btn_save_clicked)
        self.button_layout.addWidget(self.btnSave)

        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)
        self.button_layout.addWidget(self.btnCancel)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addLayout(self.button_layout)

    def on_btn_save_clicked(self):
        self.node.name = self.edtName.text()
        self.node.rank = self.edtRank.text()
        self.node.author = self.edtAuthor.text()
        self.node.comments = self.edtComments.text()
        self.node.source = self.edtSource.text()
        self.node.common_name = self.edtCommonName.text()
        self.node.redirect_to = self.edtRedirectTo.getCurrentEntry()
        self.node.redirect_reason = self.edtRedirectReason.text()
        #print("redirect:", self.node.redirect_to)
        self.accept()

    def on_btn_cancel_clicked(self):
        self.reject()

class TOLDialog(QDialog):
    def __init__(self, parent=None):
        super(TOLDialog, self).__init__(parent)
        self.m_app = parent
        self.setWindowIcon(QIcon(fg.resource_path('icons/TOL.png')))
        self.setWindowTitle(self.tr("Tree of Life"))
        self.resize(800, 600)
        self.read_settings()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.treeTOL = QTreeView()
        self.treeTOL.setHeaderHidden(True)
        self.layout.addWidget(self.treeTOL)

        self.button_layout = QHBoxLayout()

        self.btnImport = QPushButton(self.tr("Import"))
        self.btnImport.clicked.connect(self.on_btn_import_clicked)
        self.button_layout.addWidget(self.btnImport)

        self.btnExport = QPushButton(self.tr("Export"))
        self.btnExport.clicked.connect(self.on_btn_export_clicked)
        self.button_layout.addWidget(self.btnExport)

        self.btnCancel = QPushButton(self.tr("Cancel"))
        self.btnCancel.clicked.connect(self.on_btn_cancel_clicked)
        self.button_layout.addWidget(self.btnCancel)
        self.layout.addLayout(self.button_layout)

        # double click tree item to edit entry
        self.treeTOL.setEditTriggers(QTreeView.NoEditTriggers)
        self.treeTOL.doubleClicked.connect(self.on_tree_double_clicked)

        # load tree
        self.load_tree()
    
    def on_tree_double_clicked(self, index):
        item = self.treeTOL.model().itemFromIndex(index)
        node = item.data()
        if not node:
            return

        dialog = TOLNodeDialog(node, self)
        if dialog.exec_():
            # update node
            node.save()
            # update tree
            self.load_tree()

    def load_tree(self):
        # load FgTreeOfLife into treeview
        # create a model
        model = QStandardItemModel()
        self.treeTOL.setModel(model)
        # get all root nodes
        # wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        root_nodes = FgTreeOfLife.select().where(FgTreeOfLife.parent == None).order_by(FgTreeOfLife.rank, FgTreeOfLife.name)
        for root_node in root_nodes:
            name = root_node.name
            if root_node.rank and root_node.rank != "Species":
                name = f"{root_node.rank} {name}"

            root_item = QStandardItem(name)
            root_item.setData(root_node)
            model.appendRow(root_item)
            self.load_children(root_node, root_item)
        # end wait cursor
        QApplication.restoreOverrideCursor()

    def load_children(self, parent_node, parent_item):
        children = FgTreeOfLife.select().where(FgTreeOfLife.parent == parent_node).order_by(FgTreeOfLife.rank, FgTreeOfLife.name)
        for child in children:
            name = child.name
            if child.rank and child.rank != "Species":
                name = f"{child.rank} {name}"
            child_item = QStandardItem(name)
            child_item.setData(child)
            parent_item.appendRow(child_item)
            self.load_children(child, child_item)

    def write_settings(self):
        pass
    
    def read_settings(self):
        pass

    def on_btn_import_clicked(self):
        # get filename
        open_file_name = QFileDialog.getOpenFileName(self, self.tr("Open TOL data file"), "", "JSON Files (*.json)")
        if not open_file_name or open_file_name[0] == "":
            return
        
        # read json file
        with open(open_file_name[0], 'r', encoding='utf-8') as f:
            tree = json.load(f)

        # wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        with gDatabase.atomic():
            self.import_tree(tree)
        # restore cursor
        QApplication.restoreOverrideCursor()
        self.load_tree()

    def import_tree(self, tree, parent=None):
        for item in tree:
            node = FgTreeOfLife()
            node.name = item["name"]
            node.rank = item["rank"]
            node.author = item["author"]
            node.comments = item["comments"]
            node.source = item["source"]
            node.common_name = item["common_name"]
            node.redirect_reason = item["redirect_reason"]
            node.save()
            if parent:
                node.parent = parent
                node.save()
            self.import_tree(item["children"], node)

    def on_btn_export_clicked(self):

        # export tree of life
        open_file_name = QFileDialog.getSaveFileName(self, self.tr("Save TOL data file"), "", "JSON Files (*.json)")
        if not open_file_name or open_file_name[0] == "":
            return


        def read_tree(node):
            item = {
                "name": node.name,
                "rank": node.rank if node.rank else "",
                "author": node.author if node.author else "",
                "comments": node.comments if node.comments else "",
                "redirect_to": node.redirect_to.name if node.redirect_to else "",
                "redirect_reason": node.redirect_reason if node.redirect_reason else "",
                "common_name": node.common_name if node.common_name else "",
                "source": node.source if node.source else "",
                "children": [],
            }
            children = FgTreeOfLife.select().where(FgTreeOfLife.parent == node)
            for child in children:
                child_item = read_tree(child)
                item["children"].append(child_item)
            return item
        
        tree = []
        root_nodes = FgTreeOfLife.select().where(FgTreeOfLife.parent == None)
        for root_node in root_nodes:
            root_item = read_tree(root_node)
            tree.append(root_item)

        # open utf-8 file
        with open(open_file_name[0], 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=4, ensure_ascii=False)

    def on_btn_export_clicked_(self):
        # export tree of life
        open_file_name = QFileDialog.getSaveFileName(self, self.tr("Save TOL data file"), "", "TEXT Files (*.txt)")
        if open_file_name:
            # open utf-8 file
            with open(open_file_name[0], 'w', encoding='utf-8') as f:
                for i in range(self.treeTOL.model().rowCount()):
                    root_item = self.treeTOL.model().item(i)
                    self.export_node(f, root_item)

    def export_node(self, f, item, depth=0):
        #print( " " * 2 * depth + item.text())
        node = item.data()
        f.write(" " * 2 * depth + f"{node.rank} {node.name} {node.author or ""}\n")
        for i in range(item.rowCount()):
            child_item = item.child(i)
            self.export_node(f, child_item, depth+1)

    def on_btn_cancel_clicked(self):
        self.reject()
