"""配置模块测试"""

from app.core.config import Settings, get_settings


class TestSettings:
    """Settings类测试"""

    def test_default_values(self):
        """测试默认配置值"""
        settings = Settings()
        assert settings.app_name == "MEP-AI-Agent"
        assert settings.app_env == "development"
        assert settings.debug is True

    def test_database_url_property(self):
        """测试数据库URL属性"""
        settings = Settings(
            db_host="localhost",
            db_port=5433,
            db_user="test_user",
            db_password="test_pass",
            db_name="test_db",
        )
        expected = "postgresql+asyncpg://test_user:test_pass@localhost:5433/test_db"
        assert settings.database_url == expected

    def test_sync_database_url_property(self):
        """测试同步数据库URL属性"""
        settings = Settings(
            db_host="localhost",
            db_port=5433,
            db_user="test_user",
            db_password="test_pass",
            db_name="test_db",
        )
        expected = "postgresql://test_user:test_pass@localhost:5433/test_db"
        assert settings.sync_database_url == expected

    def test_redis_url_property(self):
        """测试Redis URL属性"""
        settings = Settings(redis_host="localhost", redis_port=6379)
        assert settings.redis_url == "redis://localhost:6379"


class TestGetSettings:
    """get_settings函数测试"""

    def test_returns_settings_instance(self):
        """测试返回Settings实例"""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_returns_cached_instance(self):
        """测试返回缓存实例"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
