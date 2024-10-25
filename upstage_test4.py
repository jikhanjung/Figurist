import sys
import os
import json
import time
import requests
import httpx
import logging
import fitz  # PyMuPDF
import re
import html
from contextlib import contextmanager
import functools
from FgComponents import FigureLabel
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
                           QTextEdit, QLabel, QMessageBox, QProgressBar, QGroupBox,
                           QRadioButton, QButtonGroup, QSplitter, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage

logger = logging.getLogger(__name__)

class DocumentLabel(FigureLabel):
    text_selected = pyqtSignal(str)  # Signal definition

    def __init__(self, parent=None):
        super().__init__(parent)
        self.elements = {}  # Dictionary with page numbers as keys
        self.show_text = True
        self.show_boxes = True
        self.current_page = 1
        self.category_colors = {
            'heading1': QColor(255, 0, 0, 128),
            'heading2': QColor(220, 0, 0, 128),
            'paragraph': QColor(0, 255, 0, 128),
            'list': QColor(0, 0, 255, 128),
            'table': QColor(255, 165, 0, 128),
            'image': QColor(128, 0, 128, 128),
            'default': QColor(128, 128, 128, 128)
        }
        self.setReadOnly(True)

    def handleElementClick(self, pos):
        print("handleElementClick called")  # Debug print
        """Handle clicks on text elements"""
        if self.current_page not in self.elements:
            print("No elements for current page")  # Debug print
            return False
    
        print("Checking elements for current page")  # Debug print

        # Convert click position to image coordinates
        img_x = self._2imgx(pos.x())
        img_y = self._2imgy(pos.y())
        
        # Check each element for intersection
        for element in self.elements[self.current_page]:
            if 'coordinates' not in element:
                continue

            print("Checking element:", element['category'])  # Debug print           
                
            coords = element['coordinates']
            print("Element coordinates:", coords)  # Debug print
            x = int(coords[0]['x'] * self.orig_pixmap.width())
            y = int(coords[0]['y'] * self.orig_pixmap.height())
            width = int((coords[2]['x'] - coords[0]['x']) * self.orig_pixmap.width())
            height = int((coords[2]['y'] - coords[0]['y']) * self.orig_pixmap.height())

            print("Element bounds:", x, y, width, height)  # Debug print
            print("Click position:", img_x, img_y)  # Debug print
            
            # Check if click is within element bounds
            if (x <= img_x <= x + width and y <= img_y <= y + height):
                print("Click is within element bounds", element)  # Debug print
                if 'content' in element and element['content'].get('html'):
                    print("Found text element")  # Debug print
                    text = (f"Type: {element['category']}\n\n"
                           f"Coordinates: ({x}, {y}, {width}, {height})\n\n"
                           f"Content:\n{element['content']['html']}")
                    
                    html_content = element['content']['html']
                    # Remove HTML tags (simple method)
                    plain_text = html_content.replace('<br>', '\n')  # Convert <br> to newlines first
                    # Remove all other HTML tags
                    plain_text = re.sub(r'<[^>]+>', '', plain_text)
                    # Fix any HTML entities
                    plain_text = html.unescape(plain_text)
                    
                    text = plain_text #(f"Type: {element['category']}\n\n"f"Content:\n{plain_text}")

                    print("Emitting text_selected signal:", text[:50] + "...")
                    self.text_selected.emit(text)
                    return True  # Handled the click
        return False  # Did not handle the click

    def mousePressEvent(self, event):
        print("mouse press event")
        if event.button() == Qt.LeftButton:
            print("left button")
            # Try to handle text element click first
            if self.handleElementClick(event.pos()):
                return  # Stop if we handled a text element click
            
        # If we didn't handle a text element click and we're not read-only,
        # let the parent handle it
        #if not self.read_only:
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Try to handle text element click first
            if self.handleElementClick(event.pos()):
                return  # Stop if we handled a text element click
            
        # If we didn't handle a text element click and we're not read-only,
        # let the parent handle it
        if not self.read_only:
            super().mouseDoubleClickEvent(event)

    def set_elements(self, elements, page_number=1):
        self.elements[page_number] = elements
        self.current_page = page_number  # Update current page when setting elements
        self.repaint()

    def set_page(self, page_number):
        self.current_page = page_number
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.current_page not in self.elements or not self.curr_pixmap:
            return
            
        # Only get elements for current page
        current_page_elements = [
            element for element in self.elements[self.current_page] 
            if element.get('page', self.current_page) == self.current_page
        ]
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Use a smaller font for labels
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        for element in current_page_elements:
            if 'coordinates' not in element:
                continue

               
            coords = element['coordinates']
            x = int(coords[0]['x'] * self.orig_pixmap.width())
            y = int(coords[0]['y'] * self.orig_pixmap.height())
            width = int((coords[2]['x'] - coords[0]['x']) * self.orig_pixmap.width())
            height = int((coords[2]['y'] - coords[0]['y']) * self.orig_pixmap.height())
            
            rect = QRect(x, y, width, height)
            canvas_rect = self.rect_to_canvas(rect)
            
            if self.show_boxes:
                # Get color based on category
                category = element.get('category', 'default')
                color = self.category_colors.get(category, self.category_colors['default'])
                
                # Draw bounding box
                painter.setPen(QPen(color, 2))
                painter.drawRect(canvas_rect)
                
                # Draw label background
                label_text = category
                metrics = painter.fontMetrics()
                label_width = metrics.horizontalAdvance(label_text) + 4
                label_height = metrics.height() + 2
                label_rect = QRect(
                    canvas_rect.left(),
                    canvas_rect.top() - label_height,
                    label_width,
                    label_height
                )
                
                # Ensure label is visible within the viewport
                if label_rect.top() < 0:
                    label_rect.moveTop(canvas_rect.top())
                
                # Draw label background
                painter.fillRect(label_rect, QColor(255, 255, 255, 200))
                painter.setPen(QPen(color.darker(150)))
                painter.drawRect(label_rect)
                
                # Draw label text
                painter.setPen(Qt.black)
                painter.drawText(label_rect, Qt.AlignCenter, label_text)
            
            if self.show_text and 'content' in element and element['content'].get('text'):
                text = element['content']['text']
                painter.setPen(Qt.black)
                text_rect = painter.fontMetrics().boundingRect(canvas_rect, Qt.TextWordWrap, text)
                painter.fillRect(text_rect, QColor(255, 255, 255, 180))
                painter.drawText(canvas_rect, Qt.TextWordWrap, text)

        
class UpstageClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.ssl_verification_disabled = False
        self.client = self._create_client()

    def _create_client(self):
        if self.ssl_verification_disabled:
            return httpx.Client(verify=False, follow_redirects=True)  # Add follow_redirects=True
        return httpx.Client(follow_redirects=True)  # Add follow_redirects=True

    def post(self, url, files=None, data=None):
        try:
            print("Posting to URL:", url, files, data)  # Debug print
            response = self.client.post(url, headers=self.headers, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.TransportError as e:
            logger.warning(f"Transport error occurred: {e}. Disabling SSL verification.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.post(url, files=files, data=data)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

    def get(self, url):
        try:
            print("Getting URL:", url)  # Debug print
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.TransportError as e:
            logger.warning(f"Transport error occurred: {e}. Disabling SSL verification.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.get(url)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

class AsyncWorker(QThread):
    finished = pyqtSignal(list)  # Changed to emit list of results
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, client, request_id):
        super().__init__()
        self.client = client
        self.request_id = request_id
        
    def run(self):
        try:
            url = f"https://api.upstage.ai/v1/document-ai/requests/{self.request_id}"
            
            while True:
                data = self.client.get(url)
                
                if data["status"] == "completed":
                    # Collect results from all batches
                    results = []
                    for batch in data["batches"]:
                        batch_result = self.client.get(batch["download_url"])
                        # Store page range information with results
                        results.append({
                            'start_page': batch['start_page'],
                            'end_page': batch['end_page'],
                            'result': batch_result
                        })
                    self.finished.emit(results)
                    break
                elif data["status"] == "failed":
                    self.error.emit(f"Processing failed: {data.get('failure_message', 'Unknown error')}")
                    break
                    
                progress_msg = (
                    f"Processing... Status: {data['status']}\n"
                    f"Completed pages: {data.get('completed_pages', 0)} / {data.get('total_pages', '?')}"
                )
                self.progress.emit(progress_msg)
                time.sleep(2)
                
        except Exception as e:
            self.error.emit(str(e))

def handle_error(func):
    """Decorator for consistent error handling."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.progress_bar.setVisible(False)
    return wrapper

# Modify the handle_error decorator (outside the class) to:
def handle_error(func):
    """Decorator for consistent error handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # Remove self from the wrapper parameters
        try:
            return func(*args, **kwargs)  # Pass all arguments as is
        except Exception as e:
            # Get self from args[0] since it's the first argument for class methods
            self = args[0]
            QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.progress_bar.setVisible(False)
    return wrapper

class UpstageDocParseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize instance variables
        self.async_worker = None
        self.upstage_client = None
        self.pdf_document = None
        self.current_page = 1
        self.total_pages = 1
        self.processed_results = {}  # Store results for each page
        
        # Initialize UI
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Upstage Document Parse')
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)  # Reduce spacing between elements
        
        # Top controls section - use horizontal layout
        top_controls = QHBoxLayout()
        
        # Left side controls group
        left_controls = QVBoxLayout()
        
        # API key input - horizontal group
        api_layout = QHBoxLayout()
        api_label = QLabel('API Key:')
        api_label.setFixedWidth(50)  # Fixed width for alignment
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        
        # File selection - horizontal group
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText('Select a file...')
        browse_button = QPushButton('Browse')
        browse_button.setFixedWidth(70)  # Fixed width for the button
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_button)
        
        left_controls.addLayout(api_layout)
        left_controls.addLayout(file_layout)
        
        # Add left controls to top controls
        top_controls.addLayout(left_controls, stretch=1)
        
        # Right side controls
        right_controls = QVBoxLayout()
        
        # PDF Navigation Controls in horizontal layout
        self.pdf_controls = QWidget()
        pdf_controls_layout = QHBoxLayout(self.pdf_controls)
        pdf_controls_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        self.pdf_first_button = QPushButton("<<")
        self.pdf_prev_button = QPushButton("<")
        self.page_spinner = QSpinBox()
        self.pdf_next_button = QPushButton(">")
        self.pdf_last_button = QPushButton(">>")
        
        for button in [self.pdf_first_button, self.pdf_prev_button, 
                    self.pdf_next_button, self.pdf_last_button]:
            button.setFixedWidth(30)
            pdf_controls_layout.addWidget(button)
            
        self.page_spinner.setPrefix("Page ")
        self.page_spinner.setSuffix(" / 1")
        self.page_spinner.setRange(1, 1)
        pdf_controls_layout.addWidget(self.page_spinner)
        
        # Radio button groups
        radio_layout = QHBoxLayout()
        
        # API Type group
        api_type_group = QGroupBox("API Type")
        api_type_layout = QHBoxLayout(api_type_group)
        api_button_group = QButtonGroup(self)
        self.sync_radio = QRadioButton("Synchronous")
        self.async_radio = QRadioButton("Asynchronous")
        api_button_group.addButton(self.sync_radio)
        api_button_group.addButton(self.async_radio)
        self.sync_radio.setChecked(True)
        api_type_layout.addWidget(self.sync_radio)
        api_type_layout.addWidget(self.async_radio)
        
        # Process Type group
        process_type_group = QGroupBox("Process Type")
        process_type_layout = QHBoxLayout(process_type_group)
        process_button_group = QButtonGroup(self)
        self.process_current_page = QRadioButton("Current Page")
        self.process_all_pages = QRadioButton("All Pages")
        process_button_group.addButton(self.process_current_page)
        process_button_group.addButton(self.process_all_pages)
        self.process_current_page.setChecked(True)
        process_type_layout.addWidget(self.process_current_page)
        process_type_layout.addWidget(self.process_all_pages)
        
        radio_layout.addWidget(api_type_group)
        radio_layout.addWidget(process_type_group)
        
        # Process button
        process_button = QPushButton('Process Document')
        
        right_controls.addWidget(self.pdf_controls)
        right_controls.addLayout(radio_layout)
        right_controls.addWidget(process_button)
        
        # Add right controls to top controls
        top_controls.addLayout(right_controls)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Document display
        self.document_label = DocumentLabel()
        self.document_label.text_selected.connect(self.showSelectedText)
        
        right_panel = QSplitter(Qt.Vertical)
        
        # JSON output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumWidth(400)  # Limit width of JSON panel
        
        # Selected text display
        text_group = QGroupBox("Selected Text")
        text_layout = QVBoxLayout(text_group)
        self.selected_text = QTextEdit()
        self.selected_text.setReadOnly(True)
        text_layout.addWidget(self.selected_text)
        
        right_panel.addWidget(self.output_text)
        right_panel.addWidget(text_group)
                
        content_layout.addWidget(self.document_label, stretch=1)
        content_layout.addWidget(right_panel)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add all layouts to main layout
        main_layout.addLayout(top_controls)
        main_layout.addLayout(content_layout, stretch=1)
        main_layout.addWidget(self.progress_bar)
        
        # Connect signals
        browse_button.clicked.connect(self.browseFiles)
        self.pdf_first_button.clicked.connect(self.goToFirstPage)
        self.pdf_prev_button.clicked.connect(self.goToPrevPage)
        self.page_spinner.valueChanged.connect(self.goToPage)
        self.pdf_next_button.clicked.connect(self.goToNextPage)
        self.pdf_last_button.clicked.connect(self.goToLastPage)
        #process_button.clicked.connect(self.processDocument)
        process_button.clicked.connect(lambda: self.processDocument())
        
        # Hide PDF controls initially
        self.pdf_controls.setVisible(False)

    @contextmanager
    def show_progress(self):
        """Context manager for progress bar visibility."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            yield
        finally:
            self.progress_bar.setVisible(False)
            
    def ensure_client(self):
        """Ensure UpstageClient is initialized."""
        if not self.upstage_client:
            api_key = self.api_key_input.text()
            if not api_key:
                QMessageBox.warning(self, 'Error', 'Please enter your API key.')
                return False
            self.upstage_client = UpstageClient(api_key)
        return True
        
    def validate_navigation(self, new_page):
        """Validate page navigation."""
        return (self.pdf_document and 
                1 <= new_page <= self.total_pages)


    def showSelectedText(self, text):
        #print("show selected text")
        print("showSelectedText called with:", text[:50] + "...")  # Debug print

        self.selected_text.setHtml(text)
        # Optional: highlight or scroll to make it visible
        self.selected_text.setFocus()
        
    def browseFiles(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "Documents (*.pdf *.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_name:
            self.file_path.setText(file_name)
            self.loadDocument(file_name)

    @handle_error
    def processDocument(self):
        if not self.ensure_client():
            return
            
        if self.process_all_pages.isChecked() and self.pdf_document:
            self.processAllPages()
        else:
            self.processCurrentPage()


    @handle_error
    def processAllPages(self):
        if not self.pdf_document or not self.ensure_client():
            return
            
        with self.show_progress():
            url = "https://api.upstage.ai/v1/document-ai/async/document-parse"
            file_path = self.file_path.text()
            files = {"document": open(file_path, "rb")}
            data = {"ocr": True}
            
            self.output_text.setText("Initiating document processing...")
            result = self.upstage_client.post(url, files=files, data=data)
            
            if "request_id" not in result:
                QMessageBox.critical(self, 'Error', 'Failed to get request ID')
                return
                
            self.async_worker = AsyncWorker(self.upstage_client, result["request_id"])
            self.async_worker.finished.connect(self.handleBatchResults)
            self.async_worker.progress.connect(self.handleProgress)
            self.async_worker.error.connect(self.handleError)
            self.async_worker.start()


    def handleBatchResults(self, batch_results):
        self.progress_bar.setVisible(False)
        
        # Process each batch
        for batch in batch_results:
            result = batch['result']
            
            # Group elements by page
            if 'elements' in result:
                page_elements = {}
                for element in result['elements']:
                    if 'page' in element:
                        page_num = element['page']
                        if page_num not in page_elements:
                            page_elements[page_num] = []
                        page_elements[page_num].append(element)
                
                # Store grouped elements
                self.processed_results.update(page_elements)
        
        # Update display for current page
        self.loadPdfPage(self.current_page)
        
        # Update JSON display
        self.output_text.setText(
            f"Processing complete. Results stored for pages: {sorted(self.processed_results.keys())}\n\n" +
            self.formatJson(self.processed_results.get(self.current_page, []))
        )

    def clearDocument(self):
        if self.pdf_document:
            self.pdf_document.close()
        self.pdf_document = None
        self.current_page = 1
        self.total_pages = 1
        self.processed_results.clear()
        self.document_label.clear()
        self.document_label.elements.clear()  # Clear the elements dictionary
        self.output_text.clear()
        self.selected_text.clear()  # Clear the selected text as well
        self.pdf_controls.setVisible(False)
        self.page_spinner.setRange(1, 1)
        self.page_spinner.setSuffix(" / 1")

    def loadDocument(self, file_path):
        try:
            self.clearDocument()
            
            if file_path.lower().endswith('.pdf'):
                self.pdf_document = fitz.open(file_path)
                self.total_pages = len(self.pdf_document)
                self.current_page = 1
                self.page_spinner.setRange(1, self.total_pages)
                self.page_spinner.setSuffix(f" / {self.total_pages}")
                self.pdf_controls.setVisible(True)
                self.loadPdfPage(self.current_page)
            else:
                self.pdf_document = None
                self.pdf_controls.setVisible(False)
                self.document_label.set_figure(file_path)
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load document: {str(e)}')
            self.clearDocument()

    def loadPdfPage(self, page_number):
        if not self.pdf_document:
            return
                
        try:
            page = self.pdf_document[page_number - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = QImage(pix.samples, pix.width, pix.height, 
                        pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.document_label.set_pixmap(pixmap)
            self.document_label.current_page = page_number
            
            if page_number in self.processed_results:
                self.document_label.set_elements(self.processed_results[page_number], page_number)
                self.output_text.setText(self.formatJson(self.processed_results[page_number]))
                
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load page {page_number}: {str(e)}')

    def goToFirstPage(self):
        if self.validate_navigation(1):
            self.page_spinner.setValue(1)
        
    def goToPrevPage(self):
        if self.validate_navigation(self.current_page - 1):
            self.page_spinner.setValue(self.current_page - 1)
        
    def goToNextPage(self):
        if self.validate_navigation(self.current_page + 1):
            self.page_spinner.setValue(self.current_page + 1)
        
    def goToLastPage(self):
        if self.validate_navigation(self.total_pages):
            self.page_spinner.setValue(self.total_pages)
        
    def goToPage(self, page_number):
        if self.validate_navigation(page_number):
            self.current_page = page_number
            self.loadPdfPage(page_number)

    def closeEvent(self, event):
        self.clearDocument()
        super().closeEvent(event)

    def handleResult(self, result, page_number=None):
        self.output_text.setText(self.formatJson(result))
        
        if 'elements' in result:
            if page_number is None:
                page_number = self.current_page
            self.processed_results[page_number] = result['elements']
            self.document_label.set_elements(result['elements'], page_number)

    def processSynchronous(self, file_path, page_number=None):
        url = "https://api.upstage.ai/v1/document-ai/document-parse"
        files = {"document": open(file_path, "rb")}

        self.output_text.setText("Processing document...")
        result = self.upstage_client.post(url, files=files)
        #result = self.upstage_client.post(url, data=data)
        self.handleResult(result, page_number)
        
    def processAsynchronous(self, file_path, page_number=None):
        url = "https://api.upstage.ai/v1/document-ai/async/document-parse"
        files = {"document": open(file_path, "rb")}
        data = {"ocr": True}
        
        self.output_text.setText("Initiating async processing...")
        result = self.upstage_client.post(url, files=files, data=data)
        
        if "request_id" not in result:
            QMessageBox.critical(self, 'Error', 'Failed to get request ID')
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.async_worker = AsyncWorker(self.upstage_client, result["request_id"])
        self.async_worker.finished.connect(lambda result: self.handleAsyncResult(result, page_number))
        self.async_worker.progress.connect(self.handleProgress)
        self.async_worker.error.connect(self.handleError)
        self.async_worker.start()

    def handleAsyncResult(self, result, page_number=None):
        self.progress_bar.setVisible(False)
        self.handleResult(result, page_number)
        
    def handleProgress(self, message):
        self.output_text.setText(message)
        
    def handleError(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Error', error_message)

    def processCurrentPage(self):
        if not self.upstage_client:
            # Create or update client if API key changed
            api_key = self.api_key_input.text()
            if not api_key:
                QMessageBox.warning(self, 'Error', 'Please enter your API key.')
                return
            self.upstage_client = UpstageClient(api_key)

        # Create temporary file for PDF page if needed
        temp_path = None
        try:
            if self.pdf_document:
                # Save current page as temporary image
                page = self.pdf_document[self.current_page - 1]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                temp_path = f"temp_page_{self.current_page}.png"
                pix.save(temp_path)
                file_path = temp_path
            else:
                file_path = self.file_path.text()
                if not file_path or not os.path.exists(file_path):
                    QMessageBox.warning(self, 'Error', 'Please select a valid file.')
                    return

            # Process the page
            if self.sync_radio.isChecked():
                self.processSynchronous(file_path, self.current_page)
            else:
                self.processAsynchronous(file_path, self.current_page)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass



    def formatJson(self, data):
        return json.dumps(data, indent=2, ensure_ascii=False)



def main():
    app = QApplication(sys.argv)
    ex = UpstageDocParseApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()