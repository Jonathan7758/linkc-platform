"""
D2: 数据存储服务 - 数据库管理器
================================
数据库连接池和会话管理
"""

from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import asyncio
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================

class DatabaseConfig:
    """数据库配置"""

    def __init__(
        self,
        # PostgreSQL 配置
        postgres_host: str = "localhost",
        postgres_port: int = 5432,
        postgres_user: str = "postgres",
        postgres_password: str = "",
        postgres_database: str = "linkc",

        # 连接池配置
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,

        # Redis 配置
        redis_url: Optional[str] = None,
    ):
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.postgres_database = postgres_database

        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle

        self.redis_url = redis_url

    @property
    def postgres_url(self) -> str:
        """PostgreSQL 连接URL（同步）"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    @property
    def postgres_async_url(self) -> str:
        """PostgreSQL 异步连接URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"


# ============================================================
# 数据库管理器
# ============================================================

class DatabaseManager:
    """
    数据库连接管理器

    管理 PostgreSQL 连接池和会话
    """

    _instance: Optional['DatabaseManager'] = None

    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库管理器

        Args:
            config: 数据库配置
        """
        self.config = config
        self._engine = None
        self._async_session_factory = None
        self._pool = None  # asyncpg pool for raw queries
        self._redis = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> Optional['DatabaseManager']:
        """获取单例实例"""
        return cls._instance

    @classmethod
    def set_instance(cls, instance: 'DatabaseManager') -> None:
        """设置单例实例"""
        cls._instance = instance

    async def initialize(self) -> None:
        """
        初始化数据库连接

        创建连接池和会话工厂
        """
        if self._initialized:
            logger.warning("DatabaseManager already initialized")
            return

        logger.info("Initializing database connections...")

        try:
            # 创建 SQLAlchemy 异步引擎
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker

            self._engine = create_async_engine(
                self.config.postgres_async_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                echo=False
            )

            self._async_session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            logger.info("SQLAlchemy engine created")

        except ImportError:
            logger.warning("SQLAlchemy not available, using asyncpg directly")

        # 创建 asyncpg 连接池（用于原生SQL和时序查询）
        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                database=self.config.postgres_database,
                min_size=5,
                max_size=self.config.pool_size,
                command_timeout=60
            )
            logger.info("asyncpg pool created")

        except ImportError:
            logger.warning("asyncpg not available")
        except Exception as e:
            logger.warning(f"Failed to create asyncpg pool: {e}")

        # 连接 Redis（如果配置了）
        if self.config.redis_url:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Failed to connect Redis: {e}")

        self._initialized = True
        DatabaseManager.set_instance(self)
        logger.info("DatabaseManager initialized")

    async def close(self) -> None:
        """关闭数据库连接"""
        logger.info("Closing database connections...")

        if self._engine:
            await self._engine.dispose()
            self._engine = None

        if self._pool:
            await self._pool.close()
            self._pool = None

        if self._redis:
            await self._redis.close()
            self._redis = None

        self._initialized = False
        logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator:
        """
        获取数据库会话上下文管理器

        Usage:
            async with db.session() as session:
                # 使用 session
        """
        if not self._async_session_factory:
            raise RuntimeError("Database not initialized")

        session = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator:
        """
        获取原生数据库连接

        用于复杂查询或时序数据操作

        Usage:
            async with db.connection() as conn:
                result = await conn.fetch("SELECT ...")
        """
        if not self._pool:
            raise RuntimeError("Database pool not initialized")

        async with self._pool.acquire() as conn:
            yield conn

    @property
    def redis(self):
        """获取 Redis 客户端"""
        return self._redis

    @property
    def pool(self):
        """获取 asyncpg 连接池"""
        return self._pool

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    async def execute(self, query: str, *args) -> str:
        """
        执行SQL语句

        Args:
            query: SQL语句
            *args: 参数

        Returns:
            执行结果
        """
        async with self.connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """
        查询并返回所有结果

        Args:
            query: SQL语句
            *args: 参数

        Returns:
            结果列表
        """
        async with self.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """
        查询并返回单行结果

        Args:
            query: SQL语句
            *args: 参数

        Returns:
            单行结果或None
        """
        async with self.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """
        查询并返回单个值

        Args:
            query: SQL语句
            *args: 参数

        Returns:
            单个值
        """
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)


# ============================================================
# 内存数据库管理器（测试用）
# ============================================================

class InMemoryDatabaseManager(DatabaseManager):
    """
    内存数据库管理器

    用于单元测试，不需要实际数据库连接
    """

    def __init__(self):
        super().__init__(DatabaseConfig())
        self._data = {}
        self._initialized = True

    async def initialize(self) -> None:
        """初始化（空操作）"""
        pass

    async def close(self) -> None:
        """关闭（清空数据）"""
        self._data.clear()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator:
        """返回内存会话"""
        yield InMemorySession(self._data)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator:
        """返回内存连接"""
        yield InMemoryConnection(self._data)


class InMemorySession:
    """内存会话（测试用）"""

    def __init__(self, data: dict):
        self._data = data
        self._pending = []

    def add(self, entity):
        self._pending.append(entity)

    async def commit(self):
        for entity in self._pending:
            table = entity.__class__.__name__.lower() + "s"
            if table not in self._data:
                self._data[table] = {}
            entity_id = getattr(entity, 'id', None) or getattr(entity, f'{table[:-1]}_id', None)
            if entity_id:
                self._data[table][entity_id] = entity
        self._pending.clear()

    async def rollback(self):
        self._pending.clear()

    async def refresh(self, entity):
        pass

    async def close(self):
        pass


class InMemoryConnection:
    """内存连接（测试用）"""

    def __init__(self, data: dict):
        self._data = data

    async def fetch(self, query: str, *args):
        return []

    async def fetchrow(self, query: str, *args):
        return None

    async def fetchval(self, query: str, *args):
        return None

    async def execute(self, query: str, *args):
        return "OK"

    async def executemany(self, query: str, args_list):
        return len(args_list)
