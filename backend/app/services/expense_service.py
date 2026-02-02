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


def _to_decimal_amount(x) -> Decimal:
    try:
        return Decimal(str(x)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except Exception:
        raise AppError("Invalid amount", 400)


def create_expense_equal_split(
    group_id: int,
    requester_user_id: int,
    paid_by_email: str,
    amount,
    description: str | None,
    category_id: int | None = None,
):
    require_membership(group_id, requester_user_id)
    
    cat_id = None
    if category_id is not None:
        cat_id = int(category_id)
        require_category_owned_by_user(requester_user_id, cat_id)


    paid_by_email = (paid_by_email or "").strip().lower()
    if not paid_by_email:
        raise AppError("paid_by_email is required", 400)

    amount_dec = _to_decimal_amount(amount)
    if amount_dec <= 0:
        raise AppError("Amount must be > 0", 400)

    paid_by_user = User.query.filter_by(email=paid_by_email).first()
    if not paid_by_user:
        raise AppError("paid_by_email must belong to an existing user (add them to the group first)", 400)

    # payer must be a member
    payer_membership = GroupMember.query.filter_by(group_id=group_id, user_id=paid_by_user.id).first()
    if not payer_membership:
        raise AppError("paid_by_email is not a member of this group", 400)

    members = GroupMember.query.filter_by(group_id=group_id).all()
    if len(members) < 2:
        raise AppError("Group must have at least 2 members to split expenses", 400)

    member_user_ids = [m.user_id for m in members]

    # Equal split (MVP)
    n = Decimal(len(member_user_ids))
    base = (amount_dec / n).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    # Handle rounding remainder by distributing pennies to first users
    total_base = base * n
    remainder = (amount_dec - total_base).quantize(TWOPLACES, rounding=ROUND_HALF_UP)  # could be 0.01, 0.02, etc.
    pennies = int((remainder / TWOPLACES).to_integral_value()) if remainder > 0 else 0

    expense = Expense(
        group_id=group_id,
        paid_by_user_id=paid_by_user.id,
        amount=amount_dec,
        description=(description or "").strip() or None,
        category_id=cat_id,  
    )
    db.session.add(expense)
    db.session.flush()

    for idx, uid in enumerate(member_user_ids):
        owed = base
        if idx < pennies:
            owed = (owed + TWOPLACES).quantize(TWOPLACES)
        db.session.add(ExpenseSplit(expense_id=expense.id, user_id=uid, amount_owed=owed))

    db.session.commit()
    return expense
