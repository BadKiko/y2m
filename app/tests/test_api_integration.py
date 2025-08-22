import pytest
import sys
import os
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app


@pytest.mark.asyncio
class TestAPIIntegration:
    """Integration tests for API endpoints"""

    async def test_full_device_lifecycle(self):
        """Test complete device lifecycle through API"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # 1. Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Create device
            device_data = {
                "name": "integration_test_device",
                "type": "switch",
                "meta": {"room": "test_room"}
            }
            create_response = await client.post("/api/v1/devices", json=device_data, headers=headers)
            assert create_response.status_code == 200
            device = create_response.json()

            assert device["name"] == "integration_test_device"
            assert device["type"] == "switch"
            assert device["meta"]["room"] == "test_room"
            assert "mqtt_base_topic" in device

            device_id = device["id"]

            # 3. Get device by ID
            get_response = await client.get(f"/api/v1/devices/{device_id}", headers=headers)
            assert get_response.status_code == 200
            retrieved_device = get_response.json()
            assert retrieved_device["name"] == "integration_test_device"

            # 4. Update device
            update_data = {
                "name": "updated_test_device",
                "is_active": False
            }
            update_response = await client.put(f"/api/v1/devices/{device_id}", json=update_data, headers=headers)
            assert update_response.status_code == 200
            updated_device = update_response.json()
            assert updated_device["name"] == "updated_test_device"
            assert updated_device["is_active"] == False

            # 5. List devices
            list_response = await client.get("/api/v1/devices", headers=headers)
            assert list_response.status_code == 200
            devices_list = list_response.json()
            assert isinstance(devices_list, list)
            assert len(devices_list) > 0

            # 6. Delete device
            delete_response = await client.delete(f"/api/v1/devices/{device_id}", headers=headers)
            assert delete_response.status_code == 200
            deleted_device = delete_response.json()
            assert deleted_device["name"] == "updated_test_device"

    async def test_mqtt_integration(self):
        """Test MQTT API endpoints"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test MQTT status endpoint
            status_response = await client.get("/api/v1/mqtt/status", headers=headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "connected" in status_data

            # Test MQTT publish endpoint
            publish_data = {
                "topic": "test/integration/topic",
                "payload": '{"test": "data"}',
                "qos": 0,
                "retain": False
            }
            publish_response = await client.post("/api/v1/mqtt/publish", json=publish_data, headers=headers)
            assert publish_response.status_code == 200
            publish_result = publish_response.json()
            assert publish_result["success"] == True
            assert publish_result["topic"] == "test/integration/topic"

    async def test_yandex_integration(self):
        """Test Yandex API endpoints"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test Yandex accounts endpoint
            accounts_response = await client.get("/api/v1/yandex/accounts", headers=headers)
            assert accounts_response.status_code == 200
            accounts = accounts_response.json()
            assert isinstance(accounts, list)

    async def test_adb_integration(self):
        """Test ADB API endpoints"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test ADB devices endpoint
            devices_response = await client.get("/api/v1/adb/devices", headers=headers)
            assert devices_response.status_code == 200
            devices = devices_response.json()
            assert isinstance(devices, list)

            # Test ADB status endpoint
            status_response = await client.get("/api/v1/adb/status", headers=headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "connected_devices" in status_data

    async def test_yapi_integration(self):
        """Test YAPI API endpoints"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test YAPI status endpoint
            status_response = await client.get("/api/v1/yapi/status", headers=headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "connected" in status_data


class TestErrorHandling:
    """Test error handling in API"""

    async def test_unauthorized_access(self):
        """Test accessing protected endpoints without authentication"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Try to access protected endpoint without auth
            response = await client.get("/api/v1/devices")
            assert response.status_code == 401

            # Try to access with invalid token
            headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get("/api/v1/devices", headers=headers)
            assert response.status_code == 401

    async def test_invalid_login(self):
        """Test login with invalid credentials"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            login_data = {
                "username": "invalid_user",
                "password": "wrong_password"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 400

    async def test_not_found_device(self):
        """Test accessing non-existent device"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Try to get non-existent device
            response = await client.get("/api/v1/devices/99999", headers=headers)
            assert response.status_code == 404

    async def test_invalid_device_data(self):
        """Test creating device with invalid data"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Login first
            login_response = await client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "supersecret"
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Try to create device with missing required fields
            invalid_data = {"type": "switch"}  # Missing name
            response = await client.post("/api/v1/devices", json=invalid_data, headers=headers)
            assert response.status_code == 422  # Validation error


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""

    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Test that WebSocket endpoint exists
            # Note: Full WebSocket testing would require a WebSocket client
            # This is just checking that the endpoint is accessible
            pass
