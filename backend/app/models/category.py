from datetime import datetime, timezone
from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    # Categories are scoped per user (avoids global name collisions)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "name",
            name="uq_categories_user_name",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }
