from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    mobile: str = Field(min_length=7, max_length=20)
    role: Role = Role.employee
    is_active: bool = True
    can_add_manual_ledger_entries: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class SuperAdminCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    mobile: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: Role | None = None
    is_active: bool | None = None
    can_add_manual_ledger_entries: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
