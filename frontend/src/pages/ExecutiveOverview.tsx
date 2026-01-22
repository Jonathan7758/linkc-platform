/**
 * E1 Executive Overview - Strategic Dashboard
 * 战略驾驶舱总览
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============ Type Definitions ============

interface CoreMetricsData {
  healthScore: {
    value: number;
    status: 'good' | 'warning' | 'critical';
    trend?: number;
  };
  taskCompletionRate: {
    value: number;
    trend: number;
    target: number;
  };
  costSaving: {
    value: number;
    period: 'day' | 'week' | 'month';
    breakdown: {
      laborSaving: number;
      efficiencySaving: number;
      energySaving: number;
    };
  };
  customerSatisfaction: {
    value: number;
    trend: number;
    reviewCount: number;
  };
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

interface TrendData {
  date: string;
  coverageRate: number;
  completionRate: number;
  efficiency: number;
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

interface ExecutiveOverviewProps {
  tenantId: string;
  onNavigateToOperations?: () => void;
  onNavigateToAnalytics?: () => void;
  onNavigateToReports?: () => void;
  onBuildingClick?: (buildingId: string) => void;
  onPendingActionClick?: (action: PendingActionItem) => void;
}

// ============ Mock Data ============

const mockCoreMetrics: CoreMetricsData = {
  healthScore: { value: 92, status: 'good', trend: 2.5 },
  taskCompletionRate: { value: 96.5, trend: 2.1, target: 95 },
  costSaving: {
    value: 125000,
    period: 'month',
    breakdown: {
      laborSaving: 82000,
      efficiencySaving: 31000,
      energySaving: 12000,
    },
  },
  customerSatisfaction: { value: 4.6, trend: 0.2, reviewCount: 128 },
};

const mockTodayOverview: TodayOverviewData = {
  tasks: { total: 48, completed: 42, inProgress: 5, pending: 0, failed: 1 },
  robots: { total: 15, online: 13, working: 10, error: 2 },
  coverage: { actual: 94.2, target: 95 },
  anomalies: { total: 3, handled: 2, pending: 1 },
};

const mockPendingActions: PendingActionItem[] = [
  {
    id: '1',
    level: 'critical',
    type: 'decision',
    title: '机器人采购计划需确认',
    description: '第二批机器人采购方案待批准，截止今天',
    deadline: '2026-01-21',
    source: '采购部',
    createdAt: '2026-01-20T10:00:00Z',
  },
  {
    id: '2',
    level: 'critical',
    type: 'decision',
    title: '清洁策略调整建议需批准',
    description: 'B栋清洁频率调整方案',
    source: '运营部',
    createdAt: '2026-01-20T14:00:00Z',
  },
  {
    id: '3',
    level: 'high',
    type: 'approval',
    title: '新增区域清洁排程',
    description: 'C栋新区域清洁计划待审批',
    source: '调度系统',
    createdAt: '2026-01-21T08:00:00Z',
  },
  {
    id: '4',
    level: 'high',
    type: 'approval',
    title: '耗材采购申请',
    description: '清洁耗材月度采购单',
    source: '仓储部',
    createdAt: '2026-01-21T09:00:00Z',
  },
  {
    id: '5',
    level: 'medium',
    type: 'alert',
    title: 'C栋覆盖率连续3天低于目标',
    description: '建议检查机器人配置和清洁路径',
    source: '监控系统',
    createdAt: '2026-01-21T07:00:00Z',
  },
];

const mockEfficiencyTrend: TrendData[] = [
  { date: '01-15', coverageRate: 92.5, completionRate: 95.2, efficiency: 1.15 },
  { date: '01-16', coverageRate: 93.1, completionRate: 96.1, efficiency: 1.18 },
  { date: '01-17', coverageRate: 91.8, completionRate: 94.8, efficiency: 1.12 },
  { date: '01-18', coverageRate: 94.5, completionRate: 97.2, efficiency: 1.22 },
  { date: '01-19', coverageRate: 93.8, completionRate: 96.5, efficiency: 1.19 },
  { date: '01-20', coverageRate: 94.0, completionRate: 96.8, efficiency: 1.21 },
  { date: '01-21', coverageRate: 94.2, completionRate: 96.5, efficiency: 1.20 },
];

const mockCostAnalysis: CostAnalysisData = {
  period: '2026年1月',
  totalSaving: 125000,
  breakdown: [
    { category: '人力替代', amount: 82000, percentage: 65.6 },
    { category: '效率提升', amount: 31000, percentage: 24.8 },
    { category: '能耗优化', amount: 12000, percentage: 9.6 },
  ],
  roi: 285,
  comparison: { previousPeriod: 118000, trend: 5.9 },
};

const mockBuildingStatus: BuildingStatusData[] = [
  { id: 'A', name: 'A栋', status: 'normal', coverageRate: 96, taskProgress: { completed: 12, total: 12 }, robotCount: 4, activeRobotCount: 4, alerts: 0 },
  { id: 'B', name: 'B栋', status: 'normal', coverageRate: 94, taskProgress: { completed: 10, total: 11 }, robotCount: 4, activeRobotCount: 3, alerts: 0 },
  { id: 'C', name: 'C栋', status: 'warning', coverageRate: 82, taskProgress: { completed: 6, total: 10 }, robotCount: 4, activeRobotCount: 3, alerts: 2 },
  { id: 'D', name: 'D栋', status: 'normal', coverageRate: 95, taskProgress: { completed: 8, total: 8 }, robotCount: 3, activeRobotCount: 3, alerts: 0 },
];

// ============ Sub Components ============

// Status Indicator
const StatusIndicator: React.FC<{ status: 'good' | 'warning' | 'critical' }> = ({ status }) => {
  const config = {
    good: { color: 'bg-green-500', label: '正常' },
    warning: { color: 'bg-yellow-500', label: '警告' },
    critical: { color: 'bg-red-500', label: '异常' },
  };
  const { color, label } = config[status];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white ${color}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-white mr-1"></span>
      {label}
    </span>
  );
};

// Trend Indicator
const TrendIndicator: React.FC<{ value: number; suffix?: string }> = ({ value, suffix = '%' }) => {
  if (value === 0) return <span className="text-gray-500">→ 0{suffix}</span>;
  const isUp = value > 0;
  return (
    <span className={isUp ? 'text-green-600' : 'text-red-600'}>
      {isUp ? '↑' : '↓'} {Math.abs(value).toFixed(1)}{suffix}
    </span>
  );
};

// Metric Card
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  unit?: string;
  status?: 'good' | 'warning' | 'critical';
  trend?: number;
  trendSuffix?: string;
  subtext?: string;
  onClick?: () => void;
}> = ({ title, value, unit, status, trend, trendSuffix = '%', subtext, onClick }) => {
  return (
    <div
      className={`bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow ${
        status === 'critical' ? 'border-l-4 border-red-500' :
        status === 'warning' ? 'border-l-4 border-yellow-500' :
        status === 'good' ? 'border-l-4 border-green-500' : ''
      }`}
      onClick={onClick}
    >
      <div className="text-sm text-gray-500 mb-1">{title}</div>
      <div className="flex items-baseline">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
      </div>
      <div className="mt-2 flex items-center justify-between">
        {status && <StatusIndicator status={status} />}
        {trend !== undefined && <TrendIndicator value={trend} suffix={trendSuffix} />}
        {subtext && <span className="text-xs text-gray-500">{subtext}</span>}
      </div>
    </div>
  );
};

// Core Metrics Panel
const CoreMetricsPanel: React.FC<{
  metrics: CoreMetricsData;
  onMetricClick: (key: string) => void;
}> = ({ metrics, onMetricClick }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard
        title="运营健康度"
        value={metrics.healthScore.value}
        unit="%"
        status={metrics.healthScore.status}
        trend={metrics.healthScore.trend}
        onClick={() => onMetricClick('health')}
      />
      <MetricCard
        title="任务完成率"
        value={metrics.taskCompletionRate.value}
        unit="%"
        trend={metrics.taskCompletionRate.trend}
        subtext={`目标: ${metrics.taskCompletionRate.target}%`}
        onClick={() => onMetricClick('tasks')}
      />
      <MetricCard
        title="成本节约"
        value={`¥${(metrics.costSaving.value / 10000).toFixed(1)}`}
        unit="万"
        subtext={metrics.costSaving.period === 'month' ? '本月' : metrics.costSaving.period === 'week' ? '本周' : '今日'}
        onClick={() => onMetricClick('cost')}
      />
      <MetricCard
        title="客户满意度"
        value={metrics.customerSatisfaction.value.toFixed(1)}
        unit="/5"
        trend={metrics.customerSatisfaction.trend}
        trendSuffix=""
        subtext={`${metrics.customerSatisfaction.reviewCount}条评价`}
        onClick={() => onMetricClick('satisfaction')}
      />
    </div>
  );
};

// Today Overview Panel
const TodayOverviewPanel: React.FC<{
  data: TodayOverviewData;
  onDetailClick: () => void;
}> = ({ data, onDetailClick }) => {
  const coverageStatus = data.coverage.actual >= data.coverage.target ? 'text-green-600' : 'text-yellow-600';

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">今日运营概览</h3>
        <button
          onClick={onDetailClick}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          查看详情 →
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center py-2 border-b border-gray-100">
          <span className="text-gray-600">今日任务</span>
          <span className="font-medium">
            {data.tasks.total}个
            <span className="text-green-600 ml-2">完成:{data.tasks.completed}</span>
            <span className="text-blue-600 ml-2">进行:{data.tasks.inProgress}</span>
            {data.tasks.failed > 0 && <span className="text-red-600 ml-2">失败:{data.tasks.failed}</span>}
          </span>
        </div>

        <div className="flex justify-between items-center py-2 border-b border-gray-100">
          <span className="text-gray-600">机器人</span>
          <span className="font-medium">
            {data.robots.total}台
            <span className="text-green-600 ml-2">在线:{data.robots.online}</span>
            {data.robots.error > 0 && <span className="text-red-600 ml-2">异常:{data.robots.error}</span>}
          </span>
        </div>

        <div className="flex justify-between items-center py-2 border-b border-gray-100">
          <span className="text-gray-600">覆盖率</span>
          <span className={`font-medium ${coverageStatus}`}>
            {data.coverage.actual}% <span className="text-gray-400">目标:{data.coverage.target}%</span>
          </span>
        </div>

        <div className="flex justify-between items-center py-2">
          <span className="text-gray-600">异常事件</span>
          <span className="font-medium">
            {data.anomalies.total}个
            <span className="text-green-600 ml-2">已处理:{data.anomalies.handled}</span>
            {data.anomalies.pending > 0 && <span className="text-yellow-600 ml-2">待处理:{data.anomalies.pending}</span>}
          </span>
        </div>
      </div>
    </div>
  );
};

// Pending Actions Panel
const PendingActionsPanel: React.FC<{
  items: PendingActionItem[];
  onItemClick: (item: PendingActionItem) => void;
  onViewAll: () => void;
}> = ({ items, onItemClick, onViewAll }) => {
  const levelConfig = {
    critical: { icon: '🔴', color: 'text-red-600', bg: 'bg-red-50' },
    high: { icon: '🟠', color: 'text-orange-600', bg: 'bg-orange-50' },
    medium: { icon: '🟡', color: 'text-yellow-600', bg: 'bg-yellow-50' },
    low: { icon: '🟢', color: 'text-green-600', bg: 'bg-green-50' },
  };

  const typeLabels = {
    decision: '需决策',
    approval: '需审批',
    review: '需审阅',
    alert: '需关注',
  };

  // Sort by level
  const sortedItems = [...items].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return order[a.level] - order[b.level];
  });

  // Count by level
  const criticalCount = items.filter(i => i.level === 'critical').length;
  const highCount = items.filter(i => i.level === 'high').length;
  const mediumCount = items.filter(i => i.level === 'medium' || i.level === 'low').length;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">待处理事项</h3>
        <button
          onClick={onViewAll}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          查看全部 →
        </button>
      </div>

      {/* Summary */}
      <div className="flex space-x-4 mb-4 text-sm">
        {criticalCount > 0 && <span className="text-red-600">🔴 {criticalCount}项紧急</span>}
        {highCount > 0 && <span className="text-orange-600">🟠 {highCount}项需审批</span>}
        {mediumCount > 0 && <span className="text-yellow-600">🟡 {mediumCount}项需关注</span>}
      </div>

      {/* Items */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {sortedItems.slice(0, 5).map(item => {
          const config = levelConfig[item.level];
          return (
            <div
              key={item.id}
              className={`p-2 rounded cursor-pointer hover:opacity-80 ${config.bg}`}
              onClick={() => onItemClick(item)}
            >
              <div className="flex items-start">
                <span className="mr-2">{config.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className={`font-medium text-sm ${config.color}`}>
                    {typeLabels[item.type]}: {item.title}
                  </div>
                  <div className="text-xs text-gray-500 truncate">{item.description}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Simple Line Chart using SVG
const SimpleLineChart: React.FC<{
  data: TrendData[];
  height?: number;
}> = ({ data, height = 180 }) => {
  // width removed - unused
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartWidth = 400;
  const chartHeight = height;

  // Calculate scales
  const allValues = data.flatMap(d => [d.coverageRate, d.completionRate]);
  const minY = Math.min(...allValues) - 2;
  const maxY = Math.max(...allValues) + 2;

  const xScale = (i: number) => padding.left + (i / (data.length - 1)) * (chartWidth - padding.left - padding.right);
  const yScale = (v: number) => chartHeight - padding.bottom - ((v - minY) / (maxY - minY)) * (chartHeight - padding.top - padding.bottom);

  // Generate path
  const coveragePath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.coverageRate)}`).join(' ');
  const completionPath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.completionRate)}`).join(' ');

  return (
    <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full" style={{ height }}>
      {/* Grid lines */}
      {[minY, (minY + maxY) / 2, maxY].map((v, i) => (
        <g key={i}>
          <line
            x1={padding.left}
            y1={yScale(v)}
            x2={chartWidth - padding.right}
            y2={yScale(v)}
            stroke="#e5e7eb"
            strokeDasharray="3,3"
          />
          <text x={padding.left - 5} y={yScale(v)} fontSize="10" fill="#6b7280" textAnchor="end" dominantBaseline="middle">
            {v.toFixed(0)}%
          </text>
        </g>
      ))}

      {/* X axis labels */}
      {data.map((d, i) => (
        <text
          key={i}
          x={xScale(i)}
          y={chartHeight - 10}
          fontSize="10"
          fill="#6b7280"
          textAnchor="middle"
        >
          {d.date}
        </text>
      ))}

      {/* Lines */}
      <path d={coveragePath} fill="none" stroke="#3b82f6" strokeWidth="2" />
      <path d={completionPath} fill="none" stroke="#22c55e" strokeWidth="2" />

      {/* Data points */}
      {data.map((d, i) => (
        <g key={i}>
          <circle cx={xScale(i)} cy={yScale(d.coverageRate)} r="3" fill="#3b82f6" />
          <circle cx={xScale(i)} cy={yScale(d.completionRate)} r="3" fill="#22c55e" />
        </g>
      ))}

      {/* Legend */}
      <g transform={`translate(${chartWidth - 120}, 10)`}>
        <rect x="0" y="0" width="10" height="10" fill="#3b82f6" />
        <text x="15" y="9" fontSize="10" fill="#374151">覆盖率</text>
        <rect x="60" y="0" width="10" height="10" fill="#22c55e" />
        <text x="75" y="9" fontSize="10" fill="#374151">完成率</text>
      </g>
    </svg>
  );
};

// Efficiency Trend Panel
const EfficiencyTrendPanel: React.FC<{
  data: TrendData[];
  period: 'week' | 'month' | 'quarter';
  onPeriodChange: (period: 'week' | 'month' | 'quarter') => void;
}> = ({ data, period, onPeriodChange }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">效率趋势</h3>
        <div className="flex space-x-1">
          {(['week', 'month', 'quarter'] as const).map(p => (
            <button
              key={p}
              onClick={() => onPeriodChange(p)}
              className={`px-3 py-1 text-sm rounded ${
                period === p
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {p === 'week' ? '近7天' : p === 'month' ? '近30天' : '近3月'}
            </button>
          ))}
        </div>
      </div>

      <SimpleLineChart data={data} height={180} />
    </div>
  );
};

// Cost Analysis Panel
const CostAnalysisPanel: React.FC<{
  data: CostAnalysisData;
  onDetailClick: () => void;
}> = ({ data, onDetailClick }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">成本分析</h3>
        <button
          onClick={onDetailClick}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          查看详情 →
        </button>
      </div>

      <div className="space-y-3">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-sm text-gray-500">{data.period}节约</div>
          <div className="text-2xl font-bold text-green-600">
            ¥{(data.totalSaving / 10000).toFixed(1)}万
          </div>
          <div className="text-xs text-gray-500 mt-1">
            <TrendIndicator value={data.comparison.trend} /> 较上期
          </div>
        </div>

        <div className="space-y-2">
          {data.breakdown.map((item, index) => (
            <div key={index} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{item.category}</span>
              <span className="font-medium">
                ¥{(item.amount / 10000).toFixed(1)}万
                <span className="text-gray-400 ml-1">({item.percentage}%)</span>
              </span>
            </div>
          ))}
        </div>

        <div className="pt-3 border-t border-gray-100">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">投资回报率 (ROI)</span>
            <span className="text-xl font-bold text-blue-600">{data.roi}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Building Status Card
const BuildingCard: React.FC<{
  building: BuildingStatusData;
  onClick: () => void;
}> = ({ building, onClick }) => {
  const statusConfig = {
    normal: { bg: 'bg-green-50', border: 'border-green-200', icon: '●', color: 'text-green-600' },
    warning: { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: '⚠', color: 'text-yellow-600' },
    error: { bg: 'bg-red-50', border: 'border-red-200', icon: '✖', color: 'text-red-600' },
  };
  const config = statusConfig[building.status];

  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer hover:shadow-md transition-shadow ${config.bg} ${config.border}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="font-medium text-gray-900">{building.name}</span>
        <span className={config.color}>{config.icon} {building.status === 'normal' ? '正常' : building.status === 'warning' ? '警告' : '异常'}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-500">覆盖率:</span>
          <span className={`ml-1 font-medium ${building.coverageRate >= 90 ? 'text-green-600' : 'text-yellow-600'}`}>
            {building.coverageRate}%
          </span>
        </div>
        <div>
          <span className="text-gray-500">任务:</span>
          <span className="ml-1 font-medium">
            {building.taskProgress.completed}/{building.taskProgress.total}
          </span>
        </div>
      </div>

      {building.alerts > 0 && (
        <div className="mt-2 text-sm text-red-600">
          ⚠ {building.alerts}个告警
        </div>
      )}
    </div>
  );
};

// Building Status Grid
const BuildingStatusGrid: React.FC<{
  buildings: BuildingStatusData[];
  onBuildingClick: (buildingId: string) => void;
}> = ({ buildings, onBuildingClick }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">楼宇运营状态</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {buildings.map(building => (
          <BuildingCard
            key={building.id}
            building={building}
            onClick={() => onBuildingClick(building.id)}
          />
        ))}
      </div>
    </div>
  );
};

// ============ Main Component ============

export const ExecutiveOverview: React.FC<ExecutiveOverviewProps> = ({
  tenantId,
  onNavigateToOperations,
  onNavigateToAnalytics,
  onNavigateToReports,
  onBuildingClick,
  onPendingActionClick,
}) => {
  // State
  const [coreMetrics, _setCoreMetrics] = useState<CoreMetricsData>(mockCoreMetrics);
  const [todayOverview, _setTodayOverview] = useState<TodayOverviewData>(mockTodayOverview);
  const [pendingActions, _setPendingActions] = useState<PendingActionItem[]>(mockPendingActions);
  const [efficiencyTrend, _setEfficiencyTrend] = useState<TrendData[]>(mockEfficiencyTrend);
  const [costAnalysis, _setCostAnalysis] = useState<CostAnalysisData>(mockCostAnalysis);
  const [buildingStatus, _setBuildingStatus] = useState<BuildingStatusData[]>(mockBuildingStatus);
  const [trendPeriod, setTrendPeriod] = useState<'week' | 'month' | 'quarter'>('week');
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // In production, fetch from API
      // const data = await dashboardApi.getAllData(tenantId);
      await new Promise(resolve => setTimeout(resolve, 500));
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  // Initial load and auto refresh
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every 60 seconds
    return () => clearInterval(interval);
  }, [loadData]);

  // Handlers
  const handleMetricClick = (key: string) => {
    console.log('Metric clicked:', key);
    if (key === 'tasks' && onNavigateToOperations) {
      onNavigateToOperations();
    }
  };

  const handlePendingActionClick = (action: PendingActionItem) => {
    if (onPendingActionClick) {
      onPendingActionClick(action);
    } else {
      console.log('Pending action clicked:', action);
    }
  };

  const handleBuildingClick = (buildingId: string) => {
    if (onBuildingClick) {
      onBuildingClick(buildingId);
    } else {
      console.log('Building clicked:', buildingId);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">智能清洁运营驾驶舱</h1>
          <p className="text-sm text-gray-500 mt-1">
            最后更新: {lastUpdated.toLocaleTimeString('zh-CN')}
            {loading && <span className="ml-2 text-blue-600">刷新中...</span>}
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            刷新
          </button>
          {onNavigateToReports && (
            <button
              onClick={onNavigateToReports}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              生成报表
            </button>
          )}
        </div>
      </div>

      {/* Core Metrics */}
      <CoreMetricsPanel metrics={coreMetrics} onMetricClick={handleMetricClick} />

      {/* Middle Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <TodayOverviewPanel
          data={todayOverview}
          onDetailClick={() => onNavigateToOperations?.()}
        />
        <PendingActionsPanel
          items={pendingActions}
          onItemClick={handlePendingActionClick}
          onViewAll={() => console.log('View all pending actions')}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <EfficiencyTrendPanel
          data={efficiencyTrend}
          period={trendPeriod}
          onPeriodChange={setTrendPeriod}
        />
        <CostAnalysisPanel
          data={costAnalysis}
          onDetailClick={() => onNavigateToAnalytics?.()}
        />
      </div>

      {/* Building Status */}
      <BuildingStatusGrid
        buildings={buildingStatus}
        onBuildingClick={handleBuildingClick}
      />
    </div>
  );
};

export default ExecutiveOverview;
