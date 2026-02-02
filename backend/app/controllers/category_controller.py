from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.category_service import (
    create_category,
    list_categories,
)
from app.utils.validators import require_json
from app.utils.response import success_response

category_bp = Blueprint("categories", __name__, url_prefix="/categories")


@category_bp.get("")
@jwt_required()
def list_all():
    user_id = int(get_jwt_identity())
    categories = list_categories(user_id)

    return success_response(
        {
            "categories": [
                {"id": c.id, "name": c.name}
                for c in categories
            ]
        },
        status=200,
    )


@category_bp.post("")
@jwt_required()
def create():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["name"])

    category = create_category(
        user_id=user_id,
        name=body["name"],
    )

    return success_response(
        {
            "category": {
                "id": category.id,
                "name": category.name,
            }
        },
        status=201,
    )
