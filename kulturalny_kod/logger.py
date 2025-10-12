import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8"
        )
    ],

)

logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("django").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)