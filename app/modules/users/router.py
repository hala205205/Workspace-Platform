from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import ROLE_MANAGE, USER_MANAGE
from app.modules.users import services
from app.modules.users.models import Department, Role, User
from app.modules.users.schemas import (
    AdminPasswordReset,
    BootstrapAdmin,
    ChangePasswordRequest,
    DepartmentCreate,
    DepartmentResponse,
    ProfileUpdate,
    RefreshRequest,
    RoleCreate,
    RoleResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])
directory_router = APIRouter(prefix="/directory", tags=["Directory"])


@router.post("/bootstrap", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap(data: BootstrapAdmin, db: AsyncSession = Depends(get_db)):
    try:
        return UserResponse.from_user(await services.bootstrap_admin(db, data))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await services.authenticate(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return services.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await services.refresh_tokens(db, data.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout", status_code=204)
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.token_version += 1
    await db.commit()


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.from_user(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(data: ProfileUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return UserResponse.from_user(await services.update_profile(db, user, data))


@router.post("/change-password", status_code=204)
async def change_password(data: ChangePasswordRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        await services.change_password(db, user, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(USER_MANAGE))):
    try:
        return UserResponse.from_user(await services.create_user(db, data))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.post("/users/{user_id}/reset-password", status_code=204)
async def admin_reset_password(
    user_id: str,
    data: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(USER_MANAGE)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await services.admin_reset_password(db, user, data.new_password)


@admin_router.get("/users", response_model=list[UserResponse])
async def list_users(
    q: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(USER_MANAGE)),
):
    query = select(User).order_by(User.name).limit(limit).offset(offset)
    if q:
        query = query.where(User.name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    return [UserResponse.from_user(user) for user in (await db.execute(query)).scalars()]


@admin_router.patch("/users/{user_id}", response_model=UserResponse)
async def patch_user(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(USER_MANAGE))):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return UserResponse.from_user(await services.update_user(db, user, data))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.post("/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(data: DepartmentCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(USER_MANAGE))):
    if await db.scalar(select(Department.id).where(Department.name == data.name)):
        raise HTTPException(status_code=400, detail="Department name already exists")
    if data.parent_id and not await db.get(Department, data.parent_id):
        raise HTTPException(status_code=400, detail="Parent department not found")
    item = Department(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@admin_router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(USER_MANAGE))):
    return list((await db.execute(select(Department).order_by(Department.name))).scalars())


@admin_router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ROLE_MANAGE))):
    try:
        role = await services.create_role(db, data)
        return RoleResponse(id=role.id, name=role.name, description=role.description, permission_keys=sorted(p.key for p in role.permissions))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.get("/roles", response_model=list[RoleResponse])
async def list_roles(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ROLE_MANAGE))):
    roles = list((await db.execute(select(Role).order_by(Role.name))).scalars())
    return [RoleResponse(id=r.id, name=r.name, description=r.description, permission_keys=sorted(p.key for p in r.permissions)) for r in roles]


@directory_router.get("/audiences")
async def list_audiences(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    users = list((await db.execute(select(User).where(User.is_active.is_(True)).order_by(User.name))).scalars())
    roles = list((await db.execute(select(Role).order_by(Role.name))).scalars())
    departments = list((await db.execute(select(Department).order_by(Department.name))).scalars())
    return {
        "users": [{"id": item.id, "name": item.name} for item in users],
        "roles": [{"id": item.id, "name": item.name} for item in roles],
        "departments": [{"id": item.id, "name": item.name} for item in departments],
    }
