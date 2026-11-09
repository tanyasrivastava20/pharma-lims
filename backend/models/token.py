from database import db
from models.base import utcnow


class RevokedToken(db.Model):
    """Logged-out tokens. A token listed here is refused even if it has not expired yet."""

    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=False, default=utcnow)
