import logging
import os
from logging.handlers import RotatingFileHandler

log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)


def setup_logger(name, console, file):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if file:
        file_handler = RotatingFileHandler('logs/log.log', maxBytes=10000000, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger
