from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.expense_service import create_expense_equal_split
from app.services.balance_service import compute_group_settlements
from app.models.expense import Expense
from app.utils.validators import require_json

expense_bp = Blueprint("expenses", __name__, url_prefix="/groups/<int:group_id>")


def _expense_to_dict(e: Expense):
    return {
        "id": e.id,
        "group_id": e.group_id,
        "paid_by_user_id": e.paid_by_user_id,
        "amount": float(e.amount),
        "description": e.description,
        "category_id": e.category_id,
        "created_at": e.created_at.isoformat(),
    }


@expense_bp.post("/expenses")
@jwt_required()
def create_expense(group_id: int):
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["paid_by_email", "amount"])
    e = create_expense_equal_split(
        group_id=group_id,
        requester_user_id=user_id,
        paid_by_email=body["paid_by_email"],
        amount=body["amount"],
        description=body.get("description"),
        category_id=body.get("category_id"),
    )
    return {"expense": _expense_to_dict(e)}, 201


@expense_bp.get("/balances")
@jwt_required()
def balances(group_id: int):
    user_id = int(get_jwt_identity())
    settlements = compute_group_settlements(group_id=group_id, requester_user_id=user_id)
    return {"settlements": settlements}, 200
