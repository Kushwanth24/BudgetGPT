from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.budget_service import upsert_monthly_budget, monthly_summary
from app.utils.validators import require_json

budget_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budget_bp.post("")
@jwt_required()
def upsert():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["category_id", "limit_amount"])
    month = body.get("month")  # optional
    b = upsert_monthly_budget(
        user_id=user_id,
        category_id=int(body["category_id"]),
        month=month,
        limit_amount=body["limit_amount"],
    )
    return {
        "budget": {
            "id": b.id,
            "user_id": b.user_id,
            "category_id": b.category_id,
            "month": b.month,
            "limit_amount": float(b.limit_amount),
        }
    }, 200


@budget_bp.get("/summary")
@jwt_required()
def summary():
    user_id = int(get_jwt_identity())
    month = request.args.get("month")  # YYYY-MM
    data = monthly_summary(user_id=user_id, month=month)
    return data, 200
