from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.group_service import create_group, list_groups_for_user, add_member_by_email
from app.models.group import Group
from app.utils.validators import require_json

group_bp = Blueprint("groups", __name__, url_prefix="/groups")


def _group_to_dict(g: Group):
    return {
        "id": g.id,
        "name": g.name,
        "created_by_user_id": g.created_by_user_id,
        "created_at": g.created_at.isoformat(),
    }


@group_bp.get("")
@jwt_required()
def list_groups():
    user_id = int(get_jwt_identity())
    groups = list_groups_for_user(user_id)
    return {"groups": [_group_to_dict(g) for g in groups]}, 200


@group_bp.post("")
@jwt_required()
def create():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["name"])
    g = create_group(owner_user_id=user_id, name=body["name"])
    return {"group": _group_to_dict(g)}, 201


@group_bp.post("/<int:group_id>/members")
@jwt_required()
def add_member(group_id: int):
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["email"])
    u = add_member_by_email(group_id=group_id, requester_user_id=user_id, email=body["email"])
    return {"member": {"id": u.id, "email": u.email, "name": u.name}}, 201
