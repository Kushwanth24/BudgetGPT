from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.ai_service import generate_ai_insights
from app.utils.validators import require_json

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


@ai_bp.post("/insights")
@jwt_required()
def insights():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["month"])

    result = generate_ai_insights(
        user_id=user_id,
        month=body["month"]
    )

    return {"data": result}, 200
