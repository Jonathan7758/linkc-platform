"""应用配置管理"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 忽略 .env 中未定义的额外字段
    )

    # 项目基础配置
    PROJECT_NAME: str = "ECIS Service Robot"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # 应用配置
    app_name: str = "ECIS Service Robot"
    app_env: str = "development"
    debug: bool = True

    # 数据库配置
    db_host: str = "db"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "ecis_robot"

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379

    # LLM配置 (火山引擎)
    volcengine_api_key: str = ""
    volcengine_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcengine_model: str = "doubao-pro-32k"

    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sync_database_url(self) -> str:
        """获取同步数据库连接URL (用于Alembic迁移)"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        return f"redis://{self.redis_host}:{self.redis_port}"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 配置单例实例
settings = get_settings()
