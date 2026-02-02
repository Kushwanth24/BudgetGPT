from datetime import datetime, timezone
from app.extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paid_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255))
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "paid_by_user_id": self.paid_by_user_id,
            "amount": float(self.amount),
            "description": self.description,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat(),
        }
