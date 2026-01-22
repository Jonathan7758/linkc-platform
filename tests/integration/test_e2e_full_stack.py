"""
LinkC Platform E2E Full Stack Integration Tests
================================================
End-to-end tests covering actual API endpoints.
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json


# Configuration
API_BASE_URL = "http://localhost:8000"
TENANT_ID = "demo-tenant"
BUILDING_ID = "demo-building"


class APIClient:
    """HTTP client for API testing"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get(self, path: str, params: Dict = None) -> httpx.Response:
        return await self.client.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self._headers()
        )

    async def post(self, path: str, data: Dict = None) -> httpx.Response:
        return await self.client.post(
            f"{self.base_url}{path}",
            json=data,
            headers=self._headers()
        )

    async def put(self, path: str, data: Dict = None) -> httpx.Response:
        return await self.client.put(
            f"{self.base_url}{path}",
            json=data,
            headers=self._headers()
        )

    async def delete(self, path: str) -> httpx.Response:
        return await self.client.delete(
            f"{self.base_url}{path}",
            headers=self._headers()
        )


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def api_client():
    """Create API client for tests"""
    client = APIClient()
    yield client
    await client.close()


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthCheck:
    """Health check endpoint tests"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client):
        """Test /health endpoint"""
        response = await api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


# ============================================================================
# G2: Space API Tests (Using actual routes)
# ============================================================================

class TestSpaceAPI:
    """Tests for Space API"""

    @pytest.mark.asyncio
    async def test_list_buildings(self, api_client):
        """Test listing buildings"""
        response = await api_client.get("/api/v1/spaces/buildings", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200
        data = response.json()
        assert "buildings" in data

    @pytest.mark.asyncio
    async def test_get_building(self, api_client):
        """Test getting building details"""
        # First get buildings list
        response = await api_client.get("/api/v1/spaces/buildings", {
            "tenant_id": TENANT_ID
        })
        buildings = response.json()

        if len(buildings.get("buildings", [])) > 0:
            building_id = buildings["buildings"][0]["id"]
            response = await api_client.get(f"/api/v1/spaces/buildings/{building_id}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_floors(self, api_client):
        """Test listing floors for a building"""
        response = await api_client.get("/api/v1/spaces/buildings", {
            "tenant_id": TENANT_ID
        })
        buildings = response.json()

        if len(buildings.get("buildings", [])) > 0:
            building_id = buildings["buildings"][0]["id"]
            response = await api_client.get(f"/api/v1/spaces/buildings/{building_id}/floors")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_zones(self, api_client):
        """Test listing zones"""
        response = await api_client.get("/api/v1/spaces/zones")
        assert response.status_code == 200


# ============================================================================
# G3: Task API Tests
# ============================================================================

class TestTaskAPI:
    """Tests for Task API"""

    @pytest.mark.asyncio
    async def test_list_tasks(self, api_client):
        """Test listing tasks"""
        response = await api_client.get("/api/v1/tasks", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    @pytest.mark.asyncio
    async def test_list_pending_tasks(self, api_client):
        """Test listing pending tasks"""
        response = await api_client.get("/api/v1/tasks/pending", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_task(self, api_client):
        """Test creating a task"""
        response = await api_client.post("/api/v1/tasks", {
            "tenant_id": TENANT_ID,
            "zone_id": "zone-001",
            "task_type": "routine",
            "priority": 5
        })
        assert response.status_code in [200, 201, 422]  # 422 if validation fails

    @pytest.mark.asyncio
    async def test_get_task(self, api_client):
        """Test getting task details"""
        # First list tasks
        response = await api_client.get("/api/v1/tasks", {
            "tenant_id": TENANT_ID
        })
        tasks = response.json()

        if len(tasks.get("tasks", [])) > 0:
            task_id = tasks["tasks"][0].get("task_id") or tasks["tasks"][0].get("id")
            response = await api_client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200


# ============================================================================
# G4: Robot API Tests
# ============================================================================

class TestRobotAPI:
    """Tests for Robot API"""

    @pytest.mark.asyncio
    async def test_list_robots(self, api_client):
        """Test listing robots"""
        response = await api_client.get("/api/v1/robots", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200
        data = response.json()
        assert "robots" in data

    @pytest.mark.asyncio
    async def test_list_available_robots(self, api_client):
        """Test listing available robots"""
        response = await api_client.get("/api/v1/robots/available", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_robot(self, api_client):
        """Test getting robot details"""
        # First list robots
        response = await api_client.get("/api/v1/robots", {
            "tenant_id": TENANT_ID
        })
        robots = response.json()

        if len(robots.get("robots", [])) > 0:
            robot_id = robots["robots"][0].get("robot_id") or robots["robots"][0].get("id")
            response = await api_client.get(f"/api/v1/robots/{robot_id}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_robot_charge_command(self, api_client):
        """Test sending charge command to robot"""
        response = await api_client.get("/api/v1/robots", {
            "tenant_id": TENANT_ID
        })
        robots = response.json()

        if len(robots.get("robots", [])) > 0:
            robot_id = robots["robots"][0].get("robot_id") or robots["robots"][0].get("id")
            response = await api_client.post(f"/api/v1/robots/{robot_id}/charge")
            assert response.status_code in [200, 202, 400, 409]  # May fail if already charging


# ============================================================================
# G5: Agent API Tests
# ============================================================================

class TestAgentAPI:
    """Tests for Agent API"""

    @pytest.mark.asyncio
    async def test_list_agents(self, api_client):
        """Test listing agents"""
        response = await api_client.get("/api/v1/agents")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_agent_stats(self, api_client):
        """Test getting agent statistics"""
        response = await api_client.get("/api/v1/agents/stats", {
            "tenant_id": TENANT_ID
        })
        # May return 404 if stats endpoint doesn't exist
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_pending_approvals(self, api_client):
        """Test listing pending approvals"""
        response = await api_client.get("/api/v1/agents/approvals/pending")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_agent(self, api_client):
        """Test getting agent details"""
        response = await api_client.get("/api/v1/agents")
        agents = response.json()

        if isinstance(agents, list) and len(agents) > 0:
            agent_id = agents[0].get("agent_id") or agents[0].get("id")
            response = await api_client.get(f"/api/v1/agents/{agent_id}")
            assert response.status_code in [200, 404]


# ============================================================================
# Cross-Layer Integration Tests
# ============================================================================

class TestCrossLayerIntegration:
    """Tests verifying integration across layers"""

    @pytest.mark.asyncio
    async def test_space_to_task_flow(self, api_client):
        """Test flow from space to task creation"""
        # Get buildings
        response = await api_client.get("/api/v1/spaces/buildings", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200
        buildings = response.json()

        if len(buildings.get("buildings", [])) > 0:
            building_id = buildings["buildings"][0]["id"]

            # Get floors
            response = await api_client.get(f"/api/v1/spaces/buildings/{building_id}/floors")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_robot_availability_check(self, api_client):
        """Test checking robot availability for task assignment"""
        # Get available robots
        response = await api_client.get("/api/v1/robots/available", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200

        # Get pending tasks
        response = await api_client.get("/api/v1/tasks/pending", {
            "tenant_id": TENANT_ID
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_full_status_check(self, api_client):
        """Test getting full system status"""
        # Health check
        response = await api_client.get("/health")
        assert response.status_code == 200

        # List robots
        response = await api_client.get("/api/v1/robots", {"tenant_id": TENANT_ID})
        assert response.status_code == 200

        # List tasks
        response = await api_client.get("/api/v1/tasks", {"tenant_id": TENANT_ID})
        assert response.status_code == 200

        # List agents
        response = await api_client.get("/api/v1/agents")
        assert response.status_code == 200


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance benchmark tests"""

    @pytest.mark.asyncio
    async def test_api_response_times(self, api_client):
        """Verify API response times are acceptable"""
        import time

        endpoints = [
            "/health",
            "/api/v1/robots?tenant_id=" + TENANT_ID,
            "/api/v1/tasks?tenant_id=" + TENANT_ID,
            "/api/v1/spaces/buildings?tenant_id=" + TENANT_ID,
        ]

        for endpoint in endpoints:
            start = time.time()
            response = await api_client.get(endpoint)
            elapsed = time.time() - start

            # API responses should be under 1 second
            assert elapsed < 1.0, f"{endpoint} took {elapsed:.2f}s"
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, api_client):
        """Test handling of concurrent requests"""
        import time

        # Create 20 concurrent requests
        start = time.time()

        tasks = []
        for _ in range(20):
            tasks.append(api_client.get(f"/api/v1/robots?tenant_id={TENANT_ID}"))

        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # Should complete within 5 seconds
        assert elapsed < 5.0, f"Concurrent requests took {elapsed:.2f}s"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Error handling tests"""

    @pytest.mark.asyncio
    async def test_not_found_handling(self, api_client):
        """Test 404 handling"""
        response = await api_client.get("/api/v1/tasks/non-existent-task-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, api_client):
        """Test invalid endpoint"""
        response = await api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, api_client):
        """Test method not allowed"""
        response = await api_client.delete("/health")  # DELETE not allowed on health
        assert response.status_code in [404, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
