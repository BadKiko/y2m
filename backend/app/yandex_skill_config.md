# Конфигурация навыка Яндекс.Умный дом

## Основные настройки

### Backend
- **Endpoint URL**: `https://y2m.badkiko.ru/v1.0`
- **Адрес, на который будут отправляться запросы**: `https://y2m.badkiko.ru/v1.0`

## Связка аккаунтов (OAuth 2.0)

### Основные параметры
- **Идентификатор приложения**: `yandex-kiko-smarthome`
- **Client Identifier**: `yandex-kiko-smarthome`
- **Секрет приложения**: `your-skill-client-secret-here`
- **Client Password**: `your-skill-client-secret-here`

### OAuth Endpoints
- **URL авторизации**: `https://y2m.badkiko.ru/dialog/authorize`
- **API authorization endpoint**: `https://y2m.badkiko.ru/dialog/authorize`
- **URL для получения токена**: `https://y2m.badkiko.ru/oauth/token`
- **Token Endpoint**: `https://y2m.badkiko.ru/oauth/token`
- **URL для обновления токена**: `https://y2m.badkiko.ru/oauth/token`
- **Refreshing an Access Token**: `https://y2m.badkiko.ru/oauth/token`

## Provider API Endpoints

### Основные endpoints
1. **Проверка доступности**: `HEAD https://y2m.badkiko.ru/v1.0`
2. **Список устройств**: `GET https://y2m.badkiko.ru/v1.0/user/devices`
3. **Состояния устройств**: `POST https://y2m.badkiko.ru/v1.0/user/devices/query`
4. **Управление устройствами**: `POST https://y2m.badkiko.ru/v1.0/user/devices/action`
5. **Отвязка устройства**: `POST https://y2m.badkiko.ru/v1.0/user/devices/unlink`
6. **Отвязка аккаунта**: `POST https://y2m.badkiko.ru/v1.0/user/unlink`

### OAuth Discovery
- **OAuth Discovery**: `GET https://y2m.badkiko.ru/.well-known/oauth-authorization-server`

## Требования

### SSL/TLS
- Обязательно использование HTTPS
- Валидный SSL-сертификат (fullchain)
- Порт 443 для HTTPS

### Производительность
- Время ответа не более 3 секунд
- Длина ответа не более 5000 символов
- Длина OAuth-токенов не более 2048 символов

### Безопасность
- OAuth 2.0 Authorization Code Grant
- Валидация токенов доступа
- Защита от CSRF атак

## Тестирование

### Проверка endpoints
```bash
# Проверка доступности
curl -I https://y2m.badkiko.ru/v1.0

# OAuth Discovery
curl https://y2m.badkiko.ru/.well-known/oauth-authorization-server

# Список устройств (требует токен)
curl -H "Authorization: Bearer YOUR_TOKEN" https://y2m.badkiko.ru/v1.0/user/devices
```

### Тестирование OAuth
1. Перейти на `https://y2m.badkiko.ru/dialog/authorize?response_type=code&client_id=yandex-kiko-smarthome&redirect_uri=https://social.yandex.net/broker/redirect`
2. Авторизоваться через Яндекс
3. Получить код авторизации
4. Обменять код на токен через `/oauth/token`

## Логирование

Все запросы к Provider API логируются для отладки:
- Входящие запросы
- Ошибки авторизации
- Действия с устройствами
- Ошибки выполнения команд

## Мониторинг

Рекомендуется настроить мониторинг:
- Доступность endpoints
- Время ответа
- Количество ошибок
- Использование токенов
