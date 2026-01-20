# 模块开发规格书：O1 运营控制台仪表板

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | O1 |
| 模块名称 | OperationsDashboard - 运营控制台仪表板 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 规划中 |
| 前置依赖 | G6数据API、G4机器人API、F1数据模型 |

---

## 1. 模块概述

### 1.1 职责描述

OperationsDashboard是运营控制台的核心仪表板页面，为运营经理提供全局运营视图，包括KPI指标、机器人状态概览、任务进度、告警统计等关键信息，支持快速定位问题和决策。

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      运营控制台 (Operations Console)                     │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    ★ O1: 运营仪表板 (Dashboard) ★                 │ │
│  │  ┌──────────────────────────────────────────────────────────────┐│ │
│  │  │ KPI卡片区: 完成率 | 效率 | 在线率 | 告警数                   ││ │
│  │  └──────────────────────────────────────────────────────────────┘│ │
│  │  ┌─────────────────────────┐ ┌────────────────────────────────┐ │ │
│  │  │ 机器人状态分布          │ │ 今日任务进度                   │ │ │
│  │  │ [饼图]                  │ │ [进度条+列表]                  │ │ │
│  │  └─────────────────────────┘ └────────────────────────────────┘ │ │
│  │  ┌─────────────────────────┐ ┌────────────────────────────────┐ │ │
│  │  │ 效率趋势图              │ │ 告警列表                       │ │ │
│  │  │ [折线图]                │ │ [最新告警]                     │ │ │
│  │  └─────────────────────────┘ └────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐            │
│  │ O2: 任务  │ │ O3: 机器人│ │ O4: 告警  │ │ O5: 设置  │            │
│  │ 管理      │ │ 监控      │ │ 管理      │ │           │            │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 功能概述

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| KPI卡片 | 展示核心KPI指标（完成率、效率、在线率等） | P0 |
| 机器人状态 | 饼图展示机器人状态分布 | P0 |
| 任务进度 | 今日任务完成进度和列表 | P0 |
| 效率趋势 | 展示近7天/30天效率趋势 | P1 |
| 告警摘要 | 最新未处理告警列表 | P1 |
| 楼宇筛选 | 按楼宇/楼层筛选数据 | P1 |
| 时间范围 | 选择不同时间范围的数据 | P1 |
| 数据刷新 | 自动/手动刷新数据 | P2 |
| 导出报表 | 导出仪表板数据 | P2 |

---

## 2. UI设计

### 2.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 顶部筛选栏                                                                  │
│ [楼宇: 全部 ▼] [楼层: 全部 ▼] [时间: 今日 ▼]  [🔄 刷新] [📊 导出]         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐  │
│  │ 📈 清洁完成率 │ │ ⚡ 平均效率   │ │ 🤖 机器人在线 │ │ ⚠️ 待处理告警  │  │
│  │               │ │               │ │               │ │               │  │
│  │    87.5%      │ │   156 m²/h    │ │   8/10 台     │ │    3 条       │  │
│  │   ↑ 2.3%     │ │   ↑ 5.2%     │ │   ↓ 1 台     │ │   ↑ 1 条     │  │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────────┐  │
│  │ 机器人状态分布                  │ │ 今日任务进度                    │  │
│  │                                 │ │                                 │  │
│  │      ┌─────────┐               │ │ ████████████░░░░░░░  75%        │  │
│  │     ╱    ╲    工作中: 5        │ │                                 │  │
│  │    │ 62.5% │   充电中: 2       │ │ 已完成: 12 / 16 任务            │  │
│  │     ╲    ╱    空闲: 1         │ │                                 │  │
│  │      └─────────┘  离线: 2      │ │ ┌─────────────────────────────┐ │  │
│  │                                 │ │ │ ✅ 1F大堂清洁    09:00完成  │ │  │
│  │  🟢 工作中  🔵 充电  ⚪ 空闲   │ │ │ ✅ 2F走廊清洁    10:30完成  │ │  │
│  │  🔴 离线                       │ │ │ 🔄 3F会议室      进行中...   │ │  │
│  │                                 │ │ │ ⏳ 4F办公区      待执行      │ │  │
│  └─────────────────────────────────┘ │ └─────────────────────────────┘ │  │
│                                      └─────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────────┐  │
│  │ 清洁效率趋势（近7天）           │ │ 最新告警                        │  │
│  │                                 │ │                                 │  │
│  │  180 ┤        ╭──╮             │ │ ┌─────────────────────────────┐ │  │
│  │  160 ┤    ╭───╯  ╰──╮         │ │ │ 🔴 R3 电量低于10%   5分钟前 │ │  │
│  │  140 ┤ ───╯          ╰──      │ │ │ 🟡 R5 清洁效率下降  15分钟前│ │  │
│  │  120 ┤                         │ │ │ 🟡 任务延迟告警    30分钟前 │ │  │
│  │      └──┬──┬──┬──┬──┬──┬──   │ │ └─────────────────────────────┘ │  │
│  │        周一 二  三 四 五 六 日  │ │                                 │  │
│  │                                 │ │ [查看全部告警 →]               │  │
│  └─────────────────────────────────┘ └─────────────────────────────────┘  │
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────  │
│ 最后更新: 2026-01-20 14:30:25 | 自动刷新: 5分钟                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 KPI卡片设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        KPI卡片样式                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  正常状态:                    警告状态:                         │
│  ┌───────────────────┐       ┌───────────────────┐             │
│  │ 📈 清洁完成率      │       │ ⚠️ 清洁完成率      │             │
│  │                   │       │                   │             │
│  │      87.5%        │       │      65.2%        │             │
│  │                   │       │                   │             │
│  │   ↑ 2.3% vs昨日  │       │   ↓ 5.1% vs昨日  │             │
│  │   ───────────────│       │   ───────────────│             │
│  │   目标: 85%  ✓   │       │   目标: 85%  ✗   │             │
│  └───────────────────┘       └───────────────────┘             │
│   border: green              border: orange                    │
│   bg: green/5                bg: orange/5                      │
│                                                                 │
│  严重状态:                    加载状态:                         │
│  ┌───────────────────┐       ┌───────────────────┐             │
│  │ 🔴 机器人在线      │       │ 📈 清洁完成率      │             │
│  │                   │       │                   │             │
│  │      3/10 台      │       │    ░░░░░░░░       │             │
│  │                   │       │    加载中...      │             │
│  │   ↓ 7台 vs昨日   │       │                   │             │
│  │   ───────────────│       │                   │             │
│  │   阈值: 80%  ✗   │       │                   │             │
│  └───────────────────┘       └───────────────────┘             │
│   border: red                border: gray                      │
│   bg: red/5                  bg: gray/5                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 颜色规范

```css
/* 状态颜色 */
--color-success: #22C55E;     /* 正常/达标 */
--color-warning: #F59E0B;     /* 警告/接近阈值 */
--color-error: #EF4444;       /* 严重/未达标 */
--color-info: #3B82F6;        /* 信息/中性 */

/* KPI趋势颜色 */
--color-trend-up: #22C55E;    /* 上升趋势（正向） */
--color-trend-down: #EF4444;  /* 下降趋势（负向） */
--color-trend-flat: #6B7280;  /* 持平 */

/* 机器人状态颜色 */
--color-robot-working: #22C55E;
--color-robot-charging: #3B82F6;
--color-robot-idle: #9CA3AF;
--color-robot-offline: #EF4444;
--color-robot-error: #EF4444;

/* 图表配色 */
--chart-primary: #6366F1;     /* 主要数据系列 */
--chart-secondary: #EC4899;   /* 次要数据系列 */
--chart-grid: #E5E7EB;        /* 网格线 */
```

---

## 3. 组件接口

### 3.1 Props定义

```typescript
// pages/operations/dashboard/types.ts

interface OperationsDashboardProps {
  /** 默认选中的楼宇ID */
  defaultBuildingId?: string;
  
  /** 默认时间范围 */
  defaultTimeRange?: TimeRange;
  
  /** 自动刷新间隔（毫秒），0表示不自动刷新 */
  refreshInterval?: number;
  
  /** KPI阈值配置 */
  thresholds?: KPIThresholds;
}

type TimeRange = 'today' | 'yesterday' | 'week' | 'month';

interface KPIThresholds {
  completionRate: {
    warning: number;  // 低于此值显示警告（如0.8）
    critical: number; // 低于此值显示严重（如0.6）
  };
  efficiency: {
    warning: number;
    critical: number;
  };
  onlineRate: {
    warning: number;
    critical: number;
  };
  alertCount: {
    warning: number;
    critical: number;
  };
}

// KPI数据
interface KPIData {
  completionRate: {
    value: number;           // 0-1
    trend: number;           // 相比昨日变化（百分点）
    target: number;          // 目标值
  };
  efficiency: {
    value: number;           // m²/h
    trend: number;           // 变化百分比
    target: number;
  };
  robotOnline: {
    online: number;
    total: number;
    trend: number;           // 变化数量
  };
  pendingAlerts: {
    count: number;
    trend: number;
    bySeverity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
}

// 机器人状态分布
interface RobotStatusDistribution {
  working: number;
  charging: number;
  idle: number;
  paused: number;
  error: number;
  offline: number;
}

// 任务进度
interface TaskProgress {
  total: number;
  completed: number;
  inProgress: number;
  pending: number;
  failed: number;
  tasks: TaskSummary[];
}

interface TaskSummary {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'pending' | 'failed';
  scheduledTime: string;
  completedTime?: string;
  robotName?: string;
}

// 效率趋势
interface EfficiencyTrend {
  period: string;  // 日期
  value: number;   // 效率值
  target: number;  // 目标值
}

// 告警摘要
interface AlertSummary {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: string;
  message: string;
  robotId?: string;
  robotName?: string;
  createdAt: string;
  acknowledged: boolean;
}
```

### 3.2 API调用

```typescript
// 获取KPI概览
GET /api/v1/data/kpi-overview
Query: {
  building_id?: string;
  floor_id?: string;
  date: string;          // YYYY-MM-DD
}
Response: KPIData

// 获取机器人状态分布
GET /api/v1/robots/status-distribution
Query: {
  building_id?: string;
  floor_id?: string;
}
Response: RobotStatusDistribution

// 获取今日任务进度
GET /api/v1/tasks/today-progress
Query: {
  building_id?: string;
  floor_id?: string;
}
Response: TaskProgress

// 获取效率趋势
GET /api/v1/data/efficiency-trend
Query: {
  building_id?: string;
  floor_id?: string;
  period: 'week' | 'month';
  granularity: 'day' | 'hour';
}
Response: EfficiencyTrend[]

// 获取最新告警
GET /api/v1/alerts
Query: {
  building_id?: string;
  status: 'pending';
  limit: 5;
  sort: '-created_at';
}
Response: { items: AlertSummary[], total: number }
```

---

## 4. 实现要求

### 4.1 技术栈

| 技术 | 版本 | 用途 |
|-----|------|------|
| React | 18+ | UI框架 |
| TypeScript | 5.0+ | 类型安全 |
| TailwindCSS | 3.4+ | 样式 |
| React Query | 5.0+ | 数据获取和缓存 |
| Recharts | 2.10+ | 图表渲染 |
| date-fns | 3.0+ | 日期处理 |

### 4.2 核心实现

#### 4.2.1 仪表板页面

```typescript
// pages/operations/dashboard/index.tsx
import React, { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { KPICards } from './components/KPICards';
import { RobotStatusChart } from './components/RobotStatusChart';
import { TaskProgressCard } from './components/TaskProgressCard';
import { EfficiencyTrendChart } from './components/EfficiencyTrendChart';
import { AlertList } from './components/AlertList';
import { DashboardFilters } from './components/DashboardFilters';
import { 
  fetchKPIOverview, 
  fetchRobotStatusDistribution,
  fetchTaskProgress,
  fetchEfficiencyTrend,
  fetchAlerts,
} from '../../../api/data';
import { OperationsDashboardProps, TimeRange } from './types';

const DEFAULT_THRESHOLDS: KPIThresholds = {
  completionRate: { warning: 0.8, critical: 0.6 },
  efficiency: { warning: 120, critical: 100 },
  onlineRate: { warning: 0.8, critical: 0.5 },
  alertCount: { warning: 3, critical: 5 },
};

export const OperationsDashboard: React.FC<OperationsDashboardProps> = ({
  defaultBuildingId,
  defaultTimeRange = 'today',
  refreshInterval = 300000, // 5分钟
  thresholds = DEFAULT_THRESHOLDS,
}) => {
  // 筛选状态
  const [buildingId, setBuildingId] = useState<string | undefined>(defaultBuildingId);
  const [floorId, setFloorId] = useState<string | undefined>();
  const [timeRange, setTimeRange] = useState<TimeRange>(defaultTimeRange);

  // 获取当前日期
  const getDateByRange = useCallback((range: TimeRange): string => {
    const now = new Date();
    switch (range) {
      case 'yesterday':
        now.setDate(now.getDate() - 1);
        break;
      default:
        break;
    }
    return now.toISOString().split('T')[0];
  }, []);

  const currentDate = getDateByRange(timeRange);

  // 数据查询
  const { data: kpiData, isLoading: kpiLoading } = useQuery({
    queryKey: ['kpi-overview', buildingId, floorId, currentDate],
    queryFn: () => fetchKPIOverview({ building_id: buildingId, floor_id: floorId, date: currentDate }),
    refetchInterval: refreshInterval,
  });

  const { data: robotStatus, isLoading: robotStatusLoading } = useQuery({
    queryKey: ['robot-status-distribution', buildingId, floorId],
    queryFn: () => fetchRobotStatusDistribution({ building_id: buildingId, floor_id: floorId }),
    refetchInterval: refreshInterval,
  });

  const { data: taskProgress, isLoading: taskProgressLoading } = useQuery({
    queryKey: ['task-progress', buildingId, floorId],
    queryFn: () => fetchTaskProgress({ building_id: buildingId, floor_id: floorId }),
    refetchInterval: refreshInterval,
  });

  const { data: efficiencyTrend, isLoading: trendLoading } = useQuery({
    queryKey: ['efficiency-trend', buildingId, floorId, timeRange],
    queryFn: () => fetchEfficiencyTrend({
      building_id: buildingId,
      floor_id: floorId,
      period: timeRange === 'month' ? 'month' : 'week',
      granularity: 'day',
    }),
    refetchInterval: refreshInterval,
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts-pending', buildingId],
    queryFn: () => fetchAlerts({
      building_id: buildingId,
      status: 'pending',
      limit: 5,
      sort: '-created_at',
    }),
    refetchInterval: refreshInterval,
  });

  // 手动刷新
  const handleRefresh = useCallback(() => {
    // 触发所有查询刷新
  }, []);

  // 导出报表
  const handleExport = useCallback(() => {
    // 导出PDF或Excel
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* 页面标题 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">运营仪表板</h1>
        <p className="text-gray-500">实时监控清洁运营状态</p>
      </div>

      {/* 筛选栏 */}
      <DashboardFilters
        buildingId={buildingId}
        floorId={floorId}
        timeRange={timeRange}
        onBuildingChange={setBuildingId}
        onFloorChange={setFloorId}
        onTimeRangeChange={setTimeRange}
        onRefresh={handleRefresh}
        onExport={handleExport}
      />

      {/* KPI卡片 */}
      <div className="mt-6">
        <KPICards
          data={kpiData}
          thresholds={thresholds}
          loading={kpiLoading}
        />
      </div>

      {/* 中间行：机器人状态 + 任务进度 */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RobotStatusChart
          data={robotStatus}
          loading={robotStatusLoading}
        />
        <TaskProgressCard
          data={taskProgress}
          loading={taskProgressLoading}
        />
      </div>

      {/* 底部行：效率趋势 + 告警列表 */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EfficiencyTrendChart
          data={efficiencyTrend}
          loading={trendLoading}
        />
        <AlertList
          alerts={alerts?.items || []}
          total={alerts?.total || 0}
          loading={alertsLoading}
        />
      </div>

      {/* 页脚：更新时间 */}
      <div className="mt-6 text-center text-sm text-gray-500">
        最后更新: {new Date().toLocaleString('zh-CN')} | 
        自动刷新: {refreshInterval / 1000 / 60}分钟
      </div>
    </div>
  );
};

export default OperationsDashboard;
```

#### 4.2.2 KPI卡片组件

```typescript
// pages/operations/dashboard/components/KPICards.tsx
import React from 'react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/24/solid';
import { KPIData, KPIThresholds } from '../types';

interface KPICardsProps {
  data?: KPIData;
  thresholds: KPIThresholds;
  loading: boolean;
}

type KPIStatus = 'normal' | 'warning' | 'critical';

const getStatus = (
  value: number,
  threshold: { warning: number; critical: number },
  isHigherBetter: boolean = true
): KPIStatus => {
  if (isHigherBetter) {
    if (value < threshold.critical) return 'critical';
    if (value < threshold.warning) return 'warning';
    return 'normal';
  } else {
    if (value > threshold.critical) return 'critical';
    if (value > threshold.warning) return 'warning';
    return 'normal';
  }
};

const STATUS_STYLES: Record<KPIStatus, string> = {
  normal: 'border-green-200 bg-green-50',
  warning: 'border-yellow-200 bg-yellow-50',
  critical: 'border-red-200 bg-red-50',
};

const TrendIcon: React.FC<{ value: number; positive?: boolean }> = ({ value, positive = true }) => {
  if (value === 0) return <MinusIcon className="w-4 h-4 text-gray-500" />;
  
  const isUp = value > 0;
  const isGood = positive ? isUp : !isUp;
  const color = isGood ? 'text-green-500' : 'text-red-500';
  
  return isUp 
    ? <ArrowUpIcon className={`w-4 h-4 ${color}`} />
    : <ArrowDownIcon className={`w-4 h-4 ${color}`} />;
};

export const KPICards: React.FC<KPICardsProps> = ({
  data,
  thresholds,
  loading,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-white rounded-lg border p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  if (!data) return null;

  const cards = [
    {
      title: '清洁完成率',
      icon: '📈',
      value: `${(data.completionRate.value * 100).toFixed(1)}%`,
      trend: data.completionRate.trend,
      trendLabel: 'vs昨日',
      target: `目标: ${(data.completionRate.target * 100).toFixed(0)}%`,
      targetMet: data.completionRate.value >= data.completionRate.target,
      status: getStatus(data.completionRate.value, thresholds.completionRate),
    },
    {
      title: '平均效率',
      icon: '⚡',
      value: `${data.efficiency.value.toFixed(0)} m²/h`,
      trend: data.efficiency.trend,
      trendLabel: 'vs昨日',
      target: `目标: ${data.efficiency.target} m²/h`,
      targetMet: data.efficiency.value >= data.efficiency.target,
      status: getStatus(data.efficiency.value, thresholds.efficiency),
    },
    {
      title: '机器人在线',
      icon: '🤖',
      value: `${data.robotOnline.online}/${data.robotOnline.total} 台`,
      trend: data.robotOnline.trend,
      trendLabel: '台 vs昨日',
      target: `阈值: ${(thresholds.onlineRate.warning * 100).toFixed(0)}%`,
      targetMet: data.robotOnline.online / data.robotOnline.total >= thresholds.onlineRate.warning,
      status: getStatus(data.robotOnline.online / data.robotOnline.total, thresholds.onlineRate),
    },
    {
      title: '待处理告警',
      icon: '⚠️',
      value: `${data.pendingAlerts.count} 条`,
      trend: data.pendingAlerts.trend,
      trendLabel: '条 vs昨日',
      target: `阈值: ${thresholds.alertCount.warning} 条`,
      targetMet: data.pendingAlerts.count <= thresholds.alertCount.warning,
      status: getStatus(data.pendingAlerts.count, thresholds.alertCount, false),
      trendPositive: false,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          className={`bg-white rounded-lg border-2 p-6 ${STATUS_STYLES[card.status]}`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">{card.title}</span>
            <span className="text-xl">{card.icon}</span>
          </div>
          
          <div className="text-3xl font-bold text-gray-900 mb-2">
            {card.value}
          </div>
          
          <div className="flex items-center text-sm mb-3">
            <TrendIcon value={card.trend} positive={card.trendPositive !== false} />
            <span className="ml-1">
              {Math.abs(card.trend).toFixed(1)}{card.trendLabel.includes('%') ? '%' : ''} {card.trendLabel}
            </span>
          </div>
          
          <div className="border-t pt-2 text-sm">
            <span className={card.targetMet ? 'text-green-600' : 'text-red-600'}>
              {card.target} {card.targetMet ? '✓' : '✗'}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};
```

#### 4.2.3 机器人状态饼图

```typescript
// pages/operations/dashboard/components/RobotStatusChart.tsx
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { RobotStatusDistribution } from '../types';

interface RobotStatusChartProps {
  data?: RobotStatusDistribution;
  loading: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  working: '#22C55E',
  charging: '#3B82F6',
  idle: '#9CA3AF',
  paused: '#F59E0B',
  error: '#EF4444',
  offline: '#DC2626',
};

const STATUS_LABELS: Record<string, string> = {
  working: '工作中',
  charging: '充电中',
  idle: '空闲',
  paused: '暂停',
  error: '故障',
  offline: '离线',
};

export const RobotStatusChart: React.FC<RobotStatusChartProps> = ({
  data,
  loading,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="h-64 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  if (!data) return null;

  const chartData = Object.entries(data)
    .filter(([_, value]) => value > 0)
    .map(([key, value]) => ({
      name: STATUS_LABELS[key] || key,
      value,
      color: STATUS_COLORS[key] || '#6B7280',
    }));

  const total = Object.values(data).reduce((sum, v) => sum + v, 0);

  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">机器人状态分布</h3>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [`${value} 台`, '数量']}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* 图例 */}
      <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
        {chartData.map((item, index) => (
          <div key={index} className="flex items-center">
            <div
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: item.color }}
            />
            <span>{item.name}: {item.value}</span>
          </div>
        ))}
      </div>

      <div className="mt-4 text-center text-sm text-gray-500">
        共 {total} 台机器人
      </div>
    </div>
  );
};
```

#### 4.2.4 任务进度卡片

```typescript
// pages/operations/dashboard/components/TaskProgressCard.tsx
import React from 'react';
import { CheckCircleIcon, ClockIcon, PlayCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';
import { TaskProgress, TaskSummary } from '../types';

interface TaskProgressCardProps {
  data?: TaskProgress;
  loading: boolean;
}

const STATUS_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  completed: { icon: CheckCircleIcon, color: 'text-green-500', label: '已完成' },
  in_progress: { icon: PlayCircleIcon, color: 'text-blue-500', label: '进行中' },
  pending: { icon: ClockIcon, color: 'text-gray-400', label: '待执行' },
  failed: { icon: XCircleIcon, color: 'text-red-500', label: '失败' },
};

export const TaskProgressCard: React.FC<TaskProgressCardProps> = ({
  data,
  loading,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="h-4 bg-gray-200 rounded-full mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const progressPercent = data.total > 0 
    ? Math.round((data.completed / data.total) * 100) 
    : 0;

  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">今日任务进度</h3>

      {/* 进度条 */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span>完成进度</span>
          <span className="font-medium">{progressPercent}%</span>
        </div>
        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="mt-1 text-sm text-gray-500">
          已完成: {data.completed} / {data.total} 任务
        </div>
      </div>

      {/* 任务统计 */}
      <div className="grid grid-cols-4 gap-2 mb-4 text-center text-sm">
        <div className="p-2 bg-green-50 rounded">
          <div className="font-semibold text-green-600">{data.completed}</div>
          <div className="text-gray-500">已完成</div>
        </div>
        <div className="p-2 bg-blue-50 rounded">
          <div className="font-semibold text-blue-600">{data.inProgress}</div>
          <div className="text-gray-500">进行中</div>
        </div>
        <div className="p-2 bg-gray-50 rounded">
          <div className="font-semibold text-gray-600">{data.pending}</div>
          <div className="text-gray-500">待执行</div>
        </div>
        <div className="p-2 bg-red-50 rounded">
          <div className="font-semibold text-red-600">{data.failed}</div>
          <div className="text-gray-500">失败</div>
        </div>
      </div>

      {/* 任务列表 */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {data.tasks.slice(0, 5).map((task) => {
          const config = STATUS_CONFIG[task.status];
          const Icon = config.icon;
          
          return (
            <div
              key={task.id}
              className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100"
            >
              <div className="flex items-center">
                <Icon className={`w-5 h-5 ${config.color} mr-2`} />
                <span className="text-sm font-medium">{task.name}</span>
              </div>
              <div className="text-sm text-gray-500">
                {task.status === 'completed' && task.completedTime
                  ? new Date(task.completedTime).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) + ' 完成'
                  : task.status === 'in_progress'
                    ? '进行中...'
                    : new Date(task.scheduledTime).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
                }
              </div>
            </div>
          );
        })}
      </div>

      {data.tasks.length > 5 && (
        <div className="mt-3 text-center">
          <a href="/operations/tasks" className="text-sm text-blue-600 hover:underline">
            查看全部任务 →
          </a>
        </div>
      )}
    </div>
  );
};
```

---

## 5. 测试要求

### 5.1 单元测试

```typescript
// pages/operations/dashboard/__tests__/OperationsDashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OperationsDashboard } from '../index';

const mockKPIData: KPIData = {
  completionRate: { value: 0.875, trend: 2.3, target: 0.85 },
  efficiency: { value: 156, trend: 5.2, target: 150 },
  robotOnline: { online: 8, total: 10, trend: -1 },
  pendingAlerts: { count: 3, trend: 1, bySeverity: { critical: 1, high: 1, medium: 1, low: 0 } },
};

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

jest.mock('../../../api/data', () => ({
  fetchKPIOverview: jest.fn().mockResolvedValue(mockKPIData),
  fetchRobotStatusDistribution: jest.fn().mockResolvedValue({
    working: 5, charging: 2, idle: 1, paused: 0, error: 0, offline: 2,
  }),
  fetchTaskProgress: jest.fn().mockResolvedValue({
    total: 16, completed: 12, inProgress: 1, pending: 3, failed: 0, tasks: [],
  }),
  fetchEfficiencyTrend: jest.fn().mockResolvedValue([]),
  fetchAlerts: jest.fn().mockResolvedValue({ items: [], total: 0 }),
}));

describe('OperationsDashboard', () => {
  test('renders KPI cards', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <OperationsDashboard />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('清洁完成率')).toBeInTheDocument();
      expect(screen.getByText('87.5%')).toBeInTheDocument();
    });
  });

  test('displays correct status colors based on thresholds', async () => {
    // 测试阈值判断
  });

  test('handles filter changes', async () => {
    // 测试筛选功能
  });

  test('auto-refreshes data', async () => {
    // 测试自动刷新
  });
});
```

---

## 6. 验收标准

### 6.1 功能验收

| 验收项 | 验收标准 | 优先级 |
|-------|---------|-------|
| KPI展示 | 4个KPI卡片正确显示数值和趋势 | P0 |
| 状态判断 | 根据阈值正确显示正常/警告/严重状态 | P0 |
| 饼图展示 | 机器人状态分布饼图正确渲染 | P0 |
| 任务进度 | 进度条和任务列表正确显示 | P0 |
| 趋势图 | 效率趋势折线图正确渲染 | P1 |
| 告警列表 | 最新告警正确显示 | P1 |
| 筛选功能 | 楼宇/楼层/时间筛选正常工作 | P1 |
| 自动刷新 | 按配置间隔自动刷新数据 | P2 |

### 6.2 性能要求

| 指标 | 要求 |
|-----|------|
| 首屏加载 | < 1s |
| 数据刷新 | < 500ms |
| 图表渲染 | < 200ms |
| 内存占用 | < 50MB |

---

*文档结束*
