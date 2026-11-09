"""Logging. Four files in the logs/ folder (each rotates at about 5 MB and keeps 5 old copies):

  access.log  every API request: method, path, status, time taken, IP, user
  audit.log   security and data events: logins (good and bad), token problems, permission denials,
              record created / updated / deleted, workflow changes, exports, imports
  app.log     general application messages and database errors
  error.log   unexpected errors with full details (the traceback)

Passwords, tokens and request bodies are never written to any log."""
import logging
import uuid
from logging.handlers import RotatingFileHandler

from flask import g, has_request_context
from flask.logging import default_handler

audit = logging.getLogger("pharmalims.audit")
access = logging.getLogger("pharmalims.access")
FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | req=%(request_id)s user=%(user)s | %(message)s"


class _ContextFilter(logging.Filter):
    """Adds the request id and user name to every line written during a request."""

    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
            record.user = getattr(g, "log_user", "-")
        else:
            record.request_id = record.user = "-"
        return True


def new_request_id():
    return uuid.uuid4().hex[:10]


def setup_logging(app):
    cfg = app.config
    level = getattr(logging, cfg["LOG_LEVEL"], logging.INFO)
    formatter = logging.Formatter(FORMAT)
    app_logger = app.logger

    # forget handlers from an earlier create_app() call, so nothing is logged twice
    app_logger.removeHandler(default_handler)
    for logger in (app_logger, audit, access):
        for handler in list(logger.handlers):
            if getattr(handler, "_pharmalims", False):
                logger.removeHandler(handler)
                handler.close()

    def attach(logger, handler, handler_level):
        handler.setLevel(handler_level)
        handler.setFormatter(formatter)
        handler.addFilter(_ContextFilter())
        handler._pharmalims = True
        logger.addHandler(handler)

    def rotating(name):
        return RotatingFileHandler(cfg["LOG_DIR"] / name, maxBytes=cfg["LOG_MAX_BYTES"],
                                   backupCount=cfg["LOG_BACKUP_COUNT"], encoding="utf-8", delay=True)

    app_logger.setLevel(level)
    audit.setLevel(logging.INFO)
    access.setLevel(logging.INFO)
    audit.propagate = access.propagate = False
    if cfg["LOG_TO_FILES"]:
        attach(app_logger, rotating("app.log"), level)
        attach(app_logger, rotating("error.log"), logging.ERROR)
        attach(audit, rotating("audit.log"), logging.INFO)
        attach(access, rotating("access.log"), logging.INFO)
        attach(access, rotating("error.log"), logging.ERROR)
    if cfg["LOG_TO_CONSOLE"]:
        attach(app_logger, logging.StreamHandler(), level)
        attach(audit, logging.StreamHandler(), level)
    if not (cfg["LOG_TO_FILES"] or cfg["LOG_TO_CONSOLE"]):
        for logger in (app_logger, audit, access):
            logger.addHandler(logging.NullHandler())
