from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.group_service import (
    create_group,
    list_groups_for_user,
    add_member_by_email,
)
from app.models.group import Group
from app.utils.validators import require_json
from app.utils.responses import success_response

group_bp = Blueprint("groups", __name__, url_prefix="/groups")


def _group_to_dict(group: Group):
    return {
        "id": group.id,
        "name": group.name,
        "created_by_user_id": group.created_by_user_id,
        "created_at": group.created_at.isoformat(),
    }


@group_bp.get("")
@jwt_required()
def list_groups():
    print("🔥 HIT /groups controller")
    user_id = int(get_jwt_identity())

    rows = list_groups_for_user(user_id)
    print("ROWS =", rows)

    return success_response(
        {
            "groups": [
                {
                    "id": row["group"].id,
                    "name": row["group"].name,
                    "created_by_user_id": row["group"].created_by_user_id,
                    "created_at": row["group"].created_at.isoformat(),
                    "member_count": row["member_count"],
                }
                for row in rows
            ]
        },
        status=200,
    )





@group_bp.post("")
@jwt_required()
def create():
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["name"])

    group = create_group(
        owner_user_id=user_id,
        name=body["name"],
    )

    return success_response(
        {
            "group": _group_to_dict(group)
        },
        status=201,
    )


@group_bp.post("/<int:group_id>/members")
@jwt_required()
def add_member(group_id: int):
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True)
    require_json(body, ["email"])

    user = add_member_by_email(
        group_id=group_id,
        requester_user_id=user_id,
        email=body["email"],
    )

    return success_response(
        {
            "member": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            }
        },
        status=201,
    )
