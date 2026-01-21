"""
G1: 认证授权API - 路由定义
===========================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

from .models import (
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    PermissionListResponse, CurrentUser, MessageResponse, UserStatus
)
from .service import AuthService

# ============================================================
# 路由器和依赖
# ============================================================

router = APIRouter(tags=["认证授权"])
security = HTTPBearer(auto_error=False)

# 全局服务实例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def set_auth_service(service: AuthService):
    """设置认证服务（测试用）"""
    global _auth_service
    _auth_service = service


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> CurrentUser:
    """获取当前用户（认证必须）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    user = await auth_service.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的Token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[CurrentUser]:
    """获取当前用户（可选）"""
    if not credentials:
        return None

    token = credentials.credentials
    return await auth_service.get_current_user(token)


def require_permission(permission: str):
    """权限检查依赖"""
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> CurrentUser:
        if not auth_service.check_permission(current_user.role.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}"
            )
        return current_user
    return permission_checker


# ============================================================
# 认证接口
# ============================================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录

    使用用户名和密码登录，获取访问令牌。
    """
    try:
        result = await auth_service.login(
            username=request.username,
            password=request.password,
            tenant_id=request.tenant_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    return result


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登出

    使当前Token失效。
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息"
        )

    await auth_service.logout(credentials.credentials)
    return MessageResponse(message="登出成功")


@router.post("/auth/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新Token

    使用刷新令牌获取新的访问令牌。
    """
    result = await auth_service.refresh_token(request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的刷新令牌"
        )

    return RefreshResponse(**result)


@router.get("/auth/me", response_model=CurrentUser)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    获取当前用户信息

    返回当前登录用户的详细信息，包括角色和权限。
    """
    return current_user


# ============================================================
# 用户管理接口
# ============================================================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role_id: Optional[str] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("users:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取用户列表

    支持分页、角色筛选、状态筛选和搜索。
    """
    result = await auth_service.list_users(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        role_id=role_id,
        status=status,
        search=search
    )
    return UserListResponse(**result)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    current_user: CurrentUser = Depends(require_permission("users:write")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    创建用户

    创建新用户并分配角色。
    """
    try:
        return await auth_service.create_user(
            tenant_id=current_user.tenant_id,
            data=request
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_permission("users:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取用户详情
    """
    user = await auth_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: CurrentUser = Depends(require_permission("users:write")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    更新用户信息
    """
    user = await auth_service.update_user(user_id, request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_permission("users:delete")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    删除用户
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    success = await auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return MessageResponse(message="用户已删除")


# ============================================================
# 角色管理接口
# ============================================================

@router.get("/roles", response_model=RoleListResponse)
async def list_roles(
    current_user: CurrentUser = Depends(require_permission("roles:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取角色列表
    """
    roles = await auth_service.list_roles(current_user.tenant_id)
    return RoleListResponse(items=roles)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreate,
    current_user: CurrentUser = Depends(require_permission("roles:write")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    创建角色
    """
    return await auth_service.create_role(
        tenant_id=current_user.tenant_id,
        data=request
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: CurrentUser = Depends(require_permission("roles:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取角色详情
    """
    role = await auth_service.get_role(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    request: RoleUpdate,
    current_user: CurrentUser = Depends(require_permission("roles:write")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    更新角色
    """
    try:
        role = await auth_service.update_role(role_id, request)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/roles/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: str,
    current_user: CurrentUser = Depends(require_permission("roles:write")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    删除角色
    """
    try:
        success = await auth_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return MessageResponse(message="角色已删除")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================
# 权限接口
# ============================================================

@router.get("/permissions", response_model=PermissionListResponse)
async def list_permissions(
    current_user: CurrentUser = Depends(require_permission("roles:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    获取所有可用权限
    """
    permissions = auth_service.get_all_permissions()
    return PermissionListResponse(permissions=permissions)
