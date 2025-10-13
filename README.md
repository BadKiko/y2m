# y2m — Yandex Home MQTT Bridge (MVP)

Ссылки:
- Домовёнок Кузя: https://alexstar.ru/
- yandex2mqtt: https://github.com/munrexio/yandex2mqtt
- yapi: https://github.com/ebuyan/yapi
- Типы устройств: https://yandex.ru/dev/dialogs/smart-home/doc/ru/concepts/device-types.html
- Навык: https://dialogs.yandex.ru/developer/skills/0b2a8e37-63c8-4934-bd4c-524422489871
- Auth в УД: https://yandex.ru/dev/dialogs/smart-home/doc/ru/auth.html

Запуск:
1. Создайте `.env.local` в корне (см. пример ниже).
2. `cd deploy && docker compose up -d --build`
3. Откройте Web `http://<host>:5173` и Backend `http://<host>:8000/health`.

Пример `.env.local`:
```
BACKEND_PORT=8000
WEB_PORT=5173
MOSQUITTO_PORT=1883
MOSQUITTO_WS_PORT=9001
MQTT_HOST=mosquitto
MQTT_PORT=1883
POSTGRES_USER=y2m
POSTGRES_PASSWORD=y2m
POSTGRES_DB=y2m
POSTGRES_PORT=5432
BACKEND_URL=https://y2m.badkiko.ru
WEB_URL=http://localhost:5173
YA_CLIENT_ID=
YA_CLIENT_SECRET=
YA_REDIRECT_URI=https://y2m.badkiko.ru/api/auth/yandex/callback
Y2M_ENC_KEY=
```

Web `.env` (в каталоге `web/`):
```
VITE_BACKEND_URL=https://y2m.badkiko.ru
```

ADB примеры:
- POST `/api/adb/connect` `{ "host":"192.168.1.10", "port":5555 }`
- POST `/api/adb/exec` `{ "host":"192.168.1.10", "port":5555, "cmd":"input keyevent 26" }`

MQTT:
- Вызов: `y2m/bindings/{bindingId}/invoke`
- Ответ: `y2m/devices/{deviceId}/state`

