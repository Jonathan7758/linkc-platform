"""
F4: 认证授权模块 - 单元测试
============================
测试密码、JWT和权限功能
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.shared.auth.models import User, UserRole, UserStatus, TokenPayload
from src.shared.auth.password import (
    hash_password,
    verify_password,
    validate_password,
    validate_password_strength,
)
from src.shared.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    is_token_expired,
    get_token_remaining_time,
)
from src.shared.auth.permissions import (
    Permission,
    get_role_permissions,
    get_user_permissions,
    has_permission,
    has_any_permission,
    has_all_permissions,
)


# ============================================================
# 测试数据
# ============================================================

def create_test_user(
    role: UserRole = UserRole.OPERATOR,
    permissions: list = None
) -> User:
    """创建测试用户"""
    now = datetime.now(timezone.utc)
    return User(
        user_id=uuid4(),
        tenant_id=uuid4(),
        username="testuser",
        email="test@example.com",
        display_name="Test User",
        hashed_password=hash_password("TestPass123"),
        role=role,
        permissions=permissions or [],
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


# ============================================================
# 密码测试
# ============================================================

class TestPassword:
    """密码处理测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "MySecurePass123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "MySecurePass123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "MySecurePass123"
        hashed = hash_password(password)
        assert verify_password("WrongPassword", hashed) is False

    def test_validate_password_valid(self):
        """测试有效密码验证"""
        is_valid, error = validate_password("MySecure123")
        assert is_valid is True
        assert error == ""

    def test_validate_password_too_short(self):
        """测试密码太短"""
        is_valid, error = validate_password("Ab1234")
        assert is_valid is False
        assert "8位" in error

    def test_validate_password_no_uppercase(self):
        """测试密码无大写字母"""
        is_valid, error = validate_password("mysecure123")
        assert is_valid is False
        assert "大写" in error

    def test_validate_password_no_lowercase(self):
        """测试密码无小写字母"""
        is_valid, error = validate_password("MYSECURE123")
        assert is_valid is False
        assert "小写" in error

    def test_validate_password_no_digit(self):
        """测试密码无数字"""
        is_valid, error = validate_password("MySecurePass")
        assert is_valid is False
        assert "数字" in error

    def test_validate_password_strength(self):
        """测试密码强度评估"""
        # 弱密码
        result = validate_password_strength("abc")
        assert result["strength"] == "weak"
        assert result["valid"] is False

        # 强密码
        result = validate_password_strength("MySecure123!@#")
        assert result["strength"] == "strong"
        assert result["valid"] is True


# ============================================================
# JWT测试
# ============================================================

class TestJWT:
    """JWT Token测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        user = create_test_user()
        token = create_access_token(user)
        assert token is not None
        assert len(token) > 0

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        user = create_test_user()
        token = create_refresh_token(user)
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token(self):
        """测试解码访问令牌"""
        user = create_test_user()
        token = create_access_token(user)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == str(user.user_id)
        assert payload.tenant_id == str(user.tenant_id)
        assert payload.role == user.role.value
        assert payload.type == "access"

    def test_decode_refresh_token(self):
        """测试解码刷新令牌"""
        user = create_test_user()
        token = create_refresh_token(user)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == str(user.user_id)
        assert payload.type == "refresh"

    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_verify_token_correct_type(self):
        """测试验证正确类型的令牌"""
        user = create_test_user()
        token = create_access_token(user)
        payload = verify_token(token, "access")
        assert payload is not None

    def test_verify_token_wrong_type(self):
        """测试验证错误类型的令牌"""
        user = create_test_user()
        token = create_access_token(user)
        payload = verify_token(token, "refresh")
        assert payload is None

    def test_token_not_expired(self):
        """测试未过期令牌"""
        user = create_test_user()
        token = create_access_token(user)
        payload = decode_token(token)
        assert is_token_expired(payload) is False

    def test_token_remaining_time(self):
        """测试剩余有效时间"""
        user = create_test_user()
        token = create_access_token(user)
        payload = decode_token(token)
        remaining = get_token_remaining_time(payload)
        assert remaining > 0
        assert remaining <= 30 * 60  # 最多30分钟

    def test_access_token_contains_permissions(self):
        """测试访问令牌包含权限"""
        user = create_test_user(role=UserRole.OPERATOR)
        token = create_access_token(user)
        payload = decode_token(token)

        assert payload.permissions is not None
        assert "space:read" in payload.permissions
        assert "robot:read" in payload.permissions


# ============================================================
# 权限测试
# ============================================================

class TestPermissions:
    """权限测试"""

    def test_get_role_permissions_operator(self):
        """测试获取操作员权限"""
        permissions = get_role_permissions(UserRole.OPERATOR)
        assert "space:read" in permissions
        assert "task:read" in permissions
        assert "robot:read" in permissions
        assert "user:write" not in permissions

    def test_get_role_permissions_admin(self):
        """测试获取管理员权限"""
        permissions = get_role_permissions(UserRole.TENANT_ADMIN)
        assert "user:write" in permissions
        assert "user:delete" in permissions

    def test_get_role_permissions_super_admin(self):
        """测试获取超级管理员权限"""
        permissions = get_role_permissions(UserRole.SUPER_ADMIN)
        assert "*" in permissions

    def test_get_user_permissions_with_extra(self):
        """测试获取用户权限（含额外权限）"""
        permissions = get_user_permissions(
            UserRole.VIEWER,
            extra_permissions=["special:access"]
        )
        assert "space:read" in permissions
        assert "special:access" in permissions

    def test_has_permission_normal(self):
        """测试普通权限检查"""
        permissions = ["space:read", "task:read"]
        assert has_permission(permissions, "space:read") is True
        assert has_permission(permissions, "user:write") is False

    def test_has_permission_super_admin(self):
        """测试超级管理员权限检查"""
        permissions = ["*"]
        assert has_permission(permissions, "any:permission") is True

    def test_has_any_permission(self):
        """测试任一权限检查"""
        permissions = ["space:read", "task:read"]
        assert has_any_permission(permissions, ["space:read", "user:write"]) is True
        assert has_any_permission(permissions, ["user:write", "user:delete"]) is False

    def test_has_all_permissions(self):
        """测试所有权限检查"""
        permissions = ["space:read", "task:read", "robot:read"]
        assert has_all_permissions(permissions, ["space:read", "task:read"]) is True
        assert has_all_permissions(permissions, ["space:read", "user:write"]) is False


# ============================================================
# 集成测试
# ============================================================

class TestAuthIntegration:
    """认证授权集成测试"""

    def test_full_auth_flow(self):
        """测试完整认证流程"""
        # 1. 创建用户（密码哈希）
        password = "SecurePass123"
        hashed = hash_password(password)
        user = create_test_user(role=UserRole.MANAGER)
        user.hashed_password = hashed

        # 2. 验证密码
        assert verify_password(password, user.hashed_password) is True
        assert verify_password("wrong", user.hashed_password) is False

        # 3. 生成令牌
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        # 4. 验证访问令牌
        payload = verify_token(access_token, "access")
        assert payload is not None
        assert payload.role == "manager"

        # 5. 检查权限
        assert has_permission(payload.permissions, "space:read") is True
        assert has_permission(payload.permissions, "robot:control") is True
        assert has_permission(payload.permissions, "user:delete") is False

        # 6. 验证刷新令牌
        refresh_payload = verify_token(refresh_token, "refresh")
        assert refresh_payload is not None
        assert refresh_payload.type == "refresh"

    def test_different_roles_different_permissions(self):
        """测试不同角色有不同权限"""
        roles_and_permissions = [
            (UserRole.VIEWER, "report:read", True),
            (UserRole.VIEWER, "task:write", False),
            (UserRole.OPERATOR, "robot:control", True),
            (UserRole.OPERATOR, "user:write", False),
            (UserRole.TRAINER, "agent:config", True),
            (UserRole.MANAGER, "user:read", True),
            (UserRole.TENANT_ADMIN, "user:delete", True),
        ]

        for role, permission, expected in roles_and_permissions:
            user = create_test_user(role=role)
            token = create_access_token(user)
            payload = decode_token(token)
            assert has_permission(payload.permissions, permission) is expected, \
                f"{role} should {'have' if expected else 'not have'} {permission}"
