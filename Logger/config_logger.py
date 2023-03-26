import logging
from typing import Optional, Union
from UserSettings.Configuration import RunConfiguration


def setup_logger(name: str,
                 log_path: Optional[Union[str, bool]] = None,
                 console_output: bool = True,
                 level: str = "INFO"
                ) -> logging.Logger:
    """ Sets up and configures a logger object with the specified name,
    log file path, and logging level.

    Args:
        name (str): The name of the logger.
        log_path (str): The directory path to store the log file. Defaults to None. If set to True the default path will be used.
        console_output (bool): If logs should be printed to the console. Defaults to True.
        level (str): The logging level for the logger. Defaults to "INFO".

    Returns:
        logging.Logger: The configured logger object.
    """
    logging_level_switch = {
        "NOTSET": logging.NOTSET,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARN,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    formatter = logging.Formatter("%(asctime)s :: [%(name)s - %(levelname)s] :: %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(logging_level_switch[level])

    if log_path:
        if log_path == True:
            log_path = f"Logger/Logs/{name}.log"
        file_handler = logging.FileHandler(log_path)        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if console_output:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)