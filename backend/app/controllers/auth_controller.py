from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from app.services.auth_service import (
    register_with_password,
    login_with_password,
    exchange_google_profile,
)
from app.models.user import User
from app.utils.validators import require_json
from app.utils.errors import AppError
from app.utils.response import success_response

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _issue_token(user: User):
    """
    Centralized token issuance so all auth flows behave identically.
    """
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"email": user.email},
    )
    return {
        "access_token": token,
        "user": user.to_public_dict(),
    }


@auth_bp.post("/register")
def register():
    body = request.get_json(silent=True)
    require_json(body, ["email", "password"])

    user = register_with_password(
        email=body["email"],
        password=body["password"],
        name=body.get("name"),
    )

    return success_response(
        _issue_token(user),
        status=201,
    )


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True)
    require_json(body, ["email", "password"])

    user = login_with_password(
        email=body["email"],
        password=body["password"],
    )

    return success_response(
        _issue_token(user),
        status=200,
    )


@auth_bp.post("/exchange-google")
def exchange_google():
    """
    Frontend (NextAuth) sends Google profile info:
    {
      "email": "x@y.com",
      "name": "Name",
      "provider_user_id": "google-sub"
    }
    """
    body = request.get_json(silent=True)
    require_json(body, ["email", "provider_user_id"])

    user = exchange_google_profile(
        email=body["email"],
        name=body.get("name"),
        provider_user_id=body["provider_user_id"],
    )

    return success_response(
        _issue_token(user),
        status=200,
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        raise AppError("User not found", 404, code="NOT_FOUND")

    return success_response(
        {"user": user.to_public_dict()},
        status=200,
    )
