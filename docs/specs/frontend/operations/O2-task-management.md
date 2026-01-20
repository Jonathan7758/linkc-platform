# O2 任务管理界面规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | O2 |
| 模块名称 | 任务管理界面 (Task Management) |
| 版本 | 1.0 |
| 日期 | 2026-01-20 |
| 状态 | 规划中 |
| 所属终端 | 运营控制台 (Operations Console) |
| 前置依赖 | G3-task-api, G4-robot-api, G2-space-api |

---

## 一、模块概述

### 1.1 职责描述

任务管理界面是运营控制台的核心功能模块，为运营经理提供清洁任务的全生命周期管理能力，包括任务创建、排程配置、执行监控、任务调整和历史回顾。

### 1.2 核心功能

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 任务列表 | 查看和筛选所有清洁任务 | P0 |
| 任务创建 | 手动创建即时或定时任务 | P0 |
| 排程管理 | 配置周期性清洁排程 | P0 |
| 执行监控 | 实时查看任务执行状态 | P0 |
| 任务干预 | 暂停、取消、重新分配任务 | P1 |
| 任务模板 | 创建和管理常用任务模板 | P1 |
| 批量操作 | 批量创建/修改/删除任务 | P2 |

### 1.3 用户角色

| 角色 | 权限 | 使用场景 |
|-----|------|---------|
| 运营经理 | 全部功能 | 日常任务管理 |
| 区域主管 | 查看+创建+修改本区域任务 | 区域任务调整 |
| 运营专员 | 查看+创建即时任务 | 临时任务创建 |

---

## 二、页面结构

### 2.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [任务管理]                                          [+ 新建任务] [批量操作] │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ [今日任务] [排程管理] [任务模板] [历史记录]                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐ ┌─────────────────────────────────┐│
│  │ 筛选条件                            │ │ 快速统计                        ││
│  │ [楼宇▼] [状态▼] [机器人▼] [时间▼]  │ │ 待执行:12 执行中:5 已完成:28    ││
│  │ [搜索任务...]              [筛选]   │ │ 异常:2  取消:1                   ││
│  └─────────────────────────────────────┘ └─────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 任务列表                                                      [排序▼] │  │
│  │ ┌─────────────────────────────────────────────────────────────────────┐│  │
│  │ │ □ | 任务ID | 区域 | 类型 | 状态 | 机器人 | 计划时间 | 进度 | 操作  ││  │
│  │ ├─────────────────────────────────────────────────────────────────────┤│  │
│  │ │ □ | T-001  | A栋1F大堂 | 日常 | 执行中 | GX-001 | 08:00 | 65% | ⋮  ││  │
│  │ │ □ | T-002  | A栋2F走廊 | 日常 | 待执行 | --     | 09:00 | --  | ⋮  ││  │
│  │ │ □ | T-003  | B栋1F大堂 | 临时 | ⚠异常  | GX-003 | 08:30 | 40% | ⋮  ││  │
│  │ │ □ | T-004  | A栋3F办公 | 深度 | 已完成 | EC-001 | 07:00 | 100%| ⋮  ││  │
│  │ │ ...                                                                 ││  │
│  │ └─────────────────────────────────────────────────────────────────────┘│  │
│  │ 共 48 条任务  < 1 2 3 4 5 >  每页显示 [20▼]                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Tab页说明

| Tab | 功能 | 主要内容 |
|-----|------|---------|
| 今日任务 | 查看和管理今天的任务 | 任务列表、执行状态、快速操作 |
| 排程管理 | 管理周期性清洁排程 | 排程列表、启用/禁用、编辑配置 |
| 任务模板 | 管理任务模板 | 模板列表、创建/编辑模板 |
| 历史记录 | 查看历史任务 | 历史查询、执行报告、统计分析 |

---

## 三、组件定义

### 3.1 任务列表组件 (TaskList)

```typescript
// 组件Props
interface TaskListProps {
  tasks: Task[];
  loading: boolean;
  pagination: PaginationConfig;
  onTaskClick: (taskId: string) => void;
  onTaskAction: (taskId: string, action: TaskAction) => void;
  onSelectionChange: (selectedIds: string[]) => void;
  onPageChange: (page: number, pageSize: number) => void;
}

// 任务数据
interface Task {
  id: string;
  name: string;
  zone: {
    id: string;
    name: string;
    building: string;
    floor: string;
  };
  type: 'daily' | 'deep' | 'spot' | 'emergency';
  status: TaskStatus;
  robot?: {
    id: string;
    name: string;
    type: string;
  };
  scheduledTime: string;
  startTime?: string;
  endTime?: string;
  progress: number;
  estimatedDuration: number;
  actualDuration?: number;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  createdBy: string;
  createdAt: string;
}

// 任务状态
type TaskStatus = 
  | 'pending'      // 待执行
  | 'assigned'     // 已分配
  | 'in_progress'  // 执行中
  | 'paused'       // 已暂停
  | 'completed'    // 已完成
  | 'failed'       // 失败
  | 'cancelled';   // 已取消

// 任务操作
type TaskAction = 
  | 'view'         // 查看详情
  | 'edit'         // 编辑
  | 'pause'        // 暂停
  | 'resume'       // 恢复
  | 'cancel'       // 取消
  | 'reassign'     // 重新分配
  | 'duplicate';   // 复制
```

### 3.2 任务筛选组件 (TaskFilter)

```typescript
interface TaskFilterProps {
  filters: TaskFilters;
  onChange: (filters: TaskFilters) => void;
  onReset: () => void;
}

interface TaskFilters {
  buildingId?: string;
  floorId?: string;
  zoneId?: string;
  status?: TaskStatus[];
  type?: string[];
  robotId?: string;
  dateRange?: [string, string];
  priority?: string[];
  keyword?: string;
}

// 筛选选项配置
const filterOptions = {
  status: [
    { value: 'pending', label: '待执行', color: 'gray' },
    { value: 'assigned', label: '已分配', color: 'blue' },
    { value: 'in_progress', label: '执行中', color: 'green' },
    { value: 'paused', label: '已暂停', color: 'orange' },
    { value: 'completed', label: '已完成', color: 'success' },
    { value: 'failed', label: '失败', color: 'red' },
    { value: 'cancelled', label: '已取消', color: 'gray' }
  ],
  type: [
    { value: 'daily', label: '日常清洁' },
    { value: 'deep', label: '深度清洁' },
    { value: 'spot', label: '定点清洁' },
    { value: 'emergency', label: '紧急清洁' }
  ],
  priority: [
    { value: 'low', label: '低' },
    { value: 'normal', label: '普通' },
    { value: 'high', label: '高' },
    { value: 'urgent', label: '紧急' }
  ]
};
```

### 3.3 任务创建弹窗 (TaskCreateModal)

```typescript
interface TaskCreateModalProps {
  visible: boolean;
  template?: TaskTemplate;
  onSubmit: (task: CreateTaskRequest) => Promise<void>;
  onCancel: () => void;
}

interface CreateTaskRequest {
  name: string;
  zoneId: string;
  type: string;
  priority: string;
  scheduledTime: string;
  estimatedDuration: number;
  cleaningMode?: string;
  robotId?: string;           // 指定机器人（可选）
  robotType?: string;         // 指定机器人类型
  repeatConfig?: RepeatConfig; // 重复配置
  description?: string;
}

interface RepeatConfig {
  enabled: boolean;
  frequency: 'daily' | 'weekly' | 'monthly';
  daysOfWeek?: number[];      // 周几 [1,2,3,4,5]
  daysOfMonth?: number[];     // 几号 [1,15]
  endDate?: string;           // 结束日期
  maxOccurrences?: number;    // 最大执行次数
}
```

**创建表单布局**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  新建清洁任务                                                        [×]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  基本信息                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 任务名称*     [                                                   ] │   │
│  │ 清洁区域*     [楼宇▼] [楼层▼] [区域▼]                              │   │
│  │ 任务类型*     ○日常清洁 ○深度清洁 ○定点清洁 ○紧急清洁              │   │
│  │ 优先级        ○低 ●普通 ○高 ○紧急                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  执行配置                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 计划时间*     [2026-01-20] [08:00]                                  │   │
│  │ 预计时长      [30] 分钟                                             │   │
│  │ 清洁模式      [标准模式▼]                                           │   │
│  │ 指定机器人    [自动分配▼] 或 [选择机器人...]                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  重复设置                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [✓] 设为周期任务                                                    │   │
│  │ 重复频率      ○每天 ●每周 ○每月                                     │   │
│  │ 重复日        [✓]周一 [✓]周二 [✓]周三 [✓]周四 [✓]周五 [ ]周六 [ ]周日│   │
│  │ 结束时间      ○永不 ●指定日期 [2026-06-30] ○执行[10]次后            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  备注                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [                                                                   ] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                                              [取消]  [保存为模板]  [创建]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 任务详情侧边栏 (TaskDetailDrawer)

```typescript
interface TaskDetailDrawerProps {
  visible: boolean;
  taskId: string;
  onClose: () => void;
  onAction: (action: TaskAction) => void;
}

interface TaskDetail extends Task {
  // 执行详情
  execution?: {
    startTime: string;
    endTime?: string;
    route: RoutePoint[];
    coverage: number;
    cleanedArea: number;
    totalArea: number;
  };
  // 机器人状态
  robotStatus?: {
    battery: number;
    position: { x: number; y: number };
    speed: number;
    currentAction: string;
  };
  // 异常记录
  anomalies?: {
    time: string;
    type: string;
    description: string;
    resolved: boolean;
  }[];
  // 操作日志
  logs?: {
    time: string;
    action: string;
    operator: string;
    detail: string;
  }[];
}
```

**详情布局**：

```
┌─────────────────────────────────────────────────────────────────┐
│  任务详情                                              [×]      │
├─────────────────────────────────────────────────────────────────┤
│  T-001 A栋1F大堂日常清洁                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 状态: [执行中] ████████████░░░░ 65%                       │  │
│  │ 开始: 08:00:00  预计完成: 08:35:00                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [暂停任务] [取消任务] [重新分配]                               │
├─────────────────────────────────────────────────────────────────┤
│  基本信息                                                       │
│  ├─ 区域: A栋 1层 大堂区域                                      │
│  ├─ 类型: 日常清洁                                              │
│  ├─ 优先级: 普通                                                │
│  ├─ 计划时间: 2026-01-20 08:00                                  │
│  ├─ 预计时长: 35分钟                                            │
│  └─ 创建人: 张经理 @ 2026-01-19 18:00                           │
├─────────────────────────────────────────────────────────────────┤
│  执行机器人                                                     │
│  ├─ 机器人: GX-001 (高仙X100)                                   │
│  ├─ 电量: 78%                                                   │
│  ├─ 当前动作: 清洁中                                            │
│  └─ [查看机器人详情]                                            │
├─────────────────────────────────────────────────────────────────┤
│  执行进度                                                       │
│  ├─ 已清洁面积: 420㎡ / 650㎡                                   │
│  ├─ 覆盖率: 64.6%                                               │
│  └─ [查看清洁轨迹地图]                                          │
├─────────────────────────────────────────────────────────────────┤
│  操作日志                                                       │
│  ├─ 08:00:15 任务开始执行                                       │
│  ├─ 08:05:22 机器人到达起点                                     │
│  ├─ 08:15:33 清洁进度25%                                        │
│  └─ ...                                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 排程管理组件 (ScheduleManager)

```typescript
interface ScheduleManagerProps {
  schedules: CleaningSchedule[];
  onEdit: (scheduleId: string) => void;
  onToggle: (scheduleId: string, enabled: boolean) => void;
  onDelete: (scheduleId: string) => void;
  onCreate: () => void;
}

interface CleaningSchedule {
  id: string;
  name: string;
  zone: Zone;
  type: string;
  frequency: string;
  scheduledTime: string;
  daysOfWeek?: number[];
  enabled: boolean;
  nextExecution: string;
  lastExecution?: string;
  lastStatus?: 'success' | 'failed';
  createdBy: string;
  createdAt: string;
  taskCount: number;  // 已生成的任务数
}
```

**排程列表布局**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  排程列表                                                   [+ 新建排程]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 排程名称      | 区域         | 频率      | 时间  | 状态  | 下次执行 | 操作│ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ A栋大堂日常   | A栋1F大堂    | 每天      | 08:00 | ●启用 | 明天08:00| ⋮  │ │
│ │ A栋走廊工作日 | A栋全楼走廊  | 周一至周五 | 09:00 | ●启用 | 周一09:00| ⋮  │ │
│ │ B栋深度清洁   | B栋全部      | 每周六    | 06:00 | ○禁用 | --       | ⋮  │ │
│ │ 会议室清洁    | A栋3F会议室  | 每天      | 18:00 | ●启用 | 今天18:00| ⋮  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、数据流设计

### 4.1 状态管理

```typescript
// Task Store (Zustand)
interface TaskStore {
  // 状态
  tasks: Task[];
  selectedTask: Task | null;
  filters: TaskFilters;
  pagination: PaginationConfig;
  loading: boolean;
  error: string | null;
  
  // 今日统计
  todayStats: {
    pending: number;
    inProgress: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
  
  // Actions
  fetchTasks: (filters?: TaskFilters) => Promise<void>;
  fetchTaskDetail: (taskId: string) => Promise<void>;
  createTask: (task: CreateTaskRequest) => Promise<void>;
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<void>;
  cancelTask: (taskId: string, reason: string) => Promise<void>;
  pauseTask: (taskId: string) => Promise<void>;
  resumeTask: (taskId: string) => Promise<void>;
  reassignTask: (taskId: string, robotId: string) => Promise<void>;
  
  // 筛选
  setFilters: (filters: TaskFilters) => void;
  resetFilters: () => void;
  
  // 分页
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
}

// Schedule Store
interface ScheduleStore {
  schedules: CleaningSchedule[];
  loading: boolean;
  
  fetchSchedules: () => Promise<void>;
  createSchedule: (schedule: CreateScheduleRequest) => Promise<void>;
  updateSchedule: (id: string, updates: Partial<CleaningSchedule>) => Promise<void>;
  deleteSchedule: (id: string) => Promise<void>;
  toggleSchedule: (id: string, enabled: boolean) => Promise<void>;
}
```

### 4.2 API调用

```typescript
// Task API
const taskApi = {
  // 获取任务列表
  getTasks: (params: TaskQueryParams): Promise<PaginatedResponse<Task>> =>
    api.get('/api/v1/tasks', { params }),
  
  // 获取任务详情
  getTaskDetail: (taskId: string): Promise<Task> =>
    api.get(`/api/v1/tasks/${taskId}`),
  
  // 创建任务
  createTask: (task: CreateTaskRequest): Promise<Task> =>
    api.post('/api/v1/tasks', task),
  
  // 更新任务
  updateTask: (taskId: string, updates: Partial<Task>): Promise<Task> =>
    api.patch(`/api/v1/tasks/${taskId}`, updates),
  
  // 取消任务
  cancelTask: (taskId: string, reason: string): Promise<void> =>
    api.post(`/api/v1/tasks/${taskId}/cancel`, { reason }),
  
  // 暂停任务
  pauseTask: (taskId: string): Promise<void> =>
    api.post(`/api/v1/tasks/${taskId}/pause`),
  
  // 恢复任务
  resumeTask: (taskId: string): Promise<void> =>
    api.post(`/api/v1/tasks/${taskId}/resume`),
  
  // 重新分配
  reassignTask: (taskId: string, robotId: string): Promise<void> =>
    api.post(`/api/v1/tasks/${taskId}/reassign`, { robot_id: robotId }),
  
  // 获取今日统计
  getTodayStats: (): Promise<TaskStats> =>
    api.get('/api/v1/tasks/stats/today'),
};

// Schedule API
const scheduleApi = {
  getSchedules: (): Promise<CleaningSchedule[]> =>
    api.get('/api/v1/schedules'),
  
  createSchedule: (schedule: CreateScheduleRequest): Promise<CleaningSchedule> =>
    api.post('/api/v1/schedules', schedule),
  
  updateSchedule: (id: string, updates: Partial<CleaningSchedule>): Promise<CleaningSchedule> =>
    api.patch(`/api/v1/schedules/${id}`, updates),
  
  deleteSchedule: (id: string): Promise<void> =>
    api.delete(`/api/v1/schedules/${id}`),
  
  toggleSchedule: (id: string, enabled: boolean): Promise<void> =>
    api.post(`/api/v1/schedules/${id}/toggle`, { enabled }),
};
```

### 4.3 实时更新

```typescript
// WebSocket订阅任务状态更新
const useTaskUpdates = () => {
  const updateTask = useTaskStore(state => state.updateTaskInList);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/tasks/updates`);
    
    ws.onmessage = (event) => {
      const update: TaskUpdate = JSON.parse(event.data);
      
      switch (update.type) {
        case 'task.status_changed':
          updateTask(update.taskId, { status: update.status });
          break;
        case 'task.progress_updated':
          updateTask(update.taskId, { progress: update.progress });
          break;
        case 'task.completed':
          updateTask(update.taskId, { 
            status: 'completed',
            progress: 100,
            endTime: update.endTime 
          });
          break;
        case 'task.failed':
          updateTask(update.taskId, {
            status: 'failed',
            error: update.error
          });
          break;
      }
    };
    
    return () => ws.close();
  }, []);
};
```

---

## 五、交互设计

### 5.1 任务操作流程

**创建任务**：
```
点击[新建任务] → 弹出创建弹窗 → 填写表单 → 验证 → 提交 → 成功提示 → 刷新列表
                      ↓
              可选：保存为模板
```

**干预任务**：
```
正在执行的任务 → 点击[暂停] → 确认弹窗 → 调用API → 状态变更 → UI更新
                    ↓
              点击[恢复] → 继续执行

异常任务 → 点击[重新分配] → 选择机器人弹窗 → 确认 → 新机器人接管
```

**取消任务**：
```
任务列表/详情 → 点击[取消] → 输入取消原因 → 确认 → 任务取消 → 通知相关人员
```

### 5.2 批量操作

```typescript
interface BatchOperationProps {
  selectedIds: string[];
  onBatchCancel: (ids: string[], reason: string) => void;
  onBatchReassign: (ids: string[], robotId: string) => void;
  onBatchDelete: (ids: string[]) => void;
}

// 批量操作菜单
const batchOperations = [
  { key: 'cancel', label: '批量取消', icon: 'stop', danger: true },
  { key: 'reassign', label: '批量重新分配', icon: 'swap' },
  { key: 'export', label: '导出选中', icon: 'download' },
  { key: 'delete', label: '批量删除', icon: 'delete', danger: true }
];
```

### 5.3 快捷操作

| 快捷键 | 操作 |
|-------|------|
| `N` | 新建任务 |
| `R` | 刷新列表 |
| `F` | 聚焦搜索框 |
| `Esc` | 关闭弹窗/侧边栏 |
| `Enter` | 查看选中任务详情 |

---

## 六、测试要求

### 6.1 单元测试

```typescript
describe('TaskList', () => {
  it('应正确渲染任务列表', () => {
    const tasks = mockTasks(10);
    render(<TaskList tasks={tasks} {...defaultProps} />);
    expect(screen.getAllByRole('row')).toHaveLength(11); // header + 10 rows
  });

  it('应支持选择任务', () => {
    const onSelectionChange = jest.fn();
    render(<TaskList {...defaultProps} onSelectionChange={onSelectionChange} />);
    fireEvent.click(screen.getAllByRole('checkbox')[1]);
    expect(onSelectionChange).toHaveBeenCalledWith(['task-1']);
  });

  it('应正确显示任务状态标签', () => {
    const task = mockTask({ status: 'in_progress' });
    render(<TaskList tasks={[task]} {...defaultProps} />);
    expect(screen.getByText('执行中')).toBeInTheDocument();
  });
});

describe('TaskCreateModal', () => {
  it('应验证必填字段', async () => {
    render(<TaskCreateModal visible={true} {...defaultProps} />);
    fireEvent.click(screen.getByText('创建'));
    expect(await screen.findByText('请输入任务名称')).toBeInTheDocument();
  });

  it('应正确提交任务创建', async () => {
    const onSubmit = jest.fn().mockResolvedValue({});
    render(<TaskCreateModal visible={true} onSubmit={onSubmit} {...defaultProps} />);
    
    // 填写表单
    fireEvent.change(screen.getByLabelText('任务名称'), { target: { value: '测试任务' } });
    // ... 其他字段
    
    fireEvent.click(screen.getByText('创建'));
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
  });
});

describe('TaskFilter', () => {
  it('应触发筛选回调', () => {
    const onChange = jest.fn();
    render(<TaskFilter filters={{}} onChange={onChange} onReset={() => {}} />);
    
    fireEvent.click(screen.getByText('待执行'));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({
      status: ['pending']
    }));
  });
});
```

### 6.2 集成测试

```typescript
describe('TaskManagement Integration', () => {
  it('完整的任务创建流程', async () => {
    // 1. 渲染页面
    render(<TaskManagement />);
    
    // 2. 点击新建
    fireEvent.click(screen.getByText('新建任务'));
    
    // 3. 填写表单并提交
    // ...
    
    // 4. 验证任务出现在列表中
    await waitFor(() => {
      expect(screen.getByText('测试任务')).toBeInTheDocument();
    });
  });

  it('任务状态实时更新', async () => {
    // 模拟WebSocket消息
    mockWebSocket.emit('task.status_changed', {
      taskId: 'task-1',
      status: 'completed'
    });
    
    await waitFor(() => {
      expect(screen.getByText('已完成')).toBeInTheDocument();
    });
  });
});
```

---

## 七、验收标准

### 7.1 功能验收

| 验收项 | 标准 |
|-------|------|
| 任务列表 | 正确显示任务列表，支持分页、排序、筛选 |
| 任务创建 | 可创建即时任务和周期任务 |
| 任务详情 | 显示完整的任务信息和执行进度 |
| 任务干预 | 可暂停、恢复、取消、重新分配任务 |
| 排程管理 | 可创建、编辑、启用/禁用排程 |
| 实时更新 | 任务状态变更实时反映在UI上 |

### 7.2 性能要求

| 指标 | 要求 |
|-----|------|
| 列表加载 | < 500ms |
| 创建响应 | < 1s |
| 状态更新延迟 | < 2s |
| 筛选响应 | < 300ms |

### 7.3 交互要求

| 要求 | 说明 |
|-----|------|
| 操作反馈 | 所有操作有即时反馈（loading、成功、失败） |
| 确认机制 | 危险操作需二次确认 |
| 错误处理 | 友好的错误提示，支持重试 |
| 键盘支持 | 支持常用快捷键 |

---

## 八、文件结构

```
src/pages/operations/task-management/
├── index.tsx                    # 主页面
├── TaskManagement.module.css    # 样式
├── components/
│   ├── TaskList/
│   │   ├── index.tsx
│   │   ├── TaskList.module.css
│   │   └── TaskStatusTag.tsx
│   ├── TaskFilter/
│   │   ├── index.tsx
│   │   └── TaskFilter.module.css
│   ├── TaskCreateModal/
│   │   ├── index.tsx
│   │   ├── TaskForm.tsx
│   │   └── RepeatConfigForm.tsx
│   ├── TaskDetailDrawer/
│   │   ├── index.tsx
│   │   ├── ExecutionProgress.tsx
│   │   └── TaskLogs.tsx
│   ├── ScheduleManager/
│   │   ├── index.tsx
│   │   └── ScheduleEditModal.tsx
│   └── TaskTemplates/
│       ├── index.tsx
│       └── TemplateCard.tsx
├── hooks/
│   ├── useTaskList.ts
│   ├── useTaskDetail.ts
│   ├── useSchedules.ts
│   └── useTaskUpdates.ts
├── stores/
│   ├── taskStore.ts
│   └── scheduleStore.ts
└── __tests__/
    ├── TaskList.test.tsx
    ├── TaskCreateModal.test.tsx
    └── integration.test.tsx
```

---

**规格书结束**
