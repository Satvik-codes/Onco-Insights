import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from backend.config import LOGS_DIR

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "metadata"):
            log_entry["metadata"] = record.metadata
            
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def get_logger(module_name: str) -> logging.Logger:
    logger = logging.getLogger(module_name)
    
    # Only configure if it doesn't already have handlers to avoid duplicates
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        formatter = StructuredFormatter()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = LOGS_DIR / "app.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger to avoid duplicate prints
        logger.propagate = False
        
    return logger

class StructuredLogger:
    def __init__(self, module_name: str):
        self._logger = get_logger(module_name)
        
    def debug(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        self._logger.debug(msg, extra={"metadata": metadata} if metadata else None)
        
    def info(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        self._logger.info(msg, extra={"metadata": metadata} if metadata else None)
        
    def warning(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        self._logger.warning(msg, extra={"metadata": metadata} if metadata else None)
        
    def error(self, msg: str, metadata: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        self._logger.error(msg, extra={"metadata": metadata} if metadata else None, exc_info=exc_info)
