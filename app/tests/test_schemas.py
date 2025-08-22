import pytest
import sys
import os
from datetime import datetime
from pydantic import ValidationError

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceState
from app.schemas.scenario import ButtonScenarioCreate, ActionBase
from app.schemas.yandex import YandexAccountCreate, YandexLoginRequest
from app.schemas.adb import ADBDeviceCreate, ADBCommand
from app.schemas.mqtt import MQTTPublishRequest
from app.schemas.auth import LoginRequest


class TestDeviceSchemas:
    """Test device schemas"""

    def test_device_create_valid(self):
        """Test valid device creation schema"""
        device = DeviceCreate(
            name="test_device",
            type="switch",
            meta={"room": "living_room"}
        )

        assert device.name == "test_device"
        assert device.type == "switch"
        assert device.meta == {"room": "living_room"}

    def test_device_create_minimal(self):
        """Test minimal device creation schema"""
        device = DeviceCreate(
            name="test_device",
            type="light"
        )

        assert device.name == "test_device"
        assert device.type == "light"
        assert device.meta == {}

    def test_device_update_partial(self):
        """Test partial device update schema"""
        update = DeviceUpdate(
            name="new_name",
            is_active=False
        )

        assert update.name == "new_name"
        assert update.is_active == False
        assert update.type is None  # Not provided

    def test_device_state(self):
        """Test device state schema"""
        state = DeviceState(
            power="on",
            brightness=80,
            temperature=22.5
        )

        assert state.power == "on"
        assert state.brightness == 80
        assert state.temperature == 22.5


class TestScenarioSchemas:
    """Test scenario schemas"""

    def test_button_scenario_create(self):
        """Test button scenario creation schema"""
        scenario = ButtonScenarioCreate(
            device_id=1,
            button_name="button1",
            name="Turn on light",
            actions=[
                {
                    "type": "mqtt_publish",
                    "params": {"topic": "test/topic", "payload": "on"}
                },
                {
                    "type": "delay",
                    "params": {"seconds": 1}
                }
            ]
        )

        assert scenario.device_id == 1
        assert scenario.button_name == "button1"
        assert scenario.name == "Turn on light"
        assert len(scenario.actions) == 2

    def test_action_base(self):
        """Test action base schema"""
        action = ActionBase(
            type="mqtt_publish",
            params={"topic": "test", "payload": "data"}
        )

        assert action.type == "mqtt_publish"
        assert action.params == {"topic": "test", "payload": "data"}


class TestYandexSchemas:
    """Test Yandex schemas"""

    def test_yandex_account_create(self):
        """Test Yandex account creation schema"""
        account = YandexAccountCreate(
            user="test@example.com",
            refresh_token="refresh_token_123",
            access_token="access_token_456",
            expires_at=datetime.utcnow()
        )

        assert account.user == "test@example.com"
        assert account.refresh_token == "refresh_token_123"
        assert account.access_token == "access_token_456"
        assert isinstance(account.expires_at, datetime)

    def test_yandex_login_request(self):
        """Test Yandex login request schema"""
        login = YandexLoginRequest(
            username="test@example.com",
            password="password123"
        )

        assert login.username == "test@example.com"
        assert login.password == "password123"


class TestADBSchemas:
    """Test ADB schemas"""

    def test_adb_device_create(self):
        """Test ADB device creation schema"""
        device = ADBDeviceCreate(
            name="test_android",
            ip="192.168.1.100",
            port=5555
        )

        assert device.name == "test_android"
        assert device.ip == "192.168.1.100"
        assert device.port == 5555

    def test_adb_device_create_default_port(self):
        """Test ADB device creation with default port"""
        device = ADBDeviceCreate(
            name="test_android",
            ip="192.168.1.100"
        )

        assert device.port == 5555  # Default value

    def test_adb_command(self):
        """Test ADB command schema"""
        command = ADBCommand(
            device_id=1,
            command="input keyevent 26",
            timeout=30
        )

        assert command.device_id == 1
        assert command.command == "input keyevent 26"
        assert command.timeout == 30

    def test_adb_command_default_timeout(self):
        """Test ADB command with default timeout"""
        command = ADBCommand(
            device_id=1,
            command="shell input keyevent 26"
        )

        assert command.timeout == 30  # Default value


class TestMQTTSchemas:
    """Test MQTT schemas"""

    def test_mqtt_publish_request(self):
        """Test MQTT publish request schema"""
        request = MQTTPublishRequest(
            topic="home/test/device/cmd",
            payload='{"power": "on"}',
            qos=1,
            retain=True
        )

        assert request.topic == "home/test/device/cmd"
        assert request.payload == '{"power": "on"}'
        assert request.qos == 1
        assert request.retain == True

    def test_mqtt_publish_request_defaults(self):
        """Test MQTT publish request with defaults"""
        request = MQTTPublishRequest(
            topic="home/test/device/cmd",
            payload="on"
        )

        assert request.qos == 0  # Default value
        assert request.retain == False  # Default value


class TestAuthSchemas:
    """Test authentication schemas"""

    def test_login_request(self):
        """Test login request schema"""
        login = LoginRequest(
            username="admin",
            password="supersecret"
        )

        assert login.username == "admin"
        assert login.password == "supersecret"


class TestSchemaValidation:
    """Test schema validation errors"""

    def test_device_create_name_required(self):
        """Test that device name is required"""
        with pytest.raises(ValidationError):
            DeviceCreate(type="switch")

    def test_device_create_type_required(self):
        """Test that device type is required"""
        with pytest.raises(ValidationError):
            DeviceCreate(name="test_device")

    def test_mqtt_publish_topic_required(self):
        """Test that MQTT topic is required"""
        with pytest.raises(ValidationError):
            MQTTPublishRequest(payload="test")

    def test_mqtt_publish_payload_required(self):
        """Test that MQTT payload is required"""
        with pytest.raises(ValidationError):
            MQTTPublishRequest(topic="test/topic")
