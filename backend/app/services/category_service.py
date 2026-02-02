from app.extensions import db
from app.models.category import Category
from app.utils.errors import AppError


def _normalize_name(name: str) -> str:
    return (name or "").strip()


def create_category(user_id: int, name: str) -> Category:
    name_norm = _normalize_name(name)
    if not name_norm:
        raise AppError("Category name is required", 400)

    existing = Category.query.filter_by(
        user_id=user_id,
        name=name_norm,
    ).first()

    if existing:
        return existing

    category = Category(
        user_id=user_id,
        name=name_norm,
    )
    db.session.add(category)
    db.session.commit()
    return category


def list_categories(user_id: int):
    return (
        Category.query
        .filter_by(user_id=user_id)
        .order_by(Category.name.asc())
        .all()
    )


def require_category_owned_by_user(user_id: int, category_id: int) -> Category:
    category = Category.query.filter_by(
        id=category_id,
        user_id=user_id,
    ).first()

    if not category:
        raise AppError("Category not found", 404)

    return category
