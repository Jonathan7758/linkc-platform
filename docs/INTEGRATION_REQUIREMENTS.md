# LinkC Platform 生产环境集成需求文档

> 本文档说明当前MVP中哪些模块使用了模拟实现，以及生产环境部署时需要与真实设备/系统对接的具体需求。

**文档版本**: 1.0
**最后更新**: 2026-01-22
**状态**: MVP完成，待生产对接

---

## 目录

1. [模拟实现概览](#模拟实现概览)
2. [机器人对接](#机器人对接)
3. [LLM服务对接](#llm服务对接)
4. [数据存储对接](#数据存储对接)
5. [认证系统对接](#认证系统对接)
6. [外部系统集成](#外部系统集成)
7. [对接优先级](#对接优先级)
8. [对接检查清单](#对接检查清单)

---

## 模拟实现概览

### 当前模拟组件一览

| 组件 | 模拟文件 | 生产对接 | 优先级 |
|------|----------|----------|--------|
| 高仙机器人 | `mock_client.py` | 高仙云平台API | P0 |
| 科沃斯机器人 | 未实现 | 科沃斯商用API | P1 |
| LLM服务 | 火山引擎(已对接) | - | ✅ 已完成 |
| 数据库 | PostgreSQL(已对接) | - | ✅ 已完成 |
| 用户认证 | 模拟用户数据 | OAuth2/SSO | P1 |
| 空间数据 | 内存示例数据 | 物业管理系统 | P2 |
| 推送通知 | 控制台日志 | FCM/APNs | P2 |

### 模拟 vs 真实 架构对比

```
┌─────────────────────────────────────────────────────────────────┐
│                        当前MVP架构 (模拟)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ MockGaoxian │    │ 内存存储     │    │ 模拟用户    │         │
│  │   Client    │    │ (示例数据)   │    │   数据     │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LinkC Platform                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       生产环境架构 (真实)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  高仙云平台  │    │ 物业管理     │    │  企业SSO   │         │
│  │    API      │    │   系统      │    │  (OAuth2)  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│  ┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐         │
│  │ 科沃斯商用   │    │   楼宇BMS   │    │   AD/LDAP  │         │
│  │    API      │    │    系统     │    │            │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LinkC Platform                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 机器人对接

### 1. 高仙机器人 (Gaussian Robotics)

**当前状态**: 模拟实现
**模拟文件**: `src/mcp_servers/robot_gaoxian/mock_client.py`

#### 模拟内容

```python
# 模拟的机器人数据
robots = [
    {
        "robot_id": "robot_001",
        "name": "清洁机器人A-01",
        "model": "GS-50",
        "status": "idle",
        "battery": 85,
        "location": {"x": 5.0, "y": 5.0, "floor_id": "floor_001"}
    },
    # ... 共3台模拟机器人
]

# 模拟的行为
- 电量每分钟消耗1%
- 充电每分钟恢复2%
- 任务进度每秒更新
- 1%概率随机故障
```

#### 生产对接需求

| 需求项 | 说明 |
|--------|------|
| **API端点** | 高仙云平台API地址 |
| **认证方式** | API Key 或 OAuth2 |
| **设备注册** | 在高仙平台注册设备并获取robot_id映射 |
| **数据同步** | 实时状态轮询或WebSocket推送 |
| **指令下发** | 清洁任务、充电、暂停等控制指令 |

#### 对接步骤

1. **获取API文档**
   - 联系高仙商务获取API文档和测试账号
   - 确认API版本和调用限制

2. **实现真实客户端**
   ```python
   # src/mcp_servers/robot_gaoxian/gaoxian_client.py

   class GaoxianClient:
       def __init__(self, api_url: str, api_key: str):
           self.api_url = api_url
           self.api_key = api_key
           self.session = aiohttp.ClientSession()

       async def get_robot_status(self, robot_id: str) -> RobotStatus:
           """调用高仙API获取机器人状态"""
           response = await self.session.get(
               f"{self.api_url}/robots/{robot_id}/status",
               headers={"Authorization": f"Bearer {self.api_key}"}
           )
           return self._parse_status(await response.json())

       async def start_cleaning_task(self, robot_id: str, zone_id: str):
           """下发清洁任务"""
           ...
   ```

3. **配置切换**
   ```python
   # src/mcp_servers/robot_gaoxian/server.py

   def create_robot_client():
       if os.getenv("USE_MOCK_ROBOT", "true").lower() == "true":
           return MockGaoxianClient(storage)
       else:
           return GaoxianClient(
               api_url=os.getenv("GAOXIAN_API_URL"),
               api_key=os.getenv("GAOXIAN_API_KEY")
           )
   ```

4. **数据映射**
   - 高仙API返回格式 → LinkC内部数据模型
   - 需要处理字段名称、状态枚举、坐标系统的差异

#### 环境变量

```bash
# .env.prod
USE_MOCK_ROBOT=false
GAOXIAN_API_URL=https://api.gs-robot.com/v2
GAOXIAN_API_KEY=your_api_key_here
GAOXIAN_TENANT_ID=your_tenant_id
```

---

### 2. 科沃斯机器人 (Ecovacs)

**当前状态**: 未实现 (规格书已定义)
**规格书**: `docs/specs/mcp/M4-ecovacs-mcp.md`

#### 生产对接需求

| 需求项 | 说明 |
|--------|------|
| **API端点** | 科沃斯商用API |
| **认证方式** | OAuth2 |
| **设备类型** | 科沃斯商用清洁机器人 |
| **功能范围** | 状态查询、任务控制、地图管理 |

#### 对接步骤

1. 联系科沃斯商用部门获取API访问权限
2. 参考M3实现创建 `src/mcp_servers/robot_ecovacs/` 模块
3. 实现 `EcovacsClient` 替代模拟客户端
4. 统一机器人接口，支持多品牌混合调度

---

## LLM服务对接

**当前状态**: ✅ 已对接火山引擎

### 已实现

```python
# src/shared/llm/volcengine_client.py

class VolcengineLLMClient:
    """火山引擎豆包大模型客户端 (OpenAI兼容接口)"""

    def __init__(self):
        self.api_key = os.getenv("VOLCENGINE_API_KEY")
        self.model = os.getenv("VOLCENGINE_MODEL", "doubao-pro-32k")
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
```

### 环境变量

```bash
VOLCENGINE_API_KEY=your_api_key
VOLCENGINE_MODEL=doubao-pro-32k
```

### 备选方案

如需切换其他LLM服务:

| 服务商 | 配置方式 |
|--------|----------|
| OpenAI | 修改 `base_url` 为 `https://api.openai.com/v1` |
| Azure OpenAI | 使用 Azure 端点和部署名称 |
| 本地部署 | Ollama 或 vLLM 本地服务 |

---

## 数据存储对接

**当前状态**: ✅ 已对接 PostgreSQL + TimescaleDB

### 已实现

- PostgreSQL 作为主数据库
- TimescaleDB 扩展用于时序数据
- Redis 用于缓存和消息队列

### 生产环境建议

| 组件 | 开发环境 | 生产环境建议 |
|------|----------|--------------|
| PostgreSQL | Docker容器 | 云数据库 (RDS) 或独立集群 |
| TimescaleDB | Docker容器 | Timescale Cloud 或自建 |
| Redis | Docker容器 | 云Redis 或哨兵集群 |

### 数据迁移

```bash
# 导出开发数据
pg_dump -U linkc linkc > dev_data.sql

# 导入生产数据库
psql -h prod-db.example.com -U linkc linkc < dev_data.sql
```

---

## 认证系统对接

### 当前状态: 模拟实现

**模拟文件**: `src/shared/auth/`

```python
# 当前模拟用户
MOCK_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "operator": {"password": "operator123", "role": "operator"},
    "trainer": {"password": "trainer123", "role": "trainer"}
}
```

### 生产对接需求

#### 方案A: OAuth2/OIDC 集成

```python
# 对接企业SSO
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='enterprise_sso',
    client_id=os.getenv('SSO_CLIENT_ID'),
    client_secret=os.getenv('SSO_CLIENT_SECRET'),
    authorize_url='https://sso.example.com/oauth/authorize',
    access_token_url='https://sso.example.com/oauth/token',
    userinfo_url='https://sso.example.com/userinfo',
)
```

#### 方案B: LDAP/AD 集成

```python
# 对接Active Directory
import ldap3

def authenticate_ldap(username: str, password: str) -> bool:
    server = ldap3.Server(os.getenv('LDAP_SERVER'))
    conn = ldap3.Connection(
        server,
        user=f"{username}@example.com",
        password=password
    )
    return conn.bind()
```

#### 环境变量

```bash
# OAuth2
SSO_CLIENT_ID=linkc_platform
SSO_CLIENT_SECRET=your_secret
SSO_AUTHORIZE_URL=https://sso.example.com/oauth/authorize
SSO_TOKEN_URL=https://sso.example.com/oauth/token

# LDAP
LDAP_SERVER=ldap://ad.example.com
LDAP_BASE_DN=dc=example,dc=com
```

---

## 外部系统集成

### 1. 物业管理系统 (PMS)

**用途**: 同步楼宇、楼层、区域数据

| 集成项 | 说明 |
|--------|------|
| 楼宇信息 | 楼宇名称、地址、联系人 |
| 楼层信息 | 楼层编号、面积、用途 |
| 区域信息 | 清洁区域划分、特殊要求 |
| 工单系统 | 清洁任务与PMS工单关联 |

**对接方式**: REST API 或 数据库视图

### 2. 楼宇自动化系统 (BMS)

**用途**: 电梯联动、门禁控制

| 集成项 | 说明 |
|--------|------|
| 电梯调度 | 机器人呼叫电梯 |
| 门禁开关 | 自动开门/关门 |
| 环境数据 | 温湿度、人流量 |

**对接方式**: BACnet / Modbus / 厂商API

### 3. 推送通知服务

**当前状态**: 控制台日志输出

**生产对接**:

| 平台 | 服务 |
|------|------|
| iOS | Apple Push Notification service (APNs) |
| Android | Firebase Cloud Messaging (FCM) |
| 微信 | 微信模板消息 / 企业微信 |
| 邮件 | SendGrid / 阿里云邮件推送 |
| 短信 | 阿里云短信 / Twilio |

```python
# 推送服务抽象接口
class NotificationService:
    async def send_alert(self, user_id: str, alert: Alert):
        """发送告警通知"""
        ...

    async def send_task_update(self, user_id: str, task: Task):
        """发送任务更新"""
        ...
```

---

## 对接优先级

### P0 - 必须 (上线前完成)

| 项目 | 说明 | 预计工时 |
|------|------|----------|
| 高仙机器人真实API | 核心功能依赖 | 2周 |
| 生产数据库部署 | 数据持久化 | 1周 |
| 基础认证 | 用户登录 | 1周 |

### P1 - 重要 (上线后1个月内)

| 项目 | 说明 | 预计工时 |
|------|------|----------|
| 科沃斯机器人对接 | 多品牌支持 | 2周 |
| 企业SSO集成 | 统一认证 | 1周 |
| 推送通知服务 | 实时告警 | 1周 |

### P2 - 优化 (上线后3个月内)

| 项目 | 说明 | 预计工时 |
|------|------|----------|
| 物业管理系统对接 | 数据同步 | 2周 |
| BMS系统对接 | 电梯联动 | 3周 |
| 多租户优化 | 数据隔离 | 2周 |

---

## 对接检查清单

### 机器人对接

- [ ] 获取高仙API文档和测试账号
- [ ] 实现 `GaoxianClient` 真实客户端
- [ ] 完成API响应到内部模型的数据映射
- [ ] 配置环境变量切换
- [ ] 编写集成测试
- [ ] 真实设备联调测试
- [ ] 异常处理和重试机制
- [ ] 监控和告警配置

### 认证系统对接

- [ ] 确定认证方案 (OAuth2 / LDAP / 自建)
- [ ] 获取SSO/LDAP配置信息
- [ ] 实现认证适配器
- [ ] 用户角色映射
- [ ] 会话管理
- [ ] 登录页面适配

### 外部系统对接

- [ ] 获取PMS系统API文档
- [ ] 确定数据同步策略 (实时/定时)
- [ ] 实现数据映射层
- [ ] 错误处理和日志
- [ ] 监控和告警

### 生产部署

- [ ] 云数据库配置
- [ ] SSL证书配置
- [ ] 域名解析
- [ ] 负载均衡
- [ ] 日志收集
- [ ] 监控告警
- [ ] 备份策略

---

## 附录

### A. 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 部署指南 | `docs/DEPLOYMENT.md` | 生产环境部署步骤 |
| 系统架构 | `docs/ARCHITECTURE.md` | 整体架构说明 |
| API文档 | `http://localhost:8000/docs` | Swagger UI |
| 高仙MCP规格 | `docs/specs/mcp/M3-gaoxian-mcp.md` | 机器人接口规格 |

### B. 联系方式

| 角色 | 联系方式 |
|------|----------|
| 高仙技术支持 | 联系高仙商务获取 |
| 科沃斯技术支持 | 联系科沃斯商用部门 |
| 项目技术负责人 | Jonathan Maang |

---

*文档版本: 1.0*
*创建日期: 2026-01-22*
*维护者: LinkC Platform Team*
