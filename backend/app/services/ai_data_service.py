from decimal import Decimal
from datetime import datetime

from app.extensions import db
from app.models.expense import Expense
from app.models.monthly_budget import MonthlyBudget
from app.models.category import Category
from app.services.balance_service import compute_group_settlements
from app.services.group_service import list_groups_for_user


def get_monthly_ai_context(user_id: int, month: str):
    """
    Collects all relevant data needed for AI reasoning.
    Returns a pure-data dict (NO interpretation).
    """

    # ---------- Budgets ----------
    budgets = (
        db.session.query(MonthlyBudget, Category)
        .join(Category, Category.id == MonthlyBudget.category_id)
        .filter(MonthlyBudget.user_id == user_id)
        .filter(MonthlyBudget.month == month)
        .all()
    )

    budget_map = {
        b.category_id: {
            "category": c.name,
            "limit": float(b.limit_amount),
            "spent": 0.0,
        }
        for b, c in budgets
    }

    # ---------- Expenses ----------
    expenses = (
        Expense.query
        .filter(Expense.paid_by_user_id == user_id)
        .filter(Expense.created_at.like(f"{month}%"))
        .all()
    )

    total_spent = Decimal("0.00")

    for e in expenses:
        amt = Decimal(str(e.amount))
        total_spent += amt

        if e.category_id in budget_map:
            budget_map[e.category_id]["spent"] += float(amt)

    categories = list(budget_map.values())

    # ---------- Group Balances ----------
    groups = list_groups_for_user(user_id)
    settlements = []

    for g in groups:
        group = g["group"]
        balances = compute_group_settlements(group.id, user_id)
        settlements.extend(balances)

    return {
        "month": month,
        "total_spent": float(total_spent),
        "categories": categories,
        "group_balances": settlements,
    }
