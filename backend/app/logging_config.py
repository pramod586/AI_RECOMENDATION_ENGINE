import logging
import os
from logging.handlers import RotatingFileHandler


LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)


def setup_logging():
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)

    if logger.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)