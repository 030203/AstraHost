# Nacos Setup

This repo now uses Nacos for both service discovery and centralized configuration.

## Roles

- Service discovery: `backend`, `gateway`, and `ai-service` register themselves so routing can use logical service names.
- Config center: business and infrastructure config can be moved out of local files and managed from the Nacos console.

## What to put in Nacos

Good candidates:

- database host, port, database name, username
- Redis host and port
- gateway route targets and timeout settings
- AI provider, model, external API endpoints, thresholds, feature flags
- logging levels and non-sensitive app switches

Keep in environment variables or local `.env`:

- `ROOMOS_DB_PASSWORD`
- `MYSQL_PASSWORD`
- `REDIS_PASSWORD`
- `DEEPSEEK_API_KEY`
- `QWEN_API_KEY`
- `NACOS_USERNAME`
- `NACOS_PASSWORD`

For local development compatibility:

- `backend` still falls back to `456456` if `ROOMOS_DB_PASSWORD` and `MYSQL_PASSWORD` are both unset

## Data IDs

Create these configs in Nacos Console:

- `booking-system.properties`
- `roomos-gateway.yaml`
- `roomos-ai-service.properties`

All use:

- Group: `DEFAULT_GROUP`
- Namespace: `public`

Templates are provided in:

- `docs/booking-system.nacos.properties`
- `docs/roomos-gateway.nacos.yaml`
- `docs/roomos-ai-service.nacos.properties`

## Local fallback vs Nacos override

- `backend` and `gateway` keep local defaults in `application.properties` or `application.yml`.
- When the `nacos` profile is active, they import remote config from Nacos.
- `ai-service` keeps startup config local, but hot-loads non-sensitive runtime config from Nacos.

## Start with Nacos

Start Nacos:

```bash
docker compose -f docker-compose.nacos.yml up -d
```

Backend:

```powershell
cd backend
$env:NACOS_SERVER_ADDR="127.0.0.1:8848"
$env:ROOMOS_DB_PASSWORD="your-db-password"
mvn spring-boot:run "-Dspring-boot.run.profiles=nacos"
```

Gateway:

```powershell
cd gateway
$env:NACOS_SERVER_ADDR="127.0.0.1:8848"
mvn spring-boot:run "-Dspring-boot.run.profiles=nacos"
```

AI service:

```powershell
cd ai-service
$env:NACOS_ENABLED="true"
$env:NACOS_DISCOVERY_ENABLED="true"
$env:NACOS_CONFIG_ENABLED="true"
$env:NACOS_SERVER_ADDR="127.0.0.1:8848"
$env:REDIS_PASSWORD="your-redis-password"
$env:DEEPSEEK_API_KEY="your-api-key"
python app.py
```

Or use the helper script from the repo root:

```powershell
.\scripts\start-ai-service.ps1 -EnableNacos
```

## Verification

Check backend:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8848/nacos/v1/ns/instance/list?serviceName=booking-system&groupName=DEFAULT_GROUP" | Select-Object -ExpandProperty Content
```

Check AI service:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8848/nacos/v1/ns/instance/list?serviceName=roomos-ai-service&groupName=DEFAULT_GROUP" | Select-Object -ExpandProperty Content
```

## Refresh behavior

- `ai-service`: custom runtime config is hot refreshed for non-sensitive keys.
- `backend` and `gateway`: config is centralized in Nacos, but some framework-level properties still effectively require restart to fully take effect, especially datasource and server-port changes.
- Sensitive secrets are intentionally excluded from Nacos-managed hot refresh.
