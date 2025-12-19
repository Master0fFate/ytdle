import logging
import sys

def setup_logging(verbose: bool = False):
    """
    Sets up logging configuration.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = []
    
    # File handler
    try:
        file_handler = logging.FileHandler("ytdle.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        handlers.append(file_handler)
    except Exception:
        pass

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    handlers.append(console_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )
