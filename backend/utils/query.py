"""Shared helpers for list endpoints: paging, sorting, search and filters from the URL."""
import math

from flask import request

from utils.responses import APIError


def int_arg(name, default, minimum=1, maximum=None):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise APIError(f"'{name}' must be a whole number", 400)
    if value < minimum or (maximum is not None and value > maximum):
        limit = f"between {minimum} and {maximum}" if maximum else f"at least {minimum}"
        raise APIError(f"'{name}' must be {limit}", 400)
    return value


def bool_arg(name):
    """None if the parameter is absent, otherwise True/False."""
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    if raw.lower() in ("true", "1", "yes"):
        return True
    if raw.lower() in ("false", "0", "no"):
        return False
    raise APIError(f"'{name}' must be true or false", 400)


def like_pattern(text):
    """Contains-match pattern; use with ilike(..., escape='\\\\')."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def apply_sort(query, model, allowed, default, default_order="asc", aliases=None):
    """`allowed` are the public sort names; `aliases` maps a public name to a different column name."""
    field = request.args.get("sort", default)
    order = request.args.get("order", default_order).lower()
    if field not in allowed:
        raise APIError(f"Cannot sort by '{field}'. Allowed: {', '.join(allowed)}", 400)
    if order not in ("asc", "desc"):
        raise APIError("'order' must be asc or desc", 400)
    column = getattr(model, (aliases or {}).get(field, field))
    return query.order_by(column.desc() if order == "desc" else column.asc(), model.id.asc())


def paginate(query, serializer, default_per_page=50, max_per_page=200):
    page = int_arg("page", 1)
    per_page = int_arg("per_page", default_per_page, 1, max_per_page)
    total = query.order_by(None).count()
    rows = query.limit(per_page).offset((page - 1) * per_page).all()
    return {"items": [serializer(r) for r in rows], "total": total, "page": page,
            "per_page": per_page, "pages": max(1, math.ceil(total / per_page))}
