from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.budget_service import (
    upsert_monthly_budget,
    monthly_summary,
)
from app.utils.validators import require_json
from app.utils.responses import success_response

budget_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budget_bp.post("")
@jwt_required()
def upsert():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["category_id", "limit_amount"])

    budget = upsert_monthly_budget(
        user_id=user_id,
        category_id=int(body["category_id"]),
        month=body.get("month"),  # optional YYYY-MM
        limit_amount=body["limit_amount"],
    )

    return success_response(
        {
            "budget": {
                "id": budget.id,
                "user_id": budget.user_id,
                "category_id": budget.category_id,
                "month": budget.month,
                "limit_amount": float(budget.limit_amount),
            }
        },
        status=200,
    )


@budget_bp.get("/summary")
@jwt_required()
def summary():
    user_id = int(get_jwt_identity())
    month = request.args.get("month")  # optional YYYY-MM

    data = monthly_summary(
        user_id=user_id,
        month=month,
    )

    return success_response(
        data,
        status=200,
    )
