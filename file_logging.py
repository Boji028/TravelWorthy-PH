#!/usr/bin/env python3
"""Add file-based logging to Flask app."""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_file_logging(app):
    """Configure Flask to log to a file."""
    
    # Create logs directory
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Remove existing handlers
    if app.logger.hasHandlers():
        for handler in app.logger.handlers[:]:
            app.logger.removeHandler(handler)
    
    # File handler
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler  
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG)
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG)
    
    return app

if __name__ == '__main__':
    print("File logging setup module loaded")
