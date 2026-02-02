from decimal import Decimal

from app.extensions import db
from app.models.user import User
from app.models.group_member import GroupMember
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.services.group_service import require_membership


def compute_group_settlements(group_id: int, requester_user_id: int):
    require_membership(group_id, requester_user_id)

    members = GroupMember.query.filter_by(group_id=group_id).all()
    member_ids = [m.user_id for m in members]

    # Net = paid - owed
    net = {uid: Decimal("0.00") for uid in member_ids}

    expenses = Expense.query.filter_by(group_id=group_id).all()
    if not expenses:
        return []

    expense_ids = [e.id for e in expenses]

    # Sum paid
    for e in expenses:
        net[e.paid_by_user_id] = net.get(e.paid_by_user_id, Decimal("0.00")) + Decimal(str(e.amount))

    # Sum owed
    splits = ExpenseSplit.query.filter(ExpenseSplit.expense_id.in_(expense_ids)).all()
    for s in splits:
        net[s.user_id] = net.get(s.user_id, Decimal("0.00")) - Decimal(str(s.amount_owed))

    # Separate creditors/debtors
    creditors = [(uid, amt) for uid, amt in net.items() if amt > 0]
    debtors = [(uid, -amt) for uid, amt in net.items() if amt < 0]  # store positive debt

    # Greedy matching
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    settlements = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        d_uid, d_amt = debtors[i]
        c_uid, c_amt = creditors[j]

        pay = min(d_amt, c_amt)
        if pay > 0:
            settlements.append({"from_user_id": d_uid, "to_user_id": c_uid, "amount": float(pay)})

        d_amt -= pay
        c_amt -= pay

        debtors[i] = (d_uid, d_amt)
        creditors[j] = (c_uid, c_amt)

        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    # Attach emails for convenience
    users = User.query.filter(User.id.in_(member_ids)).all()
    id_to_email = {u.id: u.email for u in users}

    for s in settlements:
        s["from_email"] = id_to_email.get(s["from_user_id"])
        s["to_email"] = id_to_email.get(s["to_user_id"])

    return settlements
