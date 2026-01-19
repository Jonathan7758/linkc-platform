"""
LinkC Platform - 统一配置管理 (F1)
================================
支持多环境配置、环境变量覆盖、配置验证。
"""

import os
from enum import Enum
from typing import Optional, List
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """运行环境"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    HOST: str = Field(default="localhost", alias="DB_HOST")
    PORT: int = Field(default=5432, alias="DB_PORT")
    USER: str = Field(default="postgres", alias="DB_USER")
    PASSWORD: str = Field(default="postgres", alias="DB_PASSWORD")
    NAME: str = Field(default="linkc", alias="DB_NAME")
    POOL_SIZE: int = Field(default=10, alias="DB_POOL_SIZE")
    MAX_OVERFLOW: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
    
    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


class RedisConfig(BaseSettings):
    """Redis配置"""
    HOST: str = Field(default="localhost", alias="REDIS_HOST")
    PORT: int = Field(default=6379, alias="REDIS_PORT")
    PASSWORD: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    DB: int = Field(default=0, alias="REDIS_DB")
    MAX_CONNECTIONS: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    @property
    def url(self) -> str:
        auth = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"redis://{auth}{self.HOST}:{self.PORT}/{self.DB}"


class MCPConfig(BaseSettings):
    """MCP服务器配置"""
    SPACE_MANAGER_URL: str = Field(default="http://localhost:8001", alias="MCP_SPACE_MANAGER_URL")
    TASK_MANAGER_URL: str = Field(default="http://localhost:8002", alias="MCP_TASK_MANAGER_URL")
    ROBOT_CONTROL_URL: str = Field(default="http://localhost:8003", alias="MCP_ROBOT_CONTROL_URL")
    CONNECTION_TIMEOUT: int = Field(default=30, alias="MCP_CONNECTION_TIMEOUT")
    REQUEST_TIMEOUT: int = Field(default=60, alias="MCP_REQUEST_TIMEOUT")


class AgentConfig(BaseSettings):
    """Agent配置"""
    DEFAULT_AUTONOMY_LEVEL: str = Field(default="L2_LIMITED", alias="AGENT_DEFAULT_AUTONOMY")
    MAX_CONCURRENT_DECISIONS: int = Field(default=10, alias="AGENT_MAX_CONCURRENT_DECISIONS")
    DECISION_TIMEOUT: int = Field(default=30, alias="AGENT_DECISION_TIMEOUT")
    APPROVAL_TIMEOUT: int = Field(default=300, alias="AGENT_APPROVAL_TIMEOUT")


class Settings(BaseSettings):
    """主配置类"""
    
    # 基础配置
    PROJECT_NAME: str = Field(default="LinkC Platform")
    VERSION: str = Field(default="0.1.0")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, alias="ENV")
    DEBUG: bool = Field(default=False)
    
    # API配置
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_V1_PREFIX: str = Field(default="/api/v1")
    API_WORKERS: int = Field(default=4)
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    
    # 日志配置
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO)
    LOG_FORMAT: str = Field(default="json")  # json or text
    LOG_FILE: Optional[str] = Field(default=None)
    
    # 安全配置
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # 租户配置
    DEFAULT_TENANT_ID: str = Field(default="tenant_001")
    MULTI_TENANT_ENABLED: bool = Field(default=True)
    
    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出默认配置实例
settings = get_settings()


__all__ = [
    "Environment",
    "LogLevel",
    "DatabaseConfig",
    "RedisConfig",
    "MCPConfig",
    "AgentConfig",
    "Settings",
    "get_settings",
    "settings",
]
