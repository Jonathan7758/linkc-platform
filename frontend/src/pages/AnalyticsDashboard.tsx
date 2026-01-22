/**
 * E2 Analytics Dashboard - Data Analysis Interface
 * 数据分析界面
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============ Type Definitions ============

type AnalysisModule = 'efficiency' | 'cost' | 'trend' | 'comparison' | 'anomaly';
// type ChartPeriod removed - unused

interface AnalysisFilters {
  dateRange: [string, string];
  buildingIds: string[];
  robotIds: string[];
}

interface EfficiencyData {
  summary: {
    avgCoverageRate: number;
    avgCompletionRate: number;
    avgEfficiencyIndex: number;
    robotUtilization: number;
    trends: {
      coverage: number;
      completion: number;
      efficiency: number;
      utilization: number;
    };
  };
  trend: { date: string; coverageRate: number; completionRate: number; efficiencyIndex: number }[];
  byBuilding: { buildingId: string; buildingName: string; coverageRate: number; completionRate: number; taskCount: number; trend: 'up' | 'down' | 'stable' }[];
  byHour: { hour: number; dayOfWeek: number; avgEfficiency: number }[];
}

interface CostData {
  summary: {
    totalCost: number;
    laborCost: number;
    robotCost: number;
    maintenanceCost: number;
    energyCost: number;
    costPerSquareMeter: number;
  };
  savings: {
    totalSaving: number;
    laborSaving: number;
    efficiencySaving: number;
    energySaving: number;
    roi: number;
  };
  trend: { date: string; totalCost: number; laborCost: number; robotCost: number }[];
  breakdown: { category: string; amount: number; percentage: number; trend: number }[];
}

interface TrendAnalysisData {
  historicalTrend: { date: string; metric: number; movingAverage: number }[];
  comparison: {
    current: number;
    previousPeriod: number;
    previousYear: number;
    momChange: number;
    yoyChange: number;
  };
}

interface ComparisonItem {
  id: string;
  name: string;
  metrics: { [key: string]: number };
  trend: number;
  rank: number;
}

interface AnomalyData {
  summary: {
    totalAnomalies: number;
    byLevel: { [level: string]: number };
    avgResolutionTime: number;
    trend: number;
  };
  trend: { date: string; count: number; p0: number; p1: number; p2: number }[];
  topAnomalies: { type: string; count: number; avgResolutionTime: number; trend: number }[];
  rootCauses: { cause: string; count: number; percentage: number; suggestion: string }[];
}

interface AnalyticsDashboardProps {
  tenantId: string;
  onExport?: (module: string, format: 'csv' | 'excel') => void;
}

// ============ Mock Data ============

const mockEfficiencyData: EfficiencyData = {
  summary: {
    avgCoverageRate: 94.2,
    avgCompletionRate: 96.8,
    avgEfficiencyIndex: 1.2,
    robotUtilization: 78.5,
    trends: { coverage: 1.5, completion: 2.1, efficiency: 0.1, utilization: 5.2 },
  },
  trend: [
    { date: '01-15', coverageRate: 92.5, completionRate: 95.2, efficiencyIndex: 1.15 },
    { date: '01-16', coverageRate: 93.1, completionRate: 96.1, efficiencyIndex: 1.18 },
    { date: '01-17', coverageRate: 91.8, completionRate: 94.8, efficiencyIndex: 1.12 },
    { date: '01-18', coverageRate: 94.5, completionRate: 97.2, efficiencyIndex: 1.22 },
    { date: '01-19', coverageRate: 93.8, completionRate: 96.5, efficiencyIndex: 1.19 },
    { date: '01-20', coverageRate: 94.0, completionRate: 96.8, efficiencyIndex: 1.21 },
    { date: '01-21', coverageRate: 94.2, completionRate: 96.5, efficiencyIndex: 1.20 },
  ],
  byBuilding: [
    { buildingId: 'A', buildingName: 'A栋', coverageRate: 96.5, completionRate: 98.2, taskCount: 125, trend: 'up' },
    { buildingId: 'B', buildingName: 'B栋', coverageRate: 94.1, completionRate: 97.5, taskCount: 118, trend: 'stable' },
    { buildingId: 'C', buildingName: 'C栋', coverageRate: 88.2, completionRate: 92.1, taskCount: 95, trend: 'down' },
    { buildingId: 'D', buildingName: 'D栋', coverageRate: 95.8, completionRate: 98.8, taskCount: 112, trend: 'up' },
  ],
  byHour: Array.from({ length: 24 }, (_, hour) => ({
    hour,
    dayOfWeek: 1,
    avgEfficiency: 0.8 + Math.random() * 0.5,
  })),
};

const mockCostData: CostData = {
  summary: {
    totalCost: 523000,
    laborCost: 281000,
    robotCost: 156000,
    maintenanceCost: 52000,
    energyCost: 34000,
    costPerSquareMeter: 2.1,
  },
  savings: {
    totalSaving: 125000,
    laborSaving: 82000,
    efficiencySaving: 31000,
    energySaving: 12000,
    roi: 285,
  },
  trend: [
    { date: '2025-08', totalCost: 580000, laborCost: 320000, robotCost: 160000 },
    { date: '2025-09', totalCost: 565000, laborCost: 310000, robotCost: 158000 },
    { date: '2025-10', totalCost: 550000, laborCost: 300000, robotCost: 157000 },
    { date: '2025-11', totalCost: 538000, laborCost: 290000, robotCost: 156000 },
    { date: '2025-12', totalCost: 530000, laborCost: 285000, robotCost: 156000 },
    { date: '2026-01', totalCost: 523000, laborCost: 281000, robotCost: 156000 },
  ],
  breakdown: [
    { category: '人力成本', amount: 281000, percentage: 53.7, trend: -3.2 },
    { category: '机器人成本', amount: 156000, percentage: 29.8, trend: 0 },
    { category: '维护成本', amount: 52000, percentage: 9.9, trend: -1.5 },
    { category: '能耗成本', amount: 34000, percentage: 6.5, trend: -2.1 },
  ],
};

const mockTrendData: TrendAnalysisData = {
  historicalTrend: Array.from({ length: 30 }, (_, i) => ({
    date: `01-${String(i + 1).padStart(2, '0')}`,
    metric: 90 + Math.random() * 8,
    movingAverage: 93 + Math.random() * 2,
  })),
  comparison: {
    current: 94.2,
    previousPeriod: 92.5,
    previousYear: 88.3,
    momChange: 1.8,
    yoyChange: 6.7,
  },
};

const mockComparisonData: ComparisonItem[] = [
  { id: 'GX-001', name: 'GX-001', metrics: { taskCount: 125, coverageRate: 96.5, completionRate: 98.2, efficiency: 1.3, utilization: 82.1 }, trend: 2.5, rank: 1 },
  { id: 'EC-001', name: 'EC-001', metrics: { taskCount: 118, coverageRate: 95.2, completionRate: 97.8, efficiency: 1.2, utilization: 79.5 }, trend: 1.2, rank: 2 },
  { id: 'GX-002', name: 'GX-002', metrics: { taskCount: 110, coverageRate: 93.8, completionRate: 96.5, efficiency: 1.1, utilization: 75.2 }, trend: -0.5, rank: 3 },
  { id: 'GX-003', name: 'GX-003', metrics: { taskCount: 98, coverageRate: 92.1, completionRate: 95.2, efficiency: 1.0, utilization: 72.8 }, trend: -1.2, rank: 4 },
];

const mockAnomalyData: AnomalyData = {
  summary: {
    totalAnomalies: 47,
    byLevel: { P0: 2, P1: 8, P2: 22, P3: 15 },
    avgResolutionTime: 25,
    trend: -12.5,
  },
  trend: [
    { date: '01-15', count: 8, p0: 0, p1: 2, p2: 4 },
    { date: '01-16', count: 6, p0: 1, p1: 1, p2: 3 },
    { date: '01-17', count: 9, p0: 0, p1: 2, p2: 5 },
    { date: '01-18', count: 5, p0: 0, p1: 1, p2: 2 },
    { date: '01-19', count: 7, p0: 1, p1: 1, p2: 3 },
    { date: '01-20', count: 6, p0: 0, p1: 1, p2: 4 },
    { date: '01-21', count: 6, p0: 0, p1: 0, p2: 3 },
  ],
  topAnomalies: [
    { type: '导航失败', count: 15, avgResolutionTime: 18, trend: -5 },
    { type: '电池异常', count: 10, avgResolutionTime: 45, trend: 2 },
    { type: '清洁效果差', count: 8, avgResolutionTime: 30, trend: -8 },
    { type: '通信中断', count: 7, avgResolutionTime: 12, trend: 0 },
    { type: '障碍物检测', count: 7, avgResolutionTime: 8, trend: -3 },
  ],
  rootCauses: [
    { cause: '地面湿滑', count: 12, percentage: 25.5, suggestion: '增加防滑检测' },
    { cause: '网络信号弱', count: 10, percentage: 21.3, suggestion: '增设WiFi中继' },
    { cause: '电池老化', count: 8, percentage: 17.0, suggestion: '更换电池组' },
    { cause: '传感器污染', count: 6, percentage: 12.8, suggestion: '定期清洁维护' },
    { cause: '地图过期', count: 5, percentage: 10.6, suggestion: '更新建筑地图' },
  ],
};

// ============ Sub Components ============

// Metric Summary Card
const MetricSummaryCard: React.FC<{
  title: string;
  value: string | number;
  unit?: string;
  trend?: number;
  target?: number;
}> = ({ title, value, unit, trend, target }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="text-sm text-gray-500">{title}</div>
    <div className="flex items-baseline mt-1">
      <span className="text-2xl font-bold text-gray-900">{value}</span>
      {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
    </div>
    <div className="mt-2 flex items-center justify-between text-sm">
      {trend !== undefined && (
        <span className={trend >= 0 ? 'text-green-600' : 'text-red-600'}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
        </span>
      )}
      {target !== undefined && (
        <span className="text-gray-400">目标: {target}%</span>
      )}
    </div>
  </div>
);

// Tab Button
const TabButton: React.FC<{
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
      active
        ? 'bg-white text-blue-600 border-b-2 border-blue-600'
        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
    }`}
  >
    {children}
  </button>
);

// SVG Line Chart Component
const LineChart: React.FC<{
  data: { date: string; [key: string]: number | string }[];
  lines: { key: string; name: string; color: string }[];
  height?: number;
}> = ({ data, lines, height = 200 }) => {
  const padding = { top: 20, right: 20, bottom: 30, left: 50 };
  const chartWidth = 500;
  const chartHeight = height;

  const allValues = data.flatMap(d => lines.map(l => d[l.key] as number));
  const minY = Math.min(...allValues) * 0.95;
  const maxY = Math.max(...allValues) * 1.05;

  const xScale = (i: number) => padding.left + (i / (data.length - 1)) * (chartWidth - padding.left - padding.right);
  const yScale = (v: number) => chartHeight - padding.bottom - ((v - minY) / (maxY - minY)) * (chartHeight - padding.top - padding.bottom);

  return (
    <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full" style={{ height }}>
      {/* Grid */}
      {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
        const y = padding.top + ratio * (chartHeight - padding.top - padding.bottom);
        const value = maxY - ratio * (maxY - minY);
        return (
          <g key={i}>
            <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#e5e7eb" strokeDasharray="3,3" />
            <text x={padding.left - 5} y={y} fontSize="10" fill="#6b7280" textAnchor="end" dominantBaseline="middle">
              {value.toFixed(0)}
            </text>
          </g>
        );
      })}

      {/* X Labels */}
      {data.filter((_, i) => i % Math.ceil(data.length / 7) === 0).map((d, i) => (
        <text key={i} x={xScale(data.indexOf(d))} y={chartHeight - 10} fontSize="10" fill="#6b7280" textAnchor="middle">
          {d.date}
        </text>
      ))}

      {/* Lines */}
      {lines.map(line => {
        const path = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d[line.key] as number)}`).join(' ');
        return (
          <g key={line.key}>
            <path d={path} fill="none" stroke={line.color} strokeWidth="2" />
            {data.map((d, i) => (
              <circle key={i} cx={xScale(i)} cy={yScale(d[line.key] as number)} r="3" fill={line.color} />
            ))}
          </g>
        );
      })}

      {/* Legend */}
      <g transform={`translate(${padding.left + 10}, ${padding.top})`}>
        {lines.map((line, i) => (
          <g key={line.key} transform={`translate(${i * 80}, 0)`}>
            <rect width="12" height="12" fill={line.color} />
            <text x="16" y="10" fontSize="10" fill="#374151">{line.name}</text>
          </g>
        ))}
      </g>
    </svg>
  );
};

// Bar Chart Component
const BarChart: React.FC<{
  data: { name: string; value: number; color?: string }[];
  height?: number;
}> = ({ data, height = 200 }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const barWidth = 100 / data.length - 5;

  return (
    <div className="flex items-end justify-around" style={{ height }}>
      {data.map((item, index) => (
        <div key={index} className="flex flex-col items-center" style={{ width: `${barWidth}%` }}>
          <div className="text-xs text-gray-600 mb-1">{item.value.toFixed(1)}%</div>
          <div
            className="w-full rounded-t"
            style={{
              height: `${(item.value / maxValue) * (height - 40)}px`,
              backgroundColor: item.color || '#3b82f6',
            }}
          />
          <div className="text-xs text-gray-500 mt-2 truncate w-full text-center">{item.name}</div>
        </div>
      ))}
    </div>
  );
};

// Heatmap Component (simplified)
const HeatmapChart: React.FC<{
  data: { hour: number; avgEfficiency: number }[];
}> = ({ data }) => {
  const getColor = (value: number) => {
    if (value >= 1.2) return 'bg-green-500';
    if (value >= 1.0) return 'bg-green-300';
    if (value >= 0.9) return 'bg-yellow-300';
    return 'bg-red-300';
  };

  return (
    <div className="grid grid-cols-12 gap-1">
      {data.slice(6, 22).map((d, i) => (
        <div key={i} className="text-center">
          <div className={`h-8 rounded ${getColor(d.avgEfficiency)}`} title={`${d.hour}时: ${d.avgEfficiency.toFixed(2)}`} />
          <span className="text-xs text-gray-500">{d.hour}</span>
        </div>
      ))}
    </div>
  );
};

// Data Table Component
const DataTable: React.FC<{
  columns: { key: string; title: string; render?: (value: any, row: any) => React.ReactNode }[];
  data: any[];
}> = ({ columns, data }) => (
  <div className="overflow-x-auto">
    <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
        <tr>
          {columns.map(col => (
            <th key={col.key} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {col.title}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="bg-white divide-y divide-gray-200">
        {data.map((row, i) => (
          <tr key={i} className="hover:bg-gray-50">
            {columns.map(col => (
              <td key={col.key} className="px-4 py-3 text-sm text-gray-900">
                {col.render ? col.render(row[col.key], row) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ============ Analysis Panels ============

// Efficiency Analysis Panel
const EfficiencyAnalysisPanel: React.FC<{ data: EfficiencyData }> = ({ data }) => (
  <div className="space-y-6">
    {/* Summary Metrics */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricSummaryCard title="平均覆盖率" value={data.summary.avgCoverageRate} unit="%" trend={data.summary.trends.coverage} target={95} />
      <MetricSummaryCard title="平均完成率" value={data.summary.avgCompletionRate} unit="%" trend={data.summary.trends.completion} />
      <MetricSummaryCard title="平均效率" value={data.summary.avgEfficiencyIndex} unit="x" trend={data.summary.trends.efficiency} />
      <MetricSummaryCard title="机器人利用率" value={data.summary.robotUtilization} unit="%" trend={data.summary.trends.utilization} />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Trend Chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">效率趋势</h4>
        <LineChart
          data={data.trend}
          lines={[
            { key: 'coverageRate', name: '覆盖率', color: '#3b82f6' },
            { key: 'completionRate', name: '完成率', color: '#22c55e' },
          ]}
        />
      </div>

      {/* Building Distribution */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">按楼宇分布</h4>
        <BarChart
          data={data.byBuilding.map(b => ({
            name: b.buildingName,
            value: b.coverageRate,
            color: b.trend === 'up' ? '#22c55e' : b.trend === 'down' ? '#ef4444' : '#3b82f6',
          }))}
        />
      </div>
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Hourly Heatmap */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">时段效率分布</h4>
        <HeatmapChart data={data.byHour} />
        <div className="flex justify-center space-x-4 mt-2 text-xs">
          <span><span className="inline-block w-3 h-3 bg-green-500 rounded mr-1"></span>高效</span>
          <span><span className="inline-block w-3 h-3 bg-green-300 rounded mr-1"></span>正常</span>
          <span><span className="inline-block w-3 h-3 bg-yellow-300 rounded mr-1"></span>一般</span>
          <span><span className="inline-block w-3 h-3 bg-red-300 rounded mr-1"></span>低效</span>
        </div>
      </div>

      {/* Building Details Table */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">楼宇效率明细</h4>
        <DataTable
          columns={[
            { key: 'buildingName', title: '楼宇' },
            { key: 'coverageRate', title: '覆盖率', render: v => `${v}%` },
            { key: 'completionRate', title: '完成率', render: v => `${v}%` },
            { key: 'trend', title: '趋势', render: v => v === 'up' ? '↑' : v === 'down' ? '↓' : '→' },
          ]}
          data={data.byBuilding}
        />
      </div>
    </div>
  </div>
);

// Cost Analysis Panel
const CostAnalysisPanel: React.FC<{ data: CostData }> = ({ data }) => (
  <div className="space-y-6">
    {/* Summary Metrics */}
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <MetricSummaryCard title="总成本" value={`¥${(data.summary.totalCost / 10000).toFixed(1)}`} unit="万" />
      <MetricSummaryCard title="人力成本" value={`¥${(data.summary.laborCost / 10000).toFixed(1)}`} unit="万" />
      <MetricSummaryCard title="机器人成本" value={`¥${(data.summary.robotCost / 10000).toFixed(1)}`} unit="万" />
      <MetricSummaryCard title="维护成本" value={`¥${(data.summary.maintenanceCost / 10000).toFixed(1)}`} unit="万" />
      <MetricSummaryCard title="单位成本" value={`¥${data.summary.costPerSquareMeter}`} unit="/㎡" trend={-8.3} />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Savings Breakdown */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">成本节约分析</h4>
        <div className="text-center p-4 bg-green-50 rounded-lg mb-4">
          <div className="text-sm text-gray-500">本月总节约</div>
          <div className="text-3xl font-bold text-green-600">¥{(data.savings.totalSaving / 10000).toFixed(1)}万</div>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">人力替代</span>
            <span className="font-medium">¥{(data.savings.laborSaving / 10000).toFixed(1)}万 ({((data.savings.laborSaving / data.savings.totalSaving) * 100).toFixed(1)}%)</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">效率提升</span>
            <span className="font-medium">¥{(data.savings.efficiencySaving / 10000).toFixed(1)}万 ({((data.savings.efficiencySaving / data.savings.totalSaving) * 100).toFixed(1)}%)</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">能耗优化</span>
            <span className="font-medium">¥{(data.savings.energySaving / 10000).toFixed(1)}万 ({((data.savings.energySaving / data.savings.totalSaving) * 100).toFixed(1)}%)</span>
          </div>
          <div className="pt-3 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <span className="text-gray-900 font-medium">投资回报率 (ROI)</span>
              <span className="text-2xl font-bold text-blue-600">{data.savings.roi}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Structure */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">成本结构</h4>
        <div className="space-y-3">
          {data.breakdown.map((item, index) => (
            <div key={index}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">{item.category}</span>
                <span className="font-medium">¥{(item.amount / 10000).toFixed(1)}万 ({item.percentage}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>

    {/* Cost Trend */}
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-sm font-medium text-gray-900 mb-4">成本趋势 (近6个月)</h4>
      <LineChart
        data={data.trend}
        lines={[
          { key: 'totalCost', name: '总成本', color: '#3b82f6' },
          { key: 'laborCost', name: '人力成本', color: '#f59e0b' },
          { key: 'robotCost', name: '机器人成本', color: '#8b5cf6' },
        ]}
        height={250}
      />
    </div>
  </div>
);

// Trend Analysis Panel
const TrendAnalysisPanel: React.FC<{ data: TrendAnalysisData }> = ({ data }) => (
  <div className="space-y-6">
    {/* Comparison Cards */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricSummaryCard title="当前值" value={data.comparison.current} unit="%" />
      <MetricSummaryCard title="上期值" value={data.comparison.previousPeriod} unit="%" />
      <MetricSummaryCard title="环比变化" value={data.comparison.momChange > 0 ? `+${data.comparison.momChange}` : data.comparison.momChange} unit="%" trend={data.comparison.momChange} />
      <MetricSummaryCard title="同比变化" value={data.comparison.yoyChange > 0 ? `+${data.comparison.yoyChange}` : data.comparison.yoyChange} unit="%" trend={data.comparison.yoyChange} />
    </div>

    {/* Historical Trend */}
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-sm font-medium text-gray-900 mb-4">历史趋势 (近30天)</h4>
      <LineChart
        data={data.historicalTrend}
        lines={[
          { key: 'metric', name: '实际值', color: '#3b82f6' },
          { key: 'movingAverage', name: '移动平均', color: '#f59e0b' },
        ]}
        height={300}
      />
    </div>
  </div>
);

// Comparison Analysis Panel
const ComparisonAnalysisPanel: React.FC<{ data: ComparisonItem[] }> = ({ data }) => {
  const [compareType, setCompareType] = useState<'building' | 'robot'>('robot');
  const [selectedMetric, setSelectedMetric] = useState('efficiency');

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">对比类型</label>
            <div className="flex space-x-2">
              <button
                onClick={() => setCompareType('building')}
                className={`px-3 py-1 text-sm rounded ${compareType === 'building' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                楼宇对比
              </button>
              <button
                onClick={() => setCompareType('robot')}
                className={`px-3 py-1 text-sm rounded ${compareType === 'robot' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                机器人对比
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">对比指标</label>
            <select
              value={selectedMetric}
              onChange={e => setSelectedMetric(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="efficiency">效率指数</option>
              <option value="coverageRate">覆盖率</option>
              <option value="completionRate">完成率</option>
              <option value="utilization">利用率</option>
            </select>
          </div>
        </div>
      </div>

      {/* Comparison Chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">对比图表</h4>
        <BarChart
          data={data.map(d => ({
            name: d.name,
            value: d.metrics[selectedMetric] || 0,
            color: d.trend > 0 ? '#22c55e' : d.trend < 0 ? '#ef4444' : '#3b82f6',
          }))}
          height={250}
        />
      </div>

      {/* Comparison Table */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">对比明细</h4>
        <DataTable
          columns={[
            { key: 'name', title: compareType === 'robot' ? '机器人' : '楼宇' },
            { key: 'taskCount', title: '任务数', render: (_, row) => row.metrics.taskCount },
            { key: 'coverageRate', title: '覆盖率', render: (_, row) => `${row.metrics.coverageRate}%` },
            { key: 'completionRate', title: '完成率', render: (_, row) => `${row.metrics.completionRate}%` },
            { key: 'efficiency', title: '效率', render: (_, row) => `${row.metrics.efficiency}x` },
            { key: 'utilization', title: '利用率', render: (_, row) => `${row.metrics.utilization}%` },
            { key: 'rank', title: '排名', render: v => `#${v}` },
          ]}
          data={data}
        />
      </div>
    </div>
  );
};

// Anomaly Analysis Panel
const AnomalyAnalysisPanel: React.FC<{ data: AnomalyData }> = ({ data }) => (
  <div className="space-y-6">
    {/* Summary */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricSummaryCard title="总异常数" value={data.summary.totalAnomalies} trend={data.summary.trend} />
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-500">按级别分布</div>
        <div className="flex space-x-2 mt-2">
          <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">P0: {data.summary.byLevel.P0}</span>
          <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded">P1: {data.summary.byLevel.P1}</span>
          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">P2: {data.summary.byLevel.P2}</span>
          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">P3: {data.summary.byLevel.P3}</span>
        </div>
      </div>
      <MetricSummaryCard title="平均解决时间" value={data.summary.avgResolutionTime} unit="分钟" />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Anomaly Trend */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">异常趋势</h4>
        <LineChart
          data={data.trend}
          lines={[
            { key: 'count', name: '总数', color: '#3b82f6' },
            { key: 'p0', name: 'P0', color: '#ef4444' },
            { key: 'p1', name: 'P1', color: '#f59e0b' },
          ]}
        />
      </div>

      {/* Top Anomalies */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-4">Top异常类型</h4>
        <DataTable
          columns={[
            { key: 'type', title: '类型' },
            { key: 'count', title: '次数' },
            { key: 'avgResolutionTime', title: '平均解决时间', render: v => `${v}分钟` },
            { key: 'trend', title: '趋势', render: v => v > 0 ? `↑${v}%` : v < 0 ? `↓${Math.abs(v)}%` : '→' },
          ]}
          data={data.topAnomalies}
        />
      </div>
    </div>

    {/* Root Cause Analysis */}
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-sm font-medium text-gray-900 mb-4">根因分析</h4>
      <div className="space-y-4">
        {data.rootCauses.map((cause, index) => (
          <div key={index} className="flex items-start p-3 bg-gray-50 rounded-lg">
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{cause.cause}</span>
                <span className="text-sm text-gray-500">{cause.count}次 ({cause.percentage}%)</span>
              </div>
              <div className="mt-1 text-sm text-blue-600">建议: {cause.suggestion}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ============ Main Component ============

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  tenantId,
  onExport,
}) => {
  // State
  const [activeModule, setActiveModule] = useState<AnalysisModule>('efficiency');
  const [filters, setFilters] = useState<AnalysisFilters>({
    dateRange: ['2026-01-01', '2026-01-21'],
    buildingIds: [],
    robotIds: [],
  });
  const [loading, setLoading] = useState(false);

  // Data states
  const [efficiencyData, _setEfficiencyData] = useState<EfficiencyData>(mockEfficiencyData);
  const [costData, _setCostData] = useState<CostData>(mockCostData);
  const [trendData, _setTrendData] = useState<TrendAnalysisData>(mockTrendData);
  const [comparisonData, _setComparisonData] = useState<ComparisonItem[]>(mockComparisonData);
  const [anomalyData, _setAnomalyData] = useState<AnomalyData>(mockAnomalyData);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // In production, fetch from API based on activeModule
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  }, [activeModule, filters, tenantId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Export handler
  const handleExport = (format: 'csv' | 'excel') => {
    if (onExport) {
      onExport(activeModule, format);
    } else {
      console.log('Export:', activeModule, format);
      alert(`导出${activeModule}数据为${format.toUpperCase()}格式`);
    }
  };

  // Render active panel
  const renderActivePanel = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">加载中...</div>
        </div>
      );
    }

    switch (activeModule) {
      case 'efficiency':
        return <EfficiencyAnalysisPanel data={efficiencyData} />;
      case 'cost':
        return <CostAnalysisPanel data={costData} />;
      case 'trend':
        return <TrendAnalysisPanel data={trendData} />;
      case 'comparison':
        return <ComparisonAnalysisPanel data={comparisonData} />;
      case 'anomaly':
        return <AnomalyAnalysisPanel data={anomalyData} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">数据分析</h1>
        <div className="flex space-x-2">
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
          >
            导出CSV
          </button>
          <button
            onClick={() => handleExport('excel')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            导出Excel
          </button>
        </div>
      </div>

      {/* Module Tabs */}
      <div className="flex space-x-1 mb-4 border-b border-gray-200">
        <TabButton active={activeModule === 'efficiency'} onClick={() => setActiveModule('efficiency')}>
          效率分析
        </TabButton>
        <TabButton active={activeModule === 'cost'} onClick={() => setActiveModule('cost')}>
          成本分析
        </TabButton>
        <TabButton active={activeModule === 'trend'} onClick={() => setActiveModule('trend')}>
          趋势分析
        </TabButton>
        <TabButton active={activeModule === 'comparison'} onClick={() => setActiveModule('comparison')}>
          对比分析
        </TabButton>
        <TabButton active={activeModule === 'anomaly'} onClick={() => setActiveModule('anomaly')}>
          异常分析
        </TabButton>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">时间范围</label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              onChange={e => {
                const value = e.target.value;
                const now = new Date();
                let start = new Date();
                if (value === '7') start.setDate(now.getDate() - 7);
                else if (value === '30') start.setDate(now.getDate() - 30);
                else if (value === '90') start.setDate(now.getDate() - 90);
                setFilters(prev => ({
                  ...prev,
                  dateRange: [start.toISOString().split('T')[0], now.toISOString().split('T')[0]],
                }));
              }}
            >
              <option value="7">近7天</option>
              <option value="30">近30天</option>
              <option value="90">近3个月</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">楼宇</label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              onChange={e => setFilters(prev => ({
                ...prev,
                buildingIds: e.target.value ? [e.target.value] : [],
              }))}
            >
              <option value="">全部楼宇</option>
              <option value="A">A栋</option>
              <option value="B">B栋</option>
              <option value="C">C栋</option>
              <option value="D">D栋</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">机器人</label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              onChange={e => setFilters(prev => ({
                ...prev,
                robotIds: e.target.value ? [e.target.value] : [],
              }))}
            >
              <option value="">全部机器人</option>
              <option value="GX-001">GX-001</option>
              <option value="GX-002">GX-002</option>
              <option value="EC-001">EC-001</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={loadData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              应用筛选
            </button>
          </div>
        </div>
      </div>

      {/* Active Panel */}
      {renderActivePanel()}
    </div>
  );
};

export default AnalyticsDashboard;
