"""
Shared utilities: structured logging with traceId
"""

from .main import trace_id_var


def log_info(msg: str, **kwargs):
    import logging

    extra = {"traceId": trace_id_var.get(""), **kwargs}
    logging.getLogger("reservation").info(msg, extra=extra)


def log_error(msg: str, **kwargs):
    import logging

    extra = {"traceId": trace_id_var.get(""), **kwargs}
    logging.getLogger("reservation").error(msg, extra=extra)
