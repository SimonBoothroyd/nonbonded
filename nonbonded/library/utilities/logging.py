import logging
import sys


def get_log_levels():
    return ["none", "debug", "info", "warning", "error", "critical"]


def string_to_log_level(log_level_string):

    if log_level_string == "none":
        return None
    if log_level_string == "debug":
        return logging.DEBUG
    elif log_level_string == "info":
        return logging.INFO
    elif log_level_string == "warning":
        return logging.WARNING
    elif log_level_string == "error":
        return logging.ERROR
    elif log_level_string == "critical":
        return logging.CRITICAL

    raise NotImplementedError()


def setup_timestamp_logging(logging_level, file_path=None):
    """Set up timestamp-based logging.

    Parameters
    ----------
    logging_level: int
        The logger level.
    file_path: str, optional
        The file to write the log to. If none, the logger will
        print to the terminal.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s", datefmt="%H:%M:%S"
    )

    if file_path is None:
        logger_handler = logging.StreamHandler(stream=sys.stdout)
    else:
        logger_handler = logging.FileHandler(file_path)

    logger_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging_level)
    logger.addHandler(logger_handler)
