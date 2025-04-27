import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Define a formatter
class CustomFormatter(logging.Formatter):
    """Custom formatter for more readable logs."""
    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class JsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self):
        super().__init__(fmt='%(asctime)s %(levelname)s %(name)s %(module)s %(filename)s %(lineno)d %(message)s')

    def process_log_record(self, log_record):
        # Add any additional processing if needed
        return super().process_log_record(log_record)
    
def get_logger(module_name: str, env: str = "dev") -> logging.Logger:
    logger = logging.getLogger(module_name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log"),
        maxBytes=5*1024*1024,
        backupCount=5
    )

    if env == "prod":
        console_handler.setLevel(logging.WARNING)
        file_handler.setLevel(logging.WARNING)

        # 🟡 Set JSON format in prod
        json_formatter = JsonFormatter()
        console_handler.setFormatter(json_formatter)
        file_handler.setFormatter(json_formatter)

    else:
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.INFO)

        console_handler.setFormatter(CustomFormatter())
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
