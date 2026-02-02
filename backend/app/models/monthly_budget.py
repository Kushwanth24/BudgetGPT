from datetime import datetime, timezone
from app.extensions import db


class MonthlyBudget(db.Model):
    __tablename__ = "monthly_budgets"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "YYYY-MM" for MVP (simple + index-friendly)
    month = db.Column(db.String(7), nullable=False, index=True)

    limit_amount = db.Column(db.Numeric(12, 2), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "category_id",
            "month",
            name="uq_monthly_budgets_user_category_month",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "month": self.month,
            "limit_amount": float(self.limit_amount),
            "created_at": self.created_at.isoformat(),
        }
