import logging
import sys

def setup_logging(log_level=logging.INFO):
    """
    Configure logging for the entire application.
    
    Args:
        log_level: The logging level (default: INFO)
    """
    # Create a logger
    logger = logging.getLogger("home_task")
    logger.setLevel(log_level)

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    return logger 