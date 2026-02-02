from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from app.extensions import db
from app.models.monthly_budget import MonthlyBudget
from app.models.expense import Expense
from app.models.category import Category
from app.services.category_service import require_category_owned_by_user
from app.utils.errors import AppError

TWOPLACES = Decimal("0.01")


def _to_decimal_amount(x) -> Decimal:
    try:
        return Decimal(str(x)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except Exception:
        raise AppError("Invalid amount", 400)


def _default_month_yyyy_mm() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def _month_bounds(month: str):
    # month format: YYYY-MM
    try:
        year = int(month[0:4])
        mon = int(month[5:7])
        if month[4] != "-" or mon < 1 or mon > 12:
            raise ValueError()
    except Exception:
        raise AppError("month must be in YYYY-MM format", 400)

    start = datetime(year, mon, 1)
    if mon == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, mon + 1, 1)
    return start, end


def upsert_monthly_budget(user_id: int, category_id: int, month: str, limit_amount):
    if not month:
        month = _default_month_yyyy_mm()

    require_category_owned_by_user(user_id, category_id)

    limit_dec = _to_decimal_amount(limit_amount)
    if limit_dec < 0:
        raise AppError("limit_amount must be >= 0", 400)

    b = MonthlyBudget.query.filter_by(user_id=user_id, category_id=category_id, month=month).first()
    if b:
        b.limit_amount = limit_dec
        db.session.commit()
        return b

    b = MonthlyBudget(user_id=user_id, category_id=category_id, month=month, limit_amount=limit_dec)
    db.session.add(b)
    db.session.commit()
    return b


def monthly_summary(user_id: int, month: str | None):
    month = month or _default_month_yyyy_mm()
    start, end = _month_bounds(month)

    # Your spending = expenses you paid (simple MVP)
    expenses = (
        db.session.query(Expense)
        .filter(Expense.paid_by_user_id == user_id)
        .filter(Expense.created_at >= start)
        .filter(Expense.created_at < end)
        .all()
    )

    # Sum by category_id (None means uncategorized)
    spend_by_cat = {}
    total = Decimal("0.00")

    for e in expenses:
        amt = Decimal(str(e.amount)).quantize(TWOPLACES)
        total += amt
        key = e.category_id  # can be None
        spend_by_cat[key] = spend_by_cat.get(key, Decimal("0.00")) + amt

    # Load categories for user and budgets for month
    categories = Category.query.filter_by(user_id=user_id).all()
    cat_map = {c.id: c.name for c in categories}

    budgets = MonthlyBudget.query.filter_by(user_id=user_id, month=month).all()
    budget_map = {b.category_id: Decimal(str(b.limit_amount)).quantize(TWOPLACES) for b in budgets}

    # Build response rows for all categories + uncategorized if needed
    rows = []
    for c in categories:
        spent = spend_by_cat.get(c.id, Decimal("0.00"))
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
                "overspent": bool(overspent) if overspent is not None else None,
            }
        )

    # Add uncategorized row if there is any spend with category_id=None
    unc = spend_by_cat.get(None, Decimal("0.00"))
    if unc > 0:
        rows.append(
            {
                "category_id": None,
                "category_name": "Uncategorized",
                "spent": float(unc),
                "limit": None,
                "remaining": None,
                "overspent": None,
            }
        )

    rows.sort(key=lambda r: (r["overspent"] is True, r["spent"]), reverse=True)

    return {
        "month": month,
        "total_spent": float(total.quantize(TWOPLACES)),
        "by_category": rows,
    }
