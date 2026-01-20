# E1 战略驾驶舱总览规格书

## 文档信息

| 属性 | 值 |
|-----|-----|
| 模块ID | E1 |
| 模块名称 | 战略驾驶舱总览 (Executive Overview) |
| 版本 | 1.0 |
| 日期 | 2026-01-20 |
| 状态 | 规划中 |
| 所属终端 | 战略驾驶舱 (Executive Dashboard) |
| 前置依赖 | G6-data-api |

---

## 一、模块概述

### 1.1 职责描述

战略驾驶舱总览是高管层的核心界面，提供清洁运营的全局视图，帮助管理层快速了解运营状况、识别问题和做出决策。设计原则是**一屏呈现关键信息，3秒内获取全局状态**。

### 1.2 目标用户

| 角色 | 关注点 | 使用频率 |
|-----|-------|---------|
| CEO/COO | 整体运营状况、成本效益 | 每天1-2次 |
| 运营总监 | KPI达成、异常情况 | 每天3-5次 |
| 财务总监 | 成本节约、ROI | 每周1-2次 |

### 1.3 设计原则

| 原则 | 说明 |
|-----|------|
| **信息密度适中** | 关键数据一目了然，避免信息过载 |
| **异常突出** | 红绿灯机制，异常情况醒目提示 |
| **可下钻** | 点击可深入查看详情 |
| **移动友好** | 适配平板和手机查看 |

---

## 二、页面布局

### 2.1 整体布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LinkC 智能清洁运营驾驶舱                    2026-01-20 08:30  张总 ▼      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          核心指标面板                               │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │   │
│  │  │ 运营健康度│ │ 任务完成率│ │ 成本节约  │ │ 客户满意度│           │   │
│  │  │   92%    │ │   96.5%   │ │  ¥12.5万  │ │   4.6/5   │           │   │
│  │  │  ●正常   │ │  ↑2.1%   │ │  本月     │ │  ↑0.2    │           │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────────┐   │
│  │ 今日运营概览                    │ │ 待处理事项                      │   │
│  │ ┌─────────────────────────────┐│ │ ┌─────────────────────────────┐ │   │
│  │ │ 今日任务: 48 完成:42 进行:5 ││ │ │ 🔴 2项紧急需决策            │ │   │
│  │ │ 机器人: 15台 在线:13 异常:2 ││ │ │ 🟠 3项需审批                │ │   │
│  │ │ 覆盖率: 94.2%  目标:95%    ││ │ │ 🟡 5项需关注                │ │   │
│  │ │ 异常事件: 3  已处理:2       ││ │ │                             │ │   │
│  │ └─────────────────────────────┘│ │ │ [查看全部 →]                │ │   │
│  │ [查看详情 →]                   │ │ └─────────────────────────────┘ │   │
│  └─────────────────────────────────┘ └─────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────────┐   │
│  │ 效率趋势 (近7天)                │ │ 成本分析                        │   │
│  │ ┌─────────────────────────────┐│ │ ┌─────────────────────────────┐ │   │
│  │ │     📈                      ││ │ │ 本月节约: ¥12.5万           │ │   │
│  │ │   /\    /\                  ││ │ │ ├─ 人力替代: ¥8.2万         │ │   │
│  │ │  /  \  /  \  /              ││ │ │ ├─ 效率提升: ¥3.1万         │ │   │
│  │ │ /    \/    \/               ││ │ │ └─ 能耗优化: ¥1.2万         │ │   │
│  │ │覆盖率 完成率 效率           ││ │ │ ROI: 285%                   │ │   │
│  │ └─────────────────────────────┘│ │ └─────────────────────────────┘ │   │
│  └─────────────────────────────────┘ └─────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 楼宇运营状态                                                        │   │
│  │ ┌──────────────┬──────────────┬──────────────┬──────────────┐       │   │
│  │ │ A栋 ●正常   │ B栋 ●正常   │ C栋 ⚠警告  │ D栋 ●正常   │       │   │
│  │ │ 覆盖:96%    │ 覆盖:94%    │ 覆盖:82%    │ 覆盖:95%    │       │   │
│  │ │ 任务:12/12  │ 任务:10/11  │ 任务:6/10   │ 任务:8/8    │       │   │
│  │ └──────────────┴──────────────┴──────────────┴──────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、组件定义

### 3.1 核心指标面板 (CoreMetrics)

```typescript
interface CoreMetricsProps {
  metrics: CoreMetricsData;
  onMetricClick: (metricKey: string) => void;
}

interface CoreMetricsData {
  healthScore: {
    value: number;        // 0-100
    status: 'good' | 'warning' | 'critical';
    trend?: number;       // 较上期变化
  };
  taskCompletionRate: {
    value: number;        // 百分比
    trend: number;        // 较上期变化
    target: number;       // 目标值
  };
  costSaving: {
    value: number;        // 金额
    period: 'day' | 'week' | 'month';
    breakdown: {
      laborSaving: number;
      efficiencySaving: number;
      energySaving: number;
    };
  };
  customerSatisfaction: {
    value: number;        // 1-5分
    trend: number;
    reviewCount: number;
  };
}

// 状态阈值配置
const healthThresholds = {
  good: { min: 85, color: '#52c41a', label: '正常' },
  warning: { min: 70, max: 85, color: '#faad14', label: '警告' },
  critical: { max: 70, color: '#ff4d4f', label: '异常' }
};
```

**指标卡片设计**：

```typescript
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  unit?: string;
  status?: 'good' | 'warning' | 'critical';
  trend?: number;
  onClick?: () => void;
}> = ({ title, value, unit, status, trend, onClick }) => {
  return (
    <div className={`metric-card ${status}`} onClick={onClick}>
      <div className="metric-title">{title}</div>
      <div className="metric-value">
        {value}{unit && <span className="unit">{unit}</span>}
      </div>
      {status && <StatusIndicator status={status} />}
      {trend !== undefined && <TrendIndicator value={trend} />}
    </div>
  );
};
```

### 3.2 今日运营概览 (TodayOverview)

```typescript
interface TodayOverviewProps {
  data: TodayOverviewData;
  onDetailClick: () => void;
}

interface TodayOverviewData {
  tasks: {
    total: number;
    completed: number;
    inProgress: number;
    pending: number;
    failed: number;
  };
  robots: {
    total: number;
    online: number;
    working: number;
    error: number;
  };
  coverage: {
    actual: number;
    target: number;
  };
  anomalies: {
    total: number;
    handled: number;
    pending: number;
  };
}
```

### 3.3 待处理事项 (PendingActions)

```typescript
interface PendingActionsProps {
  items: PendingActionItem[];
  onItemClick: (item: PendingActionItem) => void;
  onViewAll: () => void;
}

interface PendingActionItem {
  id: string;
  level: 'critical' | 'high' | 'medium' | 'low';
  type: 'decision' | 'approval' | 'review' | 'alert';
  title: string;
  description: string;
  deadline?: string;
  source: string;
  createdAt: string;
}

// 待处理事项类型
const actionTypes = {
  decision: { label: '需决策', icon: 'decision', color: 'red' },
  approval: { label: '需审批', icon: 'audit', color: 'orange' },
  review: { label: '需审阅', icon: 'file-search', color: 'blue' },
  alert: { label: '需关注', icon: 'alert', color: 'yellow' }
};
```

**待处理事项示例**：
- 🔴 决策：机器人采购计划需确认（截止今天）
- 🔴 决策：清洁策略调整建议需批准
- 🟠 审批：新增区域清洁排程
- 🟠 审批：耗材采购申请
- 🟡 关注：C栋覆盖率连续3天低于目标

### 3.4 效率趋势图 (EfficiencyTrend)

```typescript
interface EfficiencyTrendProps {
  data: TrendData[];
  period: 'week' | 'month' | 'quarter';
  onPeriodChange: (period: 'week' | 'month' | 'quarter') => void;
}

interface TrendData {
  date: string;
  coverageRate: number;      // 覆盖率
  completionRate: number;    // 完成率
  efficiency: number;        // 效率指数
}

// 使用Recharts绑制趋势图
const EfficiencyTrend: React.FC<EfficiencyTrendProps> = ({ data, period, onPeriodChange }) => {
  return (
    <div className="efficiency-trend">
      <div className="chart-header">
        <h3>效率趋势</h3>
        <SegmentedControl
          options={[
            { value: 'week', label: '近7天' },
            { value: 'month', label: '近30天' },
            { value: 'quarter', label: '近3月' }
          ]}
          value={period}
          onChange={onPeriodChange}
        />
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[80, 100]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="coverageRate" name="覆盖率" stroke="#1890ff" />
          <Line type="monotone" dataKey="completionRate" name="完成率" stroke="#52c41a" />
          <Line type="monotone" dataKey="efficiency" name="效率" stroke="#722ed1" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 3.5 成本分析卡片 (CostAnalysis)

```typescript
interface CostAnalysisProps {
  data: CostAnalysisData;
  onDetailClick: () => void;
}

interface CostAnalysisData {
  period: string;
  totalSaving: number;
  breakdown: {
    category: string;
    amount: number;
    percentage: number;
  }[];
  roi: number;
  comparison: {
    previousPeriod: number;
    trend: number;
  };
}
```

### 3.6 楼宇状态概览 (BuildingStatus)

```typescript
interface BuildingStatusProps {
  buildings: BuildingStatusData[];
  onBuildingClick: (buildingId: string) => void;
}

interface BuildingStatusData {
  id: string;
  name: string;
  status: 'normal' | 'warning' | 'error';
  coverageRate: number;
  taskProgress: {
    completed: number;
    total: number;
  };
  robotCount: number;
  activeRobotCount: number;
  alerts: number;
}

// 楼宇卡片
const BuildingCard: React.FC<{
  building: BuildingStatusData;
  onClick: () => void;
}> = ({ building, onClick }) => {
  return (
    <div 
      className={`building-card status-${building.status}`} 
      onClick={onClick}
    >
      <div className="building-header">
        <span className="building-name">{building.name}</span>
        <StatusBadge status={building.status} />
      </div>
      <div className="building-metrics">
        <div className="metric">
          <span className="label">覆盖率</span>
          <span className="value">{building.coverageRate}%</span>
        </div>
        <div className="metric">
          <span className="label">任务</span>
          <span className="value">
            {building.taskProgress.completed}/{building.taskProgress.total}
          </span>
        </div>
      </div>
      {building.alerts > 0 && (
        <div className="building-alerts">
          <AlertOutlined /> {building.alerts}个告警
        </div>
      )}
    </div>
  );
};
```

---

## 四、数据流设计

### 4.1 状态管理

```typescript
// Dashboard Store (Zustand)
interface DashboardStore {
  // 数据状态
  coreMetrics: CoreMetricsData | null;
  todayOverview: TodayOverviewData | null;
  pendingActions: PendingActionItem[];
  efficiencyTrend: TrendData[];
  costAnalysis: CostAnalysisData | null;
  buildingStatus: BuildingStatusData[];
  
  // 加载状态
  loading: {
    coreMetrics: boolean;
    todayOverview: boolean;
    pendingActions: boolean;
    efficiencyTrend: boolean;
    costAnalysis: boolean;
    buildingStatus: boolean;
  };
  
  // 配置
  trendPeriod: 'week' | 'month' | 'quarter';
  
  // Actions
  fetchCoreMetrics: () => Promise<void>;
  fetchTodayOverview: () => Promise<void>;
  fetchPendingActions: () => Promise<void>;
  fetchEfficiencyTrend: (period: string) => Promise<void>;
  fetchCostAnalysis: () => Promise<void>;
  fetchBuildingStatus: () => Promise<void>;
  
  // 刷新全部
  refreshAll: () => Promise<void>;
  
  // 设置
  setTrendPeriod: (period: 'week' | 'month' | 'quarter') => void;
}
```

### 4.2 API调用

```typescript
const dashboardApi = {
  // 核心指标
  getCoreMetrics: (): Promise<CoreMetricsData> =>
    api.get('/api/v1/dashboard/metrics'),
  
  // 今日概览
  getTodayOverview: (): Promise<TodayOverviewData> =>
    api.get('/api/v1/dashboard/today'),
  
  // 待处理事项
  getPendingActions: (): Promise<PendingActionItem[]> =>
    api.get('/api/v1/dashboard/pending-actions'),
  
  // 效率趋势
  getEfficiencyTrend: (period: string): Promise<TrendData[]> =>
    api.get('/api/v1/dashboard/efficiency-trend', { params: { period } }),
  
  // 成本分析
  getCostAnalysis: (): Promise<CostAnalysisData> =>
    api.get('/api/v1/dashboard/cost-analysis'),
  
  // 楼宇状态
  getBuildingStatus: (): Promise<BuildingStatusData[]> =>
    api.get('/api/v1/dashboard/building-status'),
};
```

### 4.3 自动刷新

```typescript
// 自动刷新Hook
const useAutoRefresh = (interval: number = 60000) => {
  const refreshAll = useDashboardStore(state => state.refreshAll);
  
  useEffect(() => {
    // 初始加载
    refreshAll();
    
    // 定时刷新
    const timer = setInterval(refreshAll, interval);
    
    return () => clearInterval(timer);
  }, [interval]);
  
  // 页面可见性变化时刷新
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        refreshAll();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);
};
```

---

## 五、交互设计

### 5.1 下钻导航

| 点击元素 | 跳转目标 | 参数 |
|---------|---------|------|
| 运营健康度 | 运营详情页 | - |
| 任务完成率 | 任务管理页 | 筛选：今日 |
| 成本节约 | 成本分析报告 | - |
| 客户满意度 | 满意度报告 | - |
| 今日概览-查看详情 | 运营控制台 | - |
| 待处理事项 | 对应详情页 | 事项ID |
| 楼宇卡片 | 楼宇详情页 | 楼宇ID |

### 5.2 数据刷新

```
自动刷新：每60秒
手动刷新：点击刷新按钮
页面激活时：自动刷新
```

### 5.3 响应式布局

```typescript
// 断点配置
const breakpoints = {
  desktop: 1200,   // 4列布局
  tablet: 768,     // 2列布局
  mobile: 480      // 1列布局
};

// 响应式Grid配置
const gridConfig = {
  desktop: {
    columns: 4,
    gap: 24
  },
  tablet: {
    columns: 2,
    gap: 16
  },
  mobile: {
    columns: 1,
    gap: 12
  }
};
```

---

## 六、测试要求

### 6.1 单元测试

```typescript
describe('CoreMetrics', () => {
  it('应正确渲染所有指标卡片', () => {
    const metrics = mockCoreMetrics();
    render(<CoreMetrics metrics={metrics} onMetricClick={() => {}} />);
    
    expect(screen.getByText('运营健康度')).toBeInTheDocument();
    expect(screen.getByText('任务完成率')).toBeInTheDocument();
    expect(screen.getByText('成本节约')).toBeInTheDocument();
    expect(screen.getByText('客户满意度')).toBeInTheDocument();
  });

  it('健康度异常时应显示警告状态', () => {
    const metrics = mockCoreMetrics({ healthScore: { value: 65, status: 'critical' } });
    render(<CoreMetrics metrics={metrics} onMetricClick={() => {}} />);
    
    expect(screen.getByTestId('health-card')).toHaveClass('status-critical');
  });
});

describe('PendingActions', () => {
  it('应按级别排序显示待处理事项', () => {
    const items = [
      mockPendingAction({ level: 'medium', title: '中级事项' }),
      mockPendingAction({ level: 'critical', title: '紧急事项' }),
      mockPendingAction({ level: 'high', title: '高级事项' }),
    ];
    render(<PendingActions items={items} onItemClick={() => {}} onViewAll={() => {}} />);
    
    const actionItems = screen.getAllByTestId('action-item');
    expect(actionItems[0]).toHaveTextContent('紧急事项');
  });
});

describe('BuildingStatus', () => {
  it('警告状态楼宇应高亮显示', () => {
    const buildings = [
      mockBuilding({ id: '1', name: 'A栋', status: 'normal' }),
      mockBuilding({ id: '2', name: 'B栋', status: 'warning' }),
    ];
    render(<BuildingStatus buildings={buildings} onBuildingClick={() => {}} />);
    
    expect(screen.getByText('B栋').closest('.building-card')).toHaveClass('status-warning');
  });
});
```

### 6.2 集成测试

```typescript
describe('Executive Overview Integration', () => {
  it('页面加载时获取所有数据', async () => {
    render(<ExecutiveOverview />);
    
    await waitFor(() => {
      expect(dashboardApi.getCoreMetrics).toHaveBeenCalled();
      expect(dashboardApi.getTodayOverview).toHaveBeenCalled();
      expect(dashboardApi.getPendingActions).toHaveBeenCalled();
    });
  });

  it('点击楼宇卡片应跳转到详情', async () => {
    const { history } = renderWithRouter(<ExecutiveOverview />);
    
    await waitFor(() => screen.getByText('A栋'));
    fireEvent.click(screen.getByText('A栋'));
    
    expect(history.location.pathname).toBe('/buildings/building-a');
  });

  it('自动刷新应更新数据', async () => {
    jest.useFakeTimers();
    render(<ExecutiveOverview />);
    
    // 快进60秒
    jest.advanceTimersByTime(60000);
    
    // 应该再次调用API
    expect(dashboardApi.getCoreMetrics).toHaveBeenCalledTimes(2);
    
    jest.useRealTimers();
  });
});
```

---

## 七、验收标准

### 7.1 功能验收

| 验收项 | 标准 |
|-------|------|
| 核心指标 | 正确显示4个核心指标，状态颜色正确 |
| 今日概览 | 正确显示今日任务和机器人状态 |
| 待处理事项 | 按级别排序显示，可点击进入详情 |
| 效率趋势 | 图表正确渲染，可切换时间范围 |
| 楼宇状态 | 正确显示各楼宇状态，异常高亮 |
| 数据刷新 | 自动刷新和手动刷新均正常 |

### 7.2 性能要求

| 指标 | 要求 |
|-----|------|
| 首屏加载 | < 2s |
| 数据刷新 | < 1s |
| 图表渲染 | < 500ms |
| 交互响应 | < 100ms |

### 7.3 可用性要求

| 要求 | 说明 |
|-----|------|
| 响应式 | 适配桌面、平板、手机 |
| 加载状态 | 数据加载时显示骨架屏 |
| 错误处理 | 加载失败显示重试按钮 |
| 无障碍 | 支持键盘导航 |

---

## 八、文件结构

```
src/pages/executive/overview/
├── index.tsx                    # 主页面
├── Overview.module.css          # 样式
├── components/
│   ├── CoreMetrics/
│   │   ├── index.tsx
│   │   └── MetricCard.tsx
│   ├── TodayOverview/
│   │   └── index.tsx
│   ├── PendingActions/
│   │   ├── index.tsx
│   │   └── ActionItem.tsx
│   ├── EfficiencyTrend/
│   │   └── index.tsx
│   ├── CostAnalysis/
│   │   └── index.tsx
│   └── BuildingStatus/
│       ├── index.tsx
│       └── BuildingCard.tsx
├── hooks/
│   ├── useDashboardData.ts
│   └── useAutoRefresh.ts
├── stores/
│   └── dashboardStore.ts
└── __tests__/
    ├── CoreMetrics.test.tsx
    ├── PendingActions.test.tsx
    └── integration.test.tsx
```

---

**规格书结束**
