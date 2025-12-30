"""
Logging configuration for YouTube Management System
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logging level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        app.config.get('LOG_FILE', 'logs/app.log'),
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Console handler for development
    if app.config.get('DEBUG'):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        app.logger.addHandler(console_handler)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # Log startup
    app.logger.info('YouTube Management System startup')

def log_error(error, context=None):
    """Log error with context"""
    from flask import current_app, request
    
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg += f" | Context: {context}"
    
    if request:
        error_msg += f" | URL: {request.url} | Method: {request.method}"
        if request.form:
            # Don't log sensitive data
            safe_form = {k: v for k, v in request.form.items() 
                        if k.lower() not in ['password', 'secret', 'token']}
            error_msg += f" | Form: {safe_form}"
    
    current_app.logger.error(error_msg)

def log_activity(action, details=None):
    """Log user activity"""
    from flask import current_app, request
    
    activity_msg = f"Activity: {action}"
    if details:
        activity_msg += f" | Details: {details}"
    
    if request:
        activity_msg += f" | IP: {request.remote_addr}"
    
    current_app.logger.info(activity_msg)
