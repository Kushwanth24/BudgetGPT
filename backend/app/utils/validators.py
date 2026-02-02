from app.utils.errors import AppError


def require_json(body, fields):
    if body is None:
        raise AppError(
            "Request body must be valid JSON",
            400,
            code="INVALID_JSON",
        )

    missing = [
        field
        for field in fields
        if field not in body or body.get(field) in (None, "", [])
    ]

    if missing:
        raise AppError(
            "Missing required fields",
            400,
            code="VALIDATION_ERROR",
            details={"missing": missing},
        )
