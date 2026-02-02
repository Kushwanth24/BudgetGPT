from app.extensions import db
from app.models.category import Category
from app.utils.errors import AppError


def create_category(user_id: int, name: str) -> Category:
    name = (name or "").strip()
    if not name:
        raise AppError("Category name is required", 400)

    existing = Category.query.filter_by(user_id=user_id, name=name).first()
    if existing:
        return existing

    c = Category(user_id=user_id, name=name)
    db.session.add(c)
    db.session.commit()
    return c


def list_categories(user_id: int):
    return Category.query.filter_by(user_id=user_id).order_by(Category.name.asc()).all()


def require_category_owned_by_user(user_id: int, category_id: int) -> Category:
    c = Category.query.filter_by(id=category_id, user_id=user_id).first()
    if not c:
        raise AppError("Category not found", 404)
    return c
