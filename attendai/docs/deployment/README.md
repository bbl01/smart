# 📦 Развёртывание AttendAI

## Локальная разработка

### Предварительные требования

| Инструмент | Версия | Назначение |
|------------|--------|-----------|
| Docker | 24.0+ | Контейнеризация |
| Docker Compose | 2.20+ | Оркестрация |
| Git | 2.40+ | Контроль версий |
| RAM | 8 GB+ | Для ML-моделей |
| GPU (опционально) | NVIDIA CUDA 11.8+ | Ускорение распознавания |

### Запуск

```bash
# 1. Клонировать и настроить
git clone https://github.com/your-org/attendai.git
cd attendai
cp .env.example .env

# 2. Обязательно изменить в .env:
#    SECRET_KEY, POSTGRES_PASSWORD, FIRST_ADMIN_PASSWORD

# 3. Запустить
docker compose up -d

# 4. Инициализировать БД
docker compose exec backend python -m app.cli init-db

# 5. Открыть
# Web: http://localhost:3000
# API: http://localhost:8000/docs
```

---

## Production развёртывание

### Рекомендуемые характеристики сервера

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32 GB |
| Диск | 100 GB SSD | 500 GB SSD |
| GPU | — | NVIDIA RTX 3080+ |
| Сеть | 100 Mbps | 1 Gbps |

### 1. Подготовка сервера (Ubuntu 22.04)

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo apt install docker-compose-plugin

# Создание директории
sudo mkdir -p /opt/attendai
cd /opt/attendai
git clone https://github.com/your-org/attendai.git .
```

### 2. SSL-сертификат (Let's Encrypt)

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.edu

# Сертификаты будут в:
# /etc/letsencrypt/live/your-domain.edu/fullchain.pem
# /etc/letsencrypt/live/your-domain.edu/privkey.pem

# Скопировать в проект
sudo cp /etc/letsencrypt/live/your-domain.edu/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.edu/privkey.pem docker/nginx/ssl/
```

### 3. Настройка production .env

```bash
cp .env.example .env
nano .env

# Критически важные настройки:
ENVIRONMENT=production
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 24)
REDIS_PASSWORD=$(openssl rand -base64 16)
MINIO_ROOT_PASSWORD=$(openssl rand -base64 16)

# Отключить DEBUG логирование:
LOG_LEVEL=WARNING
```

### 4. Production запуск

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Миграции БД
docker compose exec backend alembic upgrade head

# Создать первого администратора
docker compose exec backend python -m app.cli create-admin \
  --email admin@school.edu \
  --name "Системный администратор"
```

### 5. Systemd автозапуск

```ini
# /etc/systemd/system/attendai.service
[Unit]
Description=AttendAI Attendance System
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/attendai
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable attendai
sudo systemctl start attendai
```

---

## Мониторинг

### Grafana Dashboards

```bash
# Запустить с мониторингом
docker compose --profile monitoring up -d

# Grafana: http://your-server:3001
# По умолчанию: admin / admin (сменить!)
```

Готовые дашборды в `docker/grafana/dashboards/`:
- `system.json` — CPU, RAM, диск
- `api.json` — RPS, latency, ошибки
- `attendance.json` — метрики посещаемости

### Логи

```bash
# Все сервисы
docker compose logs -f

# Только backend
docker compose logs -f backend

# Последние 100 строк
docker compose logs --tail=100 backend
```

### Healthcheck

```bash
# Быстрая проверка
curl http://localhost:8000/health

# Полный статус
docker compose ps
```

---

## Бэкап и восстановление

### PostgreSQL бэкап

```bash
# Создать бэкап
docker compose exec postgres pg_dump \
  -U attendai attendai | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Восстановить
gunzip < backup_20260416_090000.sql.gz | \
  docker compose exec -T postgres psql -U attendai attendai
```

### Автоматический бэкап (cron)

```bash
# crontab -e
0 3 * * * cd /opt/attendai && \
  docker compose exec postgres pg_dump -U attendai attendai | \
  gzip > /backups/attendai_$(date +\%Y\%m\%d).sql.gz && \
  find /backups -name "*.sql.gz" -mtime +30 -delete
```

---

## Подключение камер

### IP-камеры (RTSP)

```bash
# Тестирование RTSP-потока
ffplay rtsp://username:password@192.168.1.100:554/stream1

# Через API
curl -X POST http://localhost:8000/api/v1/cameras \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Главный вход",
    "location": "Корпус А, 1 этаж",
    "rtsp_url": "rtsp://admin:password@192.168.1.100/stream",
    "ip_address": "192.168.1.100"
  }'
```

### Форматы RTSP URL

```
# Hikvision
rtsp://admin:password@IP:554/Streaming/Channels/101

# Dahua
rtsp://admin:password@IP:554/cam/realmonitor?channel=1&subtype=0

# Axis
rtsp://root:password@IP/axis-media/media.amp

# Generic
rtsp://username:password@IP:554/stream1
```

---

## Масштабирование

### Горизонтальное масштабирование воркеров

```bash
# Увеличить число Celery воркеров
docker compose up -d --scale celery-worker=4

# Увеличить число API воркеров (в docker-compose.prod.yml)
# command: uvicorn app.main:app --workers 4 ...
```

### GPU для распознавания

```bash
# В .env:
FACE_GPU_ID=0  # Использовать первую GPU

# В requirements.txt заменить:
# onnxruntime → onnxruntime-gpu
# faiss-cpu → faiss-gpu
```
