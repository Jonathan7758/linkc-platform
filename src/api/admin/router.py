"""
G7: 系统管理API - 路由层
============================
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .models import (
    TenantStatus, UserStatus, UserRole, AuditAction,
    TenantCreate, TenantUpdate, UserCreate, UserUpdate, SystemConfigUpdate,
    TenantListResponse, TenantDetail, TenantCreateResponse,
    UserListResponse, UserDetail,
    AuditLogResponse, SystemConfigListResponse, SystemConfig, SystemHealthResponse
)
from .service import AdminService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# 单例服务实例
_admin_service: AdminService = None


def get_admin_service() -> AdminService:
    """获取管理服务实例（单例）"""
    global _admin_service
    if _admin_service is None:
        _admin_service = AdminService()
    return _admin_service


def get_tenant_id() -> str:
    """获取租户ID"""
    return "tenant_001"


def get_current_user_id() -> str:
    """获取当前用户ID"""
    return "user_001"


# ============================================================
# 租户管理
# ============================================================

@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    tenant_status: Optional[TenantStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AdminService = Depends(get_admin_service)
):
    """获取租户列表"""
    return await service.list_tenants(tenant_status, search, page, page_size)


@router.get("/tenants/{tenant_id}", response_model=TenantDetail)
async def get_tenant(
    tenant_id: str,
    service: AdminService = Depends(get_admin_service)
):
    """获取租户详情"""
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    return tenant


@router.post("/tenants", response_model=TenantCreateResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    service: AdminService = Depends(get_admin_service)
):
    """创建租户"""
    return await service.create_tenant(data)


@router.put("/tenants/{tenant_id}", response_model=TenantDetail)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    service: AdminService = Depends(get_admin_service)
):
    """更新租户"""
    tenant = await service.update_tenant(tenant_id, data)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    return tenant


@router.delete("/tenants/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: str,
    service: AdminService = Depends(get_admin_service)
):
    """删除租户"""
    if not await service.delete_tenant(tenant_id):
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")


# ============================================================
# 用户管理
# ============================================================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    tenant_id: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    user_status: Optional[UserStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AdminService = Depends(get_admin_service)
):
    """获取用户列表"""
    return await service.list_users(tenant_id, role, user_status, search, page, page_size)


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: str,
    service: AdminService = Depends(get_admin_service)
):
    """获取用户详情"""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@router.post("/users", response_model=UserDetail, status_code=201)
async def create_user(
    data: UserCreate,
    tenant_id: str = Depends(get_tenant_id),
    service: AdminService = Depends(get_admin_service)
):
    """创建用户"""
    return await service.create_user(tenant_id, data)


@router.put("/users/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: str,
    data: UserUpdate,
    service: AdminService = Depends(get_admin_service)
):
    """更新用户"""
    user = await service.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    service: AdminService = Depends(get_admin_service)
):
    """删除用户"""
    if not await service.delete_user(user_id):
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")


# ============================================================
# 审计日志
# ============================================================

@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(
    tenant_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    service: AdminService = Depends(get_admin_service)
):
    """获取审计日志"""
    return await service.get_audit_logs(
        tenant_id, user_id, action, resource_type,
        start_time, end_time, page, page_size
    )


# ============================================================
# 系统配置
# ============================================================

@router.get("/configs", response_model=SystemConfigListResponse)
async def get_configs(
    prefix: Optional[str] = Query(None, description="配置前缀"),
    service: AdminService = Depends(get_admin_service)
):
    """获取系统配置"""
    return await service.get_configs(prefix)


@router.put("/configs", response_model=SystemConfig)
async def update_config(
    data: SystemConfigUpdate,
    user_id: str = Depends(get_current_user_id),
    service: AdminService = Depends(get_admin_service)
):
    """更新系统配置"""
    return await service.update_config(data, user_id)


# ============================================================
# 系统健康
# ============================================================

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    service: AdminService = Depends(get_admin_service)
):
    """获取系统健康状态"""
    return await service.get_system_health()
