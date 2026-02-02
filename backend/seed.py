from decimal import Decimal
from datetime import datetime
from datetime import datetime, timezone
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.category import Category
from app.models.monthly_budget import MonthlyBudget
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit


def get_or_create_user(email, name):
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(email=email, name=name)
    user.set_password("Pass1234")
    db.session.add(user)
    db.session.flush()
    return user


def get_or_create_category(user, name):
    c = Category.query.filter_by(user_id=user.id, name=name).first()
    if c:
        return c
    c = Category(user_id=user.id, name=name)
    db.session.add(c)
    db.session.flush()
    return c


def main():
    app = create_app()
    with app.app_context():
        print("🌱 Seeding demo data...")

        # -------------------------
        # Users
        # -------------------------
        alice = get_or_create_user("alice@budgetgpt.com", "Alice")
        bob = get_or_create_user("bob@budgetgpt.com", "Bob")
        charlie = get_or_create_user("charlie@budgetgpt.com", "Charlie")

        # -------------------------
        # Group
        # -------------------------
        group = Group.query.filter_by(name="Roommates").first()
        if not group:
            group = Group(name="Roommates", created_by_user_id=alice.id)
            db.session.add(group)
            db.session.flush()

            for u in [alice, bob, charlie]:
                db.session.add(GroupMember(group_id=group.id, user_id=u.id))

        # -------------------------
        # Categories (Alice)
        # -------------------------
        food = get_or_create_category(alice, "Food")
        rent = get_or_create_category(alice, "Rent")
        travel = get_or_create_category(alice, "Travel")

        # -------------------------
        # Monthly Budgets (Alice)
        # -------------------------
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        for cat, limit in [(food, 500), (rent, 1200), (travel, 300)]:
            b = MonthlyBudget.query.filter_by(
                user_id=alice.id,
                category_id=cat.id,
                month=month,
            ).first()
            if not b:
                db.session.add(
                    MonthlyBudget(
                        user_id=alice.id,
                        category_id=cat.id,
                        month=month,
                        limit_amount=Decimal(limit),
                    )
                )

        # -------------------------
        # Expenses
        # -------------------------
        if not Expense.query.filter_by(description="February Rent").first():
            rent_exp = Expense(
                group_id=group.id,
                paid_by_user_id=alice.id,
                amount=Decimal("1500.00"),
                description="February Rent",
                category_id=rent.id,
            )
            db.session.add(rent_exp)
            db.session.flush()

            for u in [alice, bob, charlie]:
                db.session.add(
                    ExpenseSplit(
                        expense_id=rent_exp.id,
                        user_id=u.id,
                        amount_owed=Decimal("500.00"),
                    )
                )

        if not Expense.query.filter_by(description="Groceries").first():
            grocery_exp = Expense(
                group_id=group.id,
                paid_by_user_id=alice.id,
                amount=Decimal("180.00"),
                description="Groceries",
                category_id=food.id,
            )
            db.session.add(grocery_exp)
            db.session.flush()

            db.session.add_all(
                [
                    ExpenseSplit(
                        expense_id=grocery_exp.id,
                        user_id=alice.id,
                        amount_owed=Decimal("30.00"),
                    ),
                    ExpenseSplit(
                        expense_id=grocery_exp.id,
                        user_id=bob.id,
                        amount_owed=Decimal("100.00"),
                    ),
                    ExpenseSplit(
                        expense_id=grocery_exp.id,
                        user_id=charlie.id,
                        amount_owed=Decimal("50.00"),
                    ),
                ]
            )

        db.session.commit()
        print("✅ Demo data seeded successfully.")


if __name__ == "__main__":
    main()
