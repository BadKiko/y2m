# Настройка OAuth приложения в Яндекс ID

## Проблема
При нажатии "Связать аккаунты" в навыке Яндекс.Умный дом происходит перенаправление в веб-приложение вместо завершения процесса связки в навыке.

## Решение
Необходимо правильно настроить OAuth приложение в Яндекс ID Console.

## Шаги настройки

### 1. Перейдите в Яндекс ID Console
Откройте [https://oauth.yandex.ru/](https://oauth.yandex.ru/) и войдите в консоль разработчика.

### 2. Создайте новое приложение
1. Нажмите "Создать приложение"
2. Заполните основную информацию:
   - **Название**: Y2M Smart Home
   - **Описание**: Интеграция с Яндекс.Умный дом
   - **Платформы**: Web

### 3. Настройте Redirect URI
В разделе "Callback URI" добавьте:
```
https://social.yandex.net/broker/redirect
```

**Важно**: Этот URI обязателен для навыков Яндекс.Умный дом.

### 4. Получите Client ID и Secret
После создания приложения вы получите:
- **Client ID**: `012e671ea67a428b8973946e71827764`
- **Client Secret**: `fbeec2a94ab0451989c497fc3e28810a`

### 5. Обновите конфигурацию
Убедитесь, что в `env.local` указаны правильные значения:
```bash
# OAuth Yandex (для авторизации через Яндекс)
YA_CLIENT_ID=012e671ea67a428b8973946e71827764
YA_CLIENT_SECRET=fbeec2a94ab0451989c497fc3e28810a

# Яндекс.Умный дом навык (Client Identifier и Password для навыка)
YANDEX_SKILL_CLIENT_ID=yandex-kiko-smarthome
YANDEX_SKILL_CLIENT_SECRET=fbeec2a94ab0451989c497fc3e28810a
```

## Правильный OAuth Flow

### 1. Пользователь нажимает "Связать аккаунты"
- Навык отправляет запрос на `/dialog/authorize`
- Сервер проверяет, есть ли уже авторизованный пользователь

### 2. Проверка авторизации
- **Если пользователь авторизован**: генерируется код авторизации и сразу перенаправление обратно в навык
- **Если не авторизован**: перенаправление на веб-приложение для авторизации

### 3. Обмен кода на токен
- Навык отправляет код на `/oauth/token`
- Сервер возвращает существующий токен пользователя
- Связка аккаунтов завершается

### 4. Управление устройствами
- Навык использует токен для доступа к Provider API
- Пользователь может управлять устройствами через Алису

## Endpoints

### Авторизация
```
GET /dialog/authorize?response_type=code&client_id=yandex-kiko-smarthome&redirect_uri=https://social.yandex.net/broker/redirect
```

**Результат**: Если пользователь авторизован - сразу перенаправление с кодом, если нет - на веб-приложение.

### Получение токена
```
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=AUTH_CODE&client_id=yandex-kiko-smarthome&client_secret=SECRET&redirect_uri=https://social.yandex.net/broker/redirect
```

## Тестирование

### 1. Проверка авторизации
```bash
curl "https://y2m.badkiko.ru/dialog/authorize?response_type=code&client_id=yandex-kiko-smarthome&redirect_uri=https://social.yandex.net/broker/redirect"
```

**Ожидаемый результат**: 
- Если пользователь авторизован: редирект с кодом авторизации
- Если не авторизован: редирект на веб-приложение

### 2. Проверка токена
```bash
curl -X POST "https://y2m.badkiko.ru/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=test&client_id=yandex-kiko-smarthome&client_secret=fbeec2a94ab0451989c497fc3e28810a&redirect_uri=https://social.yandex.net/broker/redirect"
```

## Частые ошибки

### 1. "Invalid redirect_uri"
- Проверьте, что `https://social.yandex.net/broker/redirect` добавлен в Яндекс ID Console
- Убедитесь, что URI точно совпадает (без лишних пробелов)

### 2. "Invalid client_id"
- Проверьте `YANDEX_SKILL_CLIENT_ID` в настройках навыка
- Убедитесь, что Client ID совпадает в навыке и в коде

### 3. "Invalid client_secret"
- Проверьте `YANDEX_SKILL_CLIENT_SECRET` в настройках навыка
- Убедитесь, что Secret совпадает в навыке и в коде

### 4. Перенаправление в веб-приложение
- Проверьте, что используется правильный `redirect_uri`
- Убедитесь, что callback endpoint `/broker/redirect` работает

## Логирование

Для отладки включите подробное логирование:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Проверьте логи при связке аккаунтов:
```bash
docker-compose logs -f backend | grep -E "(oauth|broker|redirect)"
```

## Готовность к тестированию

После настройки всех параметров:
1. Перезапустите сервер
2. Обновите конфигурацию Traefik
3. Протестируйте связку аккаунтов в навыке
4. Проверьте логи на наличие ошибок
