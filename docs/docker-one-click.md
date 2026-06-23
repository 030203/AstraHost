# Docker 一键启动

当前仓库支持两种启动方式：

- 默认模式：前端、后端、网关和基础设施走 Docker，`ai-service` 由你本地单独运行，便于调试。
- 全量模式：包括 `ai-service` 在内的所有服务都走 Docker。

## 1. 默认模式：单独开发 `ai-service`

在项目根目录执行：

```bash
docker compose up -d --build
```

这条命令会启动：

- `mysql`
- `redis`
- `rabbitmq`
- `elasticsearch`
- `backend`
- `gateway`
- `frontend`

其中：

- `gateway` 会把 `/ai-api/**` 转发到 `http://host.docker.internal:5001`
- 也就是你宿主机上运行的 `ai-service`

本地启动 `ai-service`：

```bash
cd ai-service
cp .env.example .env
pip install -r requirements.txt
python app.py
```

建议直接复制 `ai-service/.env.example` 为 `.env`，默认内容如下：

```env
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=5001
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=456456
MYSQL_DATABASE=booking_system
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
NACOS_ENABLED=false
NACOS_DISCOVERY_ENABLED=false
NACOS_CONFIG_ENABLED=false
```

原因很直接：

- MySQL / Redis 端口已经映射到宿主机
- 你本地跑的 `ai-service` 应该连 `127.0.0.1`
- Docker 内的 `gateway` 通过 `host.docker.internal` 回调你本机的 `ai-service`

## 2. 全量模式：所有服务都走 Docker

如果你不想本地单独跑 `ai-service`，执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.full.yml up -d --build
```

这时 `gateway` 会直接转发到容器内的 `ai-service`。

## 3. 访问地址

- 前端：`http://localhost`
- 网关：`http://localhost:8088`
- 后端健康检查：`http://localhost:8080/api/actuator/health`
- AI 服务健康检查：`http://localhost:5001/health`
- RabbitMQ 控制台：`http://localhost:15672`
- Elasticsearch：`http://localhost:9200`

## 4. 常用命令

启动默认模式：

```bash
docker compose up -d --build
```

启动全量模式：

```bash
docker compose -f docker-compose.yml -f docker-compose.full.yml up -d --build
```

停止：

```bash
docker compose down
```

停止全量模式：

```bash
docker compose -f docker-compose.yml -f docker-compose.full.yml down
```

删除数据卷：

```bash
docker compose down -v
```

查看日志：

```bash
docker compose logs -f
```

查看网关日志：

```bash
docker compose logs -f gateway
```

## 5. 说明

- 默认模式更适合你当前需求：前端、后端、网关一键启动，`ai-service` 单独改、单独重启。
- 如果你本机不是 Docker Desktop，`host.docker.internal` 解析失败时，需要确认 Docker 支持 `host-gateway`。
- 如果本地 `ai-service` 端口不是 `5001`，可以在启动 compose 前覆盖环境变量：

PowerShell：

```powershell
$env:AI_SERVICE_URL="http://host.docker.internal:5002"
docker compose up -d --build
```

`cmd`：

```cmd
set AI_SERVICE_URL=http://host.docker.internal:5002
docker compose up -d --build
```

bash：

```bash
AI_SERVICE_URL=http://host.docker.internal:你的端口 docker compose up -d --build
```

## 6. Docker Hub 拉取失败

如果构建阶段报错：

- `failed to fetch anonymous token`
- `auth.docker.io`
- `load metadata for docker.io/...`

这不是项目配置错误，而是你的 Docker 环境当前连不上 Docker Hub。

当前仓库已经支持覆盖构建基础镜像：

- `MAVEN_BUILD_IMAGE`
- `JAVA_RUNTIME_IMAGE`
- `NODE_BUILD_IMAGE`
- `NGINX_RUNTIME_IMAGE`
- `PYTHON_BASE_IMAGE`

你可以把这些变量指向你本机可访问的镜像源，然后再执行构建。

PowerShell 示例：

```powershell
$env:MAVEN_BUILD_IMAGE="你的镜像源/maven:3.9-eclipse-temurin-17"
$env:JAVA_RUNTIME_IMAGE="你的镜像源/eclipse-temurin:17-jre"
$env:NODE_BUILD_IMAGE="你的镜像源/node:18"
$env:NGINX_RUNTIME_IMAGE="你的镜像源/nginx:1.25-alpine"
docker compose up -d --build
```

如果你也要把 `ai-service` 一起容器化：

```powershell
$env:PYTHON_BASE_IMAGE="你的镜像源/python:3.12-slim"
docker compose -f docker-compose.yml -f docker-compose.full.yml up -d --build
```

更直接的方案是先把 Docker Desktop 的 registry mirror 配好，再重新执行：

```bash
docker compose up -d --build
```
