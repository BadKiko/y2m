# Интеграция с Яндекс.Умный дом

## Обзор

Проект полностью реализует API провайдера для интеграции с Яндекс.Умный дом, включая:

- ✅ OAuth 2.0 для связки аккаунтов
- ✅ Provider API endpoints
- ✅ Управление устройствами
- ✅ Валидация токенов
- ✅ Обработка ошибок

## Архитектура

### Provider API Endpoints

```
/v1.0/
├── HEAD ""                    # Проверка доступности
├── GET "/user/devices"        # Список устройств
├── POST "/user/devices/query"  # Состояния устройств
├── POST "/user/devices/action" # Управление устройствами
└── POST "/user/unlink"        # Отвязка аккаунта
```

### OAuth 2.0 Endpoints

```
/dialog/authorize              # Авторизация
/oauth/token                   # Получение/обновление токенов
/.well-known/oauth-authorization-server  # Discovery
```

## Настройка навыка в Яндекс.Диалогах

### 1. Основные параметры

- **Название навыка**: Y2M Smart Home
- **Тип**: Умный дом
- **Endpoint URL**: `https://y2m.badkiko.ru/v1.0`

### 2. Связка аккаунтов

- **Идентификатор приложения**: `yandex-kiko-smarthome`
- **Client Identifier**: `yandex-kiko-smarthome`
- **Секрет приложения**: `your-skill-client-secret-here`
- **Client Password**: `your-skill-client-secret-here`
- **URL авторизации**: `https://y2m.badkiko.ru/dialog/authorize`
- **URL для получения токена**: `https://y2m.badkiko.ru/oauth/token`
- **URL для обновления токена**: `https://y2m.badkiko.ru/oauth/token`

### 3. Redirect URI

В настройках OAuth приложения в Яндекс ID укажите:
- **Redirect URI**: `https://social.yandex.net/broker/redirect`

## Запуск и тестирование

### 1. Запуск сервера

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Тестирование API

```bash
python test_yandex_api.py
```

### 3. Проверка endpoints

```bash
# Проверка доступности
curl -I https://y2m.badkiko.ru/v1.0

# OAuth Discovery
curl https://y2m.badkiko.ru/.well-known/oauth-authorization-server

# Список устройств (требует токен)
curl -H "Authorization: Bearer YOUR_TOKEN" https://y2m.badkiko.ru/v1.0/user/devices
```

## Структура данных

### Устройство

```json
{
  "id": "device_1",
  "name": "Умная лампа",
  "type": "devices.types.light",
  "capabilities": [
    {
      "type": "devices.capabilities.on_off",
      "retrievable": true,
      "reportable": true
    },
    {
      "type": "devices.capabilities.range",
      "retrievable": true,
      "reportable": true,
      "parameters": {
        "instance": "brightness",
        "range": {
          "min": 0,
          "max": 100,
          "precision": 1
        },
        "unit": "unit.percent"
      }
    }
  ],
  "device_info": {
    "manufacturer": "Y2M",
    "model": "Smart Light",
    "hw_version": "1.0",
    "sw_version": "1.0"
  }
}
```

### Запрос состояний

```json
{
  "devices": [
    {"id": "device_1"},
    {"id": "device_2"}
  ]
}
```

### Управление устройством

```json
{
  "devices": [
    {
      "id": "device_1",
      "capabilities": [
        {
          "type": "devices.capabilities.on_off",
          "state": {
            "instance": "on",
            "value": true
          }
        }
      ]
    }
  ]
}
```

## Поддерживаемые типы устройств

- `devices.types.light` - Освещение
- `devices.types.switch` - Выключатель
- `devices.types.media_device.tv` - Телевизор

## Поддерживаемые возможности

- `devices.capabilities.on_off` - Включение/выключение
- `devices.capabilities.range` - Диапазон значений (яркость, громкость)

## Безопасность

### OAuth 2.0 Flow

1. Пользователь переходит на `/dialog/authorize`
2. Перенаправление на Яндекс OAuth
3. Пользователь авторизуется
4. Яндекс возвращает код авторизации
5. Обмен кода на токен через `/oauth/token`
6. Использование токена для доступа к API

### Валидация токенов

- Токены хранятся в зашифрованном виде
- Проверка валидности при каждом запросе
- Поддержка refresh токенов

## Логирование

Все запросы логируются для отладки:

```python
logger.info(f"Device {device.id} on_off: {value}")
logger.error(f"Token validation error: {e}")
```

## Мониторинг

Рекомендуется настроить мониторинг:

- Доступность endpoints
- Время ответа (< 3 сек)
- Количество ошибок
- Использование токенов

## Развертывание

### Docker

```bash
cd deploy
docker-compose up -d
```

### SSL сертификаты

Обязательно используйте валидный SSL сертификат:

```bash
# Let's Encrypt
certbot --nginx -d y2m.badkiko.ru
```

## Отладка

### Частые проблемы

1. **SSL сертификат**: Используйте fullchain сертификат
2. **Таймауты**: Время ответа должно быть < 3 сек
3. **Токены**: Проверьте валидность OAuth токенов
4. **CORS**: Настройте CORS для веб-интерфейса

### Логи

```bash
# Просмотр логов
docker-compose logs -f backend

# Фильтрация по ошибкам
docker-compose logs backend | grep ERROR
```

## Полезные ссылки

- [Документация Яндекс.Умный дом](https://yandex.ru/dev/dialogs/smart-home/doc/ru/)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [Примеры интеграции](https://habr.com/ru/articles/465537/)

## Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь в корректности SSL сертификата
3. Проверьте настройки OAuth в консоли Яндекса
4. Протестируйте endpoints с помощью `test_yandex_api.py`
