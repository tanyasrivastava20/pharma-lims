"""One line per API request in access.log, plus an X-Request-ID header so a problem a user reports
can be matched to the log lines. Request bodies and headers are never logged."""
import logging
import time

from flask import g, request

from utils.logging_setup import access, new_request_id


def register_request_logging(app):
    @app.before_request
    def _start():
        g.request_id = new_request_id()
        g.started = time.perf_counter()

    @app.after_request
    def _finish(response):
        elapsed_ms = (time.perf_counter() - getattr(g, "started", time.perf_counter())) * 1000
        status = response.status_code
        level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
        query = ("?" + request.query_string.decode("utf-8", "replace")[:200]) if request.query_string else ""
        access.log(level, "%s %s%s -> %s %.0fms ip=%s", request.method, request.path, query, status,
                   elapsed_ms, request.remote_addr)
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response
