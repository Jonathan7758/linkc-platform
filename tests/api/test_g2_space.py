"""
G2: 空间管理API - 单元测试
===========================
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.gateway.space.models import ZoneType, Priority, PointType
from src.api.gateway.space.service import SpaceService, InMemorySpaceStorage
from src.api.gateway.space.router import router, set_space_service
from src.api.gateway.auth.service import AuthService, InMemoryAuthStorage
from src.api.gateway.auth.router import router as auth_router, set_auth_service


# ============================================================
# 测试设置
# ============================================================

@pytest.fixture
def auth_service():
    """创建测试用认证服务"""
    storage = InMemoryAuthStorage()
    return AuthService(storage=storage)


@pytest.fixture
def space_service():
    """创建测试用空间服务"""
    storage = InMemorySpaceStorage()
    return SpaceService(storage=storage)


@pytest.fixture
def app(auth_service, space_service):
    """创建测试应用"""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(router)
    set_auth_service(auth_service)
    set_space_service(space_service)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """获取管理员Token"""
    response = client.post("/auth/login", json={
        "username": "admin@linkc.com",
        "password": "admin123"
    })
    return response.json()["access_token"]


# ============================================================
# 楼宇管理测试
# ============================================================

class TestBuildingEndpoints:
    """楼宇管理测试"""

    def test_list_buildings(self, client, admin_token):
        """测试获取楼宇列表"""
        response = client.get(
            "/spaces/buildings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1  # 至少有默认楼宇

    def test_create_building(self, client, admin_token):
        """测试创建楼宇"""
        response = client.post(
            "/spaces/buildings",
            json={
                "name": "测试楼宇",
                "address": "测试地址123号",
                "total_area_sqm": 10000
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试楼宇"
        assert data["address"] == "测试地址123号"
        assert "id" in data

    def test_get_building(self, client, admin_token):
        """测试获取楼宇详情"""
        response = client.get(
            "/spaces/buildings/building-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新鸿基中心"
        assert "floors" in data
        assert "statistics" in data

    def test_get_building_not_found(self, client, admin_token):
        """测试获取不存在的楼宇"""
        response = client.get(
            "/spaces/buildings/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_update_building(self, client, admin_token):
        """测试更新楼宇"""
        # 先创建楼宇
        create_response = client.post(
            "/spaces/buildings",
            json={"name": "更新测试楼宇", "address": "原地址"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        building_id = create_response.json()["id"]

        # 更新楼宇
        response = client.put(
            f"/spaces/buildings/{building_id}",
            json={"name": "更新后的名称", "address": "新地址"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "更新后的名称"
        assert response.json()["address"] == "新地址"

    def test_delete_building(self, client, admin_token):
        """测试删除楼宇"""
        # 先创建楼宇
        create_response = client.post(
            "/spaces/buildings",
            json={"name": "删除测试楼宇"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        building_id = create_response.json()["id"]

        # 删除楼宇
        response = client.delete(
            f"/spaces/buildings/{building_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # 确认已删除
        get_response = client.get(
            f"/spaces/buildings/{building_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404

    def test_search_buildings(self, client, admin_token):
        """测试搜索楼宇"""
        response = client.get(
            "/spaces/buildings?search=新鸿基",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert "新鸿基" in data["items"][0]["name"]


# ============================================================
# 楼层管理测试
# ============================================================

class TestFloorEndpoints:
    """楼层管理测试"""

    def test_list_floors(self, client, admin_token):
        """测试获取楼层列表"""
        response = client.get(
            "/spaces/floors?building_id=building-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_create_floor(self, client, admin_token):
        """测试创建楼层"""
        response = client.post(
            "/spaces/floors",
            json={
                "building_id": "building-001",
                "name": "2F 办公区",
                "floor_number": 2,
                "area_sqm": 1800
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "2F 办公区"
        assert data["floor_number"] == 2

    def test_create_floor_invalid_building(self, client, admin_token):
        """测试创建楼层到不存在的楼宇"""
        response = client.post(
            "/spaces/floors",
            json={
                "building_id": "nonexistent",
                "name": "测试楼层",
                "floor_number": 1
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400

    def test_get_floor(self, client, admin_token):
        """测试获取楼层详情"""
        response = client.get(
            "/spaces/floors/floor-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "1F 大堂"
        assert "zones" in data

    def test_update_floor(self, client, admin_token):
        """测试更新楼层"""
        response = client.put(
            "/spaces/floors/floor-001",
            json={"name": "1F 大堂（更新）"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "更新" in response.json()["name"]

    def test_delete_floor(self, client, admin_token):
        """测试删除楼层"""
        # 先创建楼层
        create_response = client.post(
            "/spaces/floors",
            json={
                "building_id": "building-001",
                "name": "删除测试楼层",
                "floor_number": 99
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        floor_id = create_response.json()["id"]

        # 删除楼层
        response = client.delete(
            f"/spaces/floors/{floor_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_get_floor_map(self, client, admin_token):
        """测试获取楼层地图"""
        response = client.get(
            "/spaces/floors/floor-001/map",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["floor_id"] == "floor-001"
        assert "resolution" in data


# ============================================================
# 区域管理测试
# ============================================================

class TestZoneEndpoints:
    """区域管理测试"""

    def test_list_zones(self, client, admin_token):
        """测试获取区域列表"""
        response = client.get(
            "/spaces/zones?floor_id=floor-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_list_zones_filter_type(self, client, admin_token):
        """测试按类型筛选区域"""
        response = client.get(
            "/spaces/zones?floor_id=floor-001&zone_type=lobby",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        for zone in data["items"]:
            assert zone["zone_type"] == "lobby"

    def test_create_zone(self, client, admin_token):
        """测试创建区域"""
        response = client.post(
            "/spaces/zones",
            json={
                "floor_id": "floor-001",
                "name": "测试区域B",
                "zone_type": "corridor",
                "area_sqm": 200,
                "priority": "medium"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试区域B"
        assert data["zone_type"] == "corridor"

    def test_create_zone_with_boundary(self, client, admin_token):
        """测试创建带边界的区域"""
        response = client.post(
            "/spaces/zones",
            json={
                "floor_id": "floor-001",
                "name": "边界测试区域",
                "zone_type": "office",
                "boundary": {
                    "type": "polygon",
                    "coordinates": [[0, 0], [5, 0], [5, 5], [0, 5]]
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201

    def test_get_zone(self, client, admin_token):
        """测试获取区域详情"""
        response = client.get(
            "/spaces/zones/zone-001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "大堂A区"
        assert "points" in data
        assert "statistics" in data

    def test_update_zone(self, client, admin_token):
        """测试更新区域"""
        response = client.put(
            "/spaces/zones/zone-001",
            json={"priority": "low", "cleaning_frequency": "weekly"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "low"
        assert data["cleaning_frequency"] == "weekly"

    def test_delete_zone(self, client, admin_token):
        """测试删除区域"""
        # 先创建区域
        create_response = client.post(
            "/spaces/zones",
            json={
                "floor_id": "floor-001",
                "name": "删除测试区域",
                "zone_type": "other"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        zone_id = create_response.json()["id"]

        # 删除区域
        response = client.delete(
            f"/spaces/zones/{zone_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


# ============================================================
# 点位管理测试
# ============================================================

class TestPointEndpoints:
    """点位管理测试"""

    def test_list_points(self, client, admin_token):
        """测试获取点位列表"""
        response = client.get(
            "/spaces/zones/zone-001/points",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_create_point(self, client, admin_token):
        """测试创建点位"""
        response = client.post(
            "/spaces/zones/zone-001/points",
            json={
                "name": "测试点位",
                "x": 3.5,
                "y": 4.5,
                "point_type": "waypoint"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试点位"
        assert data["x"] == 3.5
        assert data["y"] == 4.5
        assert data["point_type"] == "waypoint"

    def test_create_charging_point(self, client, admin_token):
        """测试创建充电点位"""
        response = client.post(
            "/spaces/zones/zone-001/points",
            json={
                "name": "充电桩B",
                "x": 9.0,
                "y": 9.0,
                "point_type": "charging",
                "metadata": {
                    "is_charging_station": True,
                    "charger_type": "fast"
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["point_type"] == "charging"
        assert data["metadata"]["is_charging_station"] is True


# ============================================================
# 服务层测试
# ============================================================

class TestSpaceService:
    """空间服务测试"""

    @pytest.mark.asyncio
    async def test_building_crud(self, space_service):
        """测试楼宇CRUD"""
        from src.api.gateway.space.models import BuildingCreate, BuildingUpdate

        # Create
        building = await space_service.create_building(
            "tenant_001",
            BuildingCreate(name="服务测试楼宇", address="测试地址")
        )
        assert building.name == "服务测试楼宇"

        # Read
        detail = await space_service.get_building(building.id, "tenant_001")
        assert detail is not None
        assert detail.name == "服务测试楼宇"

        # Update
        updated = await space_service.update_building(
            building.id, "tenant_001",
            BuildingUpdate(name="更新后的名称")
        )
        assert updated.name == "更新后的名称"

        # Delete
        success = await space_service.delete_building(building.id, "tenant_001")
        assert success is True

        # Verify deleted
        deleted = await space_service.get_building(building.id, "tenant_001")
        assert deleted is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, space_service):
        """测试租户隔离"""
        # tenant_001的楼宇
        buildings = await space_service.list_buildings("tenant_001")
        assert buildings["total"] >= 1

        # tenant_002的楼宇（应该为空）
        buildings_other = await space_service.list_buildings("tenant_002")
        assert buildings_other["total"] == 0

    @pytest.mark.asyncio
    async def test_floor_zone_hierarchy(self, space_service):
        """测试楼层-区域层级关系"""
        # 获取楼层
        floor = await space_service.get_floor("floor-001", "tenant_001")
        assert floor is not None

        # 楼层应包含区域列表
        assert hasattr(floor, 'zones')
        assert len(floor.zones) >= 1

        # 区域应关联到楼层
        zone = await space_service.get_zone("zone-001", "tenant_001")
        assert zone is not None
        assert zone.floor_id == "floor-001"
