# Настройка навыка Яндекс.Умный дом

## Различие между OAuth credentials

### 1. Яндекс OAuth (YA_CLIENT_ID/YA_CLIENT_SECRET)
- **Назначение**: Для авторизации пользователей через Яндекс ID
- **Использование**: В `/api/auth/yandex/login` endpoint
- **Где получить**: [Яндекс ID Console](https://oauth.yandex.ru/)

### 2. Навык Client Credentials (YANDEX_SKILL_CLIENT_ID/YANDEX_SKILL_CLIENT_SECRET)
- **Назначение**: Для связки аккаунтов в навыке Яндекс.Умный дом
- **Использование**: В `/dialog/authorize` и `/oauth/token` endpoints
- **Где получить**: В консоли разработчика Яндекс.Диалоги

## Настройка навыка

### Шаг 1: Создание навыка
1. Перейдите в [консоль разработчика Яндекс.Диалоги](https://dialogs.yandex.ru/developer)
2. Создайте новый навык типа "Умный дом"
3. Заполните основную информацию

### Шаг 2: Настройка Provider API
- **Endpoint URL**: `https://y2m.badkiko.ru/v1.0`
- **Адрес для запросов**: `https://y2m.badkiko.ru/v1.0`

### Шаг 3: Связка аккаунтов
В разделе "Связка аккаунтов" укажите:

- **Идентификатор приложения**: `yandex-kiko-smarthome`
- **Client Identifier**: `yandex-kiko-smarthome`
- **Секрет приложения**: `[СГЕНЕРИРУЙТЕ_СЕКРЕТ]`
- **Client Password**: `[ТОТ_ЖЕ_СЕКРЕТ]`

#### Генерация Client Secret
```bash
# Генерируем случайный секрет
openssl rand -base64 32
# или
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Шаг 4: OAuth Endpoints
- **URL авторизации**: `https://y2m.badkiko.ru/dialog/authorize`
- **URL для получения токена**: `https://y2m.badkiko.ru/oauth/token`
- **URL для обновления токена**: `https://y2m.badkiko.ru/oauth/token`

### Шаг 5: Redirect URI
В настройках OAuth приложения в Яндекс ID:
- **Redirect URI**: `https://social.yandex.net/broker/redirect`

**Важно**: Этот URI должен быть зарегистрирован в вашем OAuth приложении в Яндекс ID Console.

## Обновление конфигурации

### 1. Обновите env.local
```bash
# Яндекс.Умный дом навык (Client Identifier и Password для навыка)
YANDEX_SKILL_CLIENT_ID=yandex-kiko-smarthome
YANDEX_SKILL_CLIENT_SECRET=ваш-сгенерированный-секрет
```

### 2. Перезапустите сервер
```bash
docker-compose restart backend
```

## Тестирование

### 1. Проверка OAuth Discovery
```bash
curl https://y2m.badkiko.ru/.well-known/oauth-authorization-server
```

### 2. Тестирование авторизации
```bash
curl "https://y2m.badkiko.ru/dialog/authorize?response_type=code&client_id=yandex-kiko-smarthome&redirect_uri=https://social.yandex.net/broker/redirect"
```

### 3. Проверка broker redirect
```bash
curl "https://y2m.badkiko.ru/broker/redirect?code=test_code&state=test_state"
```

### 4. Проверка Provider API
```bash
curl -I https://y2m.badkiko.ru/v1.0
```

## Важные моменты

### SSL сертификаты
- Обязательно используйте валидный SSL сертификат
- Яндекс не принимает самоподписанные сертификаты
- Рекомендуется Let's Encrypt

### Производительность
- Время ответа должно быть < 3 секунд
- Длина ответа < 5000 символов
- Длина токенов < 2048 символов

### Безопасность
- Храните секреты в переменных окружения
- Не коммитьте секреты в git
- Используйте HTTPS для всех endpoints

## Отладка

### Логи
```bash
# Просмотр логов backend
docker-compose logs -f backend

# Фильтрация по ошибкам
docker-compose logs backend | grep ERROR
```

### Частые ошибки
1. **Invalid client_id**: Проверьте YANDEX_SKILL_CLIENT_ID
2. **Invalid client_secret**: Проверьте YANDEX_SKILL_CLIENT_SECRET
3. **SSL certificate error**: Обновите SSL сертификат
4. **Timeout**: Проверьте производительность сервера

## Готовность к публикации

После настройки всех параметров:
1. Протестируйте все endpoints
2. Проверьте SSL сертификаты
3. Убедитесь в корректной работе OAuth flow
4. Отправьте навык на модерацию
