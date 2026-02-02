from decimal import Decimal

from app.extensions import db
from app.models.user import User
from app.models.group_member import GroupMember
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.services.group_service import require_membership

ZERO = Decimal("0.00")


def compute_group_settlements(group_id: int, requester_user_id: int):
    # Ensure requester belongs to the group
    require_membership(group_id, requester_user_id)

    members = GroupMember.query.filter_by(group_id=group_id).all()
    member_ids = [m.user_id for m in members]

    if not member_ids:
        return []

    # Net balance per user: paid - owed
    net = {uid: ZERO for uid in member_ids}

    expenses = Expense.query.filter_by(group_id=group_id).all()
    if not expenses:
        return []

    expense_ids = [e.id for e in expenses]

    # Sum amounts paid
    for e in expenses:
        net[e.paid_by_user_id] += Decimal(str(e.amount))

    # Sum amounts owed
    splits = (
    ExpenseSplit.query
    .filter(ExpenseSplit.expense_id.in_(expense_ids))
    .filter(ExpenseSplit.user_id.in_(member_ids))
    .all()
)


    for s in splits:
        if s.user_id not in net:
            # Ignore splits for users no longer in group
            continue
        net[s.user_id] -= Decimal(str(s.amount_owed))


    # Separate creditors (positive) and debtors (negative)
    creditors = [(uid, amt) for uid, amt in net.items() if amt > ZERO]
    debtors = [(uid, -amt) for uid, amt in net.items() if amt < ZERO]  # store positive debt

    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    settlements = []
    i = j = 0

    # Greedy settlement
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt_amt = debtors[i]
        creditor_id, credit_amt = creditors[j]

        pay = min(debt_amt, credit_amt)

        if pay > ZERO:
            settlements.append(
                {
                    "from_user_id": debtor_id,
                    "to_user_id": creditor_id,
                    "amount": float(pay),
                }
            )

        debt_amt -= pay
        credit_amt -= pay

        debtors[i] = (debtor_id, debt_amt)
        creditors[j] = (creditor_id, credit_amt)

        if debtors[i][1] == ZERO:
            i += 1
        if creditors[j][1] == ZERO:
            j += 1

    # Attach emails for frontend / AI convenience
    users = User.query.filter(User.id.in_(member_ids)).all()
    id_to_email = {u.id: u.email for u in users}

    for s in settlements:
        s["from_email"] = id_to_email.get(s["from_user_id"])
        s["to_email"] = id_to_email.get(s["to_user_id"])

    return settlements
