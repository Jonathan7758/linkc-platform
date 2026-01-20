# 模块开发规格书：A2 清洁调度 Agent

## 文档信息

| 项目 | 内容 |
|-----|------|
| 模块ID | A2 |
| 模块名称 | 清洁调度 Agent |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | A1运行时框架、M2任务MCP、M3/M4机器人MCP |

---

## 1. 模块概述

### 1.1 职责描述

清洁调度Agent是系统的核心智能体，负责：
- **任务分配**：将清洁任务分配给最合适的机器人
- **实时调度**：根据机器人状态动态调整任务
- **优先级管理**：处理紧急任务和优先级调整
- **异常处理**：检测异常并触发升级
- **效率优化**：学习最优调度策略

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       Agent层                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         【A2 清洁调度Agent】 ◄── 本模块              │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              调度决策引擎                    │   │   │
│  │  │  任务匹配 / 优先级排序 / 冲突解决           │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│         ┌───────────────┼───────────────┐                  │
│         ▼               ▼               ▼                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ M2任务MCP  │ │ M3高仙MCP   │ │ M4科沃斯MCP │          │
│  │ 任务管理    │ │ 机器人控制  │ │ 机器人控制  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心工作流

```
┌─────────────────────────────────────────────────────────────┐
│                    清洁调度工作流                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 检查待执行任务                                          │
│     ├─ 调用 task_get_pending_tasks                         │
│     └─ 获取当前时段需执行的任务列表                         │
│                         │                                   │
│                         ▼                                   │
│  2. 获取机器人状态                                          │
│     ├─ 调用 gaoxian_list_robots / ecovacs_list_robots      │
│     └─ 筛选可用机器人（idle + 电量充足）                    │
│                         │                                   │
│                         ▼                                   │
│  3. 任务-机器人匹配                                         │
│     ├─ 计算匹配得分（距离、电量、历史表现）                 │
│     ├─ 考虑机器人品牌兼容性                                 │
│     └─ 选择最优分配方案                                     │
│                         │                                   │
│                         ▼                                   │
│  4. 执行分配                                                │
│     ├─ 调用 task_update_status (assigned)                  │
│     ├─ 调用 gaoxian/ecovacs_start_cleaning                 │
│     └─ 记录决策日志                                         │
│                         │                                   │
│                         ▼                                   │
│  5. 监控执行                                                │
│     ├─ 定期检查任务进度                                     │
│     ├─ 检测异常（超时、故障）                               │
│     └─ 必要时触发升级                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 接口定义

### 2.1 Agent配置

```python
class CleaningSchedulerConfig(AgentConfig):
    """清洁调度Agent配置"""
    agent_type: str = "cleaning_scheduler"
    
    # 调度参数
    scheduling_interval: int = 60           # 调度周期（秒）
    max_assignments_per_cycle: int = 10     # 每周期最大分配数
    min_battery_for_task: int = 30          # 任务所需最低电量
    max_task_wait_time: int = 30            # 最大任务等待时间（分钟）
    
    # 匹配参数
    distance_weight: float = 0.4            # 距离权重
    battery_weight: float = 0.3             # 电量权重
    performance_weight: float = 0.3         # 历史表现权重
    
    # 异常检测
    task_timeout_minutes: int = 120         # 任务超时时间
    stuck_detection_minutes: int = 10       # 卡住检测时间
```

### 2.2 调度决策接口

```python
class SchedulingDecision(BaseModel):
    """调度决策"""
    decision_id: str
    timestamp: datetime
    task_id: str
    robot_id: str
    score: float                    # 匹配得分
    factors: Dict[str, float]       # 各因素得分
    reason: str                     # 决策理由
    
class SchedulingResult(BaseModel):
    """调度结果"""
    cycle_id: str
    timestamp: datetime
    tasks_processed: int
    tasks_assigned: int
    tasks_skipped: int
    decisions: List[SchedulingDecision]
    errors: List[str]
```

### 2.3 调用的MCP Tools

```python
# 本Agent需要调用的MCP Tools

# === M2 任务管理 ===
task_get_pending_tasks(tenant_id, priority_threshold=None, limit=20)
task_update_status(task_id, new_status, assigned_robot_id=None)
task_get_task(task_id)

# === M3 高仙机器人 ===
gaoxian_list_robots(tenant_id, status=None, building_id=None)
gaoxian_get_robot_status(robot_id)
gaoxian_start_cleaning(robot_id, zone_id, clean_type="routine")
gaoxian_stop_cleaning(robot_id, return_to_dock=True)

# === M4 科沃斯机器人 ===
ecovacs_list_robots(tenant_id, status=None, building_id=None)
ecovacs_get_robot_status(robot_id)
ecovacs_start_cleaning(robot_id, zone_id, clean_mode="auto")
ecovacs_stop_cleaning(robot_id, return_to_dock=True)
```

---

## 3. 核心算法

### 3.1 任务-机器人匹配算法

```python
class TaskRobotMatcher:
    """任务-机器人匹配器"""
    
    def __init__(self, config: CleaningSchedulerConfig):
        self.config = config
        
    async def match(
        self,
        tasks: List[CleaningTask],
        robots: List[RobotStatus]
    ) -> List[SchedulingDecision]:
        """
        计算最优匹配方案
        
        使用匈牙利算法或贪心算法求解
        """
        # 过滤可用机器人
        available_robots = [
            r for r in robots 
            if r.status == "idle" and r.battery_level >= self.config.min_battery_for_task
        ]
        
        if not available_robots:
            return []
        
        # 计算得分矩阵
        score_matrix = self._compute_score_matrix(tasks, available_robots)
        
        # 贪心分配（按任务优先级）
        decisions = []
        assigned_robots = set()
        
        for task in sorted(tasks, key=lambda t: t.priority):
            best_robot = None
            best_score = -1
            
            for robot in available_robots:
                if robot.robot_id in assigned_robots:
                    continue
                    
                score = score_matrix.get((task.task_id, robot.robot_id), 0)
                if score > best_score:
                    best_score = score
                    best_robot = robot
            
            if best_robot and best_score > 0:
                decisions.append(SchedulingDecision(
                    decision_id=str(uuid4()),
                    timestamp=datetime.utcnow(),
                    task_id=task.task_id,
                    robot_id=best_robot.robot_id,
                    score=best_score,
                    factors=self._get_factors(task, best_robot),
                    reason=self._generate_reason(task, best_robot, best_score)
                ))
                assigned_robots.add(best_robot.robot_id)
        
        return decisions
    
    def _compute_score_matrix(
        self,
        tasks: List[CleaningTask],
        robots: List[RobotStatus]
    ) -> Dict[Tuple[str, str], float]:
        """计算得分矩阵"""
        scores = {}
        
        for task in tasks:
            for robot in robots:
                score = self._compute_score(task, robot)
                scores[(task.task_id, robot.robot_id)] = score
                
        return scores
    
    def _compute_score(
        self,
        task: CleaningTask,
        robot: RobotStatus
    ) -> float:
        """
        计算单个任务-机器人匹配得分
        
        得分 = 距离得分 * 距离权重 
             + 电量得分 * 电量权重 
             + 表现得分 * 表现权重
        """
        # 距离得分（越近越高）
        distance = self._calculate_distance(robot.position, task.zone_position)
        distance_score = max(0, 1 - distance / 100)  # 归一化
        
        # 电量得分（电量越高越好）
        battery_score = robot.battery_level / 100
        
        # 历史表现得分
        performance_score = self._get_robot_performance(robot.robot_id)
        
        # 加权求和
        total_score = (
            distance_score * self.config.distance_weight +
            battery_score * self.config.battery_weight +
            performance_score * self.config.performance_weight
        )
        
        # 品牌兼容性检查（不兼容则得分为0）
        if not self._is_compatible(task, robot):
            return 0
            
        return total_score
    
    def _is_compatible(self, task: CleaningTask, robot: RobotStatus) -> bool:
        """检查任务-机器人兼容性"""
        # 检查机器人是否支持任务所在区域
        # 检查机器人是否有该区域的地图
        return True  # 简化实现
```

### 3.2 异常检测算法

```python
class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, config: CleaningSchedulerConfig):
        self.config = config
        
    async def detect(
        self,
        task: CleaningTask,
        robot: RobotStatus
    ) -> List[Anomaly]:
        """检测任务执行异常"""
        anomalies = []
        
        # 1. 任务超时检测
        if task.actual_start:
            elapsed = datetime.utcnow() - task.actual_start
            if elapsed.total_seconds() > self.config.task_timeout_minutes * 60:
                anomalies.append(Anomaly(
                    type="task_timeout",
                    severity="warning",
                    message=f"任务执行超时: {elapsed.total_seconds()/60:.0f}分钟"
                ))
        
        # 2. 机器人卡住检测
        if robot.status == "working":
            # 检查位置是否长时间未变化
            if self._is_stuck(robot):
                anomalies.append(Anomaly(
                    type="robot_stuck",
                    severity="error",
                    message="机器人疑似卡住"
                ))
        
        # 3. 电量异常检测
        if robot.battery_level < 10 and robot.status == "working":
            anomalies.append(Anomaly(
                type="low_battery",
                severity="warning",
                message=f"机器人电量过低: {robot.battery_level}%"
            ))
        
        # 4. 机器人错误检测
        if robot.status == "error":
            anomalies.append(Anomaly(
                type="robot_error",
                severity="error",
                message=f"机器人报错: {robot.error_code}"
            ))
        
        return anomalies
```

---

## 4. 完整实现

### 4.1 CleaningSchedulerAgent实现

```python
class CleaningSchedulerAgent(BaseAgent):
    """清洁调度Agent"""
    
    def __init__(self, config: CleaningSchedulerConfig, runtime: AgentRuntime):
        super().__init__(config, runtime)
        self.scheduler_config = config
        self.matcher = TaskRobotMatcher(config)
        self.detector = AnomalyDetector(config)
        self._running_tasks: Dict[str, str] = {}  # task_id -> robot_id
        
    async def on_start(self):
        """启动初始化"""
        self.logger.info("CleaningSchedulerAgent starting")
        # 加载正在执行的任务
        await self._load_running_tasks()
        
    async def on_stop(self):
        """停止清理"""
        self.logger.info("CleaningSchedulerAgent stopping")
        
    async def run(self):
        """主循环"""
        # 1. 执行调度
        await self._schedule_tasks()
        
        # 2. 监控执行中的任务
        await self._monitor_running_tasks()
        
        # 3. 等待下一周期
        await asyncio.sleep(self.scheduler_config.scheduling_interval)
    
    async def _schedule_tasks(self):
        """执行任务调度"""
        self.logger.info("Starting scheduling cycle")
        
        # 获取待执行任务
        tasks_result = await self.call_tool(
            "task_get_pending_tasks",
            {
                "tenant_id": self.tenant_id,
                "limit": self.scheduler_config.max_assignments_per_cycle
            }
        )
        
        if not tasks_result.success:
            self.logger.error(f"Failed to get pending tasks: {tasks_result.error}")
            return
        
        pending_tasks = tasks_result.data.get("tasks", [])
        if not pending_tasks:
            self.logger.debug("No pending tasks")
            return
        
        # 获取机器人状态
        robots = await self._get_available_robots()
        
        if not robots:
            self.logger.warning("No available robots")
            return
        
        # 执行匹配
        decisions = await self.matcher.match(pending_tasks, robots)
        
        # 执行分配
        for decision in decisions:
            await self._execute_assignment(decision)
            
        # 记录调度结果
        self._log_scheduling_result(pending_tasks, decisions)
    
    async def _get_available_robots(self) -> List[RobotStatus]:
        """获取所有可用机器人"""
        robots = []
        
        # 获取高仙机器人
        gaoxian_result = await self.call_tool(
            "gaoxian_list_robots",
            {"tenant_id": self.tenant_id}
        )
        if gaoxian_result.success:
            robots.extend(gaoxian_result.data.get("robots", []))
        
        # 获取科沃斯机器人
        ecovacs_result = await self.call_tool(
            "ecovacs_list_robots",
            {"tenant_id": self.tenant_id}
        )
        if ecovacs_result.success:
            robots.extend(ecovacs_result.data.get("robots", []))
        
        return robots
    
    async def _execute_assignment(self, decision: SchedulingDecision):
        """执行任务分配"""
        self.logger.info(
            f"Assigning task {decision.task_id} to robot {decision.robot_id}"
        )
        
        # 更新任务状态
        update_result = await self.call_tool(
            "task_update_status",
            {
                "task_id": decision.task_id,
                "new_status": "assigned",
                "assigned_robot_id": decision.robot_id
            }
        )
        
        if not update_result.success:
            self.logger.error(f"Failed to update task: {update_result.error}")
            return
        
        # 获取任务详情（确定区域）
        task_result = await self.call_tool(
            "task_get_task",
            {"task_id": decision.task_id}
        )
        
        if not task_result.success:
            return
            
        task = task_result.data["task"]
        
        # 启动清洁
        robot = await self._get_robot_info(decision.robot_id)
        
        if robot["brand"] == "gaoxian":
            start_result = await self.call_tool(
                "gaoxian_start_cleaning",
                {
                    "robot_id": decision.robot_id,
                    "zone_id": task["zone_id"],
                    "clean_type": task["task_type"]
                }
            )
        else:  # ecovacs
            start_result = await self.call_tool(
                "ecovacs_start_cleaning",
                {
                    "robot_id": decision.robot_id,
                    "zone_id": task["zone_id"],
                    "clean_mode": "auto"
                }
            )
        
        if start_result.success:
            # 更新任务为执行中
            await self.call_tool(
                "task_update_status",
                {
                    "task_id": decision.task_id,
                    "new_status": "in_progress"
                }
            )
            # 记录
            self._running_tasks[decision.task_id] = decision.robot_id
            
            # 发送事件
            await self.emit_event("task_started", {
                "task_id": decision.task_id,
                "robot_id": decision.robot_id
            })
        else:
            self.logger.error(f"Failed to start cleaning: {start_result.error}")
            # 回滚任务状态
            await self.call_tool(
                "task_update_status",
                {
                    "task_id": decision.task_id,
                    "new_status": "pending"
                }
            )
    
    async def _monitor_running_tasks(self):
        """监控执行中的任务"""
        for task_id, robot_id in list(self._running_tasks.items()):
            # 获取任务和机器人状态
            task_result = await self.call_tool(
                "task_get_task", {"task_id": task_id}
            )
            robot_result = await self._get_robot_status(robot_id)
            
            if not task_result.success or not robot_result:
                continue
            
            task = task_result.data["task"]
            robot = robot_result
            
            # 检查任务是否完成
            if robot["status"] == "idle" and task["status"] == "in_progress":
                # 任务可能已完成
                await self._handle_task_completion(task_id, robot_id)
                continue
            
            # 异常检测
            anomalies = await self.detector.detect(task, robot)
            
            for anomaly in anomalies:
                await self._handle_anomaly(task_id, robot_id, anomaly)
    
    async def _handle_task_completion(self, task_id: str, robot_id: str):
        """处理任务完成"""
        self.logger.info(f"Task {task_id} completed")
        
        # 更新任务状态
        await self.call_tool(
            "task_update_status",
            {
                "task_id": task_id,
                "new_status": "completed",
                "completion_rate": 100
            }
        )
        
        # 移除跟踪
        del self._running_tasks[task_id]
        
        # 发送事件
        await self.emit_event("task_completed", {
            "task_id": task_id,
            "robot_id": robot_id
        })
    
    async def _handle_anomaly(
        self,
        task_id: str,
        robot_id: str,
        anomaly: Anomaly
    ):
        """处理异常"""
        self.logger.warning(
            f"Anomaly detected: {anomaly.type} for task {task_id}"
        )
        
        # 根据严重程度决定是否升级
        if anomaly.severity == "error":
            await self.escalate(
                level=EscalationLevel.ERROR,
                reason=anomaly.message,
                context={
                    "task_id": task_id,
                    "robot_id": robot_id,
                    "anomaly_type": anomaly.type
                }
            )
        elif anomaly.severity == "warning":
            await self.escalate(
                level=EscalationLevel.WARNING,
                reason=anomaly.message,
                context={
                    "task_id": task_id,
                    "robot_id": robot_id,
                    "anomaly_type": anomaly.type
                }
            )
```

---

## 5. 测试要求

### 5.1 单元测试用例

```python
class TestCleaningSchedulerAgent:
    
    async def test_task_robot_matching(self):
        """测试任务-机器人匹配算法"""
        pass
    
    async def test_execute_assignment(self):
        """测试任务分配执行"""
        pass
    
    async def test_anomaly_detection_timeout(self):
        """测试超时异常检测"""
        pass
    
    async def test_anomaly_detection_stuck(self):
        """测试卡住异常检测"""
        pass
    
    async def test_task_completion(self):
        """测试任务完成处理"""
        pass
    
    async def test_low_battery_skip(self):
        """测试低电量机器人跳过"""
        pass
```

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 能获取待执行任务列表
- [ ] 能获取可用机器人列表
- [ ] 能正确匹配任务和机器人
- [ ] 能成功启动清洁任务
- [ ] 能监控任务执行状态
- [ ] 能检测并处理异常
- [ ] 决策日志完整记录

### 6.2 性能要求

- 单次调度周期 < 5s
- 支持100+任务/100+机器人场景
- 决策延迟 < 1s

### 6.3 业务指标

- 任务分配成功率 > 95%
- 异常检测准确率 > 90%
- 机器人利用率提升可量化
