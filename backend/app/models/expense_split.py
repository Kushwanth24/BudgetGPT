from app.extensions import db


class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)

    expense_id = db.Column(
        db.Integer,
        db.ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount_owed = db.Column(db.Numeric(12, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "expense_id",
            "user_id",
            name="uq_expense_splits_expense_user",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "expense_id": self.expense_id,
            "user_id": self.user_id,
            "amount_owed": float(self.amount_owed),
        }
