from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, get_user_by_email, get_user_by_mobile

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(authenticated_user)) -> User:
    return current_user


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> User:
    if payload.role == Role.superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin users can only be created through the one-time setup endpoint.",
        )
    if payload.role == Role.admin and current_user.role != Role.superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only superadmin can create admin users.")
    if payload.role in {Role.employee, Role.manager} and current_user.role not in {Role.admin, Role.superadmin}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or superadmin can create employee and manager users.",
        )
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")
    if get_user_by_mobile(db, payload.mobile):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mobile is already registered.")
    return create_user(db, payload)
