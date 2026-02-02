from app.utils.errors import AppError


def require_json(body, fields):
    if body is None:
        raise AppError("Request body must be JSON", 400)

    missing = [f for f in fields if f not in body or body.get(
        f) in (None, "", [])]
    if missing:
        raise AppError("Missing required fields", 400, {"missing": missing})
