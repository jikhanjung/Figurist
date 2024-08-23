import os, sys

COMPANY_NAME = "PaleoBytes"
PROGRAM_VERSION = "0.1.0"
PROGRAM_NAME = "Figurist"

DB_LOCATION = ""
IMAGE_EXTENSION_LIST = ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']

#print(os.name)
USER_PROFILE_DIRECTORY = os.path.expanduser('~')

DEFAULT_DB_DIRECTORY = os.path.join( USER_PROFILE_DIRECTORY, COMPANY_NAME, PROGRAM_NAME )
DEFAULT_STORAGE_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "data/")
DEFAULT_ATTACHMENT_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "attachment/")
DEFAULT_LOG_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "logs/")
DB_BACKUP_DIRECTORY = os.path.join(DEFAULT_DB_DIRECTORY, "backups/")

if not os.path.exists(DEFAULT_DB_DIRECTORY):
    os.makedirs(DEFAULT_DB_DIRECTORY)
if not os.path.exists(DEFAULT_STORAGE_DIRECTORY):
    os.makedirs(DEFAULT_STORAGE_DIRECTORY)
if not os.path.exists(DEFAULT_LOG_DIRECTORY):
    os.makedirs(DEFAULT_LOG_DIRECTORY)
if not os.path.exists(DB_BACKUP_DIRECTORY):
    os.makedirs(DB_BACKUP_DIRECTORY)
if not os.path.exists(DEFAULT_ATTACHMENT_DIRECTORY):
    os.makedirs(DEFAULT_ATTACHMENT_DIRECTORY)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def value_to_bool(value):
    return value.lower() == 'true' if isinstance(value, str) else bool(value)

def process_dropped_file_name(file_name):
    import os
    from urllib.parse import urlparse, unquote
    #print("file_name:", file_name)
    url = file_name
    parsed_url = urlparse(url)            
    #print("parsed_url:", parsed_url)
    file_path = unquote(parsed_url.path)
    if os.name == 'nt':
        file_path = file_path[1:]
    else:
        file_path = file_path
    return file_path