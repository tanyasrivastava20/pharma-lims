"""Small helpers shared by every model."""
from datetime import date, datetime, timezone

from database import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class DictMixin:
    """to_dict() gives JSON-ready data. Columns named in _hidden are never included."""

    _hidden = ()

    def to_dict(self):
        out = {}
        for col in self.__table__.columns:
            if col.key in self._hidden:
                continue
            value = getattr(self, col.key)
            if isinstance(value, datetime):
                value = value.isoformat(timespec="seconds") + "Z"
            elif isinstance(value, date):
                value = value.isoformat()
            out[col.key] = value
        return out
