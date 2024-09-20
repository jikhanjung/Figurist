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
import traceback
from FgComponents import FgFigureView, TreeViewClickFilter, ClickableTreeView, DraggableTreeView
from FgLogger import setup_logger
from functools import reduce
import operator
import time

logger = setup_logger(fg.PROGRAM_NAME)

ICON = {'new_reference': 'icons/new_reference.png', 'about': 'icons/about.png', 'exit': 'icons/exit.png', 'preferences': 'icons/preferences.png',
        'new_collection': 'icons/new_collection.png', 'reference': 'icons/reference.png' , 'collection': 'icons/collection.png'} 

class FiguristMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(fg.resource_path('icons/Figurist.png')))
        self.setWindowTitle("{} v{}".format(self.tr("Figurist"), fg.PROGRAM_VERSION))
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

        self.prepare_database()
        self.reset_referenceView()
        self.load_references()
        #self.toggle_view()

    def on_referenceView_emptyAreaClicked(self):
        self.referenceView.clearSelection()
        self.referenceView.setCurrentIndex(self.referenceView.rootIndex())
        self.selected_reference = None
        if self.mode == "Reference":
            self.selected_collection = None
            self.load_taxa()
        self.filter_figures()

    def initUI(self):
        ''' initialize UI '''
        self.figure_tab = QTabWidget()
        self.figureView = FgFigureView()
        self.pdfView = PDFViewWidget()
        self.figure_tab.addTab(self.pdfView, self.tr("PDF"))
        self.figure_tab.addTab(self.figureView, self.tr("Figures"))
        self.referenceView = DraggableTreeView()
        self.taxonView = QTreeView()
        self.referenceView.setDragEnabled(True)
        self.referenceView.setAcceptDrops(True)
        self.referenceView.setDragDropMode(QAbstractItemView.DragDrop)        
        #self.referenceView.setAcceptDrops(True)
        self.referenceView.dropEvent = self.dropEvent
        self.referenceView.emptyAreaClicked.connect(self.on_referenceView_emptyAreaClicked)

        self.icon_mode = False
        self.mode = "Reference"
        self.figure_model = None
        self.taxon_model = None
        self.selected_taxa = []
        self.selected_reference = []

        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout()
        self.button_widget.setLayout(self.button_layout)
        self.add_figure_button = QPushButton(self.tr("Add Figure"))
        self.toggle_view_button = QPushButton(self.tr("Toggle View"))
        self.button_layout.addWidget(self.add_figure_button)
        self.button_layout.addWidget(self.toggle_view_button)

        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        self.right_layout.addWidget(self.figure_tab)
        self.right_layout.addWidget(self.button_widget)
        self.toggle_view_button.clicked.connect(self.toggle_view)
        self.add_figure_button.clicked.connect(self.add_figure)

        self.left_mode_widget = QWidget()
        self.left_mode_layout = QHBoxLayout()
        self.lblMode = QLabel(self.tr("Mode"))
        self.rbReference = QRadioButton(self.tr("Reference"))
        self.rbTaxon = QRadioButton(self.tr("Taxon"))
        self.left_mode_layout.addWidget(self.lblMode)
        self.left_mode_layout.addWidget(self.rbReference)
        self.left_mode_layout.addWidget(self.rbTaxon)
        self.left_mode_widget.setLayout(self.left_mode_layout)
        self.rbReference.setChecked(True)
        self.rbReference.toggled.connect(self.set_reference_mode)
        self.rbTaxon.toggled.connect(self.set_taxon_mode)

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)
        self.left_layout.addWidget(self.left_mode_widget)
        self.left_layout.addWidget(self.referenceView)
        self.left_layout.addWidget(self.taxonView)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([300, 800])


        self.setCentralWidget(self.splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)


        self.referenceView.doubleClicked.connect(self.on_referenceView_doubleClicked)
        self.referenceView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.referenceView.customContextMenuRequested.connect(self.open_referenceView_menu)
        self.taxonView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.taxonView.customContextMenuRequested.connect(self.open_taxonView_menu)
        self.figureView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.figureView.customContextMenuRequested.connect(self.open_figureView_menu)
        self.figureView.tableView.doubleClicked.connect(self.on_figureView_doubleClicked)
        self.figureView.listView.doubleClicked.connect(self.on_figureView_doubleClicked)
        #self.figureView.horizontalHeader().sectionResized.connect(self.update_icon_mode_columns)
        self.item_size = 220  # Default size (including spacing)
        #self.figure_model = FigureTableModel([])
        #self.figure_delegate = FigureItemDelegate()        

        #self.model = CustomTableModel(self.data)
        #self.delegate = CustomItemDelegate()
        #self.figureView.setItemDelegate(self.delegate)


        ''' toolbar and actions'''
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setIconSize(QSize(32,32))

        self.actionNewReference = QAction(QIcon(fg.resource_path(ICON['new_reference'])), self.tr("New Reference\tCtrl+N"), self)
        self.actionNewReference.triggered.connect(self.on_action_add_reference_triggered)
        self.actionNewReference.setShortcut(QKeySequence("Ctrl+N"))
        self.actionNewCollection = QAction(QIcon(fg.resource_path(ICON['new_collection'])), self.tr("New Collection"), self)
        self.actionNewCollection.triggered.connect(self.on_action_new_collection_triggered)
        self.actionNewCollection.setShortcut(QKeySequence("Ctrl+M"))
        self.actionExit = QAction(QIcon(fg.resource_path(ICON['exit'])), self.tr("Exit\tCtrl+W"), self)
        self.actionExit.triggered.connect(self.on_action_exit_triggered)
        self.actionExit.setShortcut(QKeySequence("Ctrl+W"))
        self.actionAbout = QAction(QIcon(fg.resource_path(ICON['about'])), self.tr("About\tF1"), self)
        self.actionAbout.triggered.connect(self.on_action_about_triggered)
        self.actionAbout.setShortcut(QKeySequence("F1"))
        self.actionPreferences = QAction(QIcon(fg.resource_path(ICON['preferences'])),self.tr("Preferences"), self)
        self.actionPreferences.triggered.connect(self.on_action_preferences_triggered)

        self.toolbar.addAction(self.actionNewCollection)
        self.toolbar.addAction(self.actionNewReference)
        self.toolbar.addAction(self.actionPreferences)
        self.toolbar.addAction(self.actionAbout)
        self.addToolBar(self.toolbar)


        ''' menu '''
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu(self.tr("File"))
        self.file_menu.addAction(self.actionNewCollection)
        self.file_menu.addAction(self.actionNewReference)
        self.file_menu.addAction(self.actionExit)
        self.help_menu = self.main_menu.addMenu(self.tr("Help"))
        self.help_menu.addAction(self.actionAbout)

        self.m_app = QApplication.instance()
        self.read_settings()

        #self.figureView.setDragEnabled(True)
        self.figureView.tableView.setAcceptDrops(True)
        self.figureView.tableView.setDropIndicatorShown(True)
        self.figureView.tableView.dropEvent = self.figureView_drop_event
        self.figureView.tableView.dragEnterEvent = self.figureView_drag_enter_event
        self.figureView.tableView.dragMoveEvent = self.figureView_drag_move_event

        self.figureView.listView.setAcceptDrops(True)
        self.figureView.listView.setDropIndicatorShown(True)
        self.figureView.listView.dropEvent = self.figureView_drop_event
        self.figureView.listView.dragEnterEvent = self.figureView_drag_enter_event
        self.figureView.listView.dragMoveEvent = self.figureView_drag_move_event
        '''
        self.figureView.horizontalHeader().hide()
        self.figureView.verticalHeader().hide()
        '''
        self.toggle_view(True)


    def dropEvent(self, event):
        #print("reference view drop event")
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            print("not has format")
            event.ignore()
            return

        drop_index = self.referenceView.indexAt(event.pos())
        #print("drop index:", drop_index, drop_index.isValid())
        if not drop_index.isValid():
            event.ignore()
            return

        drop_item = self.reference_model.itemFromIndex(drop_index)
        #print("drop item:", drop_item, drop_item.data())
        if not isinstance(drop_item.data(), FgCollection):
            event.ignore()
            return
    
        target_collection = drop_item.data()
        source_indexes = self.referenceView.selectedIndexes()
        old_collection = self.reference_model.itemFromIndex(source_indexes[0].parent()).data()
        for index in source_indexes:
            item = self.reference_model.itemFromIndex(index)
            if isinstance(item.data(), FgReference):
                reference = item.data()
                if event.keyboardModifiers() & Qt.ShiftModifier:
                    new_colref = FgCollectionReference.select().where(FgCollectionReference.collection==target_collection, FgCollectionReference.reference==reference).first()
                    if new_colref is None:
                        FgCollectionReference.create(collection=target_collection, reference=reference)
                    else:
                        # show messagebox that it already exists
                        msgbox = QMessageBox()
                        msgbox.setText("Reference already exists in the target collection.")
                        msgbox.exec()
                else:
                    # Move action (change collection from old_collection to target_colection)
                    new_colref = FgCollectionReference.select().where(FgCollectionReference.collection==target_collection, FgCollectionReference.reference==reference).first()
                    #(collection=target_collection, reference=reference)
                    if new_colref is None:
                        #FgCollectionReference.create(collection=target_collection, reference=reference)
                    #if new_colref is None:
                        #FgCollectionReference.create(collection=target_collection, reference=reference)
                        old_colref = FgCollectionReference.get(collection=old_collection, reference=reference)
                        old_colref.collection = target_collection
                        old_colref.save()
                    else:
                        # show messagebox that it already exists
                        msgbox = QMessageBox()
                        msgbox.setText("Reference already exists in the target collection.")
                        msgbox.exec()

                    #else:
                    #    old_colref = FgCollectionReference.get(collection=old_collection, reference=reference)
                    #    old_colref.delete_instance()

                    #old_collection_reference = FgCollectionReference.get(reference=reference)
                    #old_collection_reference.collection = target_collection
                    #old_collection_reference.save()

        self.reset_referenceView()
        self.load_references()
        event.accept()


    def _dropEvent(self, event):
        print("drop event", event.mimeData())
        if not event.mimeData().hasFormat("application/x-figurist-items"):
            event.ignore()
            return

        drop_index = self.referenceView.indexAt(event.pos())
        if not drop_index.isValid():
            event.ignore()
            return

        drop_item = self.reference_model.itemFromIndex(drop_index)
        if not isinstance(drop_item.data(), FgCollection):
            event.ignore()
            return

        target_collection = drop_item.data()

        items_data = eval(bytes(event.mimeData().data("application/x-figurist-items")).decode())
        
        for item_type, item_id in items_data:
            if item_type == 'reference':
                reference = FgReference.get_by_id(item_id)
                if event.keyboardModifiers() & Qt.ShiftModifier:
                    # Copy action
                    new_reference = FgReference.create(
                        title=reference.title,
                        author=reference.author,
                        year=reference.year,
                        # ... copy other fields as needed
                    )
                    FgCollectionReference.create(collection=target_collection, reference=new_reference)
                else:
                    # Move action
                    old_collection_reference = FgCollectionReference.get(reference=reference)
                    old_collection_reference.collection = target_collection
                    old_collection_reference.save()
            elif item_type == 'collection':
                source_collection = FgCollection.get_by_id(item_id)
                if event.keyboardModifiers() & Qt.ShiftModifier:
                    # Copy action
                    new_collection = FgCollection.create(
                        name=source_collection.name,
                        parent=target_collection
                        # ... copy other fields as needed
                    )
                    # Recursively copy subcollections and references
                    self.copy_collection_contents(source_collection, new_collection)
                else:
                    # Move action
                    source_collection.parent = target_collection
                    source_collection.save()

        self.reset_referenceView()
        self.load_references()
        event.accept()

    def copy_collection_contents(self, source_collection, target_collection):
        # Copy references
        for col_ref in source_collection.references:
            FgCollectionReference.create(
                collection=target_collection,
                reference=col_ref.reference
            )
        
        # Copy subcollections
        for subcollection in source_collection.children:
            new_subcollection = FgCollection.create(
                name=subcollection.name,
                parent=target_collection
                # ... copy other fields as needed
            )
            self.copy_collection_contents(subcollection, new_subcollection)

    def add_figure(self):
        if self.selected_reference is None:
            return
        dialog = AddFigureDialog(self)
        dialog.set_reference(self.selected_reference)
        dialog.exec_()
        self.load_figure()

    def update_icon_mode_columns(self):
        if self.icon_mode:
            view_width = self.figureView.viewport().width()
            #if self.figure_model:
            self.figure_model.update_columns(view_width, self.item_size)

    def set_reference_mode(self, checked):
        if checked:
            self.mode = "Reference"
            self.load_references()
            self.load_taxa()
            self.left_layout.removeWidget(self.referenceView)
            self.left_layout.insertWidget(1,self.referenceView)
            self.update()
            self.filter_figures()
    
    def set_taxon_mode(self, checked):
        if checked:
            self.mode = "Taxon"
            self.load_taxa()
            self.load_references()
            self.left_layout.removeWidget(self.taxonView)
            self.left_layout.insertWidget(1,self.taxonView)
            self.update()
            self.filter_figures()

    def toggle_view(self, icon_mode):
        if icon_mode:
            self.icon_mode = icon_mode #not self.icon_mode
        else:
            self.icon_mode = not self.icon_mode
        self.figureView.set_icon_mode(self.icon_mode)
        return

    def resizeEvent(self, event):
        super().resizeEvent(event)
        #self.update_icon_mode_columns()
        
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

    def on_figureView_doubleClicked(self, index):
        figure_data = self.figureView.get_data(index)
        if figure_data is None:
            return
        figure = figure_data
        self.dlg = FigureDialog(self)
        self.dlg.setModal(True)
        self.dlg.load_figure(figure)
        ret = self.dlg.exec_()
        self.load_figure()

    def on_referenceView_doubleClicked(self):
        #obj = 
        if self.selected_reference is not None:
            self.on_action_edit_reference_triggered()
            return
            self.dlg = ReferenceDialog(self)
            self.dlg.setModal(True)
            self.dlg.set_reference( self.selected_reference )
            if self.selected_collection is not None:
                self.dlg.set_collection( self.selected_collection )
            #self.dlg.set_collection( self.selected_collection )
            ret = self.dlg.exec_()
            self.reset_referenceView()
            self.load_references()
        else:
            self.on_action_edit_collection_triggered()

    def reset_referenceView(self):
        self.reference_model = QStandardItemModel()
        self.referenceView.setModel(self.reference_model)
        self.referenceView.setHeaderHidden(True)
        self.reference_selection_model = self.referenceView.selectionModel()
        self.reference_selection_model.selectionChanged.connect(self.on_reference_selection_changed)
        header = self.referenceView.header()
        self.referenceView.setSelectionBehavior(QTreeView.SelectRows)

    def load_subcollections(self, collection, parent_item):
        for subcoll in collection.children:
            item1 = QStandardItem(subcoll.name)
            item1.setIcon(QIcon(fg.resource_path(ICON['collection'])))
            item1.setData(subcoll)
            parent_item.appendRow([item1])
            self.load_subcollections(subcoll, item1)
            self.load_references_in_collection(subcoll, item1)

    def load_references_in_collection(self, collection, parent_item):

        ordered_references = (FgCollectionReference
                            .select(FgCollectionReference, FgReference)
                            .join(FgReference)
                            .where(FgCollectionReference.collection == collection)
                            .order_by(FgReference.author, FgReference.year))
        for colref in ordered_references:
            item1 = QStandardItem(colref.reference.get_abbr())
            #item2 = QStandardItem(str(ref.id))
            item1.setData(colref.reference)
            item1.setIcon(QIcon(fg.resource_path(ICON['reference'])))

            parent_item.appendRow([item1])


    def load_references(self):
        #print("load references", self.mode)
        self.reference_model.clear()
        self.selected_reference = None
        #ref_list = FgReference.filter(parent=None)

        if self.mode == "Reference":
            coll_list = FgCollection.select().where(FgCollection.parent==None).order_by(FgCollection.name)
            for coll in coll_list:
                item1 = QStandardItem(coll.name)
                item1.setIcon(QIcon(fg.resource_path(ICON['collection'])))
                item1.setData(coll)
                self.reference_model.appendRow([item1])
                self.load_subcollections(coll, item1)
                self.load_references_in_collection(coll, item1)

            #ref_list = FgReference.select().order_by(FgReference.author, FgReference.year)
        else:
            '''
            taxref = TaxonReference.select().where(TaxonReference.taxon << self.selected_taxa)
            #taxref = TaxonReference.select().where(TaxonReference.taxon == self.selected_taxon)
            ref_list = [tr.reference for tr in taxref]
            # make unique
            ref_list = list(set(ref_list))
            # order by author and year
            ref_list = sorted(ref_list, key=lambda x: (x.author, x.year))
            '''
            #print("selected taxa:", self.selected_taxa)
            if len(self.selected_taxa) > 0:
                ref_list = (FgReference
                .select(FgReference)
                .join(FgTaxonReference)
                .where(FgTaxonReference.taxon << self.selected_taxa)
                .group_by(FgReference)
                .order_by(FgReference.author, FgReference.year)
                .distinct())
            else:
                ref_list = []

            for ref in ref_list:
                item1 = QStandardItem(ref.get_abbr())
                item1.setIcon(QIcon(fg.resource_path(ICON['reference'])))
                item2 = QStandardItem(str(ref.id))
                item1.setData(ref)
                self.reference_model.appendRow([item1,item2])#,item2,item3] )
        self.referenceView.expandAll()
        self.referenceView.hideColumn(1)

    def on_figure_selection_changed(self, selected, deselected):
        pass

    def find_taxon_item(self, taxon):
        for row in range(self.taxon_model.rowCount()):
            item = self.taxon_model.item(row, 0)  # Assuming taxa are in the first column
            if item.data() == taxon:
                return item
        return None  # Return None if the taxon is not found

    def on_taxon_selection_changed(self, selected, deselected):
        #print("taxon selection changed 1", time.time())
        prev_selected_taxa = self.selected_taxa

        selected_indices = self.taxonView.selectedIndexes()
        #print("selected indices:", selected_indices)
        if selected_indices:
            self.selected_taxa = [self.taxon_model.itemFromIndex(index).data() for index in selected_indices]
        else:
            self.selected_taxa = []

        newly_selected_taxa = set(self.selected_taxa) - set(prev_selected_taxa)
        if len(newly_selected_taxa) > 0:
            #disconnect selectionchanged
            self.taxon_selection_model.selectionChanged.disconnect(self.on_taxon_selection_changed)

            for taxon in newly_selected_taxa:
                #print("newly selected taxon:", taxon.name)
                if taxon.children.count() > 0:
                    self.selected_taxa.extend(taxon.children)
                    # select children
                    for child in taxon.children:
                        child_item = self.find_taxon_item(child)
                        if child_item:
                            child_index = self.taxon_model.indexFromItem(child_item)
                            self.taxonView.selectionModel().select(child_index, QItemSelectionModel.Select)

                        # iterate taxon model and get index
                        #index = self.taxon_model.indexFromItem(child)
                        #self.taxonView.selectionModel().select(index, QItemSelectionModel.Select)

                    #print("children:", [t.name for t in taxon.children])
            self.taxon_selection_model.selectionChanged.connect(self.on_taxon_selection_changed)
        #print("selected taxa:", [t.name for t in self.selected_taxa])

        if self.mode == "Taxon":
            self.load_references()

        #print("taxon selection changed 2", time.time())

        self.filter_figures()

    def on_reference_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if len(indexes) == 0:
            return
        index = indexes[0]
        obj = self.reference_model.itemFromIndex(index).data()
        if isinstance(obj, FgReference):
            self.selected_reference = obj
            # get parent item of the selected item
            parent_item = self.reference_model.itemFromIndex(index.parent())
            if parent_item:
                self.selected_collection = parent_item.data()
            else:
                self.selected_collection = None
            #print("on reference selection changed selected reference 1:", self.selected_reference,"selected_collection:", self.selected_collection)
            if self.mode == "Reference":
                self.selected_taxa = []
                self.load_taxa()
                if self.selected_reference.zotero_key is not None and self.selected_reference.zotero_key != "":
                    pdf_dir = self.selected_reference.get_attachment_path()
                    if os.path.exists(pdf_dir):
                        #print("pdf_dir:", pdf_dir)
                        # get file list from pdf_dif
                        pdf_files = [f for f in os.listdir(pdf_dir) if os.path.isfile(os.path.join(pdf_dir, f))]
                        if len(pdf_files) > 0:
                            #print("pdf_files:", pdf_files)
                            self.pdfView.set_pdf(Path(pdf_dir) / pdf_files[0])
                        # set tab to pdf
                        self.figure_tab.setCurrentIndex(0)
                    else:
                        #self.pdfView.clear()
                        self.figure_tab.setCurrentIndex(1)
            #print("on reference selection changed selected reference 2:", self.selected_reference,"selected_collection:", self.selected_collection)
            self.filter_figures()
            #print("on reference selection changed selected reference 3:", self.selected_reference,"selected_collection:", self.selected_collection)
        elif isinstance(obj, FgCollection):
            self.selected_collection = obj
            self.selected_reference = None
        #print("selected reference:", self.selected_reference)
        return
        #else:
        #    self.filter_figures_by_taxa()

    def reset_taxonView(self):
        self.taxonView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.taxonView.setHeaderHidden(True)
        self.taxon_model = QStandardItemModel()
        self.taxonView.setModel(self.taxon_model)
        self.taxon_selection_model = self.taxonView.selectionModel()
        self.taxon_selection_model.selectionChanged.connect(self.on_taxon_selection_changed)
        #self.figure_model = CustomTableModel()
        #self.figureView.setHeaderHidden(True)
        pass

    def load_children(self, taxon, parent_item):
        for child in taxon.children:
            item1 = QStandardItem(child.name)
            item1.setData(child)
            parent_item.appendRow([item1])
            self.load_children(child, item1)

    def load_taxa(self):
        self.taxonView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.taxonView.setHeaderHidden(True)
        self.taxon_model = QStandardItemModel()
        self.taxonView.setModel(self.taxon_model)
        self.taxon_model.clear()

        taxa_list = []
        #print("selected reference:", self.selected_reference, self.mode)
        if self.mode == "Reference":
            taxref = FgTaxonReference.select().where(FgTaxonReference.reference == self.selected_reference)
            for tr in taxref:
                taxa_list.append(tr.taxon)
            for taxon in taxa_list:
                item1 = QStandardItem(taxon.name)
                item1.setData(taxon)
                self.taxon_model.appendRow([item1])
        else:
            taxa_list = FgTaxon.select().where(FgTaxon.parent==None).order_by(FgTaxon.name)
            #print("taxa_list:", taxa_list)
            for taxon in taxa_list:
                item1 = QStandardItem(taxon.name)
                item1.setData(taxon)
                self.taxon_model.appendRow([item1])
                self.load_children(taxon, item1)

        self.taxonView.expandAll()
        
        # Set up the selection model
        self.taxon_selection_model = self.taxonView.selectionModel()
        self.taxon_selection_model.selectionChanged.connect(self.on_taxon_selection_changed)

    def reset_figureView(self):
        #self.figure_model = CustomTableModel()
        #self.figureView.setHeaderHidden(True)
        pass

    def load_figure(self):
        if self.selected_reference is None:
            return
        figure_list = FgFigure.select().where(FgFigure.reference == self.selected_reference)
        self.figureView.load_figures(figure_list)

    def get_figures(self,selected_taxa=None, selected_references=None):
        query = FgFigure.select().distinct()
        conditions = []

        if selected_taxa:
            query = (query
                    .join(FgTaxonFigure)
                    .join(FgTaxon))
            conditions.append(FgTaxon.id.in_([t.id for t in selected_taxa]))

        if selected_references:
            conditions.append(FgFigure.reference.in_([r.id for r in selected_references]))

        if conditions:
            query = query.where(reduce(operator.and_, conditions))
        return query
    
    def filter_figures(self):
        selected_taxa = self.selected_taxa
        selected_references = []
        if self.selected_reference:
            selected_references = [self.selected_reference]
        #print("selected taxa:", [t.name for t in selected_taxa])
        #print("selected references:", [r.get_abbr() for r in selected_references])
        #print("filter figures 2", time.time())
        if len(selected_taxa) == 0 and len(selected_references) == 0:
            self.figureView.load_figures([])
            return
        query = self.get_figures(selected_taxa, selected_references)
        #print("filter figures 3", time.time())
        figures = query.execute()
        #print("filter figures 4", time.time())
        self.figureView.load_figures(figures)
        #print("filter figures 5", time.time())

    def filter_figures_by_taxa(self):
        selected_indices = self.taxonView.selectedIndexes()
        if not selected_indices:
            self.load_figure()  # Show all figures
        else:
            selected_taxa = [self.taxon_model.itemFromIndex(index).data() for index in selected_indices]
            filtered_figures = [
                figure for figure in FgFigure.select().where(FgFigure.reference == self.selected_reference)
                if figure.taxon in selected_taxa
            ]
            self.figureView.load_figures(filtered_figures)

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
        #print("tabelview drop event", event.mimeData().text())
        if self.selected_reference is None:
            return
        
        if event.mimeData().text() == "":
            return
        file_name_list = event.mimeData().text().strip().split("\n")
        if len(file_name_list) == 0:
            return

        #print("file name list: [", file_name_list, "]")

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
        self.reset_figureView()
        self.select_reference(reference)
        self.load_figure()
        QApplication.restoreOverrideCursor()


    def select_reference(self,reference,node=None):
        #`print("select reference", reference)
        if reference is None:
            return
        if node is None:
            node = self.reference_model.invisibleRootItem()   

        for i in range(node.rowCount()):
            item = node.child(i,0)
            if item.data() == reference:
                self.referenceView.setCurrentIndex(item.index())
                return True
            ret = self.select_reference(reference,node.child(i,0))
            if ret:
                return True
        return False

    def on_action_new_reference_triggered(self):
        dialog = ReferenceDialog(self)
        dialog.exec_()
        self.reset_referenceView()
        self.load_references()

    def on_action_new_collection_triggered(self):
        dialog = CollectionDialog(self)
        dialog.exec_()
        self.reset_referenceView()
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

    def open_taxonView_menu(self, position):
        indexes = self.taxonView.selectedIndexes()
        #print("taxonView indexes:", indexes)
        if len(indexes) == 0:
            return
        taxa_list = []
        for index in indexes:
            #level = max(level, index.row())
            taxon = self.taxon_model.itemFromIndex(index).data()
            taxa_list.append(taxon)

        self.selected_taxa = taxa_list
        if len(taxa_list) == 0:
            return
        elif len(taxa_list) == 1:
            delete_text = self.tr("Delete taxon")
        else:
            delete_text = self.tr("Delete taxa")

        action_delete_taxon = QAction(delete_text)
        action_delete_taxon.triggered.connect(self.on_action_delete_taxon_triggered)
        #action_delete_figure = QAction(self.tr("Delete figure(s)"))
        #action_delete_figure.triggered.connect(self.on_action_delete_figure_triggered)

        menu = QMenu()
        menu.addAction(action_delete_taxon)
        #menu.addAction(action_delete_figure)
        menu.exec_(self.taxonView.viewport().mapToGlobal(position))

    def on_action_delete_taxon_triggered(self):
        if not self.selected_taxa:
            return
        
        for taxon in self.selected_taxa:
            # Assuming figure_data is a dictionary with 'id' key
            if taxon and taxon.related_figures.count() > 0:
                msg = self.tr("Taxon {} has figures. Delete taxon and figures?").format(taxon.name)
                ret = QMessageBox.question(self, self.tr("Delete taxon"), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if ret == QMessageBox.No:
                    continue
            taxon.delete_instance()
        
        self.load_figure()
        self.load_taxa()

    def open_referenceView_menu(self, position):
        indexes = self.referenceView.selectedIndexes()
        if len(indexes) == 0:
            return

        if self.mode == "Reference":
            index = indexes[0]
            item = self.reference_model.itemFromIndex(index)
            obj = item.data()
            if isinstance(obj, FgReference):
                self.selected_reference = obj
                #self.selected_collection = None
            elif isinstance(obj, FgCollection):
                self.selected_collection = obj
                self.selected_reference = None
    
        action_add_collection = QAction(self.tr("Add collection"))
        action_add_collection.triggered.connect(self.on_action_add_collection_triggered)
        action_edit_collection = QAction(self.tr("Edit collection"))
        action_edit_collection.triggered.connect(self.on_action_edit_collection_triggered)
        action_add_subcollection = QAction(self.tr("Add subcollection"))
        action_add_subcollection.triggered.connect(self.on_action_add_subcollection_triggered)
        action_export_collection = QAction(self.tr("Export collection"))
        action_export_collection.triggered.connect(self.on_action_export_collection_triggered)
        action_delete_collection = QAction(self.tr("Delete collection"))
        action_delete_collection.triggered.connect(self.on_action_delete_collection_triggered)


        action_add_reference = QAction(self.tr("Add reference"))
        action_add_reference.triggered.connect(self.on_action_add_reference_triggered)
        action_edit_reference = QAction(self.tr("Edit reference"))
        action_edit_reference.triggered.connect(self.on_action_edit_reference_triggered)
        action_delete_reference = QAction(self.tr("Delete reference"))
        action_delete_reference.triggered.connect(self.on_action_delete_reference_triggered)

        menu = QMenu()
        if self.selected_reference is not None:
            menu.addAction(action_edit_reference)
            menu.addAction(action_delete_reference)
        elif self.selected_collection is not None:
            menu.addAction(action_edit_collection)
            menu.addAction(action_export_collection)
            menu.addAction(action_delete_collection)
            menu.addAction(action_add_subcollection)
            menu.addAction(action_add_reference)
        menu.exec_(self.referenceView.viewport().mapToGlobal(position))

    def on_action_edit_collection_triggered(self):
        col = self.selected_collection

        self.dlg = CollectionDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_collection( self.selected_collection )
        ret = self.dlg.exec_()
        self.reset_referenceView()
        self.load_references()
        self.select_reference(col)

    def on_action_edit_reference_triggered(self):
        if self.selected_reference is None:
            return
        ref = self.selected_reference
        print("edit reference:", ref)
        dialog = ReferenceDialog(self)
        dialog.set_reference(self.selected_reference)
        dialog.exec_()
        self.reset_referenceView()
        self.load_references()
        print("edit ref done:", ref)
        self.select_reference(ref)

    def on_action_export_collection_triggered(self):
        if self.selected_collection is None:
            return

        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setModal(True)
        dialog.setDirectory(os.path.expanduser("~"))
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        directory = dialog.exec_()
        if directory:
            directory = dialog.selectedFiles()[0]
            self.selected_collection.export(directory)
            self.statusBar.showMessage(self.tr("Exported collection to {}").format(directory), 2000)

    def on_action_delete_collection_triggered(self):
        if self.selected_collection is None:
            return
        #print("delete collection:", self.selected_collection)
        if self.selected_collection.children.count() > 0 or self.selected_collection.references.count() > 0:
            msg = self.tr("Collection {} has subcollections/references. Delete collection and subcollections/references?").format(self.selected_collection.name)
            ret = QMessageBox.question(self, self.tr("Delete collection"), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.No:
                return
        self.selected_collection.delete_instance()
        self.reset_referenceView()
        self.load_references()

    def on_action_delete_reference_triggered(self):
        #print("on delete reference 1 selected_reference:", self.selected_reference, "selected_collection:", self.selected_collection)
        if self.selected_reference is None:
            return
        if self.selected_reference.collections.count() > 1:
            colref = FgCollectionReference.get(reference=self.selected_reference, collection=self.selected_collection)
            colref.delete_instance()
            #self.selected_reference.collections[0].delete_instance()
            #return
        else:
            #print("delete reference:", self.selected_reference)
            #print("on delete reference 2 selected_reference:", self.selected_reference, "selected_collection:", self.selected_collection)
            if self.selected_reference.figures.count() > 0:
                msg = self.tr("Reference {} has figures. Delete reference and figures?").format(self.selected_reference.get_abbr())
                ret = QMessageBox.question(self, self.tr("Delete reference"), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if ret == QMessageBox.No:
                    return
            self.selected_reference.delete_instance()
        self.reset_referenceView()
        self.load_references()

    def on_action_add_collection_triggered(self):
        dialog = CollectionDialog(self)
        #dialog.set_parent_collection(self.selected_collection)
        dialog.exec_()
        self.reset_referenceView()
        self.load_references()

    def on_action_add_subcollection_triggered(self):
        dialog = CollectionDialog(self)
        dialog.set_parent_collection(self.selected_collection)
        dialog.exec_()
        self.reset_referenceView()
        self.load_references()
        self.select_reference(self.selected_collection)

    def on_action_add_reference_triggered(self):
        dialog = ReferenceDialog(self)
        dialog.set_collection(self.selected_collection)
        dialog.exec_()
        self.reset_referenceView()
        self.load_references()

    def open_figureView_menu(self, position):
        indexes = self.figureView.selectedIndexes()
        if len(indexes) == 0:
            return

        figure_list = []
        for index in indexes:
            figure_data = self.figureView.get_data(index)
            #print("figure_data:", figure_data)
            if figure_data is not None:
                figure_list.append(figure_data)

        self.selected_figures = figure_list

        if not figure_list:
            return

        action_set_taxon = QAction(self.tr("Set taxon"))
        action_set_taxon.triggered.connect(self.on_action_set_taxon_triggered)
        action_delete_figure = QAction(self.tr("Delete figure(s)"))
        action_delete_figure.triggered.connect(self.on_action_delete_figure_triggered)

        menu = QMenu()
        menu.addAction(action_set_taxon)
        menu.addAction(action_delete_figure)
        menu.exec_(self.figureView.currentWidget().viewport().mapToGlobal(position))

    def on_action_set_taxon_triggered(self):
        if self.selected_figures is None:
            return
        dialog = TaxonDialog(self)
        if self.selected_reference:
            dialog.set_reference(self.selected_reference)
        dialog.set_figures(self.selected_figures)
        dialog.exec_()
        self.load_figure()
        self.load_taxa()

    def on_action_delete_figure_triggered(self):
        if not self.selected_figures:
            return
        
        for figure in self.selected_figures:
            # Assuming figure_data is a dictionary with 'id' key
            #figure_id = figure_data.get('id')
            #print("figure_id:", figure_id)
            #print("figure:", figure.id, figure)
            #ref = figure.reference
            if figure.children.count() > 0:
                continue
                #msg = self.tr("Figure {} has subfigures. Delete figure and subfigures?").format(figure.figure_number)
                #ret = QMessageBox.question(self, self.tr("Delete figure"), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                #if ret == QMessageBox.No:
                #    continue
            figure.delete_instance()
        
        self.load_figure()
        self.load_taxa()

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