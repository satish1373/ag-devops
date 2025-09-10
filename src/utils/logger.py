import logging
import sys
from pathlib import Path

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    if logger.handlers:
        return logger
    
    file_handler = logging.FileHandler('logs/devops_autocoder.log')
    console_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
