from __future__ import annotations
import logging
from typing import Optional

from config.settings import Settings


def setup_logging(settings: Settings | None = None) -> None:
    level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
