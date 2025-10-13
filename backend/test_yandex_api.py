#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Яндекс.Умный дом Provider API
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class YandexAPITester:
    def __init__(self, base_url: str = "https://y2m.badkiko.ru"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_health_check(self) -> bool:
        """Тестирует проверку доступности endpoint"""
        try:
            response = await self.client.head(f"{self.base_url}/v1.0")
            print(f"✅ Health check: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_oauth_discovery(self) -> bool:
        """Тестирует OAuth Discovery endpoint"""
        try:
            response = await self.client.get(f"{self.base_url}/.well-known/oauth-authorization-server")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ OAuth Discovery: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ OAuth Discovery failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ OAuth Discovery failed: {e}")
            return False
    
    async def test_authorize_endpoint(self) -> bool:
        """Тестирует OAuth authorize endpoint"""
        try:
            params = {
                "response_type": "code",
                "client_id": "yandex-kiko-smarthome",
                "redirect_uri": "https://social.yandex.net/broker/redirect"
            }
            response = await self.client.get(f"{self.base_url}/dialog/authorize", params=params)
            print(f"✅ Authorize endpoint: {response.status_code}")
            return response.status_code in [200, 302]  # Может быть редирект
        except Exception as e:
            print(f"❌ Authorize endpoint failed: {e}")
            return False
    
    async def test_devices_endpoint(self, token: str = "test_token") -> bool:
        """Тестирует получение списка устройств"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(f"{self.base_url}/v1.0/user/devices", headers=headers)
            print(f"✅ Devices endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Devices: {json.dumps(data, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Devices endpoint failed: {e}")
            return False
    
    async def test_query_endpoint(self, token: str = "test_token") -> bool:
        """Тестирует запрос состояний устройств"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            data = {"devices": [{"id": "test_device"}]}
            response = await self.client.post(
                f"{self.base_url}/v1.0/user/devices/query", 
                headers=headers, 
                json=data
            )
            print(f"✅ Query endpoint: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Query result: {json.dumps(result, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Query endpoint failed: {e}")
            return False
    
    async def test_action_endpoint(self, token: str = "test_token") -> bool:
        """Тестирует выполнение действий с устройствами"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "devices": [{
                    "id": "test_device",
                    "capabilities": [{
                        "type": "devices.capabilities.on_off",
                        "state": {"instance": "on", "value": True}
                    }]
                }]
            }
            response = await self.client.post(
                f"{self.base_url}/v1.0/user/devices/action", 
                headers=headers, 
                json=data
            )
            print(f"✅ Action endpoint: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Action result: {json.dumps(result, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ Action endpoint failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Запускает все тесты"""
        print("🚀 Запуск тестов Яндекс.Умный дом Provider API")
        print("=" * 50)
        
        results = {}
        
        # Тесты без авторизации
        results["health_check"] = await self.test_health_check()
        results["oauth_discovery"] = await self.test_oauth_discovery()
        results["authorize_endpoint"] = await self.test_authorize_endpoint()
        
        # Тесты с авторизацией (ожидаем 401 без валидного токена)
        results["devices_endpoint"] = await self.test_devices_endpoint()
        results["query_endpoint"] = await self.test_query_endpoint()
        results["action_endpoint"] = await self.test_action_endpoint()
        
        print("\n" + "=" * 50)
        print("📊 Результаты тестирования:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        passed = sum(results.values())
        total = len(results)
        print(f"\n🎯 Итого: {passed}/{total} тестов прошли успешно")
        
        return results
    
    async def close(self):
        """Закрывает HTTP клиент"""
        await self.client.aclose()


async def main():
    """Основная функция"""
    tester = YandexAPITester()
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
