import logging
import sys
from ai.config import settings


def setup_logging() -> None:
    """Configures application-wide logging format and level."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    return logging.getLogger(name)
