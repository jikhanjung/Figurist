import FgUtils as fg
import logging
import os
# get date as string
from datetime import datetime


def setup_logger(name, level=logging.INFO):
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    # 
    #log_dir = os.path.join( mu.DEFAULT_LOG_DIRECTORY, 'logs')
    #if not os.path.exists(log_dir):
    #   os.makedirs(log_dir)
    logfile_path = os.path.join(fg.DEFAULT_LOG_DIRECTORY, fg.PROGRAM_NAME + '.' + date_str + '.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(logfile_path)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger