# ECIS Service Robot

> **原项目名称**: LinkC Platform  
> **当前名称**: ECIS Service Robot（物业机器人服务平台）  
> **更新日期**: 2026-01-27

---

## 项目信息

| 项目 | 值 |
|------|-----|
| 项目路径 | `/root/projects/ecis/ecis-property-service` |
| 协议路径 | `/root/projects/ecis/ecis-protocols` |
| 目标项目名 | `ecis-service-robot` |

## ECIS 协议集成

### 开发前必读 ⚠️

在开发以下功能前，**必须先阅读对应协议文档**：

| 功能类型 | 阅读命令 |
|---------|---------|
| Agent 开发 | `cat /root/projects/ecis/ecis-protocols/docs/agent-interfaces.md` |
| 跨系统通信 | `cat /root/projects/ecis/ecis-protocols/docs/federation-protocol.md` |
| 数据模型 | `cat /root/projects/ecis/ecis-protocols/docs/data-models.md` |

### Python 包使用

协议包位置: `/root/projects/ecis/ecis-protocols/reference/python`

**使用方法**:

```python
import sys
sys.path.insert(0, "/root/projects/ecis/ecis-protocols/reference/python")

# Agent 接口
from ecis_protocols.agents import (
    RobotAgentInterface,
    AgentIdentity,
    AgentStatus
)

# Federation 协议
from ecis_protocols.federation import (
    ECISEvent,
    EventTypes
)

# 共享模型
from ecis_protocols.models import (
    Task, Robot, Building
)
```

### Robot Agent 实现要求

本项目的 Robot Agent 应参考 `RobotAgentInterface` 实现。

---

## 快速状态 (Quick Status)

| 项目 | 值 |
|------|-----|
| **当前版本** | 1.0.0 |
| **MVP进度** | **100% ✅** |
| **测试总数** | 511 (全部通过) |
| **最后更新** | 2026-01-27 |

### 重要文档
| 文档 | 路径 | 说明 |
|------|------|------|
| 开发进度 | `docs/PROGRESS.md` | 实时进度追踪 |
| 系统架构 | `docs/ARCHITECTURE.md` | 整体架构设计 |
| 集成需求 | `docs/INTEGRATION_REQUIREMENTS.md` | 模拟vs真实对接说明 |
| 部署指南 | `docs/DEPLOYMENT.md` | 生产环境部署 |

---

## 项目概述

**ECIS Service Robot** 是物业机器人协同平台，基于ECIS（企业群体智能系统）架构设计。

### 核心功能

1. **空间管理**: 楼宇、楼层、区域管理
2. **机器人管理**: 清洁机器人、配送机器人控制
3. **任务调度**: 智能任务分配与执行
4. **数据采集**: 机器人状态与工作数据采集
5. **MCP 集成**: 提供 MCP 服务器接口

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI, Python 3.11+ |
| 数据库 | PostgreSQL 15+, SQLAlchemy 2.0 |
| 缓存 | Redis |
| 前端 | React, TypeScript, Vite |
| 测试 | pytest, vitest |
| 容器化 | Docker, Docker Compose |

---

## 开发规范

### 测试要求

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html

# 运行前端测试
cd frontend && npm test
```

### 代码风格

- Python: PEP 8, Type Hints
- TypeScript: ESLint 配置
- 提交规范: Conventional Commits

### 启动服务

```bash
# Docker 方式
docker-compose up -d

# 开发模式
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

---

## 目录结构

```
ecis-property-service/
├── backend/          # FastAPI 后端
│   ├── app/         # 应用代码
│   │   ├── api/     # API 路由
│   │   ├── agents/  # Agent 实现
│   │   ├── models/  # 数据模型
│   │   └── core/    # 核心配置
│   └── main.py      # 入口文件
├── src/              # 扩展源码
│   ├── api/         # API 网关
│   ├── agents/      # Agent 运行时
│   ├── data/        # 数据服务
│   ├── mcp_servers/ # MCP 服务器
│   └── shared/      # 共享模块
├── frontend/         # React 前端
├── tests/            # 测试代码
├── docs/             # 文档
└── docker-compose.yml
```

---

## 迁移说明

### 从 LinkC Platform 到 ECIS Service Robot

| 原标识 | 新标识 |
|-------|-------|
| LinkC Platform | ECIS Service Robot |
| linkc (数据库) | ecis_robot |
| linkc-backend | ecis-robot-backend |
| linkc-frontend | ecis-robot-frontend |
| linkc-network | ecis-network |

所有 "LinkC" 引用已更新为 "ECIS Service Robot"。

---

## 后续开发 (Task 4)

### Federation 集成

即将添加 Federation 支持，包括：
- FederationClient: 连接 ECIS Federation Gateway
- EventPublisher: 事件发布
- TaskReceiver: 接收编排任务

### Capability 模块

即将添加能力管理模块：
- CapabilityRegistry: 能力注册表
- CapabilityService: 能力服务
- Agent 能力声明

