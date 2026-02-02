from decimal import Decimal, ROUND_HALF_UP

from app.extensions import db
from app.models.user import User
from app.models.group_member import GroupMember
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.services.group_service import require_membership
from app.services.category_service import require_category_owned_by_user
from app.utils.errors import AppError

TWOPLACES = Decimal("0.01")


def _to_decimal_amount(value) -> Decimal:
    try:
        return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except Exception:
        raise AppError("Invalid amount", 400)


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _require_user_by_email(email: str) -> User:
    user = User.query.filter_by(email=email).first()
    if not user:
        raise AppError(
            "paid_by_email must belong to an existing user (add them to the group first)",
            400,
        )
    return user


def _require_group_members(group_id: int):
    members = GroupMember.query.filter_by(group_id=group_id).all()
    if len(members) < 2:
        raise AppError("Group must have at least 2 members to split expenses", 400)
    return members


# =========================
# Equal split
# =========================

def create_expense_equal_split(
    group_id: int,
    requester_user_id: int,
    paid_by_email: str,
    amount,
    description: str | None,
    category_id: int | None = None,
):
    require_membership(group_id, requester_user_id)

    # Validate category (optional)
    cat_id = None
    if category_id is not None:
        cat_id = int(category_id)
        require_category_owned_by_user(requester_user_id, cat_id)

    email = _normalize_email(paid_by_email)
    if not email:
        raise AppError("paid_by_email is required", 400)

    amount_dec = _to_decimal_amount(amount)
    if amount_dec <= 0:
        raise AppError("Amount must be > 0", 400)

    paid_by_user = _require_user_by_email(email)

    if not GroupMember.query.filter_by(
        group_id=group_id,
        user_id=paid_by_user.id,
    ).first():
        raise AppError("paid_by_email is not a member of this group", 400)

    members = _require_group_members(group_id)
    member_ids = [m.user_id for m in members]

    # Equal split math
    n = Decimal(len(member_ids))
    base = (amount_dec / n).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    total_base = base * n
    remainder = (amount_dec - total_base).quantize(TWOPLACES)
    pennies = int((remainder / TWOPLACES)) if remainder > 0 else 0

    expense = Expense(
        group_id=group_id,
        paid_by_user_id=paid_by_user.id,
        amount=amount_dec,
        description=(description or "").strip() or None,
        category_id=cat_id,
    )
    db.session.add(expense)
    db.session.flush()

    for idx, uid in enumerate(member_ids):
        owed = base + (TWOPLACES if idx < pennies else Decimal("0.00"))
        db.session.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=uid,
                amount_owed=owed,
            )
        )

    db.session.commit()
    return expense


# =========================
# Custom split
# =========================

def create_expense_custom_split(
    group_id: int,
    requester_user_id: int,
    paid_by_email: str,
    amount,
    splits: list[dict],
    description: str | None,
    category_id: int | None = None,
):
    require_membership(group_id, requester_user_id)

    email = _normalize_email(paid_by_email)
    if not email:
        raise AppError("paid_by_email is required", 400)

    amount_dec = _to_decimal_amount(amount)
    if amount_dec <= 0:
        raise AppError("Amount must be > 0", 400)

    if not isinstance(splits, list) or not splits:
        raise AppError("splits must be a non-empty list", 400)

    paid_by_user = _require_user_by_email(email)

    if not GroupMember.query.filter_by(
        group_id=group_id,
        user_id=paid_by_user.id,
    ).first():
        raise AppError("paid_by_email is not a member of this group", 400)

    members = _require_group_members(group_id)
    member_ids = {m.user_id for m in members}

    # Validate splits
    seen_emails = set()
    split_rows: list[tuple[int, Decimal]] = []
    total = Decimal("0.00")

    for idx, split in enumerate(splits):
        if not isinstance(split, dict):
            raise AppError(f"splits[{idx}] must be an object", 400)

        email = _normalize_email(split.get("email"))
        if not email:
            raise AppError(f"splits[{idx}].email is required", 400)

        if email in seen_emails:
            raise AppError(f"Duplicate split user: {email}", 400)
        seen_emails.add(email)

        split_amt = _to_decimal_amount(split.get("amount"))
        if split_amt < 0:
            raise AppError(f"splits[{idx}].amount must be >= 0", 400)

        user = User.query.filter_by(email=email).first()
        if not user:
            raise AppError(f"Split user does not exist: {email}", 400)
        if user.id not in member_ids:
            raise AppError(f"Split user is not a member of this group: {email}", 400)

        split_rows.append((user.id, split_amt))
        total = (total + split_amt).quantize(TWOPLACES)

    if total != amount_dec:
        raise AppError(
            f"Sum of splits ({total}) must equal amount ({amount_dec})",
            400,
        )

    # Create expense
    expense = Expense(
        group_id=group_id,
        paid_by_user_id=paid_by_user.id,
        amount=amount_dec,
        description=(description or "").strip() or None,
        category_id=category_id,
    )
    db.session.add(expense)
    db.session.flush()

    for uid, owed in split_rows:
        db.session.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=uid,
                amount_owed=owed,
            )
        )

    db.session.commit()
    return expense
