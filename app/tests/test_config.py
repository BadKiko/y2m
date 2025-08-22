import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import Settings


class TestConfig:
    """Test application configuration"""

    @patch.dict(os.environ, {
        'APP_ENV': 'production',
        'SECRET_KEY': 'test-secret-key',
        'ENCRYPTION_KEY': 'test-encryption-key',
        'DATABASE_URL': 'postgresql://test:test@localhost/test_db',
        'MQTT_BROKER': 'test-broker',
        'MQTT_PORT': '1883',
        'YANDEX_CLIENT_ID': 'test-client-id',
        'YANDEX_CLIENT_SECRET': 'test-client-secret',
        'YAPI_URL': 'http://test-yapi:8080',
        'ADMIN_USER': 'test-admin',
        'ADMIN_PASS': 'test-password'
    })
    def test_config_from_env(self):
        """Test loading configuration from environment variables"""
        settings = Settings()

        assert settings.APP_ENV == 'production'
        assert settings.SECRET_KEY == 'test-secret-key'
        assert settings.ENCRYPTION_KEY == 'test-encryption-key'
        assert settings.DATABASE_URL == 'postgresql://test:test@localhost/test_db'
        assert settings.MQTT_BROKER == 'test-broker'
        assert settings.MQTT_PORT == 1883
        assert settings.YANDEX_CLIENT_ID == 'test-client-id'
        assert settings.YANDEX_CLIENT_SECRET == 'test-client-secret'
        assert settings.YAPI_URL == 'http://test-yapi:8080'
        assert settings.ADMIN_USER == 'test-admin'
        assert settings.ADMIN_PASS == 'test-password'

    def test_config_defaults(self):
        """Test configuration default values"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ENCRYPTION_KEY': 'test-encryption-key',
            'DATABASE_URL': 'postgresql://test:test@localhost/test_db'
        }, clear=True):
            settings = Settings()

            # Test default values
            assert settings.MQTT_BROKER == 'mosquitto'
            assert settings.MQTT_PORT == 1883
            assert settings.API_V1_STR == '/api/v1'
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
            assert settings.ADMIN_USER == 'admin'
            assert settings.ADMIN_PASS == 'admin'

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ENCRYPTION_KEY': 'test-encryption-key',
            'DATABASE_URL': 'postgresql://test:test@localhost/test_db',
            'BACKEND_CORS_ORIGINS': 'https://example.com,https://test.com'
        }):
            settings = Settings()

            assert len(settings.BACKEND_CORS_ORIGINS) == 2
            assert "https://example.com" in settings.BACKEND_CORS_ORIGINS
            assert "https://test.com" in settings.BACKEND_CORS_ORIGINS

    def test_cors_origins_single_value(self):
        """Test CORS origins with single value"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ENCRYPTION_KEY': 'test-encryption-key',
            'DATABASE_URL': 'postgresql://test:test@localhost/test_db',
            'BACKEND_CORS_ORIGINS': 'https://example.com'
        }):
            settings = Settings()

            assert len(settings.BACKEND_CORS_ORIGINS) == 1
            assert "https://example.com" in settings.BACKEND_CORS_ORIGINS

    def test_cors_origins_empty(self):
        """Test CORS origins when not set"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ENCRYPTION_KEY': 'test-encryption-key',
            'DATABASE_URL': 'postgresql://test:test@localhost/test_db'
        }, clear=True):
            settings = Settings()

            assert len(settings.BACKEND_CORS_ORIGINS) == 0

    def test_required_settings(self):
        """Test that required settings are present"""
        required_env_vars = [
            'SECRET_KEY',
            'ENCRYPTION_KEY',
            'DATABASE_URL'
        ]

        # Test that missing required settings raise an error
        for var in required_env_vars:
            env_copy = os.environ.copy()
            if var in env_copy:
                del env_copy[var]

            with patch.dict(os.environ, env_copy, clear=True):
                with pytest.raises(Exception):  # Should raise validation error
                    Settings()

    def test_port_conversion(self):
        """Test that string port is converted to int"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ENCRYPTION_KEY': 'test-encryption-key',
            'DATABASE_URL': 'postgresql://test:test@localhost/test_db',
            'MQTT_PORT': '1883'
        }):
            settings = Settings()

            assert isinstance(settings.MQTT_PORT, int)
            assert settings.MQTT_PORT == 1883
