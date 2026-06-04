import logging
import os
from logging.handlers import RotatingFileHandler

from core.config import LIVE

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

FORMAT = logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_root_configured = False


def _configure_root():
    global _root_configured
    if _root_configured:
        return
    _root_configured = True

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(FORMAT)
    root.addHandler(console)

    if LIVE == "production":
        error_file = RotatingFileHandler(
            os.path.join(LOG_DIR, "error.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
        )
        error_file.setLevel(logging.ERROR)
        error_file.setFormatter(FORMAT)
        root.addHandler(error_file)

        app_file = RotatingFileHandler(
            os.path.join(LOG_DIR, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
        app_file.setLevel(logging.INFO)
        app_file.setFormatter(FORMAT)
        root.addHandler(app_file)

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)


_configure_root()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
