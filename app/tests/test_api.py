import pytest
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestHealthCheck:
    """Test health check endpoint"""

    async def test_health_check(self, client):
        """Test health check endpoint returns 200"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestAuth:
    """Test authentication endpoints"""

    async def test_login_success(self, client):
        """Test successful login"""
        login_data = {
            "username": "admin",
            "password": "supersecret"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_failure(self, client):
        """Test login with wrong credentials"""
        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 400

class TestDevices:
    """Test device management endpoints"""

    async def test_get_devices_unauthorized(self, client):
        """Test getting devices without authentication"""
        response = await client.get("/api/v1/devices")

        assert response.status_code == 401

    async def test_get_devices_authorized(self, client):
        """Test getting devices with authentication"""
        # First login
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "supersecret"
        })

        token = login_response.json()["access_token"]

        # Then get devices
        response = await client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestMQTT:
    """Test MQTT endpoints"""

    async def test_mqtt_status_unauthorized(self, client):
        """Test MQTT status without authentication"""
        response = await client.get("/api/v1/mqtt/status")

        assert response.status_code == 401

    async def test_mqtt_publish_unauthorized(self, client):
        """Test MQTT publish without authentication"""
        publish_data = {
            "topic": "test/topic",
            "payload": "test message"
        }

        response = await client.post("/api/v1/mqtt/publish", json=publish_data)

        assert response.status_code == 401
