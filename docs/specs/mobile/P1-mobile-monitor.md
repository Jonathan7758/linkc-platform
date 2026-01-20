# P1 移动端监控规格书

## 文档信息
- **模块ID**: P1
- **模块名称**: 移动端监控 (Mobile Monitor)
- **版本**: 1.0
- **日期**: 2026年1月
- **状态**: 规划中
- **前置依赖**: G4机器人API, G5 Agent API, O3机器人监控

---

## 1. 模块概述

### 1.1 职责描述

移动端监控是LinkC平台的移动端核心模块，为运营人员和管理者提供随时随地的机器人监控能力：
- 实时查看机器人状态和位置
- 接收关键事件推送通知
- 快速响应异常情况
- 远程控制机器人（紧急操作）
- 查看关键运营指标

### 1.2 核心功能

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 车队总览 | 所有机器人状态一览 | P0 |
| 实时位置 | 地图显示机器人位置 | P0 |
| 状态详情 | 单台机器人详细信息 | P0 |
| 推送通知 | 关键事件实时推送 | P0 |
| 远程控制 | 紧急停止/返回充电 | P0 |
| KPI概览 | 关键指标快速查看 | P1 |
| 历史轨迹 | 查看机器人运行轨迹 | P2 |

### 1.3 目标用户

| 角色 | 使用场景 | 关注重点 |
|-----|---------|---------|
| 现场运维 | 巡检时查看机器人状态 | 位置、异常、快速操作 |
| 运营经理 | 外出时监控运营 | 总览、异常、KPI |
| 高管 | 随时了解运营状态 | 健康度、关键指标 |
| 值班人员 | 夜间值守 | 异常告警、远程处理 |

### 1.4 设计原则

```
移动端设计原则：
├── 信息精简：只展示最关键信息
├── 操作简化：单手可完成常用操作
├── 离线可用：核心功能支持离线
├── 省电优化：后台运行不过度消耗电量
└── 快速响应：页面加载<2秒
```

---

## 2. 页面结构

### 2.1 应用架构

```
移动端监控App结构：
├── 首页（Dashboard）
│   ├── 健康度指示器
│   ├── 快速状态统计
│   ├── 异常摘要
│   └── 快捷入口
├── 车队（Fleet）
│   ├── 列表视图
│   ├── 地图视图
│   └── 筛选器
├── 机器人详情（Robot Detail）
│   ├── 基本信息
│   ├── 实时状态
│   ├── 控制面板
│   └── 历史记录
├── 通知中心（Notifications）
│   ├── 通知列表
│   ├── 通知详情
│   └── 通知设置
└── 设置（Settings）
    ├── 通知偏好
    ├── 账户管理
    └── 关于
```

### 2.2 导航结构

```typescript
// 底部导航配置
interface BottomNavigation {
  items: NavItem[];
}

interface NavItem {
  key: string;
  title: string;
  icon: string;
  activeIcon: string;
  badge?: number;        // 未读数量
  screen: string;
}

const bottomNav: BottomNavigation = {
  items: [
    {
      key: 'dashboard',
      title: '首页',
      icon: 'home-outline',
      activeIcon: 'home',
      screen: 'DashboardScreen'
    },
    {
      key: 'fleet',
      title: '车队',
      icon: 'robot-outline',
      activeIcon: 'robot',
      screen: 'FleetScreen'
    },
    {
      key: 'notifications',
      title: '通知',
      icon: 'bell-outline',
      activeIcon: 'bell',
      badge: 3,  // 动态未读数
      screen: 'NotificationsScreen'
    },
    {
      key: 'settings',
      title: '设置',
      icon: 'cog-outline',
      activeIcon: 'cog',
      screen: 'SettingsScreen'
    }
  ]
};
```

---

## 3. 首页组件

### 3.1 仪表盘页面

```typescript
// 首页数据接口
interface DashboardData {
  // 健康度
  healthScore: number;           // 0-100
  healthTrend: 'up' | 'down' | 'stable';
  
  // 快速统计
  stats: {
    total: number;               // 机器人总数
    working: number;             // 工作中
    idle: number;                // 空闲
    charging: number;            // 充电中
    error: number;               // 故障
    offline: number;             // 离线
  };
  
  // 今日摘要
  todaySummary: {
    tasksCompleted: number;      // 完成任务
    tasksTotal: number;          // 总任务
    coverageRate: number;        // 覆盖率
    efficiency: number;          // 效率指数
  };
  
  // 异常摘要
  alerts: {
    critical: number;            // 紧急
    warning: number;             // 警告
    info: number;                // 提示
  };
  
  // 最近异常
  recentAlerts: AlertSummary[];
  
  // 更新时间
  lastUpdated: string;
}

interface AlertSummary {
  id: string;
  robotId: string;
  robotName: string;
  type: AlertType;
  level: AlertLevel;
  message: string;
  timestamp: string;
}
```

### 3.2 健康度卡片

```typescript
// 健康度卡片组件
interface HealthScoreCardProps {
  score: number;
  trend: 'up' | 'down' | 'stable';
  onPress?: () => void;
}

// 健康度等级定义
const healthLevels = {
  excellent: { min: 90, color: '#52c41a', label: '优秀' },
  good: { min: 75, color: '#1890ff', label: '良好' },
  fair: { min: 60, color: '#faad14', label: '一般' },
  poor: { min: 0, color: '#ff4d4f', label: '较差' }
};

// 组件布局
/*
┌─────────────────────────────┐
│  运营健康度                  │
│  ┌─────────────────────┐    │
│  │                     │    │
│  │        85           │    │
│  │       良好 ↑        │    │
│  │                     │    │
│  └─────────────────────┘    │
│  较昨日 +2.3%               │
└─────────────────────────────┘
*/
```

### 3.3 快速统计卡片

```typescript
// 快速统计组件
interface QuickStatsProps {
  stats: DashboardData['stats'];
  onStatPress?: (stat: string) => void;
}

// 统计项配置
const statsConfig = [
  { key: 'working', label: '工作中', color: '#52c41a', icon: 'play-circle' },
  { key: 'idle', label: '空闲', color: '#1890ff', icon: 'pause-circle' },
  { key: 'charging', label: '充电', color: '#faad14', icon: 'battery-charging' },
  { key: 'error', label: '故障', color: '#ff4d4f', icon: 'alert-circle' },
  { key: 'offline', label: '离线', color: '#8c8c8c', icon: 'wifi-off' }
];

// 布局示例
/*
┌───────────────────────────────────────┐
│  机器人状态                   共 25 台 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
│  │  12 │ │  5  │ │  6  │ │  2  │     │
│  │工作中│ │空闲 │ │充电 │ │故障 │     │
│  └─────┘ └─────┘ └─────┘ └─────┘     │
└───────────────────────────────────────┘
*/
```

### 3.4 异常摘要卡片

```typescript
// 异常摘要组件
interface AlertSummaryCardProps {
  alerts: DashboardData['alerts'];
  recentAlerts: AlertSummary[];
  onViewAll?: () => void;
  onAlertPress?: (alert: AlertSummary) => void;
}

// 布局示例
/*
┌───────────────────────────────────────┐
│  待处理异常                    查看全部>│
│  ┌─────────────────────────────────┐  │
│  │ 🔴 2  │ 🟡 5  │ 🔵 3            │  │
│  │ 紧急   │ 警告   │ 提示            │  │
│  └─────────────────────────────────┘  │
│                                        │
│  ⚠️ R-005 清洁机器人卡住      2分钟前  │
│  ⚠️ R-012 电量过低警告        10分钟前 │
└───────────────────────────────────────┘
*/
```

---

## 4. 车队页面

### 4.1 车队列表视图

```typescript
// 车队列表Props
interface FleetListProps {
  robots: RobotSummary[];
  filter: FleetFilter;
  onFilterChange: (filter: FleetFilter) => void;
  onRobotPress: (robotId: string) => void;
  onRefresh: () => void;
  refreshing: boolean;
}

interface RobotSummary {
  id: string;
  name: string;
  model: string;
  brand: string;
  status: RobotStatus;
  battery: number;
  currentTask?: string;
  location?: {
    building: string;
    floor: string;
    zone?: string;
  };
  lastSeen: string;
  hasAlert: boolean;
  alertLevel?: AlertLevel;
}

interface FleetFilter {
  status?: RobotStatus[];
  building?: string;
  search?: string;
}

type RobotStatus = 
  | 'working'
  | 'idle'
  | 'charging'
  | 'error'
  | 'offline'
  | 'paused';
```

### 4.2 机器人列表项

```typescript
// 列表项组件
interface RobotListItemProps {
  robot: RobotSummary;
  onPress: () => void;
}

// 列表项布局
/*
┌───────────────────────────────────────┐
│ ┌────┐  R-005 清洁机器人-A            │
│ │ 🤖 │  高仙 · Vacuum Pro            │
│ │    │  ───────────────────────       │
│ └────┘  🟢 工作中 │ 🔋 85%           │
│         A栋 · 3F · 大堂               │
│         任务: 日常清洁-上午场次        │
│                              10:32 > │
└───────────────────────────────────────┘
*/

// 状态颜色映射
const statusColors: Record<RobotStatus, string> = {
  working: '#52c41a',
  idle: '#1890ff',
  charging: '#faad14',
  error: '#ff4d4f',
  offline: '#8c8c8c',
  paused: '#722ed1'
};

// 状态图标
const statusIcons: Record<RobotStatus, string> = {
  working: 'play-circle',
  idle: 'pause-circle',
  charging: 'battery-charging',
  error: 'alert-circle',
  offline: 'wifi-off',
  paused: 'pause'
};
```

### 4.3 筛选器组件

```typescript
// 筛选器组件
interface FleetFilterSheetProps {
  visible: boolean;
  filter: FleetFilter;
  buildings: Building[];
  onApply: (filter: FleetFilter) => void;
  onClose: () => void;
  onReset: () => void;
}

// 筛选器布局（底部Sheet）
/*
┌───────────────────────────────────────┐
│  筛选                          重置   │
│  ─────────────────────────────────    │
│  状态                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│  │工作中│ │空闲 │ │充电 │ │故障 │    │
│  └─────┘ └─────┘ └─────┘ └─────┘    │
│                                       │
│  楼宇                                 │
│  ┌─────────────────────────────┐     │
│  │ 全部楼宇                   ▼│     │
│  └─────────────────────────────┘     │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │           应用筛选              │ │
│  └─────────────────────────────────┘ │
└───────────────────────────────────────┘
*/
```

### 4.4 地图视图

```typescript
// 地图视图组件
interface FleetMapViewProps {
  robots: RobotSummary[];
  buildings: Building[];
  selectedBuilding?: string;
  selectedFloor?: string;
  onBuildingChange: (buildingId: string) => void;
  onFloorChange: (floorId: string) => void;
  onRobotPress: (robotId: string) => void;
}

// 地图状态
interface MapState {
  center: { x: number; y: number };
  zoom: number;
  selectedRobot?: string;
}

// 机器人标记
interface RobotMarker {
  id: string;
  position: { x: number; y: number };
  status: RobotStatus;
  heading: number;          // 朝向角度
  name: string;
}

// 地图布局
/*
┌───────────────────────────────────────┐
│ ┌─────────────┐  ┌─────────────┐     │
│ │ A栋 ▼      │  │ 3F ▼        │     │
│ └─────────────┘  └─────────────┘     │
├───────────────────────────────────────┤
│                                       │
│     ┌─────────────────────────┐      │
│     │                         │      │
│     │    🤖    楼层平面图     │      │
│     │  🤖   🤖               │      │
│     │           🤖            │      │
│     │                         │      │
│     └─────────────────────────┘      │
│                                       │
│        [ - ]  [ + ]                   │
└───────────────────────────────────────┘
*/
```

---

## 5. 机器人详情页

### 5.1 详情页结构

```typescript
// 详情页Props
interface RobotDetailScreenProps {
  robotId: string;
}

// 详情页数据
interface RobotDetailData {
  // 基本信息
  basic: {
    id: string;
    name: string;
    model: string;
    brand: string;
    serialNumber: string;
    firmwareVersion: string;
    registeredAt: string;
  };
  
  // 实时状态
  status: {
    state: RobotStatus;
    battery: number;
    isCharging: boolean;
    position: Position;
    heading: number;
    speed: number;
    currentTask?: TaskInfo;
    errors: ErrorInfo[];
  };
  
  // 今日统计
  todayStats: {
    workTime: number;           // 分钟
    distance: number;           // 米
    coverage: number;           // 平方米
    tasksCompleted: number;
    efficiency: number;
  };
  
  // 耗材状态
  consumables: ConsumableStatus[];
  
  // 最近活动
  recentActivities: Activity[];
}

interface Position {
  building: string;
  buildingName: string;
  floor: string;
  floorName: string;
  zone?: string;
  zoneName?: string;
  x: number;
  y: number;
}
```

### 5.2 状态信息卡片

```typescript
// 状态卡片组件
interface StatusCardProps {
  status: RobotDetailData['status'];
  onControlPress: () => void;
}

// 状态卡片布局
/*
┌───────────────────────────────────────┐
│  实时状态                             │
│  ────────────────────────────────     │
│  ┌────────────────────────────────┐   │
│  │  🟢 工作中                     │   │
│  │  ─────────────────────────     │   │
│  │  🔋 85%  │  📍 A栋 3F 大堂     │   │
│  │  ⏱️ 工作 45分钟               │   │
│  └────────────────────────────────┘   │
│                                       │
│  当前任务                             │
│  日常清洁-上午场次 · 进度 67%         │
│  ██████████░░░░░░                     │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │         打开控制面板            │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
*/
```

### 5.3 控制面板

```typescript
// 控制面板组件（底部Sheet）
interface ControlPanelProps {
  visible: boolean;
  robot: RobotDetailData;
  onClose: () => void;
  onCommand: (command: RobotCommand) => Promise<void>;
}

type RobotCommand = 
  | { type: 'start' }
  | { type: 'pause' }
  | { type: 'resume' }
  | { type: 'stop' }
  | { type: 'return_home' }
  | { type: 'emergency_stop' }
  | { type: 'locate' };

// 控制按钮配置
interface ControlButton {
  command: RobotCommand['type'];
  label: string;
  icon: string;
  color: string;
  confirmRequired: boolean;
  confirmMessage?: string;
  availableStates: RobotStatus[];
}

const controlButtons: ControlButton[] = [
  {
    command: 'pause',
    label: '暂停',
    icon: 'pause',
    color: '#faad14',
    confirmRequired: false,
    availableStates: ['working']
  },
  {
    command: 'resume',
    label: '继续',
    icon: 'play',
    color: '#52c41a',
    confirmRequired: false,
    availableStates: ['paused']
  },
  {
    command: 'stop',
    label: '停止任务',
    icon: 'stop',
    color: '#ff4d4f',
    confirmRequired: true,
    confirmMessage: '确定要停止当前任务吗？',
    availableStates: ['working', 'paused']
  },
  {
    command: 'return_home',
    label: '返回充电',
    icon: 'home',
    color: '#1890ff',
    confirmRequired: false,
    availableStates: ['idle', 'paused']
  },
  {
    command: 'emergency_stop',
    label: '紧急停止',
    icon: 'alert-octagon',
    color: '#ff4d4f',
    confirmRequired: true,
    confirmMessage: '紧急停止将立即中断所有操作，确定吗？',
    availableStates: ['working', 'paused', 'idle']
  },
  {
    command: 'locate',
    label: '定位闪灯',
    icon: 'flashlight',
    color: '#722ed1',
    confirmRequired: false,
    availableStates: ['working', 'paused', 'idle', 'charging']
  }
];

// 控制面板布局
/*
┌───────────────────────────────────────┐
│  控制 R-005                    ✕     │
│  ─────────────────────────────────    │
│  当前状态: 工作中                      │
│                                       │
│  ┌───────┐  ┌───────┐  ┌───────┐    │
│  │  ⏸️   │  │  ⏹️   │  │  🏠   │    │
│  │ 暂停  │  │ 停止  │  │ 返回  │    │
│  └───────┘  └───────┘  └───────┘    │
│                                       │
│  ┌───────────────────────────────┐   │
│  │  🚨 紧急停止                   │   │
│  └───────────────────────────────┘   │
│                                       │
│  💡 定位闪灯（帮助找到机器人）         │
└───────────────────────────────────────┘
*/
```

### 5.4 今日统计卡片

```typescript
// 今日统计组件
interface TodayStatsCardProps {
  stats: RobotDetailData['todayStats'];
}

// 布局示例
/*
┌───────────────────────────────────────┐
│  今日统计                             │
│  ─────────────────────────────────    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ 2小时   │ │ 1.2km   │ │ 500m²   │ │
│  │ 工作时长 │ │ 行驶距离 │ │ 清洁面积 │ │
│  └─────────┘ └─────────┘ └─────────┘ │
│  ┌─────────────────┐ ┌──────────────┐│
│  │ 5个任务完成      │ │ 效率 92%    ││
│  └─────────────────┘ └──────────────┘│
└───────────────────────────────────────┘
*/
```

---

## 6. 通知中心

### 6.1 通知列表

```typescript
// 通知列表组件
interface NotificationListProps {
  notifications: Notification[];
  onNotificationPress: (notification: Notification) => void;
  onMarkAsRead: (notificationId: string) => void;
  onMarkAllAsRead: () => void;
  onRefresh: () => void;
  refreshing: boolean;
}

interface Notification {
  id: string;
  type: NotificationType;
  level: NotificationLevel;
  title: string;
  message: string;
  data: NotificationData;
  isRead: boolean;
  createdAt: string;
}

type NotificationType = 
  | 'robot_alert'       // 机器人告警
  | 'task_complete'     // 任务完成
  | 'task_failed'       // 任务失败
  | 'agent_escalation'  // Agent升级
  | 'system_notice';    // 系统通知

type NotificationLevel = 
  | 'critical'    // 紧急
  | 'warning'     // 警告
  | 'info'        // 信息
  | 'success';    // 成功

interface NotificationData {
  robotId?: string;
  robotName?: string;
  taskId?: string;
  alertId?: string;
  actionUrl?: string;
}
```

### 6.2 通知项组件

```typescript
// 通知项布局
/*
未读通知:
┌───────────────────────────────────────┐
│ 🔴 ● R-005 清洁机器人卡住    10:32   │
│    │ 机器人在A栋3F卡住，需要人工      │
│    │ 干预                             │
│    └──────────────────────────────    │
└───────────────────────────────────────┘

已读通知:
┌───────────────────────────────────────┐
│ 🟢   日常清洁任务完成         09:45   │
│    │ A栋上午清洁任务已完成，           │
│    │ 覆盖率98%                        │
│    └──────────────────────────────    │
└───────────────────────────────────────┘
*/

// 通知级别配置
const notificationLevelConfig = {
  critical: { color: '#ff4d4f', icon: 'alert-circle', badge: '紧急' },
  warning: { color: '#faad14', icon: 'alert-triangle', badge: '警告' },
  info: { color: '#1890ff', icon: 'information-circle', badge: '' },
  success: { color: '#52c41a', icon: 'checkmark-circle', badge: '' }
};
```

### 6.3 通知详情

```typescript
// 通知详情页
interface NotificationDetailProps {
  notification: Notification;
  onAction?: (action: string) => void;
}

// 详情布局
/*
┌───────────────────────────────────────┐
│ ← 通知详情                            │
├───────────────────────────────────────┤
│                                       │
│  🔴 紧急告警                          │
│                                       │
│  R-005 清洁机器人卡住                 │
│  ─────────────────────────────────    │
│  时间: 2026-01-20 10:32:15           │
│  机器人: R-005 (高仙 Vacuum Pro)     │
│  位置: A栋 3F 走廊                    │
│                                       │
│  详细信息:                            │
│  机器人在执行清洁任务时检测到移动     │
│  受阻，连续3次尝试后无法脱困，        │
│  需要人工干预。                       │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │         查看机器人详情          │  │
│  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐  │
│  │         处理此告警              │  │
│  └─────────────────────────────────┘  │
│                                       │
└───────────────────────────────────────┘
*/
```

### 6.4 通知设置

```typescript
// 通知设置接口
interface NotificationSettings {
  // 推送开关
  pushEnabled: boolean;
  
  // 分级别开关
  levelSettings: {
    critical: boolean;     // 紧急通知（建议始终开启）
    warning: boolean;      // 警告通知
    info: boolean;         // 信息通知
    success: boolean;      // 成功通知
  };
  
  // 分类型开关
  typeSettings: {
    robot_alert: boolean;
    task_complete: boolean;
    task_failed: boolean;
    agent_escalation: boolean;
    system_notice: boolean;
  };
  
  // 免打扰
  doNotDisturb: {
    enabled: boolean;
    startTime: string;     // HH:mm
    endTime: string;       // HH:mm
    exceptCritical: boolean;  // 紧急通知除外
  };
  
  // 声音和振动
  sound: boolean;
  vibration: boolean;
}
```

---

## 7. 数据流设计

### 7.1 状态管理

```typescript
// 使用 Zustand 管理状态
import create from 'zustand';

interface MobileMonitorStore {
  // 仪表盘数据
  dashboard: DashboardData | null;
  dashboardLoading: boolean;
  fetchDashboard: () => Promise<void>;
  
  // 车队数据
  robots: RobotSummary[];
  robotsLoading: boolean;
  fleetFilter: FleetFilter;
  setFleetFilter: (filter: FleetFilter) => void;
  fetchRobots: () => Promise<void>;
  
  // 当前查看的机器人
  currentRobot: RobotDetailData | null;
  currentRobotLoading: boolean;
  fetchRobotDetail: (robotId: string) => Promise<void>;
  
  // 通知
  notifications: Notification[];
  unreadCount: number;
  notificationsLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  
  // WebSocket连接
  wsConnected: boolean;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

const useMobileMonitorStore = create<MobileMonitorStore>((set, get) => ({
  // 初始状态
  dashboard: null,
  dashboardLoading: false,
  robots: [],
  robotsLoading: false,
  fleetFilter: {},
  currentRobot: null,
  currentRobotLoading: false,
  notifications: [],
  unreadCount: 0,
  notificationsLoading: false,
  wsConnected: false,
  
  // Actions实现
  fetchDashboard: async () => {
    set({ dashboardLoading: true });
    try {
      const data = await api.getDashboard();
      set({ dashboard: data, dashboardLoading: false });
    } catch (error) {
      set({ dashboardLoading: false });
      throw error;
    }
  },
  
  fetchRobots: async () => {
    set({ robotsLoading: true });
    const { fleetFilter } = get();
    try {
      const data = await api.getRobots(fleetFilter);
      set({ robots: data, robotsLoading: false });
    } catch (error) {
      set({ robotsLoading: false });
      throw error;
    }
  },
  
  // ... 其他action实现
}));
```

### 7.2 API服务

```typescript
// API服务定义
interface MobileMonitorApi {
  // 仪表盘
  getDashboard(): Promise<DashboardData>;
  
  // 车队
  getRobots(filter?: FleetFilter): Promise<RobotSummary[]>;
  getRobotDetail(robotId: string): Promise<RobotDetailData>;
  
  // 机器人控制
  sendCommand(robotId: string, command: RobotCommand): Promise<CommandResult>;
  
  // 通知
  getNotifications(params?: {
    page?: number;
    pageSize?: number;
    level?: NotificationLevel;
    isRead?: boolean;
  }): Promise<PaginatedResponse<Notification>>;
  markAsRead(notificationId: string): Promise<void>;
  markAllAsRead(): Promise<void>;
  
  // 设置
  getNotificationSettings(): Promise<NotificationSettings>;
  updateNotificationSettings(settings: NotificationSettings): Promise<void>;
}

// API基础URL
const API_BASE = '/api/v1/mobile';

// API实现
const api: MobileMonitorApi = {
  getDashboard: () => 
    fetch(`${API_BASE}/dashboard`).then(r => r.json()),
  
  getRobots: (filter) =>
    fetch(`${API_BASE}/robots?${new URLSearchParams(filter as any)}`).then(r => r.json()),
  
  getRobotDetail: (robotId) =>
    fetch(`${API_BASE}/robots/${robotId}`).then(r => r.json()),
  
  sendCommand: (robotId, command) =>
    fetch(`${API_BASE}/robots/${robotId}/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(command)
    }).then(r => r.json()),
  
  // ... 其他实现
};
```

### 7.3 WebSocket实时更新

```typescript
// WebSocket服务
class MobileWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(token: string) {
    const wsUrl = `wss://api.linkc.com/ws/mobile?token=${token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      useMobileMonitorStore.setState({ wsConnected: true });
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onclose = () => {
      useMobileMonitorStore.setState({ wsConnected: false });
      this.attemptReconnect(token);
    };
  }
  
  private handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'robot_status_update':
        this.handleRobotStatusUpdate(message.data);
        break;
      case 'new_notification':
        this.handleNewNotification(message.data);
        break;
      case 'dashboard_update':
        this.handleDashboardUpdate(message.data);
        break;
    }
  }
  
  private handleRobotStatusUpdate(data: RobotStatusUpdate) {
    const store = useMobileMonitorStore.getState();
    
    // 更新车队列表中的机器人状态
    const updatedRobots = store.robots.map(robot =>
      robot.id === data.robotId
        ? { ...robot, status: data.status, battery: data.battery }
        : robot
    );
    useMobileMonitorStore.setState({ robots: updatedRobots });
    
    // 如果是当前查看的机器人，也更新详情
    if (store.currentRobot?.basic.id === data.robotId) {
      useMobileMonitorStore.setState({
        currentRobot: {
          ...store.currentRobot,
          status: { ...store.currentRobot.status, ...data }
        }
      });
    }
  }
  
  private handleNewNotification(notification: Notification) {
    const store = useMobileMonitorStore.getState();
    useMobileMonitorStore.setState({
      notifications: [notification, ...store.notifications],
      unreadCount: store.unreadCount + 1
    });
    
    // 触发本地通知
    this.showLocalNotification(notification);
  }
  
  private showLocalNotification(notification: Notification) {
    // 使用 react-native-push-notification 或 expo-notifications
    // 显示本地推送通知
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

interface WebSocketMessage {
  type: 'robot_status_update' | 'new_notification' | 'dashboard_update';
  data: any;
  timestamp: string;
}

interface RobotStatusUpdate {
  robotId: string;
  status: RobotStatus;
  battery: number;
  position?: Position;
}
```

---

## 8. 离线支持

### 8.1 离线存储策略

```typescript
// 离线数据管理
import AsyncStorage from '@react-native-async-storage/async-storage';

interface OfflineManager {
  // 缓存仪表盘数据
  cacheDashboard(data: DashboardData): Promise<void>;
  getCachedDashboard(): Promise<DashboardData | null>;
  
  // 缓存机器人列表
  cacheRobots(robots: RobotSummary[]): Promise<void>;
  getCachedRobots(): Promise<RobotSummary[]>;
  
  // 缓存机器人详情
  cacheRobotDetail(robotId: string, data: RobotDetailData): Promise<void>;
  getCachedRobotDetail(robotId: string): Promise<RobotDetailData | null>;
  
  // 清理过期缓存
  clearExpiredCache(): Promise<void>;
}

const CACHE_EXPIRY = 30 * 60 * 1000; // 30分钟

const offlineManager: OfflineManager = {
  cacheDashboard: async (data) => {
    await AsyncStorage.setItem('dashboard', JSON.stringify({
      data,
      timestamp: Date.now()
    }));
  },
  
  getCachedDashboard: async () => {
    const cached = await AsyncStorage.getItem('dashboard');
    if (!cached) return null;
    
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp > CACHE_EXPIRY) {
      return null; // 缓存过期
    }
    return data;
  },
  
  // ... 其他实现
};
```

### 8.2 离线操作队列

```typescript
// 离线操作队列
interface OfflineAction {
  id: string;
  type: 'command';
  payload: {
    robotId: string;
    command: RobotCommand;
  };
  createdAt: string;
  retryCount: number;
}

class OfflineActionQueue {
  private queue: OfflineAction[] = [];
  
  async addAction(action: Omit<OfflineAction, 'id' | 'createdAt' | 'retryCount'>) {
    const newAction: OfflineAction = {
      ...action,
      id: uuid(),
      createdAt: new Date().toISOString(),
      retryCount: 0
    };
    
    this.queue.push(newAction);
    await this.persistQueue();
  }
  
  async processQueue() {
    const networkState = await NetInfo.fetch();
    if (!networkState.isConnected) return;
    
    for (const action of this.queue) {
      try {
        await this.executeAction(action);
        this.queue = this.queue.filter(a => a.id !== action.id);
      } catch (error) {
        action.retryCount++;
        if (action.retryCount >= 3) {
          // 通知用户操作失败
          this.notifyFailure(action);
          this.queue = this.queue.filter(a => a.id !== action.id);
        }
      }
    }
    
    await this.persistQueue();
  }
  
  private async executeAction(action: OfflineAction) {
    switch (action.type) {
      case 'command':
        await api.sendCommand(action.payload.robotId, action.payload.command);
        break;
    }
  }
  
  private async persistQueue() {
    await AsyncStorage.setItem('offlineQueue', JSON.stringify(this.queue));
  }
}
```

---

## 9. 推送通知

### 9.1 推送配置

```typescript
// 推送通知配置
import messaging from '@react-native-firebase/messaging';
import PushNotification from 'react-native-push-notification';

// 初始化推送
async function initializePushNotifications() {
  // 请求权限
  const authStatus = await messaging().requestPermission();
  const enabled = 
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;
  
  if (!enabled) {
    console.log('Push notification permission denied');
    return;
  }
  
  // 获取FCM token
  const token = await messaging().getToken();
  await api.registerPushToken(token);
  
  // 监听token刷新
  messaging().onTokenRefresh(async (newToken) => {
    await api.registerPushToken(newToken);
  });
  
  // 前台消息处理
  messaging().onMessage(async (remoteMessage) => {
    handleForegroundMessage(remoteMessage);
  });
  
  // 后台消息处理
  messaging().setBackgroundMessageHandler(async (remoteMessage) => {
    handleBackgroundMessage(remoteMessage);
  });
}

// 本地通知配置
PushNotification.configure({
  onNotification: function(notification) {
    handleNotificationPress(notification);
  },
  
  popInitialNotification: true,
  requestPermissions: true,
});

// 创建通知渠道（Android）
PushNotification.createChannel({
  channelId: 'critical-alerts',
  channelName: '紧急告警',
  channelDescription: '紧急告警通知',
  playSound: true,
  soundName: 'alert.mp3',
  importance: 5,
  vibrate: true,
});

PushNotification.createChannel({
  channelId: 'general-notifications',
  channelName: '一般通知',
  channelDescription: '一般系统通知',
  playSound: true,
  importance: 3,
  vibrate: true,
});
```

### 9.2 通知处理

```typescript
// 前台消息处理
function handleForegroundMessage(message: FirebaseMessagingTypes.RemoteMessage) {
  const { notification, data } = message;
  
  // 确定通知渠道
  const channelId = data?.level === 'critical' 
    ? 'critical-alerts' 
    : 'general-notifications';
  
  // 显示本地通知
  PushNotification.localNotification({
    channelId,
    title: notification?.title,
    message: notification?.body || '',
    data: data,
    smallIcon: 'ic_notification',
    largeIcon: '',
    color: getLevelColor(data?.level as NotificationLevel),
    vibrate: true,
    vibration: 300,
    playSound: true,
  });
}

// 通知点击处理
function handleNotificationPress(notification: any) {
  const { data } = notification;
  
  // 根据通知类型导航
  switch (data?.type) {
    case 'robot_alert':
      // 导航到机器人详情
      navigationRef.navigate('RobotDetail', { robotId: data.robotId });
      break;
    case 'task_complete':
    case 'task_failed':
      // 导航到任务详情（如果有任务模块）
      navigationRef.navigate('Notifications');
      break;
    default:
      // 导航到通知中心
      navigationRef.navigate('Notifications');
  }
}
```

---

## 10. 测试要求

### 10.1 单元测试

```typescript
// 状态管理测试
describe('MobileMonitorStore', () => {
  beforeEach(() => {
    useMobileMonitorStore.setState({
      dashboard: null,
      robots: [],
      notifications: [],
      unreadCount: 0
    });
  });
  
  it('should fetch dashboard data', async () => {
    const mockDashboard: DashboardData = {
      healthScore: 85,
      healthTrend: 'up',
      stats: { total: 25, working: 12, idle: 5, charging: 6, error: 2, offline: 0 },
      todaySummary: { tasksCompleted: 15, tasksTotal: 20, coverageRate: 0.95, efficiency: 0.92 },
      alerts: { critical: 2, warning: 5, info: 3 },
      recentAlerts: [],
      lastUpdated: new Date().toISOString()
    };
    
    jest.spyOn(api, 'getDashboard').mockResolvedValue(mockDashboard);
    
    await useMobileMonitorStore.getState().fetchDashboard();
    
    expect(useMobileMonitorStore.getState().dashboard).toEqual(mockDashboard);
  });
  
  it('should update unread count when new notification arrives', () => {
    const initialCount = useMobileMonitorStore.getState().unreadCount;
    
    // 模拟新通知到达
    const newNotification: Notification = {
      id: 'notif-1',
      type: 'robot_alert',
      level: 'warning',
      title: 'Test Alert',
      message: 'Test message',
      data: {},
      isRead: false,
      createdAt: new Date().toISOString()
    };
    
    useMobileMonitorStore.setState(state => ({
      notifications: [newNotification, ...state.notifications],
      unreadCount: state.unreadCount + 1
    }));
    
    expect(useMobileMonitorStore.getState().unreadCount).toBe(initialCount + 1);
  });
});

// 组件测试
describe('HealthScoreCard', () => {
  it('should display correct health level', () => {
    const { getByText } = render(
      <HealthScoreCard score={85} trend="up" />
    );
    
    expect(getByText('85')).toBeTruthy();
    expect(getByText('良好')).toBeTruthy();
  });
  
  it('should show critical color for low scores', () => {
    const { getByTestId } = render(
      <HealthScoreCard score={45} trend="down" />
    );
    
    const scoreContainer = getByTestId('health-score-container');
    expect(scoreContainer.props.style.backgroundColor).toBe('#ff4d4f');
  });
});
```

### 10.2 集成测试

```typescript
// 端到端测试
describe('Mobile Monitor E2E', () => {
  beforeAll(async () => {
    await device.launchApp();
  });
  
  it('should show dashboard on launch', async () => {
    await expect(element(by.id('dashboard-screen'))).toBeVisible();
    await expect(element(by.id('health-score-card'))).toBeVisible();
  });
  
  it('should navigate to fleet and show robots', async () => {
    await element(by.id('nav-fleet')).tap();
    await expect(element(by.id('fleet-screen'))).toBeVisible();
    await expect(element(by.id('robot-list'))).toBeVisible();
  });
  
  it('should open robot detail when tapping a robot', async () => {
    await element(by.id('robot-item-R-005')).tap();
    await expect(element(by.id('robot-detail-screen'))).toBeVisible();
    await expect(element(by.text('R-005'))).toBeVisible();
  });
  
  it('should show control panel and execute command', async () => {
    await element(by.id('open-control-panel')).tap();
    await expect(element(by.id('control-panel'))).toBeVisible();
    
    await element(by.id('control-pause')).tap();
    await expect(element(by.text('已暂停'))).toBeVisible();
  });
});
```

---

## 11. 性能要求

### 11.1 性能指标

| 指标 | 目标 | 测量方式 |
|-----|------|---------|
| 启动时间 | < 2秒 | 冷启动到首屏渲染 |
| 页面切换 | < 300ms | 导航动画完成 |
| 列表滚动 | 60fps | FPS监控 |
| API响应 | < 1秒 | 网络请求完成 |
| 电量消耗 | < 5%/小时 | 后台运行时 |
| 内存占用 | < 150MB | 活跃使用时 |

### 11.2 优化策略

```typescript
// 列表优化
import { FlashList } from '@shopify/flash-list';

// 使用FlashList替代FlatList
<FlashList
  data={robots}
  renderItem={({ item }) => <RobotListItem robot={item} />}
  estimatedItemSize={100}
  keyExtractor={item => item.id}
/>

// 图片优化
import FastImage from 'react-native-fast-image';

<FastImage
  source={{ uri: robot.imageUrl, priority: FastImage.priority.normal }}
  style={styles.robotImage}
  resizeMode={FastImage.resizeMode.cover}
/>

// 避免不必要的重渲染
const RobotListItem = React.memo(({ robot, onPress }) => {
  // 组件实现
}, (prevProps, nextProps) => {
  return prevProps.robot.id === nextProps.robot.id &&
         prevProps.robot.status === nextProps.robot.status &&
         prevProps.robot.battery === nextProps.robot.battery;
});
```

---

## 12. 文件结构

```
src/mobile/monitor/
├── screens/
│   ├── DashboardScreen.tsx         # 首页
│   ├── FleetScreen.tsx             # 车队页
│   ├── RobotDetailScreen.tsx       # 机器人详情
│   ├── NotificationsScreen.tsx     # 通知中心
│   ├── NotificationDetailScreen.tsx # 通知详情
│   └── SettingsScreen.tsx          # 设置页
├── components/
│   ├── dashboard/
│   │   ├── HealthScoreCard.tsx
│   │   ├── QuickStatsCard.tsx
│   │   └── AlertSummaryCard.tsx
│   ├── fleet/
│   │   ├── RobotListItem.tsx
│   │   ├── FleetFilter.tsx
│   │   └── FleetMapView.tsx
│   ├── robot/
│   │   ├── StatusCard.tsx
│   │   ├── ControlPanel.tsx
│   │   ├── TodayStatsCard.tsx
│   │   └── ConsumablesCard.tsx
│   ├── notifications/
│   │   ├── NotificationItem.tsx
│   │   └── NotificationSettings.tsx
│   └── common/
│       ├── LoadingSpinner.tsx
│       ├── ErrorBoundary.tsx
│       ├── EmptyState.tsx
│       └── RefreshControl.tsx
├── store/
│   └── mobileMonitorStore.ts       # Zustand store
├── services/
│   ├── api.ts                      # API服务
│   ├── websocket.ts                # WebSocket服务
│   └── pushNotification.ts         # 推送服务
├── utils/
│   ├── offline.ts                  # 离线管理
│   ├── formatters.ts               # 格式化工具
│   └── constants.ts                # 常量定义
├── navigation/
│   └── MonitorNavigator.tsx        # 导航配置
├── hooks/
│   ├── useRobotStatus.ts
│   ├── useNotifications.ts
│   └── useOfflineStatus.ts
└── types/
    └── index.ts                    # 类型定义

tests/
├── unit/
│   ├── store.test.ts
│   └── components/
├── integration/
│   └── screens.test.ts
└── e2e/
    └── monitor.e2e.ts
```

---

## 13. 验收标准

### 13.1 功能验收

| 功能 | 验收标准 |
|-----|---------|
| 首页仪表盘 | 显示健康度、机器人状态统计、异常摘要 |
| 车队列表 | 显示所有机器人，支持筛选和搜索 |
| 地图视图 | 在楼层平面图上显示机器人位置 |
| 机器人详情 | 显示完整状态信息和今日统计 |
| 远程控制 | 成功执行暂停/恢复/停止/返回充电/紧急停止 |
| 推送通知 | 接收并正确显示各级别通知 |
| 通知管理 | 查看、标记已读、设置通知偏好 |
| 离线支持 | 无网络时显示缓存数据 |

### 13.2 性能验收

| 指标 | 验收标准 |
|-----|---------|
| 启动时间 | 冷启动 < 2秒 |
| 页面切换 | < 300ms |
| 滚动流畅度 | 60fps |
| 电量消耗 | 后台运行 < 5%/小时 |

### 13.3 兼容性验收

| 平台 | 版本要求 |
|-----|---------|
| iOS | 13.0+ |
| Android | 8.0+ (API 26+) |
| 屏幕尺寸 | 4.7寸 - 12.9寸 |

---

*文档版本: 1.0*  
*创建日期: 2026年1月*  
*最后更新: 2026年1月*
