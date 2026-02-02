from app.extensions import db
from app.models.user import User
from app.models.group import Group
from app.models.group_member import GroupMember
from app.utils.errors import AppError


def create_group(owner_user_id: int, name: str) -> Group:
    name = (name or "").strip()
    if not name:
        raise AppError("Group name is required", 400)

    group = Group(name=name, created_by_user_id=owner_user_id)
    db.session.add(group)
    db.session.flush()  # get group.id

    # Add owner as member
    gm = GroupMember(group_id=group.id, user_id=owner_user_id)
    db.session.add(gm)

    db.session.commit()
    return group


def list_groups_for_user(user_id: int):
    groups = (
        db.session.query(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.user_id == user_id)
        .order_by(Group.created_at.desc())
        .all()
    )
    return groups


def require_membership(group_id: int, user_id: int) -> None:
    exists = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not exists:
        raise AppError("You are not a member of this group", 403)


def add_member_by_email(group_id: int, requester_user_id: int, email: str) -> User:
    require_membership(group_id, requester_user_id)

    email_norm = (email or "").strip().lower()
    if not email_norm:
        raise AppError("Email is required", 400)

    user = User.query.filter_by(email=email_norm).first()
    if not user:
        # MVP: create an "invited" user record (no password/provider)
        user = User(email=email_norm, name=None, provider=None)
        db.session.add(user)
        db.session.flush()

    # Add membership if not exists
    existing = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if existing:
        return user

    db.session.add(GroupMember(group_id=group_id, user_id=user.id))
    db.session.commit()
    return user
