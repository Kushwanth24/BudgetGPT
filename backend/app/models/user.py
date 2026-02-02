from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120))

    # Optional password auth for MVP testing
    password_hash = db.Column(db.String(255))

    # OAuth (Google via NextAuth)
    provider = db.Column(db.String(40))          # e.g. "google"
    provider_user_id = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --------------------
    # Auth helpers
    # --------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    # --------------------
    # Serialization
    # --------------------
    def to_public_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "provider": self.provider,
        }
