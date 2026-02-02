from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from app.extensions import db
from app.models.monthly_budget import MonthlyBudget
from app.models.expense import Expense
from app.models.category import Category
from app.services.category_service import require_category_owned_by_user
from app.utils.errors import AppError

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0.00")


# --------------------
# Helpers
# --------------------
def _to_decimal_amount(value) -> Decimal:
    try:
        return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except Exception:
        raise AppError("Invalid amount", 400)


def _default_month() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def _month_bounds(month: str):
    """
    month format: YYYY-MM
    returns [start, end)
    """
    try:
        year, mon = int(month[:4]), int(month[5:7])
        if month[4] != "-" or mon < 1 or mon > 12:
            raise ValueError()
    except Exception:
        raise AppError("month must be in YYYY-MM format", 400)

    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)

    return start, end


# --------------------
# Budget CRUD
# --------------------
def upsert_monthly_budget(
    user_id: int,
    category_id: int,
    month: str | None,
    limit_amount,
):
    month = month or _default_month()

    require_category_owned_by_user(user_id, category_id)

    limit_dec = _to_decimal_amount(limit_amount)
    if limit_dec < ZERO:
        raise AppError("limit_amount must be >= 0", 400)

    budget = MonthlyBudget.query.filter_by(
        user_id=user_id,
        category_id=category_id,
        month=month,
    ).first()

    if budget:
        budget.limit_amount = limit_dec
        db.session.commit()
        return budget

    budget = MonthlyBudget(
        user_id=user_id,
        category_id=category_id,
        month=month,
        limit_amount=limit_dec,
    )
    db.session.add(budget)
    db.session.commit()
    return budget


# --------------------
# Monthly Summary
# --------------------
def monthly_summary(user_id: int, month: str | None):
    month = month or _default_month()
    start, end = _month_bounds(month)

    # MVP definition: "your spending" = expenses you paid
    expenses = (
        Expense.query
        .filter(Expense.paid_by_user_id == user_id)
        .filter(Expense.created_at >= start)
        .filter(Expense.created_at < end)
        .all()
    )

    spend_by_category: dict[int | None, Decimal] = {}
    total_spent = ZERO

    for e in expenses:
        amt = Decimal(str(e.amount)).quantize(TWOPLACES)
        total_spent += amt
        spend_by_category[e.category_id] = (
            spend_by_category.get(e.category_id, ZERO) + amt
        )

    categories = Category.query.filter_by(user_id=user_id).all()
    budgets = MonthlyBudget.query.filter_by(user_id=user_id, month=month).all()

    budget_map = {
        b.category_id: Decimal(str(b.limit_amount)).quantize(TWOPLACES)
        for b in budgets
    }

    rows = []

    for c in categories:
        spent = spend_by_category.get(c.id, ZERO)
        limit_amt = budget_map.get(c.id)

        remaining = None
        overspent = None

        if limit_amt is not None:
            remaining = (limit_amt - spent).quantize(TWOPLACES)
            overspent = spent > limit_amt

        rows.append(
            {
                "category_id": c.id,
                "category_name": c.name,
                "spent": float(spent),
                "limit": float(limit_amt) if limit_amt is not None else None,
                "remaining": float(remaining) if remaining is not None else None,
                "overspent": overspent,
            }
        )

    # Uncategorized
    uncategorized_spent = spend_by_category.get(None, ZERO)
    if uncategorized_spent > ZERO:
        rows.append(
            {
                "category_id": None,
                "category_name": "Uncategorized",
                "spent": float(uncategorized_spent),
                "limit": None,
                "remaining": None,
                "overspent": None,
            }
        )

    # Prioritize overspent categories
    rows.sort(
        key=lambda r: (
            r["overspent"] is True,
            r["spent"],
        ),
        reverse=True,
    )

    return {
        "month": month,
        "total_spent": float(total_spent.quantize(TWOPLACES)),
        "by_category": rows,
    }
