from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ALL_PERMISSIONS
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.modules.users.models import Department, Permission, Role, User
from app.modules.users.schemas import BootstrapAdmin, ChangePasswordRequest, ProfileUpdate, RoleCreate, UserCreate, UserUpdate


async def ensure_permissions(db: AsyncSession) -> dict[str, Permission]:
    result = await db.execute(select(Permission))
    existing = {item.key: item for item in result.scalars()}
    for key in ALL_PERMISSIONS - existing.keys():
        permission = Permission(key=key, description=key.replace(".", " ").title())
        db.add(permission)
        existing[key] = permission
    await db.flush()
    return existing


async def bootstrap_admin(db: AsyncSession, data: BootstrapAdmin) -> User:
    user_count = await db.scalar(select(func.count(User.id)))
    if user_count:
        raise ValueError("System is already initialized")
    permissions = await ensure_permissions(db)
    role = Role(name="Admin", description="System administrator", is_system=True)
    role.permissions = list(permissions.values())
    user = User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password), role=role)
    db.add_all([role, user])
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def issue_tokens(user: User) -> dict[str, str]:
    return {
        "access_token": create_token(user.id, user.token_version, "access"),
        "refresh_token": create_token(user.id, user.token_version, "refresh"),
        "token_type": "bearer",
    }


async def refresh_tokens(db: AsyncSession, token: str) -> dict[str, str]:
    payload = decode_token(token, "refresh")
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active or user.token_version != payload.get("ver"):
        raise ValueError("Invalid refresh session")
    return issue_tokens(user)


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    if await db.scalar(select(User.id).where(User.email == data.email.lower())):
        raise ValueError("Email already exists")
    if not await db.get(Role, data.role_id):
        raise ValueError("Role not found")
    if data.department_id and not await db.get(Department, data.department_id):
        raise ValueError("Department not found")
    user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role_id=data.role_id,
        department_id=data.department_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    if data.role_id is not None and not await db.get(Role, data.role_id):
        raise ValueError("Role not found")
    if data.department_id is not None and not await db.get(Department, data.department_id):
        raise ValueError("Department not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    if data.is_active is False:
        user.token_version += 1
    await db.commit()
    await db.refresh(user)
    return user


async def update_profile(db: AsyncSession, user: User, data: ProfileUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(db: AsyncSession, user: User, data: ChangePasswordRequest) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise ValueError("كلمة المرور الحالية غير صحيحة")
    user.password_hash = hash_password(data.new_password)
    user.token_version += 1
    await db.commit()


async def admin_reset_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    user.token_version += 1
    await db.commit()


async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    if await db.scalar(select(Role.id).where(Role.name == data.name)):
        raise ValueError("Role name already exists")
    permissions = await ensure_permissions(db)
    unknown = set(data.permission_keys) - permissions.keys()
    if unknown:
        raise ValueError(f"Unknown permissions: {', '.join(sorted(unknown))}")
    role = Role(name=data.name, description=data.description)
    role.permissions = [permissions[key] for key in data.permission_keys]
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role
