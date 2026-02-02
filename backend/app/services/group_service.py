from sqlalchemy import func

from app.extensions import db
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User
from app.utils.errors import AppError


# =========================
# Helpers
# =========================

def require_membership(group_id: int, user_id: int) -> None:
    member = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=user_id,
    ).first()
    if not member:
        raise AppError("You are not a member of this group", 403)


# =========================
# Core services
# =========================

def create_group(owner_user_id: int, name: str) -> Group:
    """
    Create a new group and add the owner as the first member.
    """
    name = (name or "").strip()
    if not name:
        raise AppError("Group name is required", 400)

    group = Group(
        name=name,
        created_by_user_id=owner_user_id,
    )
    db.session.add(group)
    db.session.flush()  # ensures group.id is available

    db.session.add(
        GroupMember(
            group_id=group.id,
            user_id=owner_user_id,
        )
    )

    db.session.commit()
    return group


def list_groups_for_user(user_id: int):
    """
    List all groups the user belongs to, with member count.

    Returns:
        List[dict]: [
          {
            "group": Group,
            "member_count": int
          }
        ]
    """
    rows = (
        db.session.query(
            Group,
            func.count(GroupMember.user_id).label("member_count"),
        )
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(
            GroupMember.group_id.in_(
                db.session.query(GroupMember.group_id)
                .filter(GroupMember.user_id == user_id)
            )
        )
        .group_by(Group.id)
        .order_by(Group.created_at.desc())
        .all()
    )

    return [
        {
            "group": group,
            "member_count": member_count,
        }
        for group, member_count in rows
    ]


def add_member_by_email(
    group_id: int,
    requester_user_id: int,
    email: str,
) -> User:
    """
    Add a user to a group by email.
    Only existing group members may add others.
    """
    require_membership(group_id, requester_user_id)

    email = (email or "").strip().lower()
    if not email:
        raise AppError("Email is required", 400)

    user = User.query.filter_by(email=email).first()
    if not user:
        raise AppError("User not found", 404)

    existing = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=user.id,
    ).first()
    if existing:
        return user  # idempotent add

    db.session.add(
        GroupMember(
            group_id=group_id,
            user_id=user.id,
        )
    )
    db.session.commit()
    return user
