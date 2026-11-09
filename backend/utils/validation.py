import math
from datetime import date

from flask import request

from utils.responses import APIError


def get_json_body(optional=False):
    """The JSON object sent with the request. optional=True accepts a request with no body at all."""
    if optional and not request.get_data():
        return {}
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError("Request body must be a JSON object", 400)
    return data


import re


def clean_text(data, key, max_len, errors, required=False):
    """Trimmed text, or None when blank. Records a problem in `errors` instead of raising."""
    value = data.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            errors[key] = "Required"
        return None
    if not isinstance(value, str):
        errors[key] = "Must be text"
        return None
    value = value.strip()
    if len(value) > max_len:
        errors[key] = f"At most {max_len} characters"
    return value


def clean_int(data, key, errors, minimum=0, maximum=None):
    value = data[key]
    number = None
    if isinstance(value, bool):
        number = None
    elif isinstance(value, int):
        number = value
    elif isinstance(value, float) and value.is_integer():
        number = int(value)
    elif isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        number = int(value.strip())
    if number is None:
        errors[key] = "Must be a whole number"
        return None
    if number < minimum or (maximum is not None and number > maximum):
        errors[key] = f"Must be between {minimum} and {maximum}" if maximum is not None else f"Must be at least {minimum}"
        return None
    return number


def clean_bool(data, key, errors):
    value = data[key]
    if not isinstance(value, bool):
        errors[key] = "Must be true or false"
        return None
    return value


def clean_date(data, key, errors, required=False):
    """A date in YYYY-MM-DD format, or None when blank."""
    value = data.get(key)
    if value is None or value == "":
        if required:
            errors[key] = "Required"
        return None
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    errors[key] = "Must be a valid date in YYYY-MM-DD format"
    return None


def clean_number(data, key, errors, minimum_exclusive=0, maximum=1_000_000_000):
    value = data.get(key)
    number = None
    if isinstance(value, bool):
        number = None
    elif isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            number = None
    if number is None or math.isnan(number) or math.isinf(number):
        errors[key] = "Must be a number"
        return None
    if number <= minimum_exclusive:
        errors[key] = f"Must be greater than {minimum_exclusive}"
        return None
    if number > maximum:
        errors[key] = f"Must be at most {maximum}"
        return None
    return number
