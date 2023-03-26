import logging
from typing import Optional, Union
from UserSettings.Configuration import RunConfiguration


def setup_logger(name: str,
                config: RunConfiguration
                ) -> logging.Logger:
    """ Sets up and configures a logger object with the specified name,
    log file path, and logging level.

    Args:
        name (str): The name of the logger.
        config (RunConfiguration): The configuration object.

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

    formatter = logging.Formatter(config.log_format)
    logger = logging.getLogger(name)
    logger.setLevel(logging_level_switch[config.log_level])

    log_path = config.log_path
    if log_path:
        if log_path == True:
            log_path = f"Logger/Logs/{name}.log"
        file_handler = logging.FileHandler(log_path)        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if config.log_console_output:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger