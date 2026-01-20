# O3 机器人监控界面规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | O3 |
| 模块名称 | 机器人监控界面 (Robot Monitoring) |
| 版本 | 1.0 |
| 日期 | 2026-01-20 |
| 状态 | 规划中 |
| 所属终端 | 运营控制台 (Operations Console) |
| 前置依赖 | G4-robot-api, G6-data-api, T4-robot-map |

---

## 一、模块概述

### 1.1 职责描述

机器人监控界面为运营经理提供机器人车队的实时监控和管理能力，包括状态总览、实时位置、健康状况、远程控制和维护管理。

### 1.2 核心功能

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 车队总览 | 所有机器人的状态概览 | P0 |
| 实时监控 | 单个机器人的详细实时状态 | P0 |
| 地图定位 | 在地图上查看机器人位置 | P0 |
| 远程控制 | 远程启动、停止、召回机器人 | P1 |
| 健康管理 | 查看耗材状态、安排维护 | P1 |
| 历史数据 | 机器人历史运行数据分析 | P2 |
| 告警管理 | 机器人相关告警处理 | P1 |

### 1.3 用户角色

| 角色 | 权限 | 使用场景 |
|-----|------|---------|
| 运营经理 | 全部功能 | 车队管理、决策 |
| 运营专员 | 查看+基础控制 | 日常监控、简单处理 |
| 维护人员 | 查看+维护相关 | 维护计划、耗材更换 |

---

## 二、页面结构

### 2.1 主页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [机器人监控]                                                      [刷新]   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 车队概览                                                              │  │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │  │
│  │ │ 总数    │ │ 在线    │ │ 工作中  │ │ 空闲    │ │ 异常    │          │  │
│  │ │  15     │ │  13     │ │   8     │ │   5     │ │   2     │          │  │
│  │ │ 台      │ │ ●在线   │ │ ●工作   │ │ ○空闲   │ │ ●异常   │          │  │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┐ ┌──────────────────────────────────────┐  │
│  │ 机器人列表                   │ │ 实时地图                             │  │
│  │ [品牌▼] [状态▼] [楼宇▼]     │ │ ┌────────────────────────────────┐  │  │
│  │ [搜索...]                    │ │ │                                │  │  │
│  │ ┌────────────────────────┐  │ │ │    ◉GX-001(工作中)            │  │  │
│  │ │ ◉ GX-001              │  │ │ │        ○GX-002(空闲)          │  │  │
│  │ │   高仙X100 | A栋1F     │  │ │ │                                │  │  │
│  │ │   🔋78% | 工作中       │  │ │ │            ⚠GX-003(异常)     │  │  │
│  │ ├────────────────────────┤  │ │ │                                │  │  │
│  │ │ ○ GX-002              │  │ │ │   ○EC-001(空闲)               │  │  │
│  │ │   高仙X100 | A栋2F     │  │ │ │                                │  │  │
│  │ │   🔋95% | 空闲         │  │ │ └────────────────────────────────┘  │  │
│  │ ├────────────────────────┤  │ │ [A栋▼] [1F▼]        [放大] [缩小]  │  │
│  │ │ ⚠ GX-003              │  │ └──────────────────────────────────────┘  │
│  │ │   高仙X100 | B栋1F     │  │                                          │
│  │ │   🔋45% | 异常-卡住    │  │                                          │
│  │ └────────────────────────┘  │                                          │
│  │ 显示 13/15 台                │                                          │
│  └──────────────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 机器人详情面板

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GX-001 详情                                                         [×]    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  高仙 X100 商用清洁机器人                                           │   │
│  │  ┌──────────────────┐  基本信息                                     │   │
│  │  │                  │  ├─ 编号: GX-001                              │   │
│  │  │   [机器人图片]   │  ├─ 品牌: 高仙 (Gaussian)                     │   │
│  │  │                  │  ├─ 型号: X100                                │   │
│  │  └──────────────────┘  ├─ 位置: A栋 1层 大堂                        │   │
│  │                        └─ IP: 192.168.1.101                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [实时状态] [任务历史] [健康状况] [维护记录]                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  实时状态                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 运行状态                                                            │   │
│  │ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐            │   │
│  │ │ 状态      │ │ 电量      │ │ 速度      │ │ 运行时长  │            │   │
│  │ │ ●工作中   │ │ 🔋78%    │ │ 0.8m/s   │ │ 1h 25min │            │   │
│  │ └───────────┘ └───────────┘ └───────────┘ └───────────┘            │   │
│  │                                                                     │   │
│  │ 当前任务: T-001 A栋1F大堂日常清洁                                   │   │
│  │ 进度: ████████████░░░░ 65%                                         │   │
│  │ 预计完成: 08:35                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  快速操作                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [暂停任务] [停止并返回] [紧急停止] [查看轨迹]                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  实时位置                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [小地图显示机器人当前位置和清洁轨迹]                                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、组件定义

### 3.1 车队概览组件 (FleetOverview)

```typescript
interface FleetOverviewProps {
  stats: FleetStats;
  onStatClick: (status: RobotStatus) => void;
}

interface FleetStats {
  total: number;
  online: number;
  offline: number;
  working: number;
  idle: number;
  charging: number;
  error: number;
  maintenance: number;
}

// 状态配置
const statusConfig = {
  total: { label: '总数', color: 'default', icon: 'robot' },
  online: { label: '在线', color: 'green', icon: 'check-circle' },
  working: { label: '工作中', color: 'blue', icon: 'play-circle' },
  idle: { label: '空闲', color: 'gray', icon: 'pause-circle' },
  charging: { label: '充电中', color: 'orange', icon: 'thunderbolt' },
  error: { label: '异常', color: 'red', icon: 'warning' },
  offline: { label: '离线', color: 'gray', icon: 'disconnect' }
};
```

### 3.2 机器人列表组件 (RobotList)

```typescript
interface RobotListProps {
  robots: Robot[];
  selectedId?: string;
  filters: RobotFilters;
  onSelect: (robotId: string) => void;
  onFilterChange: (filters: RobotFilters) => void;
}

interface Robot {
  id: string;
  name: string;
  brand: 'gaussian' | 'ecovacs' | 'other';
  model: string;
  serialNumber: string;
  status: RobotStatus;
  battery: number;
  location: {
    buildingId: string;
    buildingName: string;
    floorId: string;
    floorName: string;
    zoneName?: string;
    position?: { x: number; y: number };
  };
  currentTask?: {
    id: string;
    name: string;
    progress: number;
  };
  lastSeen: string;
  error?: {
    code: string;
    message: string;
  };
}

type RobotStatus = 
  | 'online'      // 在线空闲
  | 'working'     // 工作中
  | 'charging'    // 充电中
  | 'paused'      // 已暂停
  | 'error'       // 异常
  | 'maintenance' // 维护中
  | 'offline';    // 离线

interface RobotFilters {
  brand?: string[];
  status?: RobotStatus[];
  buildingId?: string;
  floorId?: string;
  keyword?: string;
}
```

### 3.3 机器人卡片组件 (RobotCard)

```typescript
interface RobotCardProps {
  robot: Robot;
  selected: boolean;
  onClick: () => void;
}

// 卡片显示内容
const RobotCard: React.FC<RobotCardProps> = ({ robot, selected, onClick }) => {
  return (
    <div className={`robot-card ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="robot-header">
        <StatusIndicator status={robot.status} />
        <span className="robot-name">{robot.name}</span>
      </div>
      <div className="robot-info">
        <span className="robot-model">{robot.brand} {robot.model}</span>
        <span className="robot-location">{robot.location.buildingName} {robot.location.floorName}</span>
      </div>
      <div className="robot-status">
        <BatteryIndicator level={robot.battery} />
        <StatusLabel status={robot.status} error={robot.error} />
      </div>
      {robot.currentTask && (
        <div className="robot-task">
          <ProgressBar progress={robot.currentTask.progress} />
        </div>
      )}
    </div>
  );
};
```

### 3.4 机器人详情组件 (RobotDetail)

```typescript
interface RobotDetailProps {
  robotId: string;
  onClose: () => void;
  onAction: (action: RobotAction) => void;
}

interface RobotDetailData extends Robot {
  // 详细状态
  detailedStatus: {
    speed: number;
    runTime: number;
    totalRunTime: number;
    distanceTraveled: number;
    areaCleaned: number;
  };
  // 传感器数据
  sensors: {
    lidar: 'normal' | 'error';
    camera: 'normal' | 'error';
    ultrasonic: 'normal' | 'error';
    cliff: 'normal' | 'error';
    bumper: 'normal' | 'error';
  };
  // 耗材状态
  consumables: {
    mainBrush: { remaining: number; total: number };
    sideBrush: { remaining: number; total: number };
    filter: { remaining: number; total: number };
    mop: { remaining: number; total: number };
    cleanWater: { remaining: number; total: number };
    dirtyWater: { remaining: number; total: number };
  };
  // 网络信息
  network: {
    ip: string;
    mac: string;
    rssi: number;
    protocol: string;
  };
}

type RobotAction = 
  | 'start'         // 开始任务
  | 'pause'         // 暂停
  | 'resume'        // 恢复
  | 'stop'          // 停止
  | 'return_home'   // 返回充电桩
  | 'emergency_stop' // 紧急停止
  | 'reboot'        // 重启
  | 'locate';       // 定位（闪灯/发声）
```

### 3.5 实时地图组件 (RobotMapView)

```typescript
interface RobotMapViewProps {
  robots: Robot[];
  selectedRobotId?: string;
  buildingId: string;
  floorId: string;
  onRobotClick: (robotId: string) => void;
  onBuildingChange: (buildingId: string) => void;
  onFloorChange: (floorId: string) => void;
}

// 复用T4-robot-map的地图组件
// 添加运营控制台特有的功能：
// - 点击机器人显示快捷操作菜单
// - 显示所有机器人的实时位置
// - 支持轨迹回放
```

### 3.6 健康状况面板 (HealthPanel)

```typescript
interface HealthPanelProps {
  robotId: string;
  consumables: RobotDetailData['consumables'];
  sensors: RobotDetailData['sensors'];
  onScheduleMaintenance: () => void;
}

// 耗材状态显示
const ConsumableItem: React.FC<{ 
  name: string; 
  remaining: number; 
  total: number; 
}> = ({ name, remaining, total }) => {
  const percentage = (remaining / total) * 100;
  const status = percentage > 30 ? 'normal' : percentage > 10 ? 'warning' : 'critical';
  
  return (
    <div className={`consumable-item ${status}`}>
      <span className="consumable-name">{name}</span>
      <Progress percent={percentage} status={status} />
      <span className="consumable-value">{remaining}h / {total}h</span>
    </div>
  );
};
```

**健康状况面板布局**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 健康状况                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 传感器状态                                                                  │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                │
│ │ 激光雷达│ │ 摄像头  │ │ 超声波  │ │ 防跌落  │ │ 碰撞    │                │
│ │ ●正常  │ │ ●正常  │ │ ●正常  │ │ ●正常  │ │ ●正常  │                │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 耗材状态                                                    [安排维护]      │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ 主刷      ████████████████░░░░ 80%  剩余约 160h                         ││
│ │ 边刷      ████████████░░░░░░░░ 60%  剩余约 120h                         ││
│ │ 滤网      ████████░░░░░░░░░░░░ 40%  剩余约 80h   ⚠ 建议更换             ││
│ │ 拖布      ██████░░░░░░░░░░░░░░ 30%  剩余约 60h   ⚠ 建议更换             ││
│ │ 清水箱    █████████████████░░░ 85%                                       ││
│ │ 污水箱    ███████████░░░░░░░░░ 55%  (需清空)                             ││
│ └─────────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ 维护提醒                                                                    │
│ • 滤网剩余寿命不足50%，建议安排更换                                         │
│ • 拖布剩余寿命不足50%，建议安排更换                                         │
│ • 上次深度保养: 30天前，建议进行深度保养                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.7 远程控制面板 (ControlPanel)

```typescript
interface ControlPanelProps {
  robot: Robot;
  onAction: (action: RobotAction, params?: any) => Promise<void>;
}

// 控制按钮配置
const controlActions = [
  { 
    key: 'start', 
    label: '开始任务', 
    icon: 'play', 
    enabledStatus: ['online'], 
    type: 'primary' 
  },
  { 
    key: 'pause', 
    label: '暂停', 
    icon: 'pause', 
    enabledStatus: ['working'], 
    type: 'default' 
  },
  { 
    key: 'resume', 
    label: '恢复', 
    icon: 'play', 
    enabledStatus: ['paused'], 
    type: 'primary' 
  },
  { 
    key: 'stop', 
    label: '停止', 
    icon: 'stop', 
    enabledStatus: ['working', 'paused'], 
    type: 'default' 
  },
  { 
    key: 'return_home', 
    label: '返回充电', 
    icon: 'home', 
    enabledStatus: ['online', 'paused'], 
    type: 'default' 
  },
  { 
    key: 'emergency_stop', 
    label: '紧急停止', 
    icon: 'warning', 
    enabledStatus: ['working', 'paused', 'online'], 
    type: 'danger' 
  },
  { 
    key: 'locate', 
    label: '定位', 
    icon: 'aim', 
    enabledStatus: ['online', 'working', 'paused'], 
    type: 'default' 
  }
];
```

---

## 四、数据流设计

### 4.1 状态管理

```typescript
// Robot Store (Zustand)
interface RobotStore {
  // 状态
  robots: Robot[];
  selectedRobotId: string | null;
  robotDetail: RobotDetailData | null;
  filters: RobotFilters;
  loading: boolean;
  error: string | null;
  
  // 车队统计
  fleetStats: FleetStats;
  
  // 地图状态
  mapConfig: {
    buildingId: string;
    floorId: string;
    zoom: number;
  };
  
  // Actions
  fetchRobots: () => Promise<void>;
  fetchRobotDetail: (robotId: string) => Promise<void>;
  selectRobot: (robotId: string | null) => void;
  
  // 控制操作
  controlRobot: (robotId: string, action: RobotAction) => Promise<void>;
  
  // 筛选
  setFilters: (filters: RobotFilters) => void;
  
  // 地图
  setMapConfig: (config: Partial<typeof mapConfig>) => void;
  
  // 实时更新
  updateRobotStatus: (robotId: string, status: Partial<Robot>) => void;
}

// 初始化store
const useRobotStore = create<RobotStore>((set, get) => ({
  robots: [],
  selectedRobotId: null,
  robotDetail: null,
  filters: {},
  loading: false,
  error: null,
  fleetStats: { total: 0, online: 0, offline: 0, working: 0, idle: 0, charging: 0, error: 0, maintenance: 0 },
  mapConfig: { buildingId: '', floorId: '', zoom: 1 },
  
  fetchRobots: async () => {
    set({ loading: true });
    try {
      const { data } = await robotApi.getRobots(get().filters);
      set({ robots: data.robots, fleetStats: data.stats, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
  
  // ... 其他方法
}));
```

### 4.2 API调用

```typescript
const robotApi = {
  // 获取机器人列表
  getRobots: (filters?: RobotFilters): Promise<{ robots: Robot[]; stats: FleetStats }> =>
    api.get('/api/v1/robots', { params: filters }),
  
  // 获取机器人详情
  getRobotDetail: (robotId: string): Promise<RobotDetailData> =>
    api.get(`/api/v1/robots/${robotId}`),
  
  // 获取机器人实时状态
  getRobotStatus: (robotId: string): Promise<Robot> =>
    api.get(`/api/v1/robots/${robotId}/status`),
  
  // 控制机器人
  controlRobot: (robotId: string, action: RobotAction, params?: any): Promise<void> =>
    api.post(`/api/v1/robots/${robotId}/control`, { action, ...params }),
  
  // 获取机器人历史轨迹
  getRobotTrajectory: (robotId: string, params: { start: string; end: string }): Promise<TrajectoryData> =>
    api.get(`/api/v1/robots/${robotId}/trajectory`, { params }),
  
  // 获取机器人任务历史
  getRobotTasks: (robotId: string, params: PaginationParams): Promise<PaginatedResponse<Task>> =>
    api.get(`/api/v1/robots/${robotId}/tasks`, { params }),
  
  // 安排维护
  scheduleMaintenance: (robotId: string, maintenance: MaintenanceRequest): Promise<void> =>
    api.post(`/api/v1/robots/${robotId}/maintenance`, maintenance),
};
```

### 4.3 实时数据订阅

```typescript
// WebSocket订阅机器人状态
const useRobotUpdates = () => {
  const updateRobotStatus = useRobotStore(state => state.updateRobotStatus);
  const selectedRobotId = useRobotStore(state => state.selectedRobotId);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/robots/status`);
    
    ws.onmessage = (event) => {
      const update: RobotUpdate = JSON.parse(event.data);
      
      switch (update.type) {
        case 'robot.status_changed':
          updateRobotStatus(update.robotId, { status: update.status });
          break;
        case 'robot.position_updated':
          updateRobotStatus(update.robotId, { 
            location: { ...update.location, position: update.position } 
          });
          break;
        case 'robot.battery_changed':
          updateRobotStatus(update.robotId, { battery: update.battery });
          break;
        case 'robot.task_progress':
          updateRobotStatus(update.robotId, {
            currentTask: { ...update.task }
          });
          break;
        case 'robot.error':
          updateRobotStatus(update.robotId, {
            status: 'error',
            error: update.error
          });
          break;
      }
    };
    
    return () => ws.close();
  }, []);
  
  // 选中机器人时，订阅详细状态
  useEffect(() => {
    if (!selectedRobotId) return;
    
    const ws = new WebSocket(`${WS_BASE_URL}/robots/${selectedRobotId}/detail`);
    // 订阅更详细的状态更新（传感器、耗材等）
    
    return () => ws.close();
  }, [selectedRobotId]);
};
```

---

## 五、交互设计

### 5.1 机器人选择和查看

```
列表点击机器人 → 高亮选中 → 地图定位到该机器人 → 显示详情面板
                    ↓
              地图点击机器人 → 同样效果
```

### 5.2 远程控制流程

```
选中机器人 → 点击控制按钮 → 确认弹窗（危险操作） → 发送命令 → 显示执行状态
                                    ↓
                              等待机器人响应 → 更新状态
```

### 5.3 异常处理流程

```
检测到异常 → 列表/地图标红 → 点击查看详情 → 显示异常信息 
                                    ↓
                           [重试] [停止] [报修]
```

### 5.4 维护安排流程

```
查看健康状况 → 发现耗材不足 → 点击[安排维护] → 选择维护类型和时间 → 创建维护工单
```

---

## 六、测试要求

### 6.1 单元测试

```typescript
describe('FleetOverview', () => {
  it('应正确显示车队统计', () => {
    const stats: FleetStats = {
      total: 15, online: 13, offline: 2, working: 8, 
      idle: 5, charging: 0, error: 2, maintenance: 0
    };
    render(<FleetOverview stats={stats} onStatClick={() => {}} />);
    
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('在线')).toBeInTheDocument();
  });

  it('点击状态卡片应触发筛选', () => {
    const onStatClick = jest.fn();
    render(<FleetOverview stats={mockStats} onStatClick={onStatClick} />);
    
    fireEvent.click(screen.getByText('异常'));
    expect(onStatClick).toHaveBeenCalledWith('error');
  });
});

describe('RobotList', () => {
  it('应正确渲染机器人列表', () => {
    const robots = mockRobots(5);
    render(<RobotList robots={robots} {...defaultProps} />);
    expect(screen.getAllByTestId('robot-card')).toHaveLength(5);
  });

  it('应正确显示机器人状态', () => {
    const robot = mockRobot({ status: 'error', error: { code: 'E001', message: '卡住' } });
    render(<RobotList robots={[robot]} {...defaultProps} />);
    expect(screen.getByText('异常-卡住')).toBeInTheDocument();
  });
});

describe('ControlPanel', () => {
  it('应根据状态启用/禁用按钮', () => {
    const robot = mockRobot({ status: 'working' });
    render(<ControlPanel robot={robot} onAction={() => {}} />);
    
    expect(screen.getByText('暂停')).not.toBeDisabled();
    expect(screen.getByText('开始任务')).toBeDisabled();
  });

  it('危险操作应弹出确认框', async () => {
    const robot = mockRobot({ status: 'working' });
    render(<ControlPanel robot={robot} onAction={() => {}} />);
    
    fireEvent.click(screen.getByText('紧急停止'));
    expect(await screen.findByText('确认紧急停止？')).toBeInTheDocument();
  });
});
```

### 6.2 集成测试

```typescript
describe('RobotMonitoring Integration', () => {
  it('选中机器人应显示详情', async () => {
    render(<RobotMonitoring />);
    
    // 等待列表加载
    await waitFor(() => expect(screen.getByText('GX-001')).toBeInTheDocument());
    
    // 点击机器人
    fireEvent.click(screen.getByText('GX-001'));
    
    // 详情面板应显示
    await waitFor(() => expect(screen.getByText('高仙 X100')).toBeInTheDocument());
  });

  it('实时状态更新', async () => {
    render(<RobotMonitoring />);
    
    // 模拟WebSocket状态更新
    mockWebSocket.emit('robot.battery_changed', {
      robotId: 'GX-001',
      battery: 50
    });
    
    await waitFor(() => {
      expect(screen.getByText('50%')).toBeInTheDocument();
    });
  });

  it('远程控制流程', async () => {
    render(<RobotMonitoring />);
    
    // 选中机器人
    fireEvent.click(screen.getByText('GX-001'));
    
    // 点击暂停
    fireEvent.click(screen.getByText('暂停'));
    
    // 确认
    fireEvent.click(screen.getByText('确定'));
    
    // 验证API调用
    await waitFor(() => {
      expect(robotApi.controlRobot).toHaveBeenCalledWith('GX-001', 'pause');
    });
  });
});
```

---

## 七、验收标准

### 7.1 功能验收

| 验收项 | 标准 |
|-------|------|
| 车队总览 | 正确显示各状态机器人数量 |
| 机器人列表 | 正确显示机器人信息，支持筛选搜索 |
| 地图定位 | 正确在地图上显示机器人位置 |
| 实时状态 | 机器人状态变更实时更新（<2s） |
| 远程控制 | 可成功执行各控制命令 |
| 健康状况 | 正确显示耗材和传感器状态 |
| 维护管理 | 可创建维护工单 |

### 7.2 性能要求

| 指标 | 要求 |
|-----|------|
| 列表加载 | < 500ms |
| 详情加载 | < 300ms |
| 状态更新延迟 | < 2s |
| 控制命令响应 | < 3s |
| 地图渲染 | < 1s |

### 7.3 可靠性要求

| 要求 | 说明 |
|-----|------|
| 断线重连 | WebSocket断开后自动重连 |
| 状态同步 | 重连后同步最新状态 |
| 操作确认 | 危险操作需二次确认 |
| 错误处理 | 控制命令失败有明确提示 |

---

## 八、文件结构

```
src/pages/operations/robot-monitoring/
├── index.tsx                    # 主页面
├── RobotMonitoring.module.css   # 样式
├── components/
│   ├── FleetOverview/
│   │   └── index.tsx
│   ├── RobotList/
│   │   ├── index.tsx
│   │   ├── RobotCard.tsx
│   │   └── RobotFilter.tsx
│   ├── RobotDetail/
│   │   ├── index.tsx
│   │   ├── StatusTab.tsx
│   │   ├── TaskHistoryTab.tsx
│   │   ├── HealthTab.tsx
│   │   └── MaintenanceTab.tsx
│   ├── RobotMapView/
│   │   ├── index.tsx
│   │   └── RobotMarker.tsx
│   ├── ControlPanel/
│   │   ├── index.tsx
│   │   └── ControlButton.tsx
│   └── HealthPanel/
│       ├── index.tsx
│       ├── ConsumableItem.tsx
│       └── SensorStatus.tsx
├── hooks/
│   ├── useRobotList.ts
│   ├── useRobotDetail.ts
│   ├── useRobotUpdates.ts
│   └── useRobotControl.ts
├── stores/
│   └── robotStore.ts
└── __tests__/
    ├── FleetOverview.test.tsx
    ├── RobotList.test.tsx
    ├── ControlPanel.test.tsx
    └── integration.test.tsx
```

---

**规格书结束**
