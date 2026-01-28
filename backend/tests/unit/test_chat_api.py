"""对话API单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.core.database import get_async_session


def create_test_app():
    """创建测试用的FastAPI app"""
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.devices import router as devices_router
    from app.api.chat import router as chat_router
    from app.core.config import get_settings

    settings = get_settings()

    test_app = FastAPI(
        title=settings.app_name,
        description="MEP机电设备智能运维Agent系统",
        version="0.1.0",
    )

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_app.include_router(devices_router)
    test_app.include_router(chat_router)

    return test_app


class TestChatAPI:
    """对话API测试"""

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        mock = MagicMock()
        mock.add = MagicMock()
        mock.flush = AsyncMock()
        mock.delete = AsyncMock()
        mock.commit = AsyncMock()
        mock.rollback = AsyncMock()
        return mock

    @pytest.fixture
    def test_app(self, mock_db):
        """创建测试app并覆盖依赖"""
        app = create_test_app()

        async def override_get_session():
            yield mock_db

        app.dependency_overrides[get_async_session] = override_get_session
        return app

    @pytest.mark.asyncio
    async def test_create_session(self, test_app, mock_db):
        """测试创建会话"""
        mock_conv = MagicMock()
        mock_conv.conversation_id = "test-session-123"
        mock_conv.title = "测试会话"
        mock_conv.created_at = datetime.now(timezone.utc)
        mock_conv.updated_at = datetime.now(timezone.utc)
        mock_conv.message_count = 0
        mock_conv.context = {}

        async def mock_refresh(obj):
            obj.conversation_id = mock_conv.conversation_id
            obj.title = mock_conv.title
            obj.created_at = mock_conv.created_at
            obj.updated_at = mock_conv.updated_at
            obj.message_count = mock_conv.message_count
            obj.context = mock_conv.context

        mock_db.refresh = mock_refresh

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/chat/sessions",
                json={"title": "测试会话"}
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_list_sessions(self, test_app, mock_db):
        """测试获取会话列表"""
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock conversations query
        mock_conv = MagicMock()
        mock_conv.conversation_id = "session-1"
        mock_conv.title = "会话1"
        mock_conv.created_at = datetime.now(timezone.utc)
        mock_conv.updated_at = datetime.now(timezone.utc)
        mock_conv.message_count = 0
        mock_conv.context = {}

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_conv]

        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_result.scalars.return_value = mock_scalars

        mock_db.execute = AsyncMock(side_effect=[
            mock_count_result,
            mock_result,
        ])

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/chat/sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_app, mock_db):
        """测试获取不存在的会话"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/chat/sessions/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message(self, test_app, mock_db):
        """测试发送消息"""
        with patch("app.api.chat.get_chat_agent") as mock_get_agent:
            # Mock conversation
            mock_conv = MagicMock()
            mock_conv.conversation_id = "session-123"
            mock_conv.message_count = 0
            mock_conv.updated_at = datetime.now(timezone.utc)

            mock_conv_result = MagicMock()
            mock_conv_result.scalar_one_or_none.return_value = mock_conv

            # Mock history result
            mock_history_result = MagicMock()
            mock_history_scalars = MagicMock()
            mock_history_scalars.all.return_value = []
            mock_history_result.scalars.return_value = mock_history_scalars

            mock_db.execute = AsyncMock(side_effect=[
                mock_conv_result,
                mock_history_result,
            ])

            # 设置refresh的行为
            refresh_calls = [0]
            async def mock_refresh(obj):
                if refresh_calls[0] == 0:
                    obj.message_id = "msg-1"
                    obj.role = "user"
                    obj.content = "你好"
                    obj.created_at = datetime.now(timezone.utc)
                else:
                    obj.message_id = "msg-2"
                    obj.role = "assistant"
                    obj.content = "你好！我是MEP AI助手。"
                    obj.created_at = datetime.now(timezone.utc)
                refresh_calls[0] += 1

            mock_db.refresh = mock_refresh

            # Mock agent
            mock_agent = MagicMock()
            mock_agent_result = MagicMock()
            mock_agent_result.success = True
            mock_agent_result.response = "你好！我是MEP AI助手。"
            mock_agent.run = AsyncMock(return_value=mock_agent_result)
            mock_get_agent.return_value = mock_agent

            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/chat/sessions/session-123/messages",
                    json={"content": "你好"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_messages(self, test_app, mock_db):
        """测试获取消息历史"""
        # Mock conversation exists
        mock_conv_result = MagicMock()
        mock_conv_result.scalar_one_or_none.return_value = MagicMock()

        # Mock messages
        mock_msg = MagicMock()
        mock_msg.message_id = "msg-1"
        mock_msg.role = "user"
        mock_msg.content = "测试消息"
        mock_msg.created_at = datetime.now(timezone.utc)
        mock_msg.tool_calls = None

        mock_msg_result = MagicMock()
        mock_msg_scalars = MagicMock()
        mock_msg_scalars.all.return_value = [mock_msg]
        mock_msg_result.scalars.return_value = mock_msg_scalars

        mock_db.execute = AsyncMock(side_effect=[
            mock_conv_result,
            mock_msg_result,
        ])

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/chat/sessions/session-123/messages")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "messages" in data["data"]

    @pytest.mark.asyncio
    async def test_delete_session(self, test_app, mock_db):
        """测试删除会话"""
        # Mock conversation
        mock_conv = MagicMock()
        mock_conv_result = MagicMock()
        mock_conv_result.scalar_one_or_none.return_value = mock_conv

        mock_db.execute = AsyncMock(return_value=mock_conv_result)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.delete("/api/v1/chat/sessions/session-123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
