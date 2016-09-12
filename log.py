import logging
import logging.handlers as handlers


def setup_custom_logger(name, level):
    #handler = handlers.RotatingFileHandler(
    #    "/usr/local/fdl/fdl_log.bz2", maxBytes=10485760, backupCount=5, encoding='bz2-codec')
    handler = logging.StreamHandler()
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
