from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import SuperAdminCreate, UserCreate, UserRead
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_mobile,
    get_user_by_role,
)
from app.utils.security import create_access_token

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if payload.role != Role.employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration can only create employee users.",
        )
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")
    if get_user_by_mobile(db, payload.mobile):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mobile is already registered.")
    return create_user(db, payload)


@router.post("/setup-superadmin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def setup_superadmin(payload: SuperAdminCreate, db: Session = Depends(get_db)) -> User:
    if get_user_by_role(db, Role.superadmin):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Superadmin is already configured.")
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")
    if get_user_by_mobile(db, payload.mobile):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mobile is already registered.")

    superadmin_payload = UserCreate(
        full_name=payload.full_name,
        email=payload.email,
        mobile=payload.mobile,
        password=payload.password,
        role=Role.superadmin,
        is_active=True,
        can_add_manual_ledger_entries=True,
    )
    return create_user(db, superadmin_payload)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=access_token, user=user)


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(authenticated_user)) -> User:
    return current_user
