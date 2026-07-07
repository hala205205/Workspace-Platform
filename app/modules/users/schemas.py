from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class BootstrapAdmin(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    role_id: str
    department_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    role_id: str | None = None
    department_id: str | None = None
    is_active: bool | None = None
    notifications_enabled: bool | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    notifications_enabled: bool | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=12, max_length=72)
    new_password: str = Field(min_length=12, max_length=72)


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=72)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role_id: str
    department_id: str | None
    is_active: bool
    notifications_enabled: bool
    created_at: datetime
    role_name: str | None = None
    permission_keys: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            role_id=user.role_id,
            department_id=user.department_id,
            is_active=user.is_active,
            notifications_enabled=user.notifications_enabled,
            created_at=user.created_at,
            role_name=user.role.name if user.role else None,
            permission_keys=sorted(user.permission_keys),
        )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    parent_id: str | None = None


class DepartmentResponse(DepartmentCreate):
    id: str
    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    permission_keys: list[str] = []


class RoleResponse(BaseModel):
    id: str
    name: str
    description: str | None
    permission_keys: list[str]
