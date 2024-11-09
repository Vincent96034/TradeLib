import sys
import logging


logger = logging.getLogger('your_library_name')
logger.propagate = False
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s : %(filename)s/%(funcName)s : %(asctime)s : %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


def setup_logger(*args, **kwargs):
    return logger
