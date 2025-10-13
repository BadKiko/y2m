# Настройка yapi для интеграции с Яндекс Станцией

## 1. Добавление переменных в env.local

Добавьте в файл `env.local`:

```bash
# Yandex OAuth Token - получите в https://oauth.yandex.ru/
YANDEX_OAUTH_TOKEN=your_oauth_token_here

# Device ID Яндекс Станции - найдите в приложении Яндекс
YANDEX_DEVICE_ID=your_device_id_here

# Порт для yapi (опционально)
YAPI_PORT=8001
```

## 2. Получение OAuth токена

1. Перейдите в [Яндекс OAuth Console](https://oauth.yandex.ru/)
2. Создайте новое приложение или используйте существующее
3. Получите OAuth токен для вашего аккаунта
4. Скопируйте токен в `YANDEX_OAUTH_TOKEN`

## 3. Получение Device ID

1. Откройте приложение Яндекс на телефоне
2. Перейдите в раздел "Устройства"
3. Найдите вашу Яндекс Станцию
4. Скопируйте ID устройства в `YANDEX_DEVICE_ID`

## 4. Запуск с yapi

```bash
# Перейдите в папку deploy
cd deploy

# Запустите все сервисы включая yapi
docker-compose up -d

# Проверьте статус yapi
docker-compose ps yapi

# Просмотр логов yapi
docker-compose logs -f yapi
```

## 5. Проверка работы

```bash
# Тест API yapi
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  -d '{"command": "sendText", "text": "Привет, это тест"}'
```

## 6. Управление yapi

```bash
# Перезапуск только yapi
docker-compose restart yapi

# Остановка yapi
docker-compose stop yapi

# Запуск yapi
docker-compose start yapi
```

## 7. Troubleshooting

### yapi не запускается
```bash
# Проверьте логи
docker-compose logs yapi

# Проверьте переменные окружения
docker-compose exec yapi env | grep -E "(OAUTH_TOKEN|DEVICE_ID)"
```

### Неверный OAuth токен
- Убедитесь, что токен действителен
- Проверьте права доступа токена
- Обновите токен в `env.local` и перезапустите контейнер

### Неверный Device ID
- Проверьте ID устройства в приложении Яндекс
- Убедитесь, что станция подключена к интернету
- Проверьте, что станция находится в том же аккаунте
