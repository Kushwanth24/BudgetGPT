from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.category_service import create_category, list_categories
from app.utils.validators import require_json

category_bp = Blueprint("categories", __name__, url_prefix="/categories")


@category_bp.get("")
@jwt_required()
def list_all():
    user_id = int(get_jwt_identity())
    cats = list_categories(user_id)
    return {"categories": [{"id": c.id, "name": c.name} for c in cats]}, 200


@category_bp.post("")
@jwt_required()
def create():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["name"])
    c = create_category(user_id=user_id, name=body["name"])
    return {"category": {"id": c.id, "name": c.name}}, 201
