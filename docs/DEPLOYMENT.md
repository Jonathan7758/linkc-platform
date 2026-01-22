# LinkC Platform 部署指南

## 目录

1. [系统要求](#系统要求)
2. [快速开始](#快速开始)
3. [生产部署](#生产部署)
4. [配置说明](#配置说明)
5. [SSL证书配置](#ssl证书配置)
6. [监控配置](#监控配置)
7. [备份与恢复](#备份与恢复)
8. [故障排查](#故障排查)

---

## 系统要求

### 硬件要求

| 环境 | CPU | 内存 | 存储 |
|------|-----|------|------|
| 开发环境 | 2核 | 4GB | 20GB |
| 测试环境 | 4核 | 8GB | 50GB |
| 生产环境 | 8核+ | 16GB+ | 100GB+ SSD |

### 软件要求

- Docker 24.0+
- Docker Compose 2.20+
- Git 2.40+

### 端口要求

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | HTTP (重定向到HTTPS) |
| 443 | Nginx | HTTPS |
| 8080 | Nginx | 监控面板 (内部) |

---

## 快速开始

### 1. 克隆代码

```bash
git clone https://github.com/your-org/linkc-platform.git
cd linkc-platform
```

### 2. 开发环境启动

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 访问服务

- 前端: http://localhost:5173
- API文档: http://localhost:8000/docs
- 后端健康检查: http://localhost:8000/health

---

## 生产部署

### 1. 服务器准备

```bash
# 更新系统
apt update && apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. 配置环境变量

创建 `.env.prod` 文件:

```bash
# 数据库配置
POSTGRES_USER=linkc
POSTGRES_PASSWORD=<强密码>
POSTGRES_DB=linkc

# JWT配置
JWT_SECRET=<随机生成的密钥>

# 火山引擎LLM
VOLCENGINE_API_KEY=<您的API Key>

# 域名
DOMAIN_NAME=your-domain.com

# 高仙机器人API (可选)
GAOXIAN_API_URL=https://api.gaoxian.com
GAOXIAN_API_KEY=<您的API Key>

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=<强密码>
```

生成安全密钥:

```bash
# 生成JWT密钥
openssl rand -base64 64

# 生成数据库密码
openssl rand -base64 32
```

### 3. 部署服务

```bash
# 创建目录结构
mkdir -p nginx/ssl nginx/logs monitoring/grafana/provisioning scripts

# 复制配置文件
cp nginx.prod.conf nginx/nginx.prod.conf
cp docker-compose.prod.yml docker-compose.prod.yml

# 启动服务
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 4. 验证部署

```bash
# 检查所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
curl -k https://localhost/health

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## 配置说明

### 环境变量

| 变量 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `POSTGRES_PASSWORD` | 是 | 数据库密码 | `s3cr3t` |
| `JWT_SECRET` | 是 | JWT签名密钥 | `base64字符串` |
| `VOLCENGINE_API_KEY` | 是 | 火山引擎API Key | `ak-xxx` |
| `DOMAIN_NAME` | 是 | 部署域名 | `linkc.example.com` |
| `GAOXIAN_API_KEY` | 否 | 高仙机器人API Key | `gx-xxx` |

### 资源限制

生产环境默认资源限制:

| 服务 | CPU | 内存 |
|------|-----|------|
| backend | 2核 | 2GB |
| postgres | 2核 | 2GB |
| agent-runtime | 1核 | 1GB |
| redis | 0.5核 | 512MB |
| MCP servers | 0.5核 | 256MB |

根据实际负载调整 `docker-compose.prod.yml` 中的 `deploy.resources` 配置。

---

## SSL证书配置

### 使用Let's Encrypt (推荐)

```bash
# 安装certbot
apt install certbot -y

# 获取证书 (先停止nginx)
docker-compose -f docker-compose.prod.yml stop nginx
certbot certonly --standalone -d your-domain.com

# 复制证书
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# 重启nginx
docker-compose -f docker-compose.prod.yml start nginx
```

### 自动续期

```bash
# 添加cron任务
echo "0 0 1 * * certbot renew --quiet && docker-compose -f /path/to/docker-compose.prod.yml restart nginx" | crontab -
```

### 使用自签名证书 (测试)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

---

## 监控配置

### Prometheus 指标

在 `monitoring/prometheus.yml` 中配置:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'linkc-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana 仪表盘

访问 `http://your-domain:8080/grafana/`

默认账号: admin / admin (首次登录请修改)

推荐导入的仪表盘:
- PostgreSQL: ID 9628
- Redis: ID 11835
- Docker: ID 893

### 告警配置

在Grafana中配置告警规则:

1. CPU使用率 > 80%
2. 内存使用率 > 85%
3. 磁盘使用率 > 90%
4. API响应时间 > 1s
5. 错误率 > 1%

---

## 备份与恢复

### 数据库备份

```bash
# 手动备份
docker exec linkc-postgres pg_dump -U linkc linkc > backup_$(date +%Y%m%d).sql

# 自动备份脚本
cat > /etc/cron.daily/linkc-backup << 'EOF'
#!/bin/bash
BACKUP_DIR=/var/backups/linkc
mkdir -p $BACKUP_DIR
docker exec linkc-postgres pg_dump -U linkc linkc | gzip > $BACKUP_DIR/db_$(date +%Y%m%d).sql.gz
# 保留最近30天
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
EOF
chmod +x /etc/cron.daily/linkc-backup
```

### 数据库恢复

```bash
# 恢复备份
gunzip -c backup_20260121.sql.gz | docker exec -i linkc-postgres psql -U linkc linkc
```

### Redis备份

Redis已配置AOF持久化，数据存储在 `redis_data` volume中。

```bash
# 备份Redis
docker exec linkc-redis redis-cli BGSAVE
docker cp linkc-redis:/data/dump.rdb ./redis_backup.rdb
```

---

## 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 查看容器日志
docker-compose -f docker-compose.prod.yml logs <service-name>

# 检查资源使用
docker stats
```

#### 2. 数据库连接失败

```bash
# 检查PostgreSQL状态
docker exec linkc-postgres pg_isready

# 检查连接
docker exec linkc-backend python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://...')
conn = engine.connect()
print('Connection OK')
"
```

#### 3. API响应慢

```bash
# 检查后端日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 检查数据库慢查询
docker exec linkc-postgres psql -U linkc -c "
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

#### 4. WebSocket连接失败

检查nginx配置中WebSocket代理设置:
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 日志位置

| 服务 | 日志位置 |
|------|---------|
| Nginx | `./nginx/logs/` |
| Backend | `docker logs linkc-backend` |
| PostgreSQL | `docker logs linkc-postgres` |

### 健康检查端点

| 端点 | 说明 |
|------|------|
| `/health` | 系统健康状态 |
| `/api/v1/admin/health` | 详细健康信息 |
| `/metrics` | Prometheus指标 |

---

## 更新部署

### 滚动更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose -f docker-compose.prod.yml build

# 滚动更新 (零停机)
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend
```

### 回滚

```bash
# 查看镜像历史
docker images | grep linkc

# 回滚到指定版本
docker-compose -f docker-compose.prod.yml up -d --no-deps backend:v1.0.0
```

---

## 安全建议

1. **定期更新**: 保持Docker镜像和系统包最新
2. **访问控制**: 限制SSH访问，使用密钥认证
3. **防火墙**: 只开放必要端口 (80, 443)
4. **日志审计**: 定期检查访问日志和错误日志
5. **密钥轮换**: 定期更换JWT密钥和数据库密码
6. **备份验证**: 定期测试备份恢复流程

---

*文档版本: 1.0*
*最后更新: 2026-01-22*
