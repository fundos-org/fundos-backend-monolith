import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pythonjsonlogger import jsonlogger

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class JsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self):
        super().__init__(fmt='%(asctime)s %(levelname)s %(name)s %(module)s %(filename)s %(lineno)d %(message)s')

    def process_log_record(self, log_record):
        return super().process_log_record(log_record)

def get_logger(module_name: str, env: str = "dev") -> logging.Logger:
    logger = logging.getLogger(module_name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Avoid duplicate logs

    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )

    if env == "prod":
        console_handler.setLevel(logging.WARNING)
        file_handler.setLevel(logging.WARNING)
        formatter = JsonFormatter()
    else:
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.INFO)
        formatter = CustomFormatter()

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
