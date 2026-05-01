# HRBuddy
# core/logger.py

# Required Libraries
import logging
import sys

# Getting the logger
def get_logger(name="HRBuddy"):
    '''
    Returns a logger instance with the specified name.
    '''
    
    logger = logging.getLogger(name)
    
    # Checking if the logger has any handlers
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Formatting the log messages
        formatter = logging.Formatter(
            '[%(levelname)s] [%(asctime)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Adding the handler to the logger
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

log = get_logger()