import pytest
import sys
import os
from unittest.mock import AsyncMock, Mock, patch

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.encryption_service import EncryptionService
from app.services.device_service import DeviceService
from app.schemas.device import DeviceCreate


class TestEncryptionService:
    """Test encryption service"""

    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption"""
        service = EncryptionService()
        test_data = "test_data_123"

        encrypted = service.encrypt(test_data)
        decrypted = service.decrypt(encrypted)

        assert decrypted == test_data
        assert encrypted != test_data

    def test_encrypt_different_outputs(self):
        """Test that same input produces different encrypted outputs"""
        service = EncryptionService()
        test_data = "test_data"

        encrypted1 = service.encrypt(test_data)
        encrypted2 = service.encrypt(test_data)

        assert encrypted1 != encrypted2  # Different outputs
        assert service.decrypt(encrypted1) == test_data
        assert service.decrypt(encrypted2) == test_data


class TestDeviceService:
    """Test device service"""

    @pytest.mark.asyncio
    async def test_create_device(self):
        """Test device creation"""
        # Mock database session
        mock_session = AsyncMock()
        mock_device = Mock()
        mock_device.id = 1
        mock_device.name = "test_device"
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Test device creation
        device_data = DeviceCreate(
            name="test_device",
            type="switch",
            meta={"room": "living_room"}
        )

        result = await DeviceService.create_device(mock_session, device_data)

        # Verify the device was added to session
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        assert result.name == "test_device"
        assert result.type == "switch"

    @pytest.mark.asyncio
    async def test_get_device_by_name_not_found(self):
        """Test getting device by name when not found"""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await DeviceService.get_device_by_name(mock_session, "nonexistent")

        assert result is None


class TestYandexService:
    """Test Yandex service"""

    @pytest.mark.asyncio
    async def test_is_token_expired(self):
        """Test token expiration check"""
        from app.services.yandex_service import YandexService
        from datetime import datetime, timedelta

        service = YandexService()

        # Test expired token
        expired_date = datetime.utcnow() - timedelta(hours=1)
        assert service.is_token_expired(expired_date) == True

        # Test valid token
        valid_date = datetime.utcnow() + timedelta(hours=1)
        assert service.is_token_expired(valid_date) == False


class TestYAPIService:
    """Test YAPI service"""

    @pytest.mark.asyncio
    async def test_execute_command_success(self):
        """Test successful YAPI command execution"""
        from app.services.yapi_service import YAPIService

        service = YAPIService()

        with patch('app.services.yapi_service.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_response.elapsed.total_seconds.return_value = 1.0
            mock_response.raise_for_status.return_value = None

            mock_context = AsyncMock()
            mock_context.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_context

            result = await service.execute_command("test command")

            assert result["success"] == True
            assert result["execution_time"] == 1.0

    @pytest.mark.asyncio
    async def test_execute_command_failure(self):
        """Test failed YAPI command execution"""
        from app.services.yapi_service import YAPIService

        service = YAPIService()

        with patch('app.services.yapi_service.httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_context.post.side_effect = Exception("Network error")
            mock_client.return_value.__aenter__.return_value = mock_context

            result = await service.execute_command("test command")

            assert result["success"] == False
            assert "Network error" in result["error"]


class TestADBService:
    """Test ADB service"""

    @pytest.mark.asyncio
    async def test_execute_command_success(self):
        """Test successful ADB command execution"""
        from app.services.adb_service import ADBService

        service = ADBService()
        device_id = 1

        # Mock ADB device
        mock_device = Mock()
        mock_device.shell.return_value = "command output"
        service.devices[device_id] = mock_device

        result = await service.execute_command(device_id, "test command")

        assert result["success"] == True
        assert result["output"] == "command output"
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_execute_command_device_not_connected(self):
        """Test ADB command execution when device not connected"""
        from app.services.adb_service import ADBService

        service = ADBService()
        device_id = 1

        result = await service.execute_command(device_id, "test command")

        assert result["success"] == False
        assert "not connected" in result["error"]
