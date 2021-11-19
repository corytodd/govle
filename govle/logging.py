"""
@file logging.py
"""

import logging
import sys

# Silence pygatt logging
logging.getLogger('pygatt').setLevel(logging.ERROR)

class FancyLogFormatter(logging.Formatter):
    light_grey = "\x1b[37m"
    grey = "\x1b[37["
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    underline_red = "\x1b[31;21m"
    reset = "\x1b[0m"
    format = '[%(asctime)s] [%(threadName)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'

    FORMATS = {
        logging.DEBUG: light_grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: underline_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


file_handler = logging.FileHandler(filename='govle.log')
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(FancyLogFormatter())
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(threadName)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger('govle')