import logging
import os
import json
from datetime import datetime

def setup_logger(name, log_file, level=logging.INFO):
    """Function to set up a logger with file handler"""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

def log_activity(logger, data):
    """Log general activity to the specified logger"""
    if isinstance(data, dict):
        logger.info(json.dumps(data))
    else:
        logger.info(str(data))

def log_attack_attempt(logger, data):
    """Log attack attempts to the specified logger"""
    if isinstance(data, dict):
        logger.warning(json.dumps(data))
    else:
        logger.warning(str(data))

def get_geolocation(ip_address):
    """Get geolocation data for an IP address"""
    try:
        # Use a free IP geolocation API
        import requests
        response = requests.get(f"https://ipapi.co/{ip_address}/json/")
        if response.status_code == 200:
            return response.json()
        return {"error": "Could not retrieve geolocation data"}
    except Exception as e:
        return {"error": str(e)}

def get_browser_fingerprint(user_agent, headers):
    """Create a browser fingerprint from request data"""
    import hashlib
    
    fingerprint = {
        "user_agent": user_agent,
        "accept": headers.get("Accept", ""),
        "accept_encoding": headers.get("Accept-Encoding", ""),
        "accept_language": headers.get("Accept-Language", ""),
        "dnt": headers.get("DNT", ""),  # Do Not Track
    }
    
    # Generate a unique hash for this fingerprint
    fingerprint_str = json.dumps(fingerprint, sort_keys=True)
    fingerprint_hash = hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    return {
        "details": fingerprint,
        "hash": fingerprint_hash
    }