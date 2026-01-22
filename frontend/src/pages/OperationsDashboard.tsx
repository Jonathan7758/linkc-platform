/**
 * O1: Operations Dashboard
 * 运营控制台仪表板 - 提供全局运营视图
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============================================================
// Types
// ============================================================

interface KPIData {
  completionRate: number;
  completionRateTrend: number;
  avgEfficiency: number;
  efficiencyTrend: number;
  onlineRobots: number;
  totalRobots: number;
  robotTrend: number;
  pendingAlerts: number;
  alertTrend: number;
}

interface RobotStatusDistribution {
  working: number;
  charging: number;
  idle: number;
  offline: number;
  error: number;
}

interface TaskProgress {
  completed: number;
  total: number;
  tasks: {
    id: string;
    name: string;
    status: 'completed' | 'in_progress' | 'pending' | 'failed';
    time?: string;
  }[];
}

interface EfficiencyTrendPoint {
  date: string;
  value: number;
}

interface Alert {
  id: string;
  level: 'critical' | 'warning' | 'info';
  message: string;
  time: string;
  robotId?: string;
}

interface DashboardProps {
  tenantId: string;
  onNavigateToAlerts?: () => void;
  onNavigateToTasks?: () => void;
  onNavigateToRobots?: () => void;
}

// ============================================================
// Mock Data (Replace with API calls)
// ============================================================

const mockKPI: KPIData = {
  completionRate: 87.5,
  completionRateTrend: 2.3,
  avgEfficiency: 156,
  efficiencyTrend: 5.2,
  onlineRobots: 8,
  totalRobots: 10,
  robotTrend: -1,
  pendingAlerts: 3,
  alertTrend: 1,
};

const mockRobotStatus: RobotStatusDistribution = {
  working: 5,
  charging: 2,
  idle: 1,
  offline: 2,
  error: 0,
};

const mockTaskProgress: TaskProgress = {
  completed: 12,
  total: 16,
  tasks: [
    { id: 't1', name: '1F大堂清洁', status: 'completed', time: '09:00' },
    { id: 't2', name: '2F走廊清洁', status: 'completed', time: '10:30' },
    { id: 't3', name: '3F会议室', status: 'in_progress' },
    { id: 't4', name: '4F办公区', status: 'pending' },
  ],
};

const mockEfficiencyTrend: EfficiencyTrendPoint[] = [
  { date: '周一', value: 142 },
  { date: '周二', value: 148 },
  { date: '周三', value: 155 },
  { date: '周四', value: 162 },
  { date: '周五', value: 158 },
  { date: '周六', value: 165 },
  { date: '周日', value: 156 },
];

const mockAlerts: Alert[] = [
  { id: 'a1', level: 'critical', message: 'R3 电量低于10%', time: '5分钟前', robotId: 'robot_003' },
  { id: 'a2', level: 'warning', message: 'R5 清洁效率下降', time: '15分钟前', robotId: 'robot_005' },
  { id: 'a3', level: 'warning', message: '任务延迟告警', time: '30分钟前' },
];

// ============================================================
// KPI Card Component
// ============================================================

interface KPICardProps {
  title: string;
  icon: string;
  value: string;
  trend: number;
  trendLabel?: string;
  status?: 'normal' | 'warning' | 'critical';
  onClick?: () => void;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  icon,
  value,
  trend,
  trendLabel,
  status = 'normal',
  onClick,
}) => {
  const statusColors = {
    normal: 'bg-white',
    warning: 'bg-yellow-50 border-yellow-200',
    critical: 'bg-red-50 border-red-200',
  };

  const trendColor = trend >= 0 ? 'text-green-600' : 'text-red-600';
  const trendIcon = trend >= 0 ? '↑' : '↓';

  return (
    <div
      className={`p-4 rounded-lg border shadow-sm ${statusColors[status]} ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
        <span>{icon}</span>
        <span>{title}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className={`text-sm mt-1 ${trendColor}`}>
        {trendIcon} {Math.abs(trend)}{trendLabel || '%'}
      </div>
    </div>
  );
};

// ============================================================
// Robot Status Pie Chart Component
// ============================================================

interface RobotStatusChartProps {
  data: RobotStatusDistribution;
  onClick?: () => void;
}

const RobotStatusChart: React.FC<RobotStatusChartProps> = ({ data, onClick }) => {
  const total = data.working + data.charging + data.idle + data.offline + data.error;

  const segments = [
    { key: 'working', label: '工作中', count: data.working, color: '#22c55e' },
    { key: 'charging', label: '充电中', count: data.charging, color: '#3b82f6' },
    { key: 'idle', label: '空闲', count: data.idle, color: '#9ca3af' },
    { key: 'offline', label: '离线', count: data.offline, color: '#ef4444' },
    { key: 'error', label: '故障', count: data.error, color: '#f97316' },
  ].filter(s => s.count > 0);

  // Calculate pie chart segments
  let currentAngle = 0;
  const pieSegments = segments.map(segment => {
    const angle = (segment.count / total) * 360;
    const startAngle = currentAngle;
    currentAngle += angle;
    return { ...segment, startAngle, angle };
  });

  const polarToCartesian = (cx: number, cy: number, r: number, angle: number) => {
    const rad = (angle - 90) * Math.PI / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  };

  const describeArc = (cx: number, cy: number, r: number, startAngle: number, endAngle: number) => {
    const start = polarToCartesian(cx, cy, r, endAngle);
    const end = polarToCartesian(cx, cy, r, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;
    return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`;
  };

  return (
    <div
      className={`bg-white p-4 rounded-lg border shadow-sm ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      <h3 className="font-semibold text-gray-900 mb-4">机器人状态分布</h3>

      <div className="flex items-center gap-6">
        {/* Pie Chart */}
        <svg width="120" height="120" viewBox="0 0 120 120">
          {pieSegments.map((segment) => (
            <path
              key={segment.key}
              d={describeArc(60, 60, 50, segment.startAngle, segment.startAngle + segment.angle)}
              fill={segment.color}
            />
          ))}
          {/* Center circle for donut effect */}
          <circle cx="60" cy="60" r="30" fill="white" />
          <text x="60" y="55" textAnchor="middle" className="text-lg font-bold fill-gray-900">
            {total}
          </text>
          <text x="60" y="70" textAnchor="middle" className="text-xs fill-gray-500">
            台
          </text>
        </svg>

        {/* Legend */}
        <div className="flex flex-col gap-2">
          {segments.map(segment => (
            <div key={segment.key} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: segment.color }}
              />
              <span className="text-sm text-gray-600">
                {segment.label}: {segment.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============================================================
// Task Progress Component
// ============================================================

interface TaskProgressProps {
  data: TaskProgress;
  onClick?: () => void;
}

const TaskProgressCard: React.FC<TaskProgressProps> = ({ data, onClick }) => {
  const percentage = Math.round((data.completed / data.total) * 100);

  const statusConfig = {
    completed: { icon: '✅', color: 'text-green-600' },
    in_progress: { icon: '🔄', color: 'text-blue-600' },
    pending: { icon: '⏳', color: 'text-gray-400' },
    failed: { icon: '❌', color: 'text-red-600' },
  };

  return (
    <div
      className={`bg-white p-4 rounded-lg border shadow-sm ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      <h3 className="font-semibold text-gray-900 mb-4">今日任务进度</h3>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">已完成: {data.completed} / {data.total} 任务</span>
          <span className="font-medium">{percentage}%</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Task List */}
      <div className="space-y-2">
        {data.tasks.slice(0, 4).map(task => (
          <div
            key={task.id}
            className="flex items-center justify-between py-1.5 border-b last:border-0"
          >
            <div className="flex items-center gap-2">
              <span>{statusConfig[task.status].icon}</span>
              <span className={`text-sm ${statusConfig[task.status].color}`}>
                {task.name}
              </span>
            </div>
            <span className="text-xs text-gray-400">
              {task.status === 'completed' && task.time ? `${task.time}完成` :
               task.status === 'in_progress' ? '进行中...' :
               task.status === 'pending' ? '待执行' : '失败'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================
// Efficiency Trend Chart Component
// ============================================================

interface EfficiencyTrendProps {
  data: EfficiencyTrendPoint[];
}

const EfficiencyTrendChart: React.FC<EfficiencyTrendProps> = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue || 1;

  const chartWidth = 280;
  const chartHeight = 120;
  const padding = 30;

  const points = data.map((d, i) => ({
    x: padding + (i / (data.length - 1)) * (chartWidth - padding * 2),
    y: chartHeight - padding - ((d.value - minValue) / range) * (chartHeight - padding * 2),
    value: d.value,
    date: d.date,
  }));

  const linePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ');

  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      <h3 className="font-semibold text-gray-900 mb-4">清洁效率趋势（近7天）</h3>

      <svg width={chartWidth} height={chartHeight}>
        {/* Grid lines */}
        {[0, 1, 2, 3].map(i => (
          <line
            key={i}
            x1={padding}
            y1={padding + (i / 3) * (chartHeight - padding * 2)}
            x2={chartWidth - padding}
            y2={padding + (i / 3) * (chartHeight - padding * 2)}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        ))}

        {/* Y-axis labels */}
        <text x="5" y={padding + 5} className="text-xs fill-gray-400">
          {Math.round(maxValue)}
        </text>
        <text x="5" y={chartHeight - padding} className="text-xs fill-gray-400">
          {Math.round(minValue)}
        </text>

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
        />

        {/* Points */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="4" fill="#3b82f6" />
            <text
              x={p.x}
              y={chartHeight - 5}
              textAnchor="middle"
              className="text-xs fill-gray-500"
            >
              {p.date}
            </text>
          </g>
        ))}
      </svg>

      <div className="text-center text-sm text-gray-500 mt-2">
        单位: m²/h
      </div>
    </div>
  );
};

// ============================================================
// Alert List Component
// ============================================================

interface AlertListProps {
  alerts: Alert[];
  onViewAll?: () => void;
}

const AlertList: React.FC<AlertListProps> = ({ alerts, onViewAll }) => {
  const levelConfig = {
    critical: { color: 'bg-red-100 text-red-800', icon: '🔴' },
    warning: { color: 'bg-yellow-100 text-yellow-800', icon: '🟡' },
    info: { color: 'bg-blue-100 text-blue-800', icon: '🔵' },
  };

  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      <h3 className="font-semibold text-gray-900 mb-4">最新告警</h3>

      <div className="space-y-2">
        {alerts.slice(0, 5).map(alert => (
          <div
            key={alert.id}
            className={`flex items-center justify-between p-2 rounded ${levelConfig[alert.level].color}`}
          >
            <div className="flex items-center gap-2">
              <span>{levelConfig[alert.level].icon}</span>
              <span className="text-sm">{alert.message}</span>
            </div>
            <span className="text-xs opacity-70">{alert.time}</span>
          </div>
        ))}

        {alerts.length === 0 && (
          <div className="text-center py-4 text-gray-400">
            暂无告警
          </div>
        )}
      </div>

      {onViewAll && alerts.length > 0 && (
        <button
          onClick={onViewAll}
          className="w-full mt-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
        >
          查看全部告警 →
        </button>
      )}
    </div>
  );
};

// ============================================================
// Filter Bar Component
// ============================================================

interface FilterBarProps {
  selectedBuilding: string;
  selectedFloor: string;
  selectedTimeRange: string;
  onBuildingChange: (value: string) => void;
  onFloorChange: (value: string) => void;
  onTimeRangeChange: (value: string) => void;
  onRefresh: () => void;
  onExport: () => void;
  lastUpdated: string;
}

const FilterBar: React.FC<FilterBarProps> = ({
  selectedBuilding,
  selectedFloor,
  selectedTimeRange,
  onBuildingChange,
  onFloorChange,
  onTimeRangeChange,
  onRefresh,
  onExport,
  lastUpdated,
}) => {
  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm mb-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <select
            value={selectedBuilding}
            onChange={(e) => onBuildingChange(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">全部楼宇</option>
            <option value="building_1">A座</option>
            <option value="building_2">B座</option>
          </select>

          <select
            value={selectedFloor}
            onChange={(e) => onFloorChange(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">全部楼层</option>
            <option value="1">1F</option>
            <option value="2">2F</option>
            <option value="3">3F</option>
          </select>

          <select
            value={selectedTimeRange}
            onChange={(e) => onTimeRangeChange(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="today">今日</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm"
          >
            🔄 刷新
          </button>
          <button
            onClick={onExport}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
          >
            📊 导出
          </button>
        </div>
      </div>

      <div className="text-xs text-gray-400 mt-2">
        最后更新: {lastUpdated} | 自动刷新: 5分钟
      </div>
    </div>
  );
};

// ============================================================
// Main Dashboard Component
// ============================================================

export const OperationsDashboard: React.FC<DashboardProps> = ({
  tenantId,
  onNavigateToAlerts,
  onNavigateToTasks,
  onNavigateToRobots,
}) => {
  const [kpi, _setKpi] = useState<KPIData>(mockKPI);
  const [robotStatus, _setRobotStatus] = useState<RobotStatusDistribution>(mockRobotStatus);
  const [taskProgress, _setTaskProgress] = useState<TaskProgress>(mockTaskProgress);
  const [efficiencyTrend, _setEfficiencyTrend] = useState<EfficiencyTrendPoint[]>(mockEfficiencyTrend);
  const [alerts, _setAlerts] = useState<Alert[]>(mockAlerts);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleString('zh-CN'));

  // Filters
  const [selectedBuilding, setSelectedBuilding] = useState('');
  const [selectedFloor, setSelectedFloor] = useState('');
  const [selectedTimeRange, setSelectedTimeRange] = useState('today');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API calls
      // const kpiData = await getKPIOverview({ tenantId, buildingId: selectedBuilding });
      // setKpi(kpiData);
      setLastUpdated(new Date().toLocaleString('zh-CN'));
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId, selectedBuilding, selectedFloor, selectedTimeRange]);

  useEffect(() => {
    loadData();
    // Auto refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Export dashboard data');
  };

  const alertStatus = kpi.pendingAlerts > 5 ? 'critical' : kpi.pendingAlerts > 0 ? 'warning' : 'normal';

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">运营仪表板</h1>
        <p className="text-gray-500">实时监控运营状态和关键指标</p>
      </div>

      {/* Filter Bar */}
      <FilterBar
        selectedBuilding={selectedBuilding}
        selectedFloor={selectedFloor}
        selectedTimeRange={selectedTimeRange}
        onBuildingChange={setSelectedBuilding}
        onFloorChange={setSelectedFloor}
        onTimeRangeChange={setSelectedTimeRange}
        onRefresh={loadData}
        onExport={handleExport}
        lastUpdated={lastUpdated}
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPICard
          title="清洁完成率"
          icon="📈"
          value={`${kpi.completionRate}%`}
          trend={kpi.completionRateTrend}
          onClick={onNavigateToTasks}
        />
        <KPICard
          title="平均效率"
          icon="⚡"
          value={`${kpi.avgEfficiency} m²/h`}
          trend={kpi.efficiencyTrend}
          trendLabel=" m²/h"
        />
        <KPICard
          title="机器人在线"
          icon="🤖"
          value={`${kpi.onlineRobots}/${kpi.totalRobots} 台`}
          trend={kpi.robotTrend}
          trendLabel=" 台"
          onClick={onNavigateToRobots}
        />
        <KPICard
          title="待处理告警"
          icon="⚠️"
          value={`${kpi.pendingAlerts} 条`}
          trend={kpi.alertTrend}
          trendLabel=" 条"
          status={alertStatus}
          onClick={onNavigateToAlerts}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <RobotStatusChart data={robotStatus} onClick={onNavigateToRobots} />
        <TaskProgressCard data={taskProgress} onClick={onNavigateToTasks} />
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <EfficiencyTrendChart data={efficiencyTrend} />
        <AlertList alerts={alerts} onViewAll={onNavigateToAlerts} />
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50">
          <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
            加载中...
          </div>
        </div>
      )}
    </div>
  );
};

export default OperationsDashboard;
