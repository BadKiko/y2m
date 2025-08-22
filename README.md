# MQTT2Yandex Bridge

Полнофункциональный мост/панель управления для автоматического создания MQTT-устройств и управления ими через Яндекс (Yandex Home).

## 🚀 Функциональность

### Backend (FastAPI)
- **REST API** для управления устройствами и сценариями
- **WebSocket** для real-time обновлений
- **MQTT интеграция** (публикация/подписка)
- **Yandex Home интеграция** через yandex2mqtt
- **YAPI интеграция** для silent-вызовов на Яндекс-станцию
- **ADB модуль** для управления Android устройствами
- **PostgreSQL** база данных
- **Аутентификация** и авторизация

### Frontend (Streamlit)
- **Dashboard** - общий статус системы
- **Device Management** - создание/редактирование/удаление устройств
- **Scenario Builder** - визуальный редактор сценариев для кнопок
- **Yandex Integration** - управление аккаунтами Яндекс
- **ADB Console** - выполнение команд на Android устройствах
- **Settings** - конфигурация приложения

## 🏗️ Архитектура

```
mqtt2yandex/
├── app/                    # FastAPI backend
│   ├── api/               # API endpoints
│   ├── core/              # Configuration & security
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── streamlit_app/         # Streamlit frontend
├── migrations/            # Database migrations
├── docker/               # Docker configurations
└── docs/                 # Documentation
```

## 📋 Предварительные требования

- Docker и Docker Compose
- Доменное имя (для Traefik с HTTPS)
- Аккаунт Яндекс для OAuth (опционально)

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd mqtt2yandex
```

### 2. Конфигурация

```bash
cp env.example .env
```

Отредактируйте `.env` файл:

```env
# Базовые настройки
APP_ENV=production
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# База данных
DATABASE_URL=postgresql://postgres:password@db:5432/mqtt2yandex

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883

# Yandex OAuth (получите в Яндекс.OAuth)
YANDEX_CLIENT_ID=your-client-id
YANDEX_CLIENT_SECRET=your-client-secret

# Домен для Traefik
TRAFFIC_HOST=your-domain.com
ACME_EMAIL=your-email@example.com
```

### 3. Запуск

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build
```

### 4. Доступ к приложениям

- **Backend API**: https://your-domain.com
- **Streamlit UI**: https://your-domain.com/ui
- **Traefik Dashboard**: http://localhost:8080

## 🔧 Конфигурация

### Настройка Яндекс OAuth

1. Перейдите на [oauth.yandex.ru](https://oauth.yandex.ru/)
2. Создайте новое приложение
3. Добавьте права:
   - `yandex.home:read`
   - `yandex.home:write`
4. Укажите Callback URL: `https://your-domain.com/api/v1/yandex/callback`
5. Скопируйте Client ID и Client Secret в `.env`

### Настройка MQTT

По умолчанию используется Eclipse Mosquitto. Для использования внешнего брокера:

```env
MQTT_BROKER=your-mqtt-broker.com
MQTT_PORT=1883
MQTT_USERNAME=your-username
MQTT_PASSWORD=your-password
```

### Настройка ADB

Для использования ADB функциональности:

1. Убедитесь, что Android устройства в сети
2. Включите ADB debugging на устройствах
3. Добавьте устройства через Streamlit UI

## 📡 API Использование

### Аутентификация

```bash
curl -X POST "https://your-domain.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "supersecret"}'
```

### Создание устройства

```bash
curl -X POST "https://your-domain.com/api/v1/devices" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "living_room_light",
    "type": "switch",
    "meta": {"room": "living_room"}
  }'
```

### Публикация MQTT сообщения

```bash
curl -X POST "https://your-domain.com/api/v1/mqtt/publish" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "home/project/living_room_light/cmd",
    "payload": "{\"power\": \"on\"}",
    "qos": 0,
    "retain": false
  }'
```

## 🔧 Разработка

### Локальная разработка

```bash
# Backend
cd app
pip install -r requirements.txt
uvicorn main:app --reload

# Streamlit
cd streamlit_app
streamlit run app.py
```

### Тестирование

```bash
# Запуск тестов
pytest

# С линтингом
flake8 app/
black app/
```

## 🐳 Docker сервисы

- **app** - FastAPI backend (порт 8000)
- **streamlit** - Streamlit UI (порт 8501)
- **db** - PostgreSQL база данных (порт 5432)
- **mosquitto** - MQTT брокер (порт 1883)
- **yandex2mqtt** - Yandex Home интеграция (опционально)
- **yapi** - Yandex Station API (опционально)
- **traefik** - Reverse proxy с HTTPS
- **pgadmin** - Database admin (опционально, порт 5050)

## 📝 MQTT топики

При создании устройства `device_name`:

- **Base topic**: `home/project/device_name`
- **State topic**: `home/project/device_name/state`
- **Command topic**: `home/project/device_name/cmd`
- **Button topic**: `home/project/device_name/button/{button_id}`

## 🔒 Безопасность

- JWT токены для аутентификации
- Шифрование чувствительных данных
- HTTPS через Let's Encrypt
- RBAC для пользователей
- Rate limiting для API

## 📊 Мониторинг

- Health check endpoint: `/health`
- Structured logging
- Prometheus metrics (опционально)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 Лицензия

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи: `docker-compose logs`
2. Убедитесь, что все сервисы запущены: `docker-compose ps`
3. Проверьте конфигурацию в `.env`
4. Создайте issue с описанием проблемы

## 📚 Документация

- [API Documentation](https://your-domain.com/docs) - OpenAPI/Swagger
- [Architecture Overview](./docs/architecture.md)
- [Development Guide](./docs/development.md)
- [Deployment Guide](./docs/deployment.md)
