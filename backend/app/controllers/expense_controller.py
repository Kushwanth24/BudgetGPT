from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.models.category import Category
from app.models.expense import Expense
from app.services.expense_service import (
    create_expense_equal_split,
    create_expense_custom_split,
)
from app.services.balance_service import compute_group_settlements
from app.utils.validators import require_json
from app.utils.response import success_response

expense_bp = Blueprint("expenses", __name__, url_prefix="/groups/<int:group_id>")


def _expense_to_dict(expense: Expense):
    paid_by = User.query.get(expense.paid_by_user_id)
    category = Category.query.get(expense.category_id) if expense.category_id else None

    return {
        "id": expense.id,
        "group_id": expense.group_id,
        "amount": float(expense.amount),
        "description": expense.description,
        "paid_by": {
            "id": paid_by.id,
            "email": paid_by.email,
        } if paid_by else None,
        "category": (
            {
                "id": category.id,
                "name": category.name,
            }
            if category else None
        ),
        "created_at": expense.created_at.isoformat(),
    }


@expense_bp.post("/expenses")
@jwt_required()
def create_expense(group_id: int):
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["paid_by_email", "amount"])

    expense = create_expense_equal_split(
        group_id=group_id,
        requester_user_id=user_id,
        paid_by_email=body["paid_by_email"],
        amount=body["amount"],
        description=body.get("description"),
        category_id=body.get("category_id"),
    )

    return success_response(
        {"expense": _expense_to_dict(expense)},
        status=201,
    )


@expense_bp.post("/expenses/custom")
@jwt_required()
def create_expense_custom(group_id: int):
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["paid_by_email", "amount", "splits"])

    expense = create_expense_custom_split(
        group_id=group_id,
        requester_user_id=user_id,
        paid_by_email=body["paid_by_email"],
        amount=body["amount"],
        splits=body["splits"],
        description=body.get("description"),
        category_id=body.get("category_id"),
    )

    return success_response(
        {"expense": _expense_to_dict(expense)},
        status=201,
    )


@expense_bp.get("/balances")
@jwt_required()
def balances(group_id: int):
    user_id = int(get_jwt_identity())

    settlements = compute_group_settlements(
        group_id=group_id,
        requester_user_id=user_id,
    )

    return success_response(
        {"settlements": settlements},
        status=200,
    )
