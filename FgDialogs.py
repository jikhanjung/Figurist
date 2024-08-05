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

from FgModel import *
import numpy as np
import cv2
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QModelIndex, QRect, QPoint, QSettings, QByteArray

from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import math
from FgComponents import FigureLabel
import fitz
import os
import sys

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

        colref = FgCollectionReference.select().where(FgCollectionReference.collection == self.collection, FgCollectionReference.reference == self.ref)
        if colref.count() == 0:
            colref = FgCollectionReference()
            colref.collection = self.collection
            colref.reference = self.ref
            colref.save()

        self.accept()

    def on_btn_cancel_clicked(self):
        print("Cancel clicked")
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

        self.initUI()
        #self.prepare_database()

    def read_settings(self):
        settings = QSettings()
        if settings.contains("geometry") and self.remember_geometry:
            self.setGeometry(settings.value("geometry"))
        else:
            self.setGeometry(QRect(100, 100, 400, 300))

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
        self.form_layout.addRow(self.lblParent, self.edtParent)
        self.form_layout.addRow(self.lblCollectionName, self.edtCollectionName)
        self.form_layout.addRow(self.lblDescription, self.edtDescription)
        self.form_layout.addRow(self.lblZoteroKey, self.edtZoteroKey)
        #self.form_layout.addRow(self.btnSave, self.btnCancel)
        self.form_widget.setLayout(self.form_layout)
        #self.layout.addRow(self.btnSave, self.btnCancel)
        self.all_layout.addWidget(self.form_widget)
        self.all_layout.addWidget(self.btn_widget)
        self.setLayout(self.all_layout)

    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.collection is None:
            self.collection = FgCollection()
        #self.ref = FgReference()
        self.collection.name = self.edtCollectionName.text()
        self.collection.description = self.edtDescription.toPlainText()
        self.collection.zotero_key = self.edtZoteroKey.text()
        if self.parent_collection:
            self.collection.parent = self.parent_collection
        self.collection.save()
        self.accept()

    def on_btn_cancel_clicked(self):
        print("Cancel clicked")
        self.reject()

    def set_collection(self, collection):
        self.collection = collection
        if self.collection.parent:
            self.parent_collection = self.collection.parent
            self.edtParent.setText(self.parent_collection.name)
        self.edtCollectionName.setText(collection.name)
        self.edtDescription.setText(collection.description)
        #self.edtZoteroKey.setText(collection.zotero_key)

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
        lblSerialPort (QLabel): The label for the serial port selection.
        comboSerialPort (QComboBox): The combobox for selecting the serial port.
        lblPtmFitter (QLabel): The label for the PTM fitter selection.
        edtPtmFitter (QLineEdit): The line edit for entering the PTM fitter path.
        btnPtmFitter (QPushButton): The button for browsing the PTM fitter executable.
        ptmfitter_widget (QWidget): The widget for containing the PTM fitter line edit and button.
        ptmfitter_layout (QHBoxLayout): The layout for the PTM fitter widget.
        lblNumberOfLEDs (QLabel): The label for the number of LEDs setting.
        edtNumberOfLEDs (QLineEdit): The line edit for entering the number of LEDs.
        lblRetryCount (QLabel): The label for the retry count setting.
        edtRetryCount (QLineEdit): The line edit for entering the retry count.
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


        self.lblZoteroKey = QLabel(self.tr("Zotero Key"))
        self.edtZoteroKey = QLineEdit()

        self.btnOkay = QPushButton(self.tr("OK"))
        self.btnOkay.clicked.connect(self.Okay)

        self.layout = QFormLayout()

        self.layout.addRow(self.language_label, self.language_combobox)
        self.layout.addRow(self.lblZoteroKey, self.edtZoteroKey)
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
        self.zotero_key = self.m_app.settings.value("zotero_key", "")
        self.language = self.m_app.settings.value("language", "en")
        self.prev_language = self.language
        self.update_language(self.language)

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
        self.m_app.settings.setValue("zotero_key", self.zotero_key)

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
        self.lblZoteroKey.setText(self.tr("Zotero Key"))
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
        print("Cancel clicked")
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
        self.read_settings()

    def read_settings(self):
        settings = QSettings()
        if settings.contains("geometry") and self.remember_geometry:
            self.setGeometry(settings.value("geometry"))
        else:
            self.setGeometry(QRect(100, 100, 1024,768))
    
    def initUI(self):
        ''' initialize UI '''
        self.lblFigure = FigureLabel()
        #self.lblFigure.setFixedSize(600,400)
        self.lblFile = QLabel(self.tr("File"))
        self.edtFile = QLineEdit()
        self.lblFigureNumber = QLabel(self.tr("Figure Number"))
        self.edtFigureNumber = QLineEdit()
        self.lblCaption = QLabel(self.tr("Caption"))
        self.edtCaption = QLineEdit()
        self.lblComments = QLabel(self.tr("Comments"))
        self.edtComments = QLineEdit()
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
        self.form_layout.addRow(self.lblFile, self.edtFile)
        self.form_layout.addRow(self.lblFigureNumber, self.edtFigureNumber)
        self.form_layout.addRow(self.lblCaption, self.edtCaption)
        self.form_layout.addRow(self.lblComments, self.edtComments)
        self.form_widget.setLayout(self.form_layout)
 
        self.all_layout.addWidget(self.lblFigure,1)
        self.all_layout.addWidget(self.form_widget)
        self.all_layout.addWidget(self.btn_widget)
        self.setLayout(self.all_layout)

    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.figure is None:
            self.figure = FgFigure()
        #self.figure = FgFigure()
        self.figure.file_name = self.edtFile.text()
        self.figure.figure_number = self.edtFigureNumber.text()
        self.figure.caption = self.edtCaption.text()
        self.figure.comments = self.edtComments.text()
        self.figure.save()
        self.accept()

    def on_btn_cancel_clicked(self):
        print("Cancel clicked")
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

        self.edtFile.setText(figure.file_name)
        self.edtFigureNumber.setText(figure.figure_number)
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
            
class AddFigureDialog(QDialog):
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle(self.tr("Figurist - Figure Information"))
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.initUI()
        self.reference = None
        #self.
        self.read_settings()

    def read_settings(self):
        settings = QSettings()
        if settings.contains("geometry") and self.remember_geometry:
            self.setGeometry(settings.value("geometry"))
        else:
            self.setGeometry(QRect(100, 100, 1024,768))
    
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
    

        self.figureView = QTableView()
        #self.figureView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.figureView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.figureView.setSortingEnabled(True)
        #self.figureView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.figureView.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.figureView.setAlternatingRowColors(True)
        self.figureView.setShowGrid(True)
        self.figureView.setGridStyle(Qt.SolidLine)
        self.figureView.setWordWrap(True)
        self.figureView.setCornerButtonEnabled(False)
        #self.figureView.setDragDropMode(QAbstractItemView.InternalMove)  # Enable drag and drop
        #self.figureView.setDragEnabled(True)
        #self.figureView.setDragEnabled(True)
        #self.figureView.setAcceptDrops(True)
        #self.figureView.setDropIndicatorShown(True)
        self.figureView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #self.figureView.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

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
        self.model = QStandardItemModel()
        self.figureView.setModel(self.model)
        #self.model.rows_moved.connect(self.on_rows_moved)  # New signal connection
        #self.model.rowsMoved.connect(self.on_rows_moved)  # New signal connection
        self.model.dataChanged.connect(self.on_data_changed)

        # selection changed
        self.figureView.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # figureView custom menu
        self.figureView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.figureView.customContextMenuRequested.connect(self.on_custom_context_menu)

        # set header 
        self.model.setHorizontalHeaderLabels(["File Name", "Figure Number", "Caption", "Comments"])


        self.loadButton = QPushButton(self.tr("Load figure"))
        self.loadButton.clicked.connect(self.on_btn_load_clicked)
        self.detectButton = QPushButton(self.tr("Detect Figures"))
        self.detectButton.clicked.connect(self.on_btn_detect_clicked)
        #self.detectButton.setEnabled(False)
        self.saveButton = QPushButton(self.tr("Save"))
        self.saveButton.clicked.connect(self.on_btn_save_clicked)
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

        self.figure_widget = QWidget()
        self.figure_layout = QVBoxLayout()
        self.figure_widget.setLayout(self.figure_layout)
        self.figure_layout.addWidget(self.prefix_widget)
        self.figure_layout.addWidget(self.figureView)
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
        self.left_layout.addWidget(self.pdfcontrol_widget)
        self.left_layout.addWidget(self.lblFigure,1)


        '''
        self.middle_widget = QWidget()
        self.middle_layout = QHBoxLayout()
        self.middle_widget.setLayout(self.middle_layout)
        self.middle_layout.addWidget(self.left_widget,1)
        self.middle_layout.addWidget(self.figure_widget,2)
        '''
        # use splitter instead of middle_widget
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.figure_widget)
        self.splitter.setStretchFactor(0,1)
        self.splitter.setStretchFactor(1,2)
        self.splitter.setSizes([200,500]) 
        
        self.bottom_widget = QWidget()
        self.bottom_layout = QHBoxLayout()
        self.bottom_widget.setLayout(self.bottom_layout)
        self.bottom_layout.addWidget(self.loadButton)
        self.bottom_layout.addWidget(self.detectButton)
        self.bottom_layout.addWidget(self.saveButton)
        self.bottom_layout.addWidget(self.cancelButton)

        self.statusBar = QLineEdit()
        self.statusBar.setReadOnly(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(self.splitter,1)
        self.layout.addWidget(self.bottom_widget)
        self.layout.addWidget(self.statusBar)
        self.setLayout(self.layout)

    def fill_selected_cells(self):
        selection_model = self.figureView.selectionModel()
        if not selection_model.hasSelection():
            return

        value, ok = QInputDialog.getText(self, "Fill Cells", "Enter value to fill:")
        if not ok:
            return

        for index in selection_model.selectedIndexes():
            self.model.setData(index, value, Qt.EditRole)

    def move_up(self):
        #print("Move up")
        row = -1
        indexes = self.figureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            if row > 0:
                #self.model.moveRow(QModelIndex(), row, QModelIndex(), row-1)
                self.subfigure_list[row], self.subfigure_list[row-1] = self.subfigure_list[row-1], self.subfigure_list[row]
        self.load_subfigure_list(self.subfigure_list)
        if row > 0:
            self.figureView.selectRow(row-1)
        # select row-1 row

    def select_row(self, row):
        self.figureView.selectRow(row)

    def clear_selection(self):
        self.figureView.clearSelection()
    
    def move_down(self):
        #print("Move down")
        indexes = self.figureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            if row < len(self.subfigure_list) - 1:
                #self.model.moveRow(QModelIndex(), row, QModelIndex(), row+1)
                self.subfigure_list[row], self.subfigure_list[row+1] = self.subfigure_list[row+1], self.subfigure_list[row]

        self.load_subfigure_list(self.subfigure_list)
        # select row+1 row
        self.figureView.selectRow(row+1)

    def on_add_subfigure(self):
        print("Add subfigure")
    
    def on_edit_subfigure(self):
        print("Edit subfigure")
        indexes = self.figureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            subfigure = self.subfigure_list[row]

    def on_data_changed(self, top_left, bottom_right, roles):
        if Qt.EditRole in roles:
            row = top_left.row()
            col = top_left.column()
            new_value = self.model.data(top_left)
            print(f"Data changed at row {row}, column {col}: {new_value}")
            # Update your subfigure_list or perform any other necessary actions here

    def load_subfigure_list(self, figure_list):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["File Name", "Index", "Taxon name", "Caption", "Comments"])
        self.subfigure_list = figure_list
        for i, (cropped_pixmap, rect) in enumerate(self.subfigure_list):
            name = QStandardItem("")
            figure_number = QStandardItem(f"{i+1}")
            taxon_name = QStandardItem("")
            caption = QStandardItem("")
            comments = QStandardItem("")
            
            #name.setData(cropped_pixmap, Qt.DecorationRole)
            #name.setData(rect, Qt.UserRole)
            for item in [ taxon_name, caption, comments]:
                item.setEditable(True)

            self.model.appendRow([name, figure_number, taxon_name, caption, comments])

    def on_custom_context_menu(self, pos):
        menu = QMenu()
        fill_action = menu.addAction("Fill Cells")
        fill_action.triggered.connect(self.fill_selected_cells)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.on_delete_subfigure)
        menu.exec_(self.figureView.viewport().mapToGlobal(pos))

    def on_delete_subfigure(self):
        #print("Delete figure")
        # get selected index
        indexes = self.figureView.selectionModel().selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            #print("row:", row)
            # get segment result
            #self.subfigure_list = segmentation_results
            cropped_pixmap, rect = self.subfigure_list[row]
            # remove item from model
            self.model.removeRow(row)
            # remove item from subfigure_list
            self.subfigure_list.pop(row)
            # update figure image
        self.lblFigure.set_subfigure_list(self.subfigure_list)
        self.update()

    def on_selection_changed(self, selected, deselected):
        #print("selection changed")
        # get selected index
        indexes = selected.indexes()
        if len(indexes) > 0:
            index = indexes[0]
            row = index.row()
            self.lblFigure.set_current_subfigure(row)
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
            self.model.clear()
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
    
    def on_page_changed(self, page_number):
        #print("Page changed:", page_number)
        self.current_page = self.pdf_document[page_number-1]
        pix = self.current_page.get_pixmap(dpi=600, alpha=False, annots=True, matrix=fitz.Matrix(2, 2))
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)  # QImage
        self.original_figure_image = QPixmap.fromImage(img)  # QPixmap
        #print("pixmap size:", self.original_figure_image .size())
        self.lblFigure.set_pixmap(self.original_figure_image )
        self.detectButton.setEnabled(True)
        self.model.clear()
        self.subfigure_list = []
        self.lblFigure.set_subfigure_list(self.subfigure_list)
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

    def on_btn_detect_clicked(self):
        # get segmentation result from image
        # call segment_figures_qt function
        segmentation_results, annotated_pixmap = self.segment_figures_qt(self.original_figure_image)
        #self.annotated_pixmap = annotated_pixmap
        #scaled_pixmap = annotated_pixmap.scaled(self.lblFigure.width(), self.lblFigure.height(), Qt.KeepAspectRatio)
        #self.lblFigure.setPixmap(scaled_pixmap)
        #self.model.clear()

        #self.model.setHorizontalHeaderLabels(["File Name", "Figure Number", "Caption", "Comments"])
        self.subfigure_list = segmentation_results
        self.lblFigure.set_subfigure_list(self.subfigure_list)

        self.load_subfigure_list(self.subfigure_list)


        self.figureView.resizeColumnsToContents()
        self.figureView.resizeRowsToContents()

    def update_subfigure_list(self, source_row, destination_row):
        print(f"Updating subfigure_list: Moving from {source_row} to {destination_row}")
        
        # Reorder the subfigure_list to match the new model order
        moved_item = self.subfigure_list.pop(source_row)
        if destination_row == -1 or destination_row >= len(self.subfigure_list):
            self.subfigure_list.append(moved_item)
        else:
            self.subfigure_list.insert(destination_row, moved_item)

        # reload the figureView from self.subfigure_list
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["File Name", "Figure Number", "Caption", "Comments"])
        for i, (cropped_pixmap, rect) in enumerate(self.subfigure_list):
            name = QStandardItem(f"Figure{i+1}")
            figure_number = QStandardItem(f"Figure{i+1}")
            caption = QStandardItem("Caption")
            comments = QStandardItem("Comments")
            
            name.setData(cropped_pixmap, Qt.DecorationRole)
            name.setData(rect, Qt.UserRole)
            self.model.appendRow([name, figure_number, caption, comments])
        print(f"New subfigure_list order: {[item[1] for item in self.subfigure_list]}")

    def on_btn_save_clicked(self):
        # wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)

        type = self.comboType.currentText()
        number1 = self.edtNumber1.text()
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
        
        if sub_type == "--None--" and len(self.subfigure_list) == 1:
            separator = ""
        

        if len(self.subfigure_list) > 0:
            parent_figure = FgFigure()
            parent_figure.file_name = f"{type}{number1}.png"
            parent_figure.figure_number = f"{type}{number1}"
            #figure.caption = self.model.item(0, 3).text()
            #figure.comments = self.model.item(0, 4).text()
            parent_figure.reference = self.reference
            parent_figure.file_path = ""
            parent_figure.save()
            parent_figure.add_pixmap(self.original_figure_image)
            #self.original_figure_image.save(f"{type}{number1}.png")
       
        for i, (cropped_pixmap, rect) in enumerate(self.subfigure_list):
            figure = FgFigure()
            figure.reference = self.reference
            figure.parent = parent_figure
            sub_number = sub_number_list[i]
            figure.file_name = f"{type}{number1}{separator}{sub_type}{sub_number}.png"
            figure.figure_number = f"{type}{number1}{separator}{sub_type}{sub_number}"
            figure.file_path = ""
            #print("figure number:", figure.figure_number)
            figure.part1_prefix = type
            figure.part1_number = number1
            figure.part2_prefix = sub_type
            figure.part2_number = sub_number
            #figure.caption = 
            taxon_name = self.model.item(i, 2).text()
            taxon = self.process_taxon_name(taxon_name)

            figure.caption = self.model.item(i, 3).text()
            figure.comments = self.model.item(i, 4).text()
            figure.save()
            figure.add_pixmap(cropped_pixmap)

            self.update_taxon_figure(taxon, figure)
            self.update_taxon_reference(taxon, self.reference)
            #print(f"Name: {name.text()}, Figure Number: {figure_number.text()}, Caption: {caption.text()}, Comments: {comments.text()}")

        # restore cursor
        QApplication.restoreOverrideCursor()
        self.accept()
    
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


    def process_taxon_name(self, taxon_name, taxon_rank = "Species"):
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
                print("genus:",genus)
                genus.rank = "Genus"
                genus.save()
                taxon.parent = genus
                taxon.rank = "Species"
            else:
                taxon.rank = taxon_rank
            taxon.save()
        return taxon

    def on_btn_cancel_clicked(self):
        print("Cancel clicked")
        self.reject()

    def detect_figures(self):
        print("Detecting figures")
        #self.figureView.setModel

    def set_reference(self, ref):
        self.reference = ref
        self.setWindowTitle(self.tr("Figurist - Figure Information for ") + ref.get_abbr())
        self.edtReference.setText(ref.get_abbr())


    def check_overlap(self, box1, box2):
        x1, y1, w1, h1 = box1[:4]
        x2, y2, w2, h2 = box2[:4]
        
        if (x1 <= x2 <= x1 + w1 or x2 <= x1 <= x2 + w2) and (y1 <= y2 <= y1 + h1 or y2 <= y1 <= y2 + h2):
            return True
        return False

    def segment_figures_qt_1(self, qpixmap):

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
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Apply threshold
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get bounding boxes for all contours
        bounding_boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < 1000:  # Adjust this value as needed
                continue
            x, y, w, h = cv2.boundingRect(contour)
            bounding_boxes.append((x, y, w, h))

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

        if not valid_boxes:
            print("No valid boxes found.")
            return []

        # Calculate average height of boxes
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
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))

        # Process valid boxes
        result = []
        for i, (x, y, w, h, _) in enumerate(valid_boxes, start=1):
            # Add some padding
            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.shape[1] - x, w + 2*padding)
            h = min(img.shape[0] - y, h + 2*padding)

            # Crop the figure
            figure = original_img[y:y+h, x:x+w]

            # Convert cv2 image to QPixmap
            height, width, channel = figure.shape
            bytes_per_line = 3 * width
            #q_img = QImage(figure.data, width, height, bytes_per_line, QImage.Format_RGB888)
            q_img = QImage(figure.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
            cropped_pixmap = QPixmap.fromImage(q_img)

            # Add the cropped pixmap and its coordinates to the result
            result.append((cropped_pixmap, QRect(x, y, w, h)))
            painter.drawRect(x, y, w, h)

        painter.end()
        return result, annotated_pixmap
    
    def segment_figures_qt_2(self, qpixmap):
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

        gray = cv2.cvtColor(proc_img, cv2.COLOR_RGB2GRAY)
        
        # Apply morphological operations
        kernel = np.ones((5,5), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)

        # Apply threshold
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Calculate minimum and maximum contour area based on image size
        total_area = proc_width * proc_height
        min_contour_area = total_area * 0.005  # Minimum figure size (1% of image)
        max_contour_area = total_area * 0.8   # Maximum figure size (50% of image)
        
        # Get bounding boxes for all contours
        bounding_boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_contour_area < area < max_contour_area:
                x, y, w, h = cv2.boundingRect(contour)
                bounding_boxes.append((x, y, w, h))

        # Adaptive threshold adjustment
        if len(bounding_boxes) < 10 or len(bounding_boxes) > 50:
            # Binary search to find optimal threshold
            low, high = 0.001, 0.05  # 0.1% to 5% of image area
            while high - low > 0.0001:
                mid = (low + high) / 2
                min_contour_area = total_area * mid
                bounding_boxes = [cv2.boundingRect(c) for c in contours if min_contour_area < cv2.contourArea(c) < max_contour_area]
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
            w = min(img.shape[1] - x, w + 2*padding)
            h = min(img.shape[0] - y, h + 2*padding)

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

    def segment_figures_qt_3(self, qpixmap):
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

        # Function to process the image and return bounding boxes
        def process_image(img, invert=False):
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            if invert:
                gray = cv2.bitwise_not(gray)
            
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
            min_contour_area = total_area * 0.01  # Minimum figure size (1% of image)
            max_contour_area = total_area * 0.5   # Maximum figure size (50% of image)
            
            # Get bounding boxes for all contours
            bounding_boxes = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_contour_area < area < max_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    bounding_boxes.append((x, y, w, h))
            
            return bounding_boxes

        # Process the image normally
        bounding_boxes = process_image(proc_img)

        # If we detect only one large bounding box, try inverting the image
        if len(bounding_boxes) == 1 and cv2.contourArea(cv2.convexHull(np.array(bounding_boxes[0]))) > 0.9 * proc_width * proc_height:
            bounding_boxes = process_image(proc_img, invert=True)

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