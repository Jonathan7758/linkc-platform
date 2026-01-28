/**
 * E1 Executive Overview - Strategic Dashboard
 * 战略驾驶舱总览
 *
 * 数据来源: /api/v1/demo/kpi API
 */

import React, { useState, useEffect, useCallback } from "react";

const API_BASE = "http://101.47.67.225:8000";

// ============ Type Definitions ============

interface CoreMetricsData {
  healthScore: { value: number; status: "good" | "warning" | "critical"; trend?: number };
  taskCompletionRate: { value: number; trend: number; target: number };
  costSaving: { value: number; period: "day" | "week" | "month"; breakdown: { laborSaving: number; efficiencySaving: number; energySaving: number } };
  customerSatisfaction: { value: number; trend: number; reviewCount: number };
}

interface TodayOverviewData {
  tasks: { total: number; completed: number; inProgress: number; pending: number; failed: number };
  robots: { total: number; online: number; working: number; error: number };
  coverage: { actual: number; target: number };
  anomalies: { total: number; handled: number; pending: number };
}

interface PendingActionItem {
  id: string;
  level: "critical" | "high" | "medium" | "low";
  type: "decision" | "approval" | "review" | "alert";
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
  breakdown: { category: string; amount: number; percentage: number }[];
  roi: number;
  comparison: { previousPeriod: number; trend: number };
}

interface BuildingStatusData {
  id: string;
  name: string;
  status: "normal" | "warning" | "error";
  coverageRate: number;
  taskProgress: { completed: number; total: number };
  robotCount: number;
  activeRobotCount: number;
  alerts: number;
}

// ============ Default Data ============

const defaultCoreMetrics: CoreMetricsData = {
  healthScore: { value: 92, status: "good", trend: 3 },
  taskCompletionRate: { value: 96.8, trend: 2.1, target: 95 },
  costSaving: { value: 428600, period: "month", breakdown: { laborSaving: 280000, efficiencySaving: 100000, energySaving: 48600 } },
  customerSatisfaction: { value: 4.8, trend: 0.6, reviewCount: 256 },
};

const defaultTodayOverview: TodayOverviewData = {
  tasks: { total: 127, completed: 123, inProgress: 3, pending: 0, failed: 1 },
  robots: { total: 8, online: 7, working: 4, error: 1 },
  coverage: { actual: 94.2, target: 95 },
  anomalies: { total: 2, handled: 1, pending: 1 },
};

const defaultPendingActions: PendingActionItem[] = [
  { id: "1", level: "critical", type: "decision", title: "清洁策略调整需批准", description: "太古广场B区清洁频率调整方案", source: "运营部", createdAt: new Date().toISOString() },
  { id: "2", level: "high", type: "approval", title: "新增区域清洁排程", description: "环球贸易广场新区域清洁计划", source: "调度系统", createdAt: new Date().toISOString() },
  { id: "3", level: "medium", type: "alert", title: "机器人维护提醒", description: "A-06需要定期维护保养", source: "监控系统", createdAt: new Date().toISOString() },
];

// ============ Sub Components ============

const StatusIndicator: React.FC<{ status: "good" | "warning" | "critical" }> = ({ status }) => {
  const config = { good: { color: "bg-green-500", label: "正常" }, warning: { color: "bg-yellow-500", label: "警告" }, critical: { color: "bg-red-500", label: "异常" } };
  const { color, label } = config[status];
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white ${color}`}><span className="w-1.5 h-1.5 rounded-full bg-white mr-1"></span>{label}</span>;
};

const TrendIndicator: React.FC<{ value: number; suffix?: string }> = ({ value, suffix = "%" }) => {
  if (value === 0) return <span className="text-gray-500">- 0{suffix}</span>;
  const isUp = value > 0;
  return <span className={isUp ? "text-green-600" : "text-red-600"}>{isUp ? "↑" : "↓"} {Math.abs(value).toFixed(1)}{suffix}</span>;
};

const MetricCard: React.FC<{ title: string; value: string | number; unit?: string; status?: "good" | "warning" | "critical"; trend?: number; trendSuffix?: string; subtext?: string; onClick?: () => void }> = ({ title, value, unit, status, trend, trendSuffix = "%", subtext, onClick }) => {
  return (
    <div className={`bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow ${status === "critical" ? "border-l-4 border-red-500" : status === "warning" ? "border-l-4 border-yellow-500" : status === "good" ? "border-l-4 border-green-500" : ""}`} onClick={onClick}>
      <div className="text-sm text-gray-500 mb-1">{title}</div>
      <div className="flex items-baseline"><span className="text-2xl font-bold text-gray-900">{value}</span>{unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}</div>
      <div className="mt-2 flex items-center justify-between">
        {status && <StatusIndicator status={status} />}
        {trend !== undefined && <TrendIndicator value={trend} suffix={trendSuffix} />}
        {subtext && <span className="text-xs text-gray-500">{subtext}</span>}
      </div>
    </div>
  );
};

const CoreMetricsPanel: React.FC<{ metrics: CoreMetricsData; onMetricClick: (key: string) => void }> = ({ metrics, onMetricClick }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <MetricCard title="运营健康度" value={metrics.healthScore.value} unit="分" status={metrics.healthScore.status} trend={metrics.healthScore.trend} onClick={() => onMetricClick("health")} />
    <MetricCard title="任务完成率" value={metrics.taskCompletionRate.value} unit="%" trend={metrics.taskCompletionRate.trend} subtext={`目标: ${metrics.taskCompletionRate.target}%`} onClick={() => onMetricClick("tasks")} />
    <MetricCard title="月成本节约" value={`¥${(metrics.costSaving.value / 10000).toFixed(1)}`} unit="万" subtext="本月累计" onClick={() => onMetricClick("cost")} />
    <MetricCard title="客户满意度" value={metrics.customerSatisfaction.value.toFixed(1)} unit="/5.0" trend={metrics.customerSatisfaction.trend} trendSuffix="" subtext={`${metrics.customerSatisfaction.reviewCount}条评价`} onClick={() => onMetricClick("satisfaction")} />
  </div>
);

const TodayOverviewPanel: React.FC<{ data: TodayOverviewData; onDetailClick: () => void }> = ({ data, onDetailClick }) => {
  const coverageStatus = data.coverage.actual >= data.coverage.target ? "text-green-600" : "text-yellow-600";
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4"><h3 className="text-lg font-medium text-gray-900">今日运营概览</h3><button onClick={onDetailClick} className="text-sm text-blue-600 hover:text-blue-800">查看详情 →</button></div>
      <div className="space-y-3">
        <div className="flex justify-between items-center py-2 border-b border-gray-100"><span className="text-gray-600">今日任务</span><span className="font-medium">{data.tasks.total}个<span className="text-green-600 ml-2">完成:{data.tasks.completed}</span><span className="text-blue-600 ml-2">进行:{data.tasks.inProgress}</span>{data.tasks.failed > 0 && <span className="text-red-600 ml-2">失败:{data.tasks.failed}</span>}</span></div>
        <div className="flex justify-between items-center py-2 border-b border-gray-100"><span className="text-gray-600">机器人</span><span className="font-medium">{data.robots.total}台<span className="text-green-600 ml-2">在线:{data.robots.online}</span>{data.robots.error > 0 && <span className="text-red-600 ml-2">异常:{data.robots.error}</span>}</span></div>
        <div className="flex justify-between items-center py-2 border-b border-gray-100"><span className="text-gray-600">覆盖率</span><span className={`font-medium ${coverageStatus}`}>{data.coverage.actual}% <span className="text-gray-400">目标:{data.coverage.target}%</span></span></div>
        <div className="flex justify-between items-center py-2"><span className="text-gray-600">异常事件</span><span className="font-medium">{data.anomalies.total}个<span className="text-green-600 ml-2">已处理:{data.anomalies.handled}</span>{data.anomalies.pending > 0 && <span className="text-yellow-600 ml-2">待处理:{data.anomalies.pending}</span>}</span></div>
      </div>
    </div>
  );
};

const PendingActionsPanel: React.FC<{ items: PendingActionItem[]; onItemClick: (item: PendingActionItem) => void; onViewAll: () => void }> = ({ items, onItemClick, onViewAll }) => {
  const levelConfig = { critical: { icon: "🔴", color: "text-red-600", bg: "bg-red-50" }, high: { icon: "🟠", color: "text-orange-600", bg: "bg-orange-50" }, medium: { icon: "🟡", color: "text-yellow-600", bg: "bg-yellow-50" }, low: { icon: "🟢", color: "text-green-600", bg: "bg-green-50" } };
  const typeLabels: Record<string, string> = { decision: "需决策", approval: "需审批", review: "需审阅", alert: "需关注" };
  const sortedItems = [...items].sort((a, b) => { const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }; return order[a.level] - order[b.level]; });
  const criticalCount = items.filter(i => i.level === "critical").length;
  const highCount = items.filter(i => i.level === "high").length;
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4"><h3 className="text-lg font-medium text-gray-900">待处理事项</h3><button onClick={onViewAll} className="text-sm text-blue-600 hover:text-blue-800">查看全部 →</button></div>
      <div className="flex space-x-4 mb-4 text-sm">{criticalCount > 0 && <span className="text-red-600">🔴 {criticalCount}项紧急</span>}{highCount > 0 && <span className="text-orange-600">🟠 {highCount}项需审批</span>}</div>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {sortedItems.slice(0, 5).map(item => { const config = levelConfig[item.level]; return (
          <div key={item.id} className={`p-2 rounded cursor-pointer hover:opacity-80 ${config.bg}`} onClick={() => onItemClick(item)}>
            <div className="flex items-start"><span className="mr-2">{config.icon}</span><div className="flex-1 min-w-0"><div className={`font-medium text-sm ${config.color}`}>{typeLabels[item.type]}: {item.title}</div><div className="text-xs text-gray-500 truncate">{item.description}</div></div></div>
          </div>
        ); })}
      </div>
    </div>
  );
};

const SimpleLineChart: React.FC<{ data: TrendData[]; height?: number }> = ({ data, height = 180 }) => {
  if (data.length === 0) return <div className="flex items-center justify-center h-40 text-gray-400">加载中...</div>;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartWidth = 400;
  const chartHeight = height;
  const allValues = data.flatMap(d => [d.coverageRate, d.completionRate]);
  const minY = Math.min(...allValues) - 2;
  const maxY = Math.max(...allValues) + 2;
  const xScale = (i: number) => padding.left + (i / (data.length - 1)) * (chartWidth - padding.left - padding.right);
  const yScale = (v: number) => chartHeight - padding.bottom - ((v - minY) / (maxY - minY)) * (chartHeight - padding.top - padding.bottom);
  const coveragePath = data.map((d, i) => `${i === 0 ? "M" : "L"} ${xScale(i)} ${yScale(d.coverageRate)}`).join(" ");
  const completionPath = data.map((d, i) => `${i === 0 ? "M" : "L"} ${xScale(i)} ${yScale(d.completionRate)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full" style={{ height }}>
      {[minY, (minY + maxY) / 2, maxY].map((v, i) => (<g key={i}><line x1={padding.left} y1={yScale(v)} x2={chartWidth - padding.right} y2={yScale(v)} stroke="#e5e7eb" strokeDasharray="3,3" /><text x={padding.left - 5} y={yScale(v)} fontSize="10" fill="#6b7280" textAnchor="end" dominantBaseline="middle">{v.toFixed(0)}%</text></g>))}
      {data.map((d, i) => (<text key={i} x={xScale(i)} y={chartHeight - 10} fontSize="10" fill="#6b7280" textAnchor="middle">{d.date}</text>))}
      <path d={coveragePath} fill="none" stroke="#3b82f6" strokeWidth="2" />
      <path d={completionPath} fill="none" stroke="#22c55e" strokeWidth="2" />
      {data.map((d, i) => (<g key={i}><circle cx={xScale(i)} cy={yScale(d.coverageRate)} r="3" fill="#3b82f6" /><circle cx={xScale(i)} cy={yScale(d.completionRate)} r="3" fill="#22c55e" /></g>))}
      <g transform={`translate(${chartWidth - 120}, 10)`}><rect x="0" y="0" width="10" height="10" fill="#3b82f6" /><text x="15" y="9" fontSize="10" fill="#374151">利用率</text><rect x="60" y="0" width="10" height="10" fill="#22c55e" /><text x="75" y="9" fontSize="10" fill="#374151">完成率</text></g>
    </svg>
  );
};

const EfficiencyTrendPanel: React.FC<{ data: TrendData[]; period: "week" | "month" | "quarter"; onPeriodChange: (period: "week" | "month" | "quarter") => void }> = ({ data, period, onPeriodChange }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="flex justify-between items-center mb-4">
      <h3 className="text-lg font-medium text-gray-900">效率趋势</h3>
      <div className="flex space-x-1">{(["week", "month", "quarter"] as const).map(p => (<button key={p} onClick={() => onPeriodChange(p)} className={`px-3 py-1 text-sm rounded ${period === p ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>{p === "week" ? "近7天" : p === "month" ? "近30天" : "近3月"}</button>))}</div>
    </div>
    <SimpleLineChart data={data} height={180} />
  </div>
);

const CostAnalysisPanel: React.FC<{ data: CostAnalysisData; onDetailClick: () => void }> = ({ data, onDetailClick }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="flex justify-between items-center mb-4"><h3 className="text-lg font-medium text-gray-900">成本分析</h3><button onClick={onDetailClick} className="text-sm text-blue-600 hover:text-blue-800">查看详情 →</button></div>
    <div className="space-y-3">
      <div className="text-center p-3 bg-green-50 rounded-lg"><div className="text-sm text-gray-500">{data.period}节约</div><div className="text-2xl font-bold text-green-600">¥{(data.totalSaving / 10000).toFixed(1)}万</div><div className="text-xs text-gray-500 mt-1"><TrendIndicator value={data.comparison.trend} /> 较上期</div></div>
      <div className="space-y-2">{data.breakdown.map((item, index) => (<div key={index} className="flex items-center justify-between text-sm"><span className="text-gray-600">{item.category}</span><span className="font-medium">¥{(item.amount / 10000).toFixed(1)}万<span className="text-gray-400 ml-1">({item.percentage}%)</span></span></div>))}</div>
      <div className="pt-3 border-t border-gray-100"><div className="flex justify-between items-center"><span className="text-gray-600">投资回报率 (ROI)</span><span className="text-xl font-bold text-blue-600">{data.roi}%</span></div></div>
    </div>
  </div>
);

const BuildingCard: React.FC<{ building: BuildingStatusData; onClick: () => void }> = ({ building, onClick }) => {
  const statusConfig = { normal: { bg: "bg-green-50", border: "border-green-200", icon: "●", color: "text-green-600" }, warning: { bg: "bg-yellow-50", border: "border-yellow-200", icon: "⚠", color: "text-yellow-600" }, error: { bg: "bg-red-50", border: "border-red-200", icon: "✖", color: "text-red-600" } };
  const config = statusConfig[building.status];
  return (
    <div className={`p-4 rounded-lg border cursor-pointer hover:shadow-md transition-shadow ${config.bg} ${config.border}`} onClick={onClick}>
      <div className="flex justify-between items-center mb-2"><span className="font-medium text-gray-900">{building.name}</span><span className={config.color}>{config.icon} {building.status === "normal" ? "正常" : building.status === "warning" ? "警告" : "异常"}</span></div>
      <div className="grid grid-cols-2 gap-2 text-sm"><div><span className="text-gray-500">覆盖率:</span><span className={`ml-1 font-medium ${building.coverageRate >= 90 ? "text-green-600" : "text-yellow-600"}`}>{building.coverageRate}%</span></div><div><span className="text-gray-500">任务:</span><span className="ml-1 font-medium">{building.taskProgress.completed}/{building.taskProgress.total}</span></div></div>
      {building.alerts > 0 && <div className="mt-2 text-sm text-red-600">⚠ {building.alerts}个告警</div>}
    </div>
  );
};

const BuildingStatusGrid: React.FC<{ buildings: BuildingStatusData[]; onBuildingClick: (buildingId: string) => void }> = ({ buildings, onBuildingClick }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <h3 className="text-lg font-medium text-gray-900 mb-4">楼宇运营状态</h3>
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">{buildings.map(building => (<BuildingCard key={building.id} building={building} onClick={() => onBuildingClick(building.id)} />))}</div>
  </div>
);

// ============ Main Component ============

export const ExecutiveOverview: React.FC = () => {
  const [coreMetrics, setCoreMetrics] = useState<CoreMetricsData>(defaultCoreMetrics);
  const [todayOverview, setTodayOverview] = useState<TodayOverviewData>(defaultTodayOverview);
  const [pendingActions] = useState<PendingActionItem[]>(defaultPendingActions);
  const [efficiencyTrend, setEfficiencyTrend] = useState<TrendData[]>([]);
  const [costAnalysis, setCostAnalysis] = useState<CostAnalysisData>({ period: "2026年1月", totalSaving: 428600, breakdown: [{ category: "人力替代", amount: 280000, percentage: 65 }, { category: "效率提升", amount: 100000, percentage: 23 }, { category: "能耗优化", amount: 48600, percentage: 12 }], roi: 285, comparison: { previousPeriod: 380000, trend: 12.8 } });
  const [buildingStatus, setBuildingStatus] = useState<BuildingStatusData[]>([]);
  const [trendPeriod, setTrendPeriod] = useState<"week" | "month" | "quarter">("week");
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/demo/kpi`);
      const data = await response.json();

      if (data.success && data.kpi) {
        const kpi = data.kpi;

        // Update core metrics from API
        setCoreMetrics({
          healthScore: { value: kpi.health_score.overall, status: kpi.health_score.overall >= 90 ? "good" : kpi.health_score.overall >= 70 ? "warning" : "critical", trend: parseFloat(kpi.health_score.trend) || 3 },
          taskCompletionRate: { value: kpi.task_completion_rate, trend: 2.1, target: 95 },
          costSaving: { value: kpi.monthly_cost_savings, period: "month", breakdown: { laborSaving: kpi.monthly_cost_savings * 0.65, efficiencySaving: kpi.monthly_cost_savings * 0.23, energySaving: kpi.monthly_cost_savings * 0.12 } },
          customerSatisfaction: { value: kpi.customer_satisfaction, trend: 0.6, reviewCount: 256 },
        });

        // Update today overview
        setTodayOverview({
          tasks: { total: kpi.today.completed_tasks + 4, completed: kpi.today.completed_tasks, inProgress: 3, pending: 0, failed: 1 },
          robots: { total: 8, online: 7, working: 4, error: 1 },
          coverage: { actual: 94.2, target: 95 },
          anomalies: { total: 2, handled: 1, pending: 1 },
        });

        // Update cost analysis
        setCostAnalysis(prev => ({ ...prev, totalSaving: kpi.monthly_cost_savings, breakdown: [{ category: "人力替代", amount: kpi.monthly_cost_savings * 0.65, percentage: 65 }, { category: "效率提升", amount: kpi.monthly_cost_savings * 0.23, percentage: 23 }, { category: "能耗优化", amount: kpi.monthly_cost_savings * 0.12, percentage: 12 }] }));

        // Update efficiency trend from API
        if (kpi.trends) {
          const trendData: TrendData[] = kpi.trends.dates.map((date: string, i: number) => ({
            date,
            coverageRate: kpi.trends.robot_utilization[i],
            completionRate: kpi.trends.task_completion[i],
            efficiency: kpi.trends.cleaning_area[i] / 40000,
          }));
          setEfficiencyTrend(trendData);
        }

        // Update building status from API
        if (kpi.buildings_status) {
          const buildings: BuildingStatusData[] = kpi.buildings_status.map((b: { building_id: string; name: string; status: string; completion_rate: number; tasks_today: number; robot_count: number; online_count: number }) => ({
            id: b.building_id,
            name: b.name,
            status: b.status === "healthy" ? "normal" as const : b.status === "attention" ? "warning" as const : "error" as const,
            coverageRate: b.completion_rate,
            taskProgress: { completed: Math.floor(b.tasks_today * b.completion_rate / 100), total: b.tasks_today },
            robotCount: b.robot_count,
            activeRobotCount: b.online_count,
            alerts: b.status === "attention" ? 1 : 0,
          }));
          setBuildingStatus(buildings);
        }
      }
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">智能清洁运营驾驶舱</h1>
          <p className="text-sm text-gray-500 mt-1">最后更新: {lastUpdated.toLocaleTimeString("zh-CN")}{loading && <span className="ml-2 text-blue-600">刷新中...</span>}</p>
        </div>
        <div className="flex space-x-2">
          <button onClick={loadData} disabled={loading} className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50">刷新</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">生成报表</button>
        </div>
      </div>
      <CoreMetricsPanel metrics={coreMetrics} onMetricClick={(key) => console.log("Metric clicked:", key)} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <TodayOverviewPanel data={todayOverview} onDetailClick={() => window.location.href = "/operations"} />
        <PendingActionsPanel items={pendingActions} onItemClick={(item) => console.log("Action:", item)} onViewAll={() => console.log("View all")} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <EfficiencyTrendPanel data={efficiencyTrend} period={trendPeriod} onPeriodChange={setTrendPeriod} />
        <CostAnalysisPanel data={costAnalysis} onDetailClick={() => console.log("Cost details")} />
      </div>
      <BuildingStatusGrid buildings={buildingStatus} onBuildingClick={(id) => console.log("Building:", id)} />
    </div>
  );
};

export default ExecutiveOverview;
