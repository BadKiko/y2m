import pytest
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import Base
from app.models.device import Device
from app.models.scenario import ButtonScenario
from app.models.yandex_account import YandexAccount
from app.models.adb_device import ADBDevice
from app.models.audit_log import AuditLog


class TestDeviceModel:
    """Test Device model"""

    def test_device_creation(self):
        """Test creating a device instance"""
        device = Device(
            name="test_device",
            type="switch",
            mqtt_base_topic="home/project/test_device",
            state_topic="home/project/test_device/state",
            command_topic="home/project/test_device/cmd",
            meta={"room": "living_room"}
        )

        assert device.name == "test_device"
        assert device.type == "switch"
        assert device.mqtt_base_topic == "home/project/test_device"
        assert device.is_active == True  # Default value
        assert device.meta == {"room": "living_room"}

    def test_device_defaults(self):
        """Test device default values"""
        device = Device(
            name="test_device",
            type="light",
            mqtt_base_topic="home/project/test_device",
            state_topic="home/project/test_device/state",
            command_topic="home/project/test_device/cmd"
        )

        assert device.is_active == True
        assert device.meta == None


class TestButtonScenarioModel:
    """Test ButtonScenario model"""

    def test_scenario_creation(self):
        """Test creating a scenario instance"""
        scenario = ButtonScenario(
            device_id=1,
            button_name="button1",
            name="Turn on light",
            actions=[
                {"type": "mqtt_publish", "params": {"topic": "test", "payload": "on"}},
                {"type": "delay", "params": {"seconds": 1}}
            ]
        )

        assert scenario.device_id == 1
        assert scenario.button_name == "button1"
        assert scenario.name == "Turn on light"
        assert len(scenario.actions) == 2
        assert scenario.is_active == True  # Default value

    def test_scenario_defaults(self):
        """Test scenario default values"""
        scenario = ButtonScenario(
            device_id=1,
            button_name="button1",
            name="Test scenario",
            actions=[]
        )

        assert scenario.is_active == True


class TestYandexAccountModel:
    """Test YandexAccount model"""

    def test_account_creation(self):
        """Test creating a Yandex account instance"""
        account = YandexAccount(
            user="test@example.com",
            refresh_token="encrypted_refresh_token",
            access_token="encrypted_access_token",
            expires_at=datetime.utcnow()
        )

        assert account.user == "test@example.com"
        assert account.refresh_token == "encrypted_refresh_token"
        assert account.access_token == "encrypted_access_token"
        assert isinstance(account.expires_at, datetime)


class TestADBDeviceModel:
    """Test ADBDevice model"""

    def test_adb_device_creation(self):
        """Test creating an ADB device instance"""
        device = ADBDevice(
            name="test_android",
            ip="192.168.1.100",
            port=5555
        )

        assert device.name == "test_android"
        assert device.ip == "192.168.1.100"
        assert device.port == 5555
        assert device.is_connected == False  # Default value

    def test_adb_device_defaults(self):
        """Test ADB device default values"""
        device = ADBDevice(
            name="test_android",
            ip="192.168.1.100"
        )

        assert device.port == 5555  # Default port
        assert device.is_connected == False


class TestAuditLogModel:
    """Test AuditLog model"""

    def test_audit_log_creation(self):
        """Test creating an audit log instance"""
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            user="admin",
            action="create_device",
            resource="device",
            resource_id=1,
            payload={"name": "test_device"},
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0..."
        )

        assert audit_log.user == "admin"
        assert audit_log.action == "create_device"
        assert audit_log.resource == "device"
        assert audit_log.resource_id == 1
        assert audit_log.ip_address == "127.0.0.1"
