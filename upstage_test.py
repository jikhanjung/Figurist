import sys
import os
import json
import time
import requests
import httpx
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
                           QTextEdit, QLabel, QMessageBox, QProgressBar, 
                           QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

logger = logging.getLogger(__name__)

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
            # This catches SSL errors and other transport-level issues
            logger.warning(f"Transport error occurred: {e}. Disabling SSL verification.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.post(url, files=files, data=data)  # Retry with new client
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
            # This catches SSL errors and other transport-level issues
            logger.warning(f"Transport error occurred: {e}. Disabling SSL verification.")
            self.ssl_verification_disabled = True
            self.client = self._create_client()
            return self.get(url)  # Retry with new client
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
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
                    # Get results from download_url of first batch
                    download_url = data["batches"][0]["download_url"]
                    result = self.client.get(download_url)
                    self.finished.emit(result)
                    break
                elif data["status"] == "failed":
                    self.error.emit(f"Processing failed: {data.get('failure_message', 'Unknown error')}")
                    break
                    
                self.progress.emit(f"Processing... Status: {data['status']}")
                time.sleep(2)  # Poll every 2 seconds
                
        except Exception as e:
            self.error.emit(str(e))

class UpstageDocParseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.async_worker = None
        self.upstage_client = None
        
    def initUI(self):
        self.setWindowTitle('Upstage Document Parse')
        self.setGeometry(100, 100, 1000, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create API key input
        api_layout = QHBoxLayout()
        api_label = QLabel('API Key:')
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        
        # Create file selection widgets
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText('Select a file...')
        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.browseFiles)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_button)
        
        # Create API type selection
        api_type_layout = QHBoxLayout()
        self.sync_radio = QRadioButton("Synchronous API")
        self.async_radio = QRadioButton("Asynchronous API")
        self.sync_radio.setChecked(True)
        api_type_layout.addWidget(self.sync_radio)
        api_type_layout.addWidget(self.async_radio)
        
        # Create process button
        process_button = QPushButton('Process Document')
        process_button.clicked.connect(self.processDocument)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Create output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        # Add widgets to main layout
        layout.addLayout(api_layout)
        layout.addLayout(file_layout)
        layout.addLayout(api_type_layout)
        layout.addWidget(process_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.output_text)
        
    def browseFiles(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "Images (*.png *.jpg *.jpeg);;PDF Files (*.pdf);;All Files (*)"
        )
        if file_name:
            self.file_path.setText(file_name)
            
    def formatJson(self, data):
        return json.dumps(data, indent=2)
            
    def processDocument(self):
        # Validate inputs
        api_key = self.api_key_input.text()
        file_path = self.file_path.text()
        
        if not api_key:
            QMessageBox.warning(self, 'Error', 'Please enter your API key.')
            return
            
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, 'Error', 'Please select a valid file.')
            return
        
        # Create or update client if API key changed
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
        self.output_text.setText(self.formatJson(result))
        
    def processAsynchronous(self, file_path):
        url = "https://api.upstage.ai/v1/document-ai/async/document-parse"
        files = {"document": open(file_path, "rb")}
        data = {"ocr": True}
        
        self.output_text.setText("Initiating async processing...")
        result = self.upstage_client.post(url, files=files, data=data)
        
        if "request_id" not in result:
            QMessageBox.critical(self, 'Error', 'Failed to get request ID')
            return
            
        # Start async worker to poll for results
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.async_worker = AsyncWorker(self.upstage_client, result["request_id"])
        self.async_worker.finished.connect(self.handleAsyncResult)
        self.async_worker.progress.connect(self.handleProgress)
        self.async_worker.error.connect(self.handleError)
        self.async_worker.start()
        
    def handleAsyncResult(self, result):
        self.progress_bar.setVisible(False)
        self.output_text.setText(self.formatJson(result))
        
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