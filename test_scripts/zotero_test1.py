import ssl
import certifi
import requests
from pyzotero import zotero
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import os
import subprocess
import tempfile

import logging
import urllib3

logging.basicConfig(level=logging.DEBUG)
urllib3.connectionpool.HTTPConnection.debuglevel = 1
urllib3.connectionpool.HTTPSConnection.debuglevel = 1
def get_windows_cert_store():
    # Create a temporary directory to store individual certificates
    with tempfile.TemporaryDirectory() as temp_dir:
        # Export certificates from the Windows cert store
        subprocess.run([
            "powershell",
            "-Command",
            f"Get-ChildItem -Path Cert:\\LocalMachine\\Root | ForEach-Object {{ $_.Thumbprint }} | ForEach-Object {{ Export-Certificate -Cert Cert:\\LocalMachine\\Root\\$_ -FilePath {temp_dir}\\$_.cer }}"
        ], check=True)

        # Combine all certificates into a single PEM file
        pem_path = os.path.join(temp_dir, 'combined_certs.pem')
        with open(pem_path, 'wb') as pem_file:
            for cert_file in os.listdir(temp_dir):
                if cert_file.endswith('.cer'):
                    cert_path = os.path.join(temp_dir, cert_file)
                    with open(cert_path, 'rb') as cert_data:
                        cert = x509.load_der_x509_certificate(cert_data.read())
                        pem_data = cert.public_bytes(encoding=serialization.Encoding.PEM)
                        pem_file.write(pem_data)

        # Read the combined PEM file
        with open(pem_path, 'rb') as pem_file:
            return pem_file.read()

class ZoteroBackend(zotero.Zotero):
    def __init__(self, library_id, library_type, api_key):
        super().__init__(library_id, library_type, api_key)
        self.session = requests.Session()
        self.session.verify = self.create_ssl_context()

    def create_ssl_context(self):
        context = ssl.create_default_context(cafile=certifi.where())
        
        # Add certificates from Windows store
        windows_certs = get_windows_cert_store()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as temp_cert_file:
            temp_cert_file.write(windows_certs)
            temp_cert_path = temp_cert_file.name

        context.load_verify_locations(cafile=temp_cert_path)
        
        # Clean up temporary file
        os.unlink(temp_cert_path)
        
        return context

    def _request(self, method, url, **kwargs):
        return self.session.request(method, url, **kwargs)
    
    def get_collections(self):
        return self.collections()

    def get_collection(self, collection_key):
        return self.collection(collection_key)

    def get_items_in_collection(self, collection_key):
        return self.collection_items(collection_key)

    def get_subcollections(self, collection_key):
        return self.collections_sub(collection_key)
    

from decouple import config
# add test code
zotero_user_id = config("ZOTERO_USER_ID")
library_type = 'user'
zotero_api_key = config("ZOTERO_API_KEY")
zot = ZoteroBackend(zotero_user_id, library_type, zotero_api_key)
collections = zot.get_collections()
print(collections)

