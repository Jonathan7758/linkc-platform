"""
F4: 认证授权模块 - 密码处理
============================
密码哈希和验证
"""

import re
from typing import Tuple
from passlib.context import CryptContext

# 使用bcrypt算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password(password: str) -> Tuple[bool, str]:
    """
    验证密码强度

    要求:
    - 至少8个字符
    - 包含大写字母
    - 包含小写字母
    - 包含数字

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含大写字母"
    if not re.search(r"[a-z]", password):
        return False, "密码必须包含小写字母"
    if not re.search(r"\d", password):
        return False, "密码必须包含数字"
    return True, ""


def validate_password_strength(password: str) -> dict:
    """
    评估密码强度

    Returns:
        {
            "valid": bool,
            "score": int (0-5),
            "issues": list[str],
            "strength": "weak" | "fair" | "good" | "strong"
        }
    """
    issues = []
    score = 0

    # 长度检查
    if len(password) < 8:
        issues.append("密码长度至少8位")
    elif len(password) >= 12:
        score += 2
    else:
        score += 1

    # 大写字母
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        issues.append("密码必须包含大写字母")

    # 小写字母
    if re.search(r"[a-z]", password):
        score += 1
    else:
        issues.append("密码必须包含小写字母")

    # 数字
    if re.search(r"\d", password):
        score += 1
    else:
        issues.append("密码必须包含数字")

    # 特殊字符（加分项）
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1

    # 计算强度等级
    if score <= 2:
        strength = "weak"
    elif score <= 3:
        strength = "fair"
    elif score <= 4:
        strength = "good"
    else:
        strength = "strong"

    return {
        "valid": len(issues) == 0,
        "score": score,
        "issues": issues,
        "strength": strength
    }
