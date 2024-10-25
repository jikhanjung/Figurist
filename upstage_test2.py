import sys
import os
import json
import time
import requests
import httpx
import logging
from FgComponents import FigureLabel
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
                           QTextEdit, QLabel, QMessageBox, QProgressBar, 
                           QRadioButton, QButtonGroup, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage

logger = logging.getLogger(__name__)

class DocumentLabel(FigureLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.elements = []
        self.show_text = True
        self.show_boxes = True
        
    def set_elements(self, elements):
        self.elements = elements
        self.repaint()
        
    def paintEvent(self, event):
        # Call parent's paintEvent first to draw the image
        super().paintEvent(event)
        
        if not self.elements or not self.curr_pixmap:
            return
            
        painter = QPainter(self)
        
        for element in self.elements:
            if 'coordinates' not in element:
                continue
                
            # Get the original coordinates relative to image size
            coords = element['coordinates']
            x = int(coords[0]['x'] * self.orig_pixmap.width())
            y = int(coords[0]['y'] * self.orig_pixmap.height())
            width = int((coords[2]['x'] - coords[0]['x']) * self.orig_pixmap.width())
            height = int((coords[2]['y'] - coords[0]['y']) * self.orig_pixmap.height())
            
            # Create a rect in image coordinates
            rect = QRect(x, y, width, height)
            
            # Transform to canvas coordinates using parent's methods
            canvas_rect = self.rect_to_canvas(rect)
            
            # Draw bounding box
            if self.show_boxes:
                if element['category'] == 'heading1':
                    painter.setPen(QPen(QColor(255, 0, 0, 128), 2))  # Red for headings
                elif element['category'] == 'paragraph':
                    painter.setPen(QPen(QColor(0, 255, 0, 128), 2))  # Green for paragraphs
                else:
                    painter.setPen(QPen(QColor(0, 0, 255, 128), 2))  # Blue for other elements
                painter.drawRect(canvas_rect)
            
            # Draw text
            if self.show_text and 'content' in element and element['content'].get('text'):
                text = element['content']['text']
                painter.setPen(Qt.black)
                # Create semi-transparent white background for text
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
            return httpx.Client(verify=False)
        return httpx.Client()

    def post(self, url, files=None, data=None):
        try:
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
    finished = pyqtSignal(dict)
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
                    download_url = data["batches"][0]["download_url"]
                    result = self.client.get(download_url)
                    self.finished.emit(result)
                    break
                elif data["status"] == "failed":
                    self.error.emit(f"Processing failed: {data.get('failure_message', 'Unknown error')}")
                    break
                    
                self.progress.emit(f"Processing... Status: {data['status']}")
                time.sleep(2)
                
        except Exception as e:
            self.error.emit(str(e))



class UpstageDocParseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.async_worker = None
        self.upstage_client = None
        self.current_image = None
        
    def initUI(self):
        self.setWindowTitle('Upstage Document Parse')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create top controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # API key input
        api_layout = QHBoxLayout()
        api_label = QLabel('API Key:')
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText('Select a file...')
        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.browseFiles)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_button)
        
        # API type selection and process button
        action_layout = QHBoxLayout()
        self.sync_radio = QRadioButton("Synchronous API")
        self.async_radio = QRadioButton("Asynchronous API")
        self.sync_radio.setChecked(True)
        process_button = QPushButton('Process Document')
        process_button.clicked.connect(self.processDocument)
        action_layout.addWidget(self.sync_radio)
        action_layout.addWidget(self.async_radio)
        action_layout.addWidget(process_button)
        
        # Add controls to top section
        controls_layout.addLayout(api_layout)
        controls_layout.addLayout(file_layout)
        controls_layout.addLayout(action_layout)
        
        # Create splitter for document view and JSON output
        splitter = QSplitter(Qt.Horizontal)
        
        # Document display
        self.document_label = DocumentLabel()
        self.document_label.setMinimumWidth(600)
        
        # JSON output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        splitter.addWidget(self.document_label)
        splitter.addWidget(self.output_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add all components to main layout
        main_layout.addWidget(controls_widget)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.progress_bar)
        
    def browseFiles(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "Images (*.png *.jpg *.jpeg);;PDF Files (*.pdf);;All Files (*)"
        )
        if file_name:
            self.file_path.setText(file_name)
            # Load and display the image
            self.document_label.set_figure(file_name)
            
    def formatJson(self, data):
        return json.dumps(data, indent=2)
            
    def processDocument(self):
        api_key = self.api_key_input.text()
        file_path = self.file_path.text()
        
        if not api_key:
            QMessageBox.warning(self, 'Error', 'Please enter your API key.')
            return
            
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, 'Error', 'Please select a valid file.')
            return
        
        if self.upstage_client is None or self.upstage_client.api_key != api_key:
            self.upstage_client = UpstageClient(api_key)
            
        try:
            if self.sync_radio.isChecked():
                self.processSynchronous(file_path)
            else:
                self.processAsynchronous(file_path)
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            
    def processSynchronous(self, file_path):
        url = "https://api.upstage.ai/v1/document-ai/document-parse"
        files = {"document": open(file_path, "rb")}
        
        self.output_text.setText("Processing document...")
        result = self.upstage_client.post(url, files=files)
        self.handleResult(result)
        
    def processAsynchronous(self, file_path):
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
        self.async_worker.finished.connect(self.handleAsyncResult)
        self.async_worker.progress.connect(self.handleProgress)
        self.async_worker.error.connect(self.handleError)
        self.async_worker.start()
        
    def handleResult(self, result):
        # Display JSON result
        self.output_text.setText(self.formatJson(result))
        
        # Update document view with elements
        if 'elements' in result:
            self.document_label.set_elements(result['elements'])
        
    def handleAsyncResult(self, result):
        self.progress_bar.setVisible(False)
        self.handleResult(result)
        
    def handleProgress(self, message):
        self.output_text.setText(message)
        
    def handleError(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Error', error_message)

def main():
    app = QApplication(sys.argv)
    ex = UpstageDocParseApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()