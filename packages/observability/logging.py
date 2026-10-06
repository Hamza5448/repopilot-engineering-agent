"""Small structured logging helper shared by the API and worker."""

import json
import logging
from typing import Any


def log_event(logger: logging.Logger, event_name: str, **fields: Any) -> None:
    """Emit a structured, credential-free event as one log record."""

    logger.info("%s %s", event_name, json.dumps(fields, sort_keys=True, default=str))
