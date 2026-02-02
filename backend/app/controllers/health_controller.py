from flask import Blueprint, current_app

from app.utils.responses import success_response

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.get("")
def health():
    return success_response(
        {
            "status": "ok",
            "app": current_app.config.get("APP_NAME", "BudgetGPT"),
        },
        status=200,
    )
