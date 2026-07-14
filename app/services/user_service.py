from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Role, User
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash, verify_password


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_mobile(db: Session, mobile: str) -> User | None:
    return db.scalar(select(User).where(User.mobile == mobile))


def get_user_by_role(db: Session, role: Role) -> User | None:
    return db.scalar(select(User).where(User.role == role).limit(1))


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        mobile=payload.mobile,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        is_active=payload.is_active,
        can_add_manual_ledger_entries=payload.can_add_manual_ledger_entries,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
