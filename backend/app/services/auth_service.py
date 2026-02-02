from app.extensions import db
from app.models.user import User
from app.utils.errors import AppError


def _normalize_email(email: str) -> str:
    return email.lower().strip()


def register_with_password(email: str, password: str, name: str | None = None) -> User:
    email_norm = _normalize_email(email)

    existing = User.query.filter_by(email=email_norm).first()
    if existing:
        raise AppError("Email already registered", 409)

    user = User(
        email=email_norm,
        name=name,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user


def login_with_password(email: str, password: str) -> User:
    email_norm = _normalize_email(email)

    user = User.query.filter_by(email=email_norm).first()
    if not user or not user.check_password(password):
        raise AppError("Invalid email or password", 401)

    return user


def exchange_google_profile(
    email: str,
    name: str | None,
    provider_user_id: str,
) -> User:
    """
    MVP approach:
    - Frontend (NextAuth) sends verified Google profile fields
    - Backend trusts frontend in Chunk 1
    - Token verification can be added later if needed
    """

    email_norm = _normalize_email(email)

    user = User.query.filter_by(email=email_norm).first()

    if user:
        changed = False

        if user.provider != "google":
            user.provider = "google"
            changed = True

        if provider_user_id and user.provider_user_id != provider_user_id:
            user.provider_user_id = provider_user_id
            changed = True

        if name and not user.name:
            user.name = name
            changed = True

        if changed:
            db.session.commit()

        return user

    user = User(
        email=email_norm,
        name=name,
        provider="google",
        provider_user_id=provider_user_id,
    )

    db.session.add(user)
    db.session.commit()
    return user
