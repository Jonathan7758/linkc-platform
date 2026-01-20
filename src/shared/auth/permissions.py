"""
F4: 认证授权模块 - 权限定义
============================
权限枚举和角色-权限映射
"""

from enum import Enum
from typing import List
from .models import UserRole


class Permission(str, Enum):
    """系统权限"""
    # 空间管理
    SPACE_READ = "space:read"
    SPACE_WRITE = "space:write"
    SPACE_DELETE = "space:delete"

    # 任务管理
    TASK_READ = "task:read"
    TASK_WRITE = "task:write"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"

    # 机器人管理
    ROBOT_READ = "robot:read"
    ROBOT_CONTROL = "robot:control"
    ROBOT_CONFIG = "robot:config"

    # Agent管理
    AGENT_READ = "agent:read"
    AGENT_CONTROL = "agent:control"
    AGENT_CONFIG = "agent:config"

    # 用户管理
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # 报表
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"

    # 系统管理
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"


# 角色-权限映射
ROLE_PERMISSIONS: dict[UserRole, List[str]] = {
    UserRole.SUPER_ADMIN: ["*"],  # 所有权限

    UserRole.TENANT_ADMIN: [
        Permission.SPACE_READ.value, Permission.SPACE_WRITE.value, Permission.SPACE_DELETE.value,
        Permission.TASK_READ.value, Permission.TASK_WRITE.value, Permission.TASK_DELETE.value, Permission.TASK_ASSIGN.value,
        Permission.ROBOT_READ.value, Permission.ROBOT_CONTROL.value, Permission.ROBOT_CONFIG.value,
        Permission.AGENT_READ.value, Permission.AGENT_CONTROL.value, Permission.AGENT_CONFIG.value,
        Permission.USER_READ.value, Permission.USER_WRITE.value, Permission.USER_DELETE.value,
        Permission.REPORT_READ.value, Permission.REPORT_EXPORT.value,
        Permission.AUDIT_READ.value,
    ],

    UserRole.MANAGER: [
        Permission.SPACE_READ.value, Permission.SPACE_WRITE.value,
        Permission.TASK_READ.value, Permission.TASK_WRITE.value, Permission.TASK_ASSIGN.value,
        Permission.ROBOT_READ.value, Permission.ROBOT_CONTROL.value,
        Permission.AGENT_READ.value, Permission.AGENT_CONTROL.value,
        Permission.USER_READ.value,
        Permission.REPORT_READ.value, Permission.REPORT_EXPORT.value,
    ],

    UserRole.TRAINER: [
        Permission.SPACE_READ.value,
        Permission.TASK_READ.value, Permission.TASK_WRITE.value,
        Permission.ROBOT_READ.value, Permission.ROBOT_CONTROL.value,
        Permission.AGENT_READ.value, Permission.AGENT_CONTROL.value, Permission.AGENT_CONFIG.value,
        Permission.REPORT_READ.value,
    ],

    UserRole.OPERATOR: [
        Permission.SPACE_READ.value,
        Permission.TASK_READ.value, Permission.TASK_WRITE.value,
        Permission.ROBOT_READ.value, Permission.ROBOT_CONTROL.value,
        Permission.AGENT_READ.value,
    ],

    UserRole.VIEWER: [
        Permission.SPACE_READ.value,
        Permission.TASK_READ.value,
        Permission.ROBOT_READ.value,
        Permission.AGENT_READ.value,
        Permission.REPORT_READ.value,
    ],
}


def get_role_permissions(role: UserRole) -> List[str]:
    """获取角色的所有权限"""
    return ROLE_PERMISSIONS.get(role, [])


def get_user_permissions(role: UserRole, extra_permissions: List[str] = None) -> List[str]:
    """获取用户的所有权限（角色权限 + 额外权限）"""
    permissions = get_role_permissions(role).copy()
    if extra_permissions:
        for perm in extra_permissions:
            if perm not in permissions:
                permissions.append(perm)
    return permissions


def has_permission(user_permissions: List[str], required_permission: str) -> bool:
    """检查用户是否有指定权限"""
    # 超级管理员拥有所有权限
    if "*" in user_permissions:
        return True
    return required_permission in user_permissions


def has_any_permission(user_permissions: List[str], required_permissions: List[str]) -> bool:
    """检查用户是否有任一指定权限"""
    if "*" in user_permissions:
        return True
    return any(perm in user_permissions for perm in required_permissions)


def has_all_permissions(user_permissions: List[str], required_permissions: List[str]) -> bool:
    """检查用户是否有所有指定权限"""
    if "*" in user_permissions:
        return True
    return all(perm in user_permissions for perm in required_permissions)
