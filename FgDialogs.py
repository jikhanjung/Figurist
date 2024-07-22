from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QColorDialog, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, QStatusBar, QMessageBox, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QSizePolicy, \
                            QTableWidget, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QListWidgetItem,\
                            QTabWidget, QListWidget, QSpinBox, QPlainTextEdit, QSlider, QScrollArea, QShortcut
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem, QImage,\
                        QFont, QPainter, QBrush, QMouseEvent, QWheelEvent, QDoubleValidator, QIcon, QCursor,\
                        QFontMetrics, QIntValidator, QKeySequence
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSize, QPoint, QTranslator,\
                         pyqtSlot, pyqtSignal, QItemSelectionModel, QTimer, QEvent, QSettings

from FgModel import *

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
        self.accept()

    def on_btn_cancel_clicked(self):
        print("Cancel clicked")
        self.reject()

    def load_reference(self, ref):
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
            item = QListWidgetItem(figure.figure_number)
            self.lstFigure.addItem(item)
            self.figure_list.append(figure)

    def on_btn_save_clicked(self):
        #print("Save clicked")
        if self.taxon is None:
            self.taxon = FgTaxon()
        #self.taxon = FgTaxon()
        self.taxon.name = self.edtTaxonName.text()
        self.taxon.rank = self.edtTaxonRank.text()
        self.taxon.parent = None
        self.taxon.save()

        for fig in self.figure_list:
            fig.taxon = self.taxon
            fig.save()

        taxref = TaxonReference()
        taxref.taxon = self.taxon
        taxref.reference = self.reference
        taxref.save()

        for fig in self.figure_list:
            taxfig = TaxonFigure()
            taxfig.taxon = self.taxon
            taxfig.figure = fig
            taxfig.save()

        self.accept()
    
    def on_btn_cancel_clicked(self):
        print("Cancel clicked")
        self.reject()
