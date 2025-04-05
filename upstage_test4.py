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
import hashlib
from contextlib import contextmanager
import functools
from FgComponents import FigureLabel
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
                           QTextEdit, QLabel, QMessageBox, QProgressBar, QGroupBox,
                           QRadioButton, QButtonGroup, QSplitter, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QSettings
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('upstage_app.log')
    ]
)
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
        logger.debug("handleElementClick called")
        """Handle clicks on text elements"""
        if self.current_page not in self.elements:
            logger.debug("No elements for current page")
            return False
    
        logger.debug("Checking elements for current page")

        # Convert click position to image coordinates
        img_x = self._2imgx(pos.x())
        img_y = self._2imgy(pos.y())
        
        # Check each element for intersection
        for element in self.elements[self.current_page]:
            if 'coordinates' not in element:
                continue

            logger.debug("Checking element: %s", element['category'])           
                
            coords = element['coordinates']
            logger.debug("Element coordinates: %s", coords)
            x = int(coords[0]['x'] * self.orig_pixmap.width())
            y = int(coords[0]['y'] * self.orig_pixmap.height())
            width = int((coords[2]['x'] - coords[0]['x']) * self.orig_pixmap.width())
            height = int((coords[2]['y'] - coords[0]['y']) * self.orig_pixmap.height())

            logger.debug("Element bounds: %s, %s, %s, %s", x, y, width, height)
            logger.debug("Click position: %s, %s", img_x, img_y)
            
            # Check if click is within element bounds
            if (x <= img_x <= x + width and y <= img_y <= y + height):
                logger.debug("Click is within element bounds: %s", element)
                if 'content' in element and element['content'].get('html'):
                    logger.debug("Found text element")
                    text = (f"Type: {element['category']}\n\n"
                           f"Coordinates: ({x}, {y}, {width}, {height})\n\n"
                           f"Content:\n{element['content']['html']}")
                    
                    html_content = element['content']['html']
                    logger.debug("HTML content: %s", html_content)
                    # Remove HTML tags (simple method)
                    plain_text = html_content.replace('<br>', '\n')  # Convert <br> to newlines first
                    # Remove all other HTML tags
                    plain_text = re.sub(r'<[^>]+>', '', plain_text)
                    # Fix any HTML entities
                    plain_text = html.unescape(plain_text)
                    logger.debug("text content: %s", plain_text)
                    
                    text = plain_text #(f"Type: {element['category']}\n\n"f"Content:\n{plain_text}")

                    logger.debug("Emitting text_selected signal: %s...", text[:50])
                    self.text_selected.emit(text)
                    return True  # Handled the click
        return False  # Did not handle the click

    def mousePressEvent(self, event):
        logger.debug("mouse press event")
        if event.button() == Qt.LeftButton:
            logger.debug("left button")
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

    def clear_page_elements(self, page_number):
        """Clear elements for a specific page."""
        if page_number in self.elements:
            del self.elements[page_number]
            self.repaint()

    def set_elements(self, elements, page_number=1):
        """Set elements for a specific page."""
        logger.debug("=== Setting Elements in DocumentLabel ===")
        try:
            logger.debug("Setting %d elements for page %d", len(elements), page_number)
            self.elements[page_number] = elements
            self.current_page = page_number  # Update current page when setting elements
            logger.debug("Elements stored, triggering repaint")
            self.repaint()
        except Exception as e:
            logger.error("Error in set_elements: %s", str(e))
            logger.error("Element data: %s", elements)
            raise

    def paintEvent(self, event):
        try:
            # Clear the canvas first
            clear_painter = QPainter(self)
            if clear_painter.isActive():
                clear_painter.fillRect(self.rect, QColor(Qt.white))
                clear_painter.end()
            
            # Draw the base image
            super().paintEvent(event)
            
            if self.current_page not in self.elements or not self.curr_pixmap:
                return
                
            # Only get elements for current page
            current_page_elements = self.elements[self.current_page]
            
            for i, element in enumerate(current_page_elements):
                try:
                    if 'coordinates' not in element:
                        continue

                    try:
                        coords = element['coordinates']
                        
                        # Validate coordinates
                        if not all(isinstance(c, dict) and 'x' in c and 'y' in c for c in coords):
                            continue
                            
                        x = int(coords[0]['x'] * self.orig_pixmap.width())
                        y = int(coords[0]['y'] * self.orig_pixmap.height())
                        width = int((coords[2]['x'] - coords[0]['x']) * self.orig_pixmap.width())
                        height = int((coords[2]['y'] - coords[0]['y']) * self.orig_pixmap.height())
                        
                        # Validate dimensions
                        if width <= 0 or height <= 0:
                            continue
                            
                        rect = QRect(x, y, width, height)
                        canvas_rect = self.rect_to_canvas(rect)
                    except Exception as e:
                        continue
                    
                    if self.show_boxes:
                        try:
                            # Create a new painter for the bounding box
                            box_painter = QPainter(self)
                            if not box_painter.isActive():
                                continue
                                
                            box_painter.setRenderHint(QPainter.Antialiasing)
                            
                            # Get color based on category
                            category = element.get('category', 'default')
                            color = self.category_colors.get(category, self.category_colors['default'])
                            
                            # Create and set pen
                            pen = QPen(color, 2)
                            box_painter.setPen(pen)
                            
                            # Draw rectangle
                            box_painter.drawRect(canvas_rect)
                            box_painter.end()
                            
                        except Exception as e:
                            if 'box_painter' in locals() and box_painter.isActive():
                                box_painter.end()
                            continue
                            
                        # Draw label with separate painter
                        try:
                            label_painter = QPainter(self)
                            if not label_painter.isActive():
                                continue
                                
                            label_painter.setRenderHint(QPainter.Antialiasing)
                            
                            # Prepare label
                            label_text = category
                            font = label_painter.font()
                            font.setPointSize(8)
                            label_painter.setFont(font)
                            
                            metrics = label_painter.fontMetrics()
                            label_width = metrics.horizontalAdvance(label_text) + 4
                            label_height = metrics.height() + 2
                            
                            label_rect = QRect(
                                canvas_rect.left(),
                                canvas_rect.top() - label_height,
                                label_width,
                                label_height
                            )
                            
                            if label_rect.top() < 0:
                                label_rect.moveTop(canvas_rect.top())
                            
                            # Draw label
                            label_painter.fillRect(label_rect, QColor(255, 255, 255, 200))
                            label_painter.setPen(QPen(color.darker(150)))
                            label_painter.drawRect(label_rect)
                            label_painter.setPen(Qt.black)
                            label_painter.drawText(label_rect, Qt.AlignCenter, label_text)
                            
                            label_painter.end()
                            
                        except Exception as e:
                            if 'label_painter' in locals() and label_painter.isActive():
                                label_painter.end()
                            continue
                    
                    if self.show_text and 'content' in element and element['content'].get('text'):
                        try:
                            # Create a new painter for text
                            text_painter = QPainter(self)
                            if not text_painter.isActive():
                                continue
                                
                            text_painter.setRenderHint(QPainter.Antialiasing)
                            
                            # Draw text
                            text = element['content']['text']
                            text_painter.setPen(Qt.black)
                            text_rect = text_painter.fontMetrics().boundingRect(canvas_rect, Qt.TextWordWrap, text)
                            text_painter.fillRect(text_rect, QColor(255, 255, 255, 180))
                            text_painter.drawText(canvas_rect, Qt.TextWordWrap, text)
                            
                            text_painter.end()
                            
                        except Exception as e:
                            if 'text_painter' in locals() and text_painter.isActive():
                                text_painter.end()
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error("Error in paintEvent: %s", str(e))
            logger.error("Full error details:", exc_info=True)

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
            # Log request details
            logger.debug("=== Request Details ===")
            logger.debug("URL: %s", url)
            logger.debug("Headers: %s", {k: '***' if k == 'Authorization' else v for k, v in self.headers.items()})
            if files:
                logger.debug("Files: %s", {k: f"<file: {v.name}>" for k, v in files.items()})
            if data:
                logger.debug("Data: %s", data)
            
            response = self.client.post(url, headers=self.headers, files=files, data=data)
            response.raise_for_status()
            
            # Log response details
            logger.debug("=== Response Details ===")
            logger.debug("Status Code: %d", response.status_code)
            logger.debug("Headers: %s", dict(response.headers))
            response_data = response.json()
            logger.debug("Response Data: %s", json.dumps(response_data, indent=2))
            
            return response_data
        except httpx.TransportError as e:
            logger.warning(f"Transport error occurred: {e}. Disabling SSL verification.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.post(url, files=files, data=data)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            if e.response:
                logger.error("Error Response: %s", e.response.text)
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

    def get(self, url):
        try:
            # Log request details
            logger.debug("=== Request Details ===")
            logger.debug("URL: %s", url)
            logger.debug("Headers: %s", {k: '***' if k == 'Authorization' else v for k, v in self.headers.items()})
            
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Log response details
            logger.debug("=== Response Details ===")
            logger.debug("Status Code: %d", response.status_code)
            logger.debug("Headers: %s", dict(response.headers))
            response_data = response.json()
            logger.debug("Response Data: %s", json.dumps(response_data, indent=2))
            
            return response_data
        except httpx.TransportError as e:
            logger.warning(f"Transport error occurred: {e}. Disabling SSL verification.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.get(url)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            if e.response:
                logger.error("Error Response: %s", e.response.text)
            raise
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
        self.page_elements = {}  # Store structured data for each page
        self.current_file_path = None
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".upstage_cache")
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Initialize settings
        self.settings = QSettings("PaleoBytes", "UpstageDocParse")
        
        # Initialize UI
        self.initUI()
        
        # Load saved settings
        self.loadSettings()

    def get_cache_file_path(self, file_path):
        """Generate a cache file path based on the document path."""
        # Use the same directory as the PDF file
        directory = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return os.path.join(directory, f"{base_name}_cache.json")

    def save_document_cache(self):
        """Save current document processing results to cache file."""
        if not self.current_file_path or not self.page_elements:
            return
            
        cache_file = self.get_cache_file_path(self.current_file_path)
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'file_path': self.current_file_path,
                    'page_elements': self.page_elements,
                    'total_pages': self.total_pages,
                    'last_modified': os.path.getmtime(self.current_file_path)
                }, f, indent=2)
            logger.debug(f"Saved document cache to {cache_file}")
        except Exception as e:
            logger.error(f"Failed to save document cache: {e}")

    def load_document_cache(self, file_path):
        """Load document processing results from cache file."""
        cache_file = self.get_cache_file_path(file_path)
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if the file hasn't been modified since caching
                if (cache_data['file_path'] == file_path and 
                    cache_data['last_modified'] == os.path.getmtime(file_path)):
                    self.page_elements = cache_data['page_elements']
                    self.total_pages = cache_data['total_pages']
                    logger.debug(f"Loaded document cache from {cache_file}")
                    return True
        except Exception as e:
            logger.error(f"Failed to load document cache: {e}")
        return False

    def get_document_info_file_path(self, file_path):
        """Generate a document info file path based on the document path."""
        # Use the same directory as the PDF file
        directory = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return os.path.join(directory, f"{base_name}.json")

    def save_document_info(self):
        """Save all document information to a single file."""
        if not self.current_file_path:
            return
            
        try:
            info_file = self.get_document_info_file_path(self.current_file_path)
            
            # Create document info structure
            document_info = {
                'document': {
                    'file_path': self.current_file_path,
                    'total_pages': self.total_pages,
                    'current_page': self.current_page,
                    'last_modified': os.path.getmtime(self.current_file_path)
                },
                'pages': {}
            }
            
            # Add page elements and structure
            for page_num, elements in self.page_elements.items():
                page_info = {
                    'page_number': page_num,
                    'total_pages': self.total_pages,
                    'elements': elements,
                    'timestamp': time.time()
                }
                document_info['pages'][str(page_num)] = page_info
            
            # Save updated info
            with open(info_file, 'w') as f:
                json.dump(document_info, f, indent=2)
            logger.debug(f"Saved document info to {info_file}")
        except Exception as e:
            logger.error(f"Failed to save document info: {e}")

    def load_document_info(self, file_path):
        """Load all document information from file."""
        info_file = self.get_document_info_file_path(file_path)
        
        logger.debug("=== Loading Document Info ===")
        logger.debug("Info file path: %s", info_file)
        
        try:
            if os.path.exists(info_file):
                logger.debug("Info file exists, attempting to load...")
                with open(info_file, 'r') as f:
                    info = json.load(f)
                
                # Check if the file hasn't been modified since caching
                file_mtime = os.path.getmtime(file_path)
                info_mtime = info['document']['last_modified']
                logger.debug("File modification times - Document: %s, Info: %s", file_mtime, info_mtime)
                
                if info_mtime == file_mtime:
                    logger.debug("Document hasn't been modified since last save")
                    # Update document info
                    self.total_pages = info['document']['total_pages']
                    self.current_page = info['document']['current_page']
                    logger.debug("Loaded document info - Total pages: %d, Current page: %d", 
                               self.total_pages, self.current_page)
                    
                    # Update page elements
                    self.page_elements.clear()
                    for page_num, page_info in info['pages'].items():
                        self.page_elements[int(page_num)] = page_info['elements']
                    
                    logger.debug("Loaded elements for pages: %s", list(self.page_elements.keys()))
                    logger.debug("Number of pages with elements: %d", len(self.page_elements))
                    return True
                else:
                    logger.debug("Document has been modified since last save")
                    logger.debug("Document modification time: %s", file_mtime)
                    logger.debug("Info file modification time: %s", info_mtime)
            else:
                logger.debug("No document info file found at: %s", info_file)
        except Exception as e:
            logger.error("Error loading document info: %s", str(e))
            logger.error("Full error details:", exc_info=True)
        return False

    def loadSettings(self):
        """Load saved settings from QSettings."""
        api_key = self.settings.value("api_key", "")
        if api_key:
            self.api_key_input.setText(api_key)
            self.upstage_client = UpstageClient(api_key)

    def saveSettings(self):
        """Save current settings to QSettings."""
        self.settings.setValue("api_key", self.api_key_input.text())

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
        
        # Create a horizontal splitter for the main content
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Add document label to the left side
        main_splitter.addWidget(self.document_label)
        
        # Create right panel with vertical splitter
        right_panel = QSplitter(Qt.Vertical)
        
        # JSON output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumWidth(300)  # Set minimum width instead of maximum
        
        # Selected text display
        text_group = QGroupBox("Selected Text")
        text_layout = QVBoxLayout(text_group)
        self.selected_text = QTextEdit()
        self.selected_text.setReadOnly(True)
        text_layout.addWidget(self.selected_text)
        
        # Add widgets to right panel
        right_panel.addWidget(self.output_text)
        right_panel.addWidget(text_group)
        
        # Add right panel to main splitter
        main_splitter.addWidget(right_panel)
        
        # Set initial sizes for the splitters
        main_splitter.setSizes([800, 400])  # Document area gets more space
        right_panel.setSizes([200, 400])    # Selected text gets more space than JSON
        
        # Add the main splitter to the content layout
        content_layout.addWidget(main_splitter)
        
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
            self.saveSettings()  # Save the API key when it's first used
        return True
        
    def validate_navigation(self, new_page):
        """Validate page navigation."""
        return (self.pdf_document and 
                1 <= new_page <= self.total_pages)


    def showSelectedText(self, text):
        logger.debug("showSelectedText called with: %s...", text[:50])
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
        try:
            logger.debug("=== Starting Batch Results Processing ===")
            logger.debug("Number of batches: %d", len(batch_results))
            
            self.progress_bar.setVisible(False)
            
            # Process each batch
            for i, batch in enumerate(batch_results):
                logger.debug("Processing batch %d/%d", i + 1, len(batch_results))
                logger.debug("Batch range: %d-%d", batch['start_page'], batch['end_page'])
                
                try:
                    result = batch['result']
                    logger.debug("Batch result keys: %s", result.keys() if isinstance(result, dict) else "Not a dictionary")
                    
                    # Group elements by page
                    if 'elements' in result:
                        page_elements = {}
                        for j, element in enumerate(result['elements']):
                            try:
                                logger.debug("Processing element %d/%d", j + 1, len(result['elements']))
                                if 'page' in element:
                                    page_num = element['page']
                                    if page_num not in page_elements:
                                        page_elements[page_num] = []
                                    page_elements[page_num].append(element)
                            except Exception as e:
                                logger.error("Error processing element %d: %s", j, str(e))
                                logger.error("Element data: %s", element)
                                raise
                        
                        logger.debug("Grouped elements by page: %s", list(page_elements.keys()))
                        
                        # Store grouped elements in both dictionaries
                        self.processed_results.update(page_elements)
                        self.page_elements.update(page_elements)  # Update page_elements
                        
                        # Save document info after each batch
                        self.save_document_info()
                    else:
                        logger.warning("No 'elements' key found in batch result")
                except Exception as e:
                    logger.error("Error processing batch %d: %s", i, str(e))
                    logger.error("Batch data: %s", batch)
                    raise
            
            # Update display for current page
            try:
                logger.debug("Updating display for page %d", self.current_page)
                self.loadPdfPage(self.current_page)
                logger.debug("Display updated successfully")
            except Exception as e:
                logger.error("Error updating display: %s", str(e))
                raise
            
            # Update JSON display
            try:
                current_page_elements = self.page_elements.get(self.current_page, [])
                logger.debug("Updating JSON display with %d elements", len(current_page_elements))
                self.output_text.setText(
                    f"Processing complete. Results stored for pages: {sorted(self.page_elements.keys())}\n\n" +
                    self.formatJson(current_page_elements)
                )
                logger.debug("JSON display updated successfully")
            except Exception as e:
                logger.error("Error updating JSON display: %s", str(e))
                raise
                
        except Exception as e:
            logger.error("Fatal error in handleBatchResults: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            QMessageBox.critical(self, 'Error', f'An error occurred while processing results: {str(e)}')
            self.progress_bar.setVisible(False)

    def handleResult(self, result, page_number=None):
        logger.debug("=== Handling Processing Result ===")
        try:
            logger.debug("Formatting result for display")
            self.output_text.setText(self.formatJson(result))
            
            if 'elements' in result:
                if page_number is None:
                    page_number = self.current_page
                logger.debug("Processing elements for page %d", page_number)
                
                try:
                    logger.debug("Number of elements to process: %d", len(result['elements']))
                    self.processed_results[page_number] = result['elements']
                    self.page_elements[page_number] = result['elements']  # Store in page_elements
                    
                    # Save document info
                    self.save_document_info()
                    
                    logger.debug("Setting elements in document label")
                    self.document_label.set_elements(result['elements'], page_number)
                    logger.debug("Successfully processed %d elements", len(result['elements']))
                except Exception as e:
                    logger.error("Error processing elements: %s", str(e))
                    logger.error("Element data: %s", result['elements'])
                    raise
            else:
                logger.warning("No elements found in result")
        except Exception as e:
            logger.error("Error in handleResult: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            raise

    def processCurrentPage(self):
        logger.debug("=== Starting Single Page Processing ===")
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
            logger.debug("Processing page %d", self.current_page)
            
            if self.pdf_document:
                logger.debug("Saving current page as temporary image")
                # Save current page as temporary image
                page = self.pdf_document[self.current_page - 1]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                temp_path = f"temp_page_{self.current_page}.png"
                pix.save(temp_path)
                file_path = temp_path
                logger.debug("Temporary file created: %s", temp_path)
            else:
                file_path = self.file_path.text()
                if not file_path or not os.path.exists(file_path):
                    QMessageBox.warning(self, 'Error', 'Please select a valid file.')
                    return
                logger.debug("Using original file: %s", file_path)

            # Process the page
            logger.debug("Starting page processing (sync=%s)", self.sync_radio.isChecked())
            if self.sync_radio.isChecked():
                self.processSynchronous(file_path, self.current_page)
            else:
                self.processAsynchronous(file_path, self.current_page)

        except Exception as e:
            logger.error("Error in processCurrentPage: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            QMessageBox.critical(self, 'Error', f'An error occurred while processing the page: {str(e)}')
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    logger.debug("Cleaning up temporary file: %s", temp_path)
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning("Failed to remove temporary file: %s", str(e))

    def processSynchronous(self, file_path, page_number=None):
        logger.debug("=== Starting Synchronous Processing ===")
        url = "https://api.upstage.ai/v1/document-ai/document-parse"
        files = {"document": open(file_path, "rb")}
        logger.debug("Sending request for page %s", page_number)

        try:
            self.output_text.setText("Processing document...")
            result = self.upstage_client.post(url, files=files)
            logger.debug("Received synchronous response")
            self.handleResult(result, page_number)
        except Exception as e:
            logger.error("Error in processSynchronous: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            raise
        finally:
            files["document"].close()

    def processAsynchronous(self, file_path, page_number=None):
        logger.debug("=== Starting Asynchronous Processing ===")
        url = "https://api.upstage.ai/v1/document-ai/async/document-parse"
        files = {"document": open(file_path, "rb")}
        data = {"ocr": True}
        
        try:
            logger.debug("Sending async request for page %s", page_number)
            self.output_text.setText("Initiating async processing...")
            result = self.upstage_client.post(url, files=files, data=data)
            
            if "request_id" not in result:
                logger.error("No request_id in response: %s", result)
                QMessageBox.critical(self, 'Error', 'Failed to get request ID')
                return
                
            logger.debug("Got request_id: %s", result["request_id"])
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.async_worker = AsyncWorker(self.upstage_client, result["request_id"])
            self.async_worker.finished.connect(lambda result: self.handleAsyncResult(result, page_number))
            self.async_worker.progress.connect(self.handleProgress)
            self.async_worker.error.connect(self.handleError)
            self.async_worker.start()
        except Exception as e:
            logger.error("Error in processAsynchronous: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            raise
        finally:
            files["document"].close()

    def handleAsyncResult(self, result, page_number=None):
        self.progress_bar.setVisible(False)
        self.handleResult(result, page_number)
        
    def handleProgress(self, message):
        self.output_text.setText(message)
        
    def handleError(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Error', error_message)

    def formatJson(self, data):
        return json.dumps(data, indent=2, ensure_ascii=False)

    def clearDocument(self):
        if self.pdf_document:
            self.pdf_document.close()
        self.pdf_document = None
        self.current_page = 1
        self.total_pages = 1
        self.processed_results.clear()
        self.page_elements.clear()  # Clear the page elements dictionary
        self.current_file_path = None
        self.document_label.clear()
        self.document_label.elements.clear()  # Clear the elements dictionary
        self.output_text.clear()
        self.selected_text.clear()  # Clear the selected text as well
        self.pdf_controls.setVisible(False)
        self.page_spinner.setRange(1, 1)
        self.page_spinner.setSuffix(" / 1")
        
        # Remove cache files if they exist
        if self.current_file_path:
            try:
                cache_file = self.get_cache_file_path(self.current_file_path)
                info_file = self.get_document_info_file_path(self.current_file_path)
                
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                if os.path.exists(info_file):
                    os.remove(info_file)
            except Exception as e:
                logger.error(f"Failed to remove cache files: {e}")

    def loadDocument(self, file_path):
        try:
            logger.debug("=== Starting Document Load ===")
            logger.debug("File path: %s", file_path)
            
            self.clearDocument()
            self.current_file_path = file_path
            
            if file_path.lower().endswith('.pdf'):
                logger.debug("Opening PDF document...")
                self.pdf_document = fitz.open(file_path)
                self.total_pages = len(self.pdf_document)
                logger.debug("PDF document opened successfully")
                logger.debug("Total pages: %d", self.total_pages)
                
                # Try to load document info
                logger.debug("Attempting to load document info...")
                if self.load_document_info(file_path):
                    logger.debug("Document info loaded successfully")
                    # Update UI with loaded information
                    self.page_spinner.setRange(1, self.total_pages)
                    self.page_spinner.setSuffix(f" / {self.total_pages}")
                    self.page_spinner.setValue(self.current_page)
                    self.pdf_controls.setVisible(True)
                    
                    # Load and display the current page with its structure
                    logger.debug("Loading current page with structure...")
                    self.loadPdfPage(self.current_page)
                    
                    # Show loaded elements in JSON display
                    if self.current_page in self.page_elements:
                        logger.debug("Found elements for current page %d", self.current_page)
                        self.output_text.setText(
                            f"Loaded structure information for page {self.current_page}.\n\n" +
                            self.formatJson(self.page_elements[self.current_page])
                        )
                    else:
                        logger.debug("No elements found for current page %d", self.current_page)
                    
                    QMessageBox.information(self, 'Information Loaded', 
                        f'Loaded previous information for {self.total_pages} pages.\n'
                        f'Starting from page {self.current_page}.')
                else:
                    logger.debug("No document info found or failed to load")
                    # No previous information found
                    self.current_page = 1
                    self.page_spinner.setRange(1, self.total_pages)
                    self.page_spinner.setSuffix(f" / {self.total_pages}")
                    self.pdf_controls.setVisible(True)
                    self.loadPdfPage(self.current_page)
                    self.output_text.setText("No previous structure information found.")
            else:
                logger.debug("Not a PDF file, skipping PDF-specific loading")
                self.pdf_document = None
                self.pdf_controls.setVisible(False)
                self.document_label.set_figure(file_path)
                
        except Exception as e:
            logger.error("Error loading document: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            QMessageBox.critical(self, 'Error', f'Failed to load document: {str(e)}')
            self.clearDocument()

    def loadPdfPage(self, page_number):
        logger.debug("=== Loading PDF Page ===")
        logger.debug("Page number: %d", page_number)
        if not self.pdf_document:
            logger.debug("No PDF document loaded")
            return
                
        try:
            logger.debug("Clearing canvas...")
            # Clear the canvas and elements
            self.document_label.clear()
            self.document_label.elements.clear()  # Clear all elements
            self.selected_text.clear()  # Clear the selected text area
            
            # Load and set the new page
            logger.debug("Loading page from PDF document...")
            page = self.pdf_document[page_number - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = QImage(pix.samples, pix.width, pix.height, 
                        pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.document_label.set_pixmap(pixmap)
            
            # Update the main application's current page
            self.current_page = page_number
            logger.debug("Page loaded successfully - Current page: %d", self.current_page)
            
            # If we have processed results for this page, display them
            if page_number in self.page_elements:
                logger.debug("Found elements for page %d, displaying structure", page_number)
                logger.debug("Number of elements to display: %d", len(self.page_elements[page_number]))
                self.document_label.set_elements(self.page_elements[page_number], page_number)
                self.output_text.setText(
                    f"Displaying structure for page {page_number}.\n\n" +
                    self.formatJson(self.page_elements[page_number])
                )
            else:
                logger.debug("No elements found for page %d", page_number)
                self.output_text.setText(f"No structure information available for page {page_number}.")
                # Ensure no elements are set for this page
                self.document_label.elements.clear()
            
            # Save document info after loading
            logger.debug("Saving document info...")
            self.save_document_info()
                
        except Exception as e:
            logger.error("Error loading PDF page: %s", str(e))
            logger.error("Full error details:", exc_info=True)
            QMessageBox.warning(self, 'Error', f'Failed to load page {page_number}: {str(e)}')
        
        self.repaint()

    def goToFirstPage(self):
        if self.validate_navigation(1):
            self.page_spinner.setValue(1)
        
    def goToPrevPage(self):
        if self.validate_navigation(self.current_page - 1):
            self.current_page = self.current_page - 1
            self.page_spinner.setValue(self.current_page)
        
    def goToNextPage(self):
        if self.validate_navigation(self.current_page + 1):
            self.current_page = self.current_page + 1
            self.page_spinner.setValue(self.current_page)
        
    def goToLastPage(self):
        if self.validate_navigation(self.total_pages):
            self.page_spinner.setValue(self.total_pages)
        
    def goToPage(self, page_number):
        logger.debug("=== Going to Page %d ===", page_number)
        if self.validate_navigation(page_number):
            self.current_page = page_number
            self.loadPdfPage(page_number)

    def closeEvent(self, event):
        """Handle window close event."""
        self.saveSettings()
        self.clearDocument()
        super().closeEvent(event)



def main():
    app = QApplication(sys.argv)
    ex = UpstageDocParseApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()