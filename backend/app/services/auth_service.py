from app.extensions import db
from app.models.user import User
from app.utils.errors import AppError


def register_with_password(email: str, password: str, name: str | None = None) -> User:
    existing = User.query.filter_by(email=email.lower().strip()).first()
    if existing:
        raise AppError("Email already registered", 409)

    user = User(email=email.lower().strip(), name=name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user


def login_with_password(email: str, password: str) -> User:
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user or not user.check_password(password):
        raise AppError("Invalid email or password", 401)
    return user


def exchange_google_profile(email: str, name: str | None, provider_user_id: str) -> User:
    """
    MVP approach: NextAuth (frontend) supplies verified Google profile fields.
    We DO NOT validate Google tokens here in Chunk 1 to keep it simple.
    Later we can add token verification if needed.
    """
    email_norm = email.lower().strip()

    user = User.query.filter_by(email=email_norm).first()
    if user:
        # Link provider info if missing
        changed = False
        if user.provider != "google":
            user.provider = "google"
            changed = True
        if provider_user_id and user.provider_user_id != provider_user_id:
            user.provider_user_id = provider_user_id
            changed = True
        if name and (not user.name):
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
