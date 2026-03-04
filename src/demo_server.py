"""
ECIS v6 Demo Server — Tower C 智能清洁调度演示

FastAPI 应用，串联 Sprint 0-3 全部核心模块:
  - K1 场景知识库 + K2 治理规则引擎 + K3 决策日志
  - A5 决策校验流水线
  - G8/G9 管理API
  - B5 人机自主性边界
  - P1 离线队列 + P3 通知服务
  - WebSocket 实时推送

启动: PYTHONPATH=src uvicorn demo_server:app --host 0.0.0.0 --port 9000
访问: http://101.47.67.225:9000/docs  (Swagger UI)
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# ── K1/K2/K3 知识层 ──────────────────────────────────────────────
from knowledge.scenario_kb import (
    ScenarioKnowledge,
    ScenarioKnowledgeBase,
    PromptTemplate,
    _estimate_tokens,
)
from knowledge.rule_engine import (
    GovernanceRule,
    GovernanceRuleEngine,
    RuleEvalResult,
)
from knowledge.decision_logger import (
    DecisionContext,
    DecisionOutcome,
    DecisionRecord,
    DecisionLogger,
)
from knowledge.seed_data import load_tower_c_seed_data

# ── A5 决策校验 ──────────────────────────────────────────────────
from validation.decision_validator import DecisionValidator

# ── B5 人机自主性 ────────────────────────────────────────────────
from autonomy.human_agent_boundary import (
    AutonomyLevel,
    HumanAgentBoundary,
    TaskAutonomyConfig,
)

# ── P1 离线 + P3 通知 ────────────────────────────────────────────
from offline.offline_queue import OfflineQueueManager, CacheManager
from notifications.notification_service import NotificationService

# ── G8/G9 API handlers ──────────────────────────────────────────
from api.knowledge_api import (
    KnowledgeManagementAPI,
    RuleManagementAPI,
    DecisionLogAPI,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecis-demo")


# ====================================================================
# Global service instances (in-memory, demo lifecycle)
# ====================================================================

kb = ScenarioKnowledgeBase()
engine = GovernanceRuleEngine()
decision_logger = DecisionLogger()
validator = DecisionValidator()
boundary = HumanAgentBoundary()
offline_queue = OfflineQueueManager()
cache_mgr = CacheManager()
notification_svc = NotificationService()

g8_api = KnowledgeManagementAPI(kb)
g9_api = RuleManagementAPI(engine)
log_api = DecisionLogAPI(decision_logger)

# WebSocket connections
ws_connections: List[WebSocket] = []


# ====================================================================
# Lifespan — 启动时加载种子数据
# ====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ECIS v6 Demo Server starting...")

    # Load Tower C seed data
    seed_result = await load_tower_c_seed_data(kb)
    logger.info(
        "📦 Tower C knowledge loaded: %d entries, %d templates",
        seed_result["knowledge_loaded"],
        seed_result["templates_loaded"],
    )

    rule_count = await engine.load_tower_c_seed_rules()
    logger.info("📋 Tower C governance rules loaded: %d rules", rule_count)

    loaded = await boundary.load_tower_c_defaults()
    logger.info("🤖 Tower C autonomy configs loaded: %d task types", loaded)

    logger.info("✅ ECIS v6 Demo Server ready — visit /docs for Swagger UI")
    yield
    logger.info("👋 ECIS v6 Demo Server shutting down")


# ====================================================================
# FastAPI app
# ====================================================================

app = FastAPI(
    title="ECIS v6 — 企业群体智能系统 Demo",
    description="""
## Tower C 智能清洁调度演示

**ECIS = Enterprise Collective Intelligence System**

20台清洁机器人 × 10名训练师 × 45层办公楼

### 核心能力演示:
- 🧠 **AI调度决策** — 基于场景知识的Prompt动态组装
- 🛡️ **4层安全校验** — Schema → Reference → Constraint → Safety
- 📋 **治理规则引擎** — 低电量阻止、VIP区域优先、噪音管控
- 📊 **决策全追溯** — Context → Decision → Outcome 三元组
- 🤝 **人机协作** — L0~L3 四级自主性可配置
- 📡 **实时推送** — WebSocket 事件通道
- 📱 **离线支持** — 操作队列 + 冲突解决
- 🔔 **通知重试** — 优先级调度 + 指数退避

### Sprint 进度: 361 tests ✅
""",
    version="6.0.0-demo",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================================================================
# 0. 首页 — 演示仪表盘
# ====================================================================

@app.get("/", response_class=HTMLResponse, tags=["首页"])
async def dashboard():
    """演示首页 — 系统概览仪表盘"""
    knowledge_items = await kb.query_applicable_knowledge(
        scenario_category="cleaning", max_items=50,
    )
    rules = await engine.get_active_rules()
    stats = await decision_logger.get_decision_stats(
        "cleaning_scheduler", time_range_days=30,
    )
    pending_approvals = await boundary.get_pending_approvals()

    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>ECIS v6 — Tower C 智能清洁调度</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }}
            .header {{ background: linear-gradient(135deg, #1e3a5f, #0f172a); padding: 32px; text-align: center; border-bottom: 2px solid #3b82f6; }}
            .header h1 {{ font-size: 28px; color: #60a5fa; margin-bottom: 8px; }}
            .header p {{ color: #94a3b8; font-size: 14px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; padding: 24px; max-width: 1400px; margin: 0 auto; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }}
            .card h3 {{ color: #60a5fa; font-size: 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
            .stat {{ font-size: 36px; font-weight: 700; color: #f1f5f9; }}
            .stat-label {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}
            .btn {{ display: inline-block; margin-top: 16px; padding: 10px 20px; background: #3b82f6; color: white;
                     border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 500; }}
            .btn:hover {{ background: #2563eb; }}
            .btn-green {{ background: #10b981; }}
            .btn-green:hover {{ background: #059669; }}
            .status-bar {{ background: #10b981; color: white; text-align: center; padding: 8px; font-size: 13px; }}
            .tag {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; margin: 2px; }}
            .tag-blue {{ background: #1e40af; color: #93c5fd; }}
            .tag-green {{ background: #065f46; color: #6ee7b7; }}
            .tag-red {{ background: #7f1d1d; color: #fca5a5; }}
            .section {{ padding: 0 24px 24px; max-width: 1400px; margin: 0 auto; }}
            .section h2 {{ color: #60a5fa; font-size: 20px; margin-bottom: 16px; padding-top: 8px; border-top: 1px solid #334155; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 10px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #334155; }}
            td {{ padding: 10px; font-size: 14px; border-bottom: 1px solid #1e293b; }}
        </style>
    </head>
    <body>
        <div class="status-bar">ECIS v6 Demo Server Running — 361 Tests Passing — All Systems Operational</div>
        <div class="header">
            <h1>ECIS v6 — Tower C</h1>
            <p>Enterprise Collective Intelligence System | 20 Robots | 10 Users | 45 Floors</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Knowledge Base (K1)</h3>
                <div class="stat">{len(knowledge_items)}</div>
                <div class="stat-label">Active Knowledge Entries</div>
                <a href="/docs#/K1" class="btn">Manage Knowledge</a>
            </div>
            <div class="card">
                <h3>Governance Rules (K2)</h3>
                <div class="stat">{len(rules)}</div>
                <div class="stat-label">Active Governance Rules</div>
                <a href="/docs#/K2" class="btn">Manage Rules</a>
            </div>
            <div class="card">
                <h3>Decision Log (K3)</h3>
                <div class="stat">{stats['total_decisions']}</div>
                <div class="stat-label">Decisions Logged</div>
                <a href="/docs#/K3" class="btn">View Logs</a>
            </div>
            <div class="card">
                <h3>Autonomy (B5)</h3>
                <div class="stat">{len(pending_approvals)}</div>
                <div class="stat-label">Pending Human Approvals</div>
                <a href="/docs#/B5" class="btn">Review</a>
            </div>
        </div>

        <div class="section">
            <h2>Quick Demo Actions</h2>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <a href="/docs#/Demo/simulate_scheduling_demo_simulate_schedule_post" class="btn btn-green">Run AI Schedule</a>
                <a href="/docs#/Demo/evaluate_rules_demo_evaluate_rules_post" class="btn">Test Rule Engine</a>
                <a href="/docs#/Demo/assemble_prompt_demo_assemble_prompt_post" class="btn">Build AI Prompt</a>
                <a href="/demo/ws-test" class="btn">WebSocket Test</a>
                <a href="/docs" class="btn">Full API Docs</a>
            </div>
        </div>

        <div class="section">
            <h2>Active Governance Rules</h2>
            <table>
                <tr><th>ID</th><th>Name</th><th>Type</th><th>Action</th><th>Priority</th></tr>
                {"".join(f'<tr><td>{r.rule_id}</td><td>{r.rule_name}</td><td><span class="tag tag-blue">{r.rule_type}</span></td><td><span class="tag {"tag-red" if r.action_type == "block" else "tag-green"}">{r.action_type}</span></td><td>{r.priority}</td></tr>' for r in rules)}
            </table>
        </div>
    </body>
    </html>
    """


# ====================================================================
# 1. Demo — 核心演示端点
# ====================================================================

@app.post("/demo/simulate-schedule", tags=["Demo"],
          summary="模拟AI调度决策（完整流水线）")
async def simulate_scheduling(
    robot_count: int = Query(default=5, description="参与调度的机器人数量"),
    include_low_battery: bool = Query(default=True, description="包含低电量机器人"),
):
    """
    **完整演示流水线:**
    1. 从K1加载场景知识
    2. 组装AI Prompt
    3. 模拟Agent决策（分配机器人到区域）
    4. A5 决策校验（4层流水线）
    5. K2 规则引擎评估
    6. B5 自主性检查
    7. K3 记录决策日志
    8. 通过WebSocket广播结果

    返回完整的决策流水线执行报告。
    """
    pipeline_start = time.monotonic()
    report = {"pipeline_steps": []}

    def step(name, data):
        report["pipeline_steps"].append({
            "step": name,
            "elapsed_ms": round((time.monotonic() - pipeline_start) * 1000, 1),
            "data": data,
        })

    # ── Step 1: Load knowledge ──
    knowledge = await kb.query_applicable_knowledge(
        scenario_category="cleaning",
        building_type="office_tower",
    )
    step("1_load_knowledge", {
        "knowledge_count": len(knowledge),
        "items": [{"id": k.knowledge_id, "name": k.name, "type": k.knowledge_type}
                  for k in knowledge[:5]],
    })

    # ── Step 2: Assemble prompt ──
    prompt = await kb.assemble_prompt(
        template_id="pt-tc-001",
        variables={
            "building_name": "Tower C",
            "current_time": datetime.now().strftime("%H:%M"),
            "robot_count": str(robot_count),
        },
        scenario_category="cleaning",
        context={"building_type": "office_tower"},
    )
    step("2_assemble_prompt", {
        "prompt_length": len(prompt),
        "estimated_tokens": _estimate_tokens(prompt),
        "prompt_preview": prompt[:300] + "..." if len(prompt) > 300 else prompt,
    })

    # ── Step 3: Simulate agent decision ──
    zones = ["1F-lobby", "B1-parking", "3F-dining", "10F-office", "25F-office",
             "45F-executive", "2F-commercial", "15F-office"]
    robots = []
    for i in range(robot_count):
        battery = 15 if (include_low_battery and i == 0) else (60 + i * 5)
        status = "error" if (include_low_battery and i == 1 and robot_count > 3) else "idle"
        robots.append({
            "robot_id": f"hx-{i+1:03d}",
            "battery_level": min(battery, 100),
            "status": status,
            "model": "Gaussin X1" if i % 2 == 0 else "Ecovacs T30",
        })

    assignments = []
    for i, robot in enumerate(robots):
        zone = zones[i % len(zones)]
        assignments.append({
            "robot_id": robot["robot_id"],
            "zone_id": zone,
            "task_type": "deep" if "executive" in zone else "standard",
            "priority": 5 if "executive" in zone else 3,
        })

    decision = {
        "action": "schedule",
        "task_type": "standard",
        "assignments": assignments,
        "robot_id": robots[0]["robot_id"] if robots else "hx-001",
        "priority": 3,
    }
    step("3_agent_decision", {
        "robot_count": len(robots),
        "robots": robots,
        "assignments": assignments,
    })

    # ── Step 4: A5 Decision validation ──
    context_for_validation = {
        "robot_states": {
            r["robot_id"]: {"battery_level": r["battery_level"], "status": r["status"]}
            for r in robots
        },
        "closed_zones": [],
        "total_robots_in_building": robot_count,
        "known_robot_ids": [r["robot_id"] for r in robots],
        "known_zone_ids": zones,
    }

    validation_result = await validator.validate(
        decision=decision,
        context=context_for_validation,
        agent_type="cleaning_scheduler",
    )
    step("4_validation", {
        "valid": validation_result.valid,
        "errors": [{"validator": e.validator, "field": e.field, "message": e.message,
                    "severity": e.severity.value if hasattr(e.severity, 'value') else str(e.severity)}
                   for e in validation_result.errors],
        "warnings": [{"validator": w.validator, "field": w.field, "message": w.message}
                     for w in validation_result.warnings],
        "validators_executed": validation_result.validators_executed,
        "duration_ms": validation_result.validation_duration_ms,
    })

    # ── Step 5: K2 Rule evaluation ──
    rule_results_all = []
    for robot in robots:
        results = await engine.evaluate(
            decision={"task_type": decision["task_type"], "robot_id": robot["robot_id"]},
            context={
                "battery_level": robot["battery_level"],
                "robot_status": robot["status"],
            },
        )
        for r in results:
            rule_results_all.append({
                "robot_id": robot["robot_id"],
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "action": r.action_type,
                "severity": r.severity,
                "message": r.message,
            })

    blocked_robots = list(set(
        r["robot_id"] for r in rule_results_all if r["action"] == "block"
    ))
    step("5_rule_evaluation", {
        "total_triggered": len(rule_results_all),
        "blocked_robots": blocked_robots,
        "blocked_count": len(blocked_robots),
        "details": rule_results_all,
    })

    # ── Step 6: B5 Autonomy check ──
    autonomy_level = await boundary.get_autonomy_level(
        task_type="standard_clean",
        context={
            "priority": 3,
            "is_emergency": False,
            "robot_count": robot_count,
            "human_available": True,
        },
    )
    auto_check = await boundary.check_can_auto_execute(
        task_type="standard_clean",
        context={
            "priority": 3,
            "is_emergency": False,
            "robot_count": robot_count,
            "human_available": True,
        },
    )
    step("6_autonomy_check", {
        "autonomy_level": autonomy_level,
        "can_auto_execute": auto_check.can_execute,
        "required_actions": auto_check.required_actions,
        "reason": auto_check.reason,
    })

    # ── Step 7: K3 Log decision ──
    ctx = DecisionContext(
        trigger_type="scheduled",
        llm_model="claude-3-sonnet (simulated)",
        llm_latency_ms=150,
        validation_passed=validation_result.valid,
        validation_errors=[
            {"validator": e.validator, "message": e.message}
            for e in validation_result.errors
        ],
        knowledge_used=[k.knowledge_id for k in knowledge[:3]],
        rules_evaluated=[r["rule_id"] for r in rule_results_all[:5]],
    )
    record = DecisionRecord(
        record_id="",
        agent_id="cleaning-agent-001",
        agent_type="cleaning_scheduler",
        decision_type="schedule",
        timestamp=datetime.now(timezone.utc),
        context=ctx,
        decision=decision,
    )
    record_id = await decision_logger.log_decision(record)
    step("7_decision_logged", {"record_id": record_id})

    # ── Step 8: WebSocket broadcast ──
    broadcast_msg = {
        "event": "schedule_completed",
        "record_id": record_id,
        "robot_count": robot_count,
        "blocked_count": len(blocked_robots),
        "autonomy_level": autonomy_level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    disconnected = []
    for ws in ws_connections:
        try:
            await ws.send_json(broadcast_msg)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        ws_connections.remove(ws)

    step("8_websocket_broadcast", {
        "active_connections": len(ws_connections),
        "message": broadcast_msg,
    })

    total_ms = round((time.monotonic() - pipeline_start) * 1000, 1)

    report["summary"] = {
        "total_pipeline_ms": total_ms,
        "robots_scheduled": robot_count,
        "robots_blocked": len(blocked_robots),
        "robots_active": robot_count - len(blocked_robots),
        "validation_passed": validation_result.valid,
        "autonomy_level": autonomy_level,
        "decision_record_id": record_id,
        "verdict": (
            "SCHEDULE APPROVED — AI auto-executed"
            if auto_check.can_execute and validation_result.valid
            else "SCHEDULE BLOCKED — requires human review"
        ),
    }

    return report


@app.post("/demo/evaluate-rules", tags=["Demo"],
          summary="测试规则引擎（输入电量和状态）")
async def evaluate_rules_demo(
    battery_level: int = Query(default=15, description="机器人电量 (0-100)"),
    robot_status: str = Query(default="idle", description="机器人状态: idle/working/error/charging"),
    task_type: str = Query(default="standard", description="任务类型: standard/deep/quick/spot"),
):
    """
    测试治理规则引擎。输入机器人状态，查看哪些规则会被触发。

    **试试:**
    - battery=15 → 低电量阻止
    - robot_status=error → 错误状态阻止
    - battery=45 → 中电量警告
    - battery=85 → 全部通过
    """
    results = await engine.evaluate(
        decision={"task_type": task_type, "robot_id": "demo-robot"},
        context={
            "battery_level": battery_level,
            "robot_status": robot_status,
        },
    )

    blocks = [r for r in results if r.action_type == "block"]
    warns = [r for r in results if r.action_type == "warn"]
    modifies = [r for r in results if r.action_type == "modify"]

    return {
        "input": {
            "battery_level": battery_level,
            "robot_status": robot_status,
            "task_type": task_type,
        },
        "verdict": "BLOCKED" if blocks else ("WARNING" if warns else "APPROVED"),
        "blocked": len(blocks) > 0,
        "summary": {
            "block_count": len(blocks),
            "warn_count": len(warns),
            "modify_count": len(modifies),
        },
        "triggered_rules": [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "action": r.action_type,
                "severity": r.severity,
                "message": r.message,
            }
            for r in results
        ],
    }


@app.post("/demo/assemble-prompt", tags=["Demo"],
          summary="动态组装AI Prompt（注入场景知识）")
async def assemble_prompt_demo(
    building_name: str = Query(default="Tower C"),
    current_time: str = Query(default="08:00"),
    robot_count: int = Query(default=20),
):
    """
    展示K1场景知识如何被动态注入AI Prompt。

    Prompt模板中的 `{{variable}}` 被填充，知识槽被注入匹配的领域知识。
    """
    prompt = await kb.assemble_prompt(
        template_id="pt-tc-001",
        variables={
            "building_name": building_name,
            "current_time": current_time,
            "robot_count": str(robot_count),
        },
        scenario_category="cleaning",
        context={"building_type": "office_tower"},
    )

    return {
        "prompt": prompt,
        "estimated_tokens": _estimate_tokens(prompt),
        "prompt_length": len(prompt),
        "template_id": "pt-tc-001",
        "variables_filled": {
            "building_name": building_name,
            "current_time": current_time,
            "robot_count": str(robot_count),
        },
    }


@app.post("/demo/autonomy-check", tags=["Demo"],
          summary="人机自主性边界检查")
async def autonomy_check_demo(
    task_type: str = Query(default="standard_clean",
                           description="standard_clean/deep_clean/emergency/reassignment/special_event"),
    priority: int = Query(default=3, description="优先级 1-5"),
    is_emergency: bool = Query(default=False),
    robot_count: int = Query(default=20),
    human_available: bool = Query(default=True),
):
    """
    检查AI在当前上下文下的自主性级别。

    **试试:**
    - task=standard_clean → L2 (AI执行, 通知人类)
    - task=deep_clean → L1 (需人工审批)
    - task=emergency → L3 (AI全权处理)
    - task=special_event → L0 (完全人工)
    - human_available=false → 自动提升到L2
    """
    context = {
        "priority": priority,
        "is_emergency": is_emergency,
        "robot_count": robot_count,
        "human_available": human_available,
    }

    level = await boundary.get_autonomy_level(task_type, context)
    check = await boundary.check_can_auto_execute(task_type, context)

    level_descriptions = {
        AutonomyLevel.FULL_HUMAN: "L0 完全人工 — 所有决策由人类做出",
        AutonomyLevel.HUMAN_APPROVE: "L1 人工审批 — AI建议，人类批准",
        AutonomyLevel.AI_EXECUTE_NOTIFY: "L2 AI执行+通知 — AI自动执行，通知人类",
        AutonomyLevel.FULL_AI: "L3 完全AI — AI全权决策和执行",
    }

    return {
        "input": {"task_type": task_type, **context},
        "autonomy_level": level,
        "level_description": level_descriptions.get(level, level),
        "can_auto_execute": check.can_execute,
        "reason": check.reason,
        "required_actions": check.required_actions,
        "escalate_to": check.escalate_to,
    }


# ====================================================================
# 2. K1 — 场景知识库
# ====================================================================

@app.get("/knowledge", tags=["K1 场景知识库"],
         summary="查询场景知识")
async def list_knowledge(
    category: str = Query(default="cleaning"),
    building_type: str = Query(default="all"),
    max_items: int = Query(default=20),
):
    """查询当前上下文适用的场景知识条目"""
    result = await g8_api.list_knowledge({
        "scenario_category": category,
        "building_type": building_type,
        "max_items": max_items,
    })
    return result


@app.post("/knowledge", tags=["K1 场景知识库"],
          summary="创建知识条目")
async def create_knowledge(data: dict):
    return await g8_api.create_knowledge(data)


@app.get("/knowledge/{knowledge_id}", tags=["K1 场景知识库"],
         summary="获取单条知识")
async def get_knowledge(knowledge_id: str):
    return await g8_api.get_knowledge(knowledge_id)


@app.get("/templates/{template_id}", tags=["K1 场景知识库"],
         summary="获取Prompt模板")
async def get_template(template_id: str):
    return await g8_api.get_template(template_id)


# ====================================================================
# 3. K2 — 治理规则引擎
# ====================================================================

@app.get("/rules", tags=["K2 治理规则引擎"],
         summary="查询活跃规则")
async def list_rules(
    scope: Optional[str] = Query(default=None),
    agent_type: Optional[str] = Query(default=None),
):
    return await g9_api.list_rules({
        "scope": scope,
        "agent_type": agent_type,
    })


@app.post("/rules", tags=["K2 治理规则引擎"],
          summary="创建治理规则")
async def create_rule(data: dict):
    return await g9_api.create_rule(data)


@app.get("/rules/{rule_id}", tags=["K2 治理规则引擎"],
         summary="获取单条规则")
async def get_rule(rule_id: str):
    return await g9_api.get_rule(rule_id)


@app.put("/rules/{rule_id}/disable", tags=["K2 治理规则引擎"],
         summary="禁用规则")
async def disable_rule(rule_id: str):
    return await g9_api.disable_rule(rule_id)


# ====================================================================
# 4. K3 — 决策日志
# ====================================================================

@app.get("/decisions", tags=["K3 决策日志"],
         summary="查询决策记录")
async def query_decisions(
    agent_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20),
):
    return await log_api.query_decisions({
        "agent_type": agent_type,
        "limit": limit,
    })


@app.get("/decisions/stats", tags=["K3 决策日志"],
         summary="决策统计")
async def decision_stats(
    agent_type: str = Query(default="cleaning_scheduler"),
    days: int = Query(default=30),
):
    """获取决策统计: 总数、校验通过率、人工覆盖率、质量评分"""
    return await log_api.get_stats(agent_type, time_range_days=days)


@app.post("/decisions/{record_id}/outcome", tags=["K3 决策日志"],
          summary="补填决策结果")
async def update_outcome(record_id: str, data: dict):
    return await log_api.update_outcome(record_id, data)


# ====================================================================
# 5. B5 — 人机自主性
# ====================================================================

@app.get("/autonomy/pending", tags=["B5 人机自主性"],
         summary="查看待审批请求")
async def pending_approvals():
    return await boundary.get_pending_approvals()


@app.post("/autonomy/request-approval", tags=["B5 人机自主性"],
          summary="创建人工审批请求")
async def request_approval(
    task_type: str = Query(default="deep_clean"),
    task_id: str = Query(default=""),
):
    if not task_id:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
    request_id = await boundary.request_human_approval(
        task_id=task_id,
        task_type=task_type,
        decision={"action": "schedule", "zone": "45F-executive"},
        context={"priority": 4, "robot_count": 20},
    )
    return {"request_id": request_id, "task_id": task_id, "status": "pending"}


@app.post("/autonomy/approve/{request_id}", tags=["B5 人机自主性"],
          summary="批准/拒绝审批请求")
async def approve_request(
    request_id: str,
    approved: bool = Query(default=True),
):
    result = await boundary.process_human_response(
        request_id=request_id,
        approved=approved,
    )
    return result


# ====================================================================
# 6. P1 — 离线队列
# ====================================================================

@app.post("/offline/enqueue", tags=["P1 离线支持"],
          summary="入队离线操作")
async def enqueue_operation(
    user_id: str = Query(default="trainer-001"),
    operation_type: str = Query(default="task_confirm"),
    task_id: str = Query(default="task-001"),
):
    """模拟训练师在离线环境中确认/完成任务"""
    op_id = await offline_queue.enqueue(
        user_id=user_id,
        operation_type=operation_type,
        payload={"task_id": task_id, "confirmed": True,
                 "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    return {"operation_id": op_id, "status": "pending", "user_id": user_id}


@app.get("/offline/pending/{user_id}", tags=["P1 离线支持"],
         summary="查看用户待同步操作")
async def get_pending_ops(user_id: str):
    ops = await offline_queue.get_pending_ops(user_id)
    return {"user_id": user_id, "pending_count": len(ops),
            "operations": [{"id": o.operation_id, "type": o.operation_type,
                           "status": o.sync_status, "created": o.created_at}
                          for o in ops]}


@app.get("/offline/status", tags=["P1 离线支持"],
         summary="离线队列状态")
async def offline_status():
    return offline_queue.get_status()


# ====================================================================
# 7. P3 — 通知服务
# ====================================================================

@app.post("/notifications/send", tags=["P3 通知服务"],
          summary="发送通知")
async def send_notification(
    user_id: str = Query(default="supervisor-001"),
    title: str = Query(default="机器人 hx-001 电量不足"),
    priority: str = Query(default="urgent", description="normal/urgent/critical"),
):
    """发送通知到指定用户（带重试机制）"""
    nid = await notification_svc.store_notification(
        user_id=user_id,
        notification_type="robot_alert",
        title=title,
        message=f"[{priority.upper()}] {title}",
        priority=priority,
    )
    return {"notification_id": nid, "user_id": user_id, "priority": priority}


@app.get("/notifications/{user_id}", tags=["P3 通知服务"],
         summary="获取用户待读通知")
async def get_notifications(user_id: str):
    pending = await notification_svc.get_pending_notifications(user_id)
    return {"user_id": user_id, "count": len(pending),
            "notifications": [
                {"id": n.notification_id, "title": n.title,
                 "priority": n.priority, "status": n.delivery_status,
                 "created_at": n.created_at.isoformat() if n.created_at else None}
                for n in pending
            ]}


@app.get("/notifications/stats/{user_id}", tags=["P3 通知服务"],
         summary="通知统计")
async def notification_stats(user_id: str):
    return await notification_svc.get_notification_stats(user_id)


# ====================================================================
# 8. WebSocket — 实时推送
# ====================================================================

@app.get("/demo/ws-test", response_class=HTMLResponse, tags=["WebSocket"],
         summary="WebSocket实时推送测试页")
async def ws_test_page():
    """打开此页面后，运行 /demo/simulate-schedule 可看到实时推送"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ECIS WebSocket Monitor</title>
        <style>
            body { font-family: monospace; background: #0f172a; color: #e2e8f0; padding: 20px; }
            h2 { color: #60a5fa; }
            #log { background: #1e293b; padding: 16px; border-radius: 8px; max-height: 500px;
                   overflow-y: auto; border: 1px solid #334155; }
            .msg { padding: 8px; border-bottom: 1px solid #334155; }
            .connected { color: #10b981; }
            .event { color: #f59e0b; }
            .btn { padding: 10px 20px; background: #3b82f6; color: white; border: none;
                   border-radius: 8px; cursor: pointer; margin: 5px; font-size: 14px; }
        </style>
    </head>
    <body>
        <h2>ECIS WebSocket Real-time Monitor</h2>
        <p>Status: <span id="status" class="connected">Connecting...</span></p>
        <button class="btn" onclick="connect()">Reconnect</button>
        <button class="btn" onclick="document.getElementById('log').innerHTML=''">Clear</button>
        <div id="log"></div>
        <script>
            let ws;
            function connect() {
                const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(protocol + '//' + location.host + '/ws');
                ws.onopen = () => {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').className = 'connected';
                    addLog('WebSocket connected', 'connected');
                };
                ws.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    addLog(JSON.stringify(data, null, 2), 'event');
                };
                ws.onclose = () => {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').style.color = '#ef4444';
                    addLog('WebSocket disconnected', '');
                    setTimeout(connect, 3000);
                };
            }
            function addLog(text, cls) {
                const div = document.getElementById('log');
                const msg = document.createElement('div');
                msg.className = 'msg ' + cls;
                msg.textContent = new Date().toLocaleTimeString() + ' | ' + text;
                div.insertBefore(msg, div.firstChild);
            }
            connect();
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    logger.info("WebSocket client connected (total: %d)", len(ws_connections))
    try:
        await websocket.send_json({
            "event": "connected",
            "message": "ECIS v6 WebSocket connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        while True:
            # Keep connection alive, handle pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        ws_connections.remove(websocket)
        logger.info("WebSocket client disconnected (total: %d)", len(ws_connections))


# ====================================================================
# 9. System info
# ====================================================================

@app.get("/system/health", tags=["System"],
         summary="系统健康检查")
async def health():
    return {
        "status": "healthy",
        "version": "6.0.0-demo",
        "modules": {
            "K1_knowledge_base": "active",
            "K2_rule_engine": "active",
            "K3_decision_logger": "active",
            "A5_validator": "active",
            "B5_autonomy": "active",
            "P1_offline": "active",
            "P3_notifications": "active",
            "websocket": f"{len(ws_connections)} connections",
        },
        "stats": {
            "knowledge_entries": len(kb._knowledge),
            "governance_rules": len(engine._rules),
            "decision_records": decision_logger.record_count,
            "tests_passing": 361,
        },
    }


@app.get("/system/modules", tags=["System"],
         summary="查看所有已加载模块")
async def list_modules():
    """列出 Sprint 0-3 所有已实现的模块"""
    return {
        "sprints": {
            "sprint_0": {
                "status": "complete",
                "modules": ["ecis-protocols v1.3 (7 models)", "CLAUDE.md v3",
                            "EventBusInterface", "docker-compose.dev.yml"],
            },
            "sprint_1": {
                "status": "complete",
                "modules": ["A5 DecisionValidator (4-layer pipeline)",
                            "A1 RealtimeClient + EventDrivenCollector",
                            "G4 WebSocket endpoints"],
                "tests": 91,
            },
            "sprint_2": {
                "status": "complete",
                "modules": ["K1 ScenarioKnowledgeBase", "K2 GovernanceRuleEngine",
                            "K3 DecisionLogger", "G8/G9 Management APIs",
                            "Tower C seed data"],
                "tests": 265,
            },
            "sprint_3": {
                "status": "complete",
                "modules": ["P1 OfflineQueueManager + CacheManager",
                            "B5 HumanAgentBoundary (L0-L3)",
                            "P3 NotificationPersistenceService"],
                "tests": 361,
            },
            "sprint_4": {
                "status": "pending",
                "modules": ["Production Docker Compose", "DB migration",
                            "SSL", "Monitoring", "Gradual rollout"],
            },
        },
        "total_tests": 361,
        "total_source_files": 16,
    }
