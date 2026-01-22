/**
 * O4: Alert Management Interface
 * 告警管理界面 - 系统告警的查看和处理
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============================================================
// Types
// ============================================================

type AlertLevel = 'critical' | 'warning' | 'info';
type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'ignored';
type AlertCategory = 'robot' | 'task' | 'system' | 'maintenance';

interface Alert {
  alertId: string;
  title: string;
  description: string;
  level: AlertLevel;
  status: AlertStatus;
  category: AlertCategory;
  source: string;
  sourceId?: string;
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  acknowledgedBy?: string;
  resolvedBy?: string;
  actions?: string[];
}

interface AlertStats {
  total: number;
  critical: number;
  warning: number;
  info: number;
  unresolved: number;
}

interface AlertManagementProps {
  tenantId: string;
  onAlertClick?: (alertId: string) => void;
}

// ============================================================
// Mock Data
// ============================================================

const mockAlerts: Alert[] = [
  {
    alertId: 'alert_001',
    title: '机器人电量严重不足',
    description: 'GX-003 电量低于10%，需要立即充电或召回',
    level: 'critical',
    status: 'active',
    category: 'robot',
    source: 'GX-003',
    sourceId: 'robot_003',
    createdAt: '5分钟前',
    actions: ['召回充电', '忽略', '查看机器人'],
  },
  {
    alertId: 'alert_002',
    title: '任务执行超时',
    description: 'T-005 A栋3F走廊清洁任务执行时间超过预期30%',
    level: 'warning',
    status: 'active',
    category: 'task',
    source: '任务 T-005',
    sourceId: 'task_005',
    createdAt: '15分钟前',
    actions: ['查看详情', '延长时间', '取消任务'],
  },
  {
    alertId: 'alert_003',
    title: '机器人传感器异常',
    description: 'GX-002 前方激光雷达数据异常，可能影响导航',
    level: 'warning',
    status: 'acknowledged',
    category: 'robot',
    source: 'GX-002',
    sourceId: 'robot_002',
    createdAt: '30分钟前',
    acknowledgedAt: '25分钟前',
    acknowledgedBy: '张运营',
    actions: ['安排维修', '暂停使用', '继续观察'],
  },
  {
    alertId: 'alert_004',
    title: '耗材即将耗尽',
    description: 'EC-001 刷盘磨损度已达85%，建议尽快更换',
    level: 'info',
    status: 'active',
    category: 'maintenance',
    source: 'EC-001',
    sourceId: 'robot_004',
    createdAt: '1小时前',
    actions: ['创建维护工单', '延后处理', '标记已更换'],
  },
  {
    alertId: 'alert_005',
    title: '系统连接异常',
    description: '与高仙云平台的连接中断超过5分钟',
    level: 'critical',
    status: 'resolved',
    category: 'system',
    source: '高仙云平台',
    createdAt: '2小时前',
    resolvedAt: '1小时50分钟前',
    resolvedBy: '系统自动恢复',
  },
];

const mockStats: AlertStats = {
  total: 23,
  critical: 3,
  warning: 8,
  info: 12,
  unresolved: 15,
};

// ============================================================
// Helper Functions
// ============================================================

const getLevelConfig = (level: AlertLevel) => {
  const configs = {
    critical: { label: '严重', color: 'bg-red-100 text-red-800 border-red-200', icon: '🔴', dotColor: 'bg-red-500' },
    warning: { label: '警告', color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: '🟡', dotColor: 'bg-yellow-500' },
    info: { label: '提示', color: 'bg-blue-100 text-blue-800 border-blue-200', icon: '🔵', dotColor: 'bg-blue-500' },
  };
  return configs[level];
};

const getStatusConfig = (status: AlertStatus) => {
  const configs = {
    active: { label: '待处理', color: 'bg-red-50 text-red-700' },
    acknowledged: { label: '已确认', color: 'bg-yellow-50 text-yellow-700' },
    resolved: { label: '已解决', color: 'bg-green-50 text-green-700' },
    ignored: { label: '已忽略', color: 'bg-gray-50 text-gray-500' },
  };
  return configs[status];
};

const getCategoryLabel = (category: AlertCategory) => {
  const labels = {
    robot: '机器人',
    task: '任务',
    system: '系统',
    maintenance: '维护',
  };
  return labels[category];
};

// ============================================================
// Alert Stats Component
// ============================================================

interface AlertStatsProps {
  stats: AlertStats;
  onFilterChange: (level: string) => void;
  currentFilter: string;
}

const AlertStatsComponent: React.FC<AlertStatsProps> = ({ stats, onFilterChange, currentFilter }) => {
  const items = [
    { key: '', label: '全部', value: stats.total, color: 'bg-gray-100' },
    { key: 'critical', label: '严重', value: stats.critical, color: 'bg-red-100', dotColor: 'bg-red-500' },
    { key: 'warning', label: '警告', value: stats.warning, color: 'bg-yellow-100', dotColor: 'bg-yellow-500' },
    { key: 'info', label: '提示', value: stats.info, color: 'bg-blue-100', dotColor: 'bg-blue-500' },
  ];

  return (
    <div className="flex gap-3 mb-4">
      {items.map(item => (
        <button
          key={item.key}
          onClick={() => onFilterChange(item.key)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            currentFilter === item.key ? 'ring-2 ring-blue-500' : ''
          } ${item.color}`}
        >
          {item.dotColor && <span className={`w-2 h-2 rounded-full ${item.dotColor}`} />}
          <span className="font-medium">{item.value}</span>
          <span className="text-sm opacity-70">{item.label}</span>
        </button>
      ))}
      <div className="ml-auto flex items-center gap-2 px-4 py-2 bg-orange-100 rounded-lg">
        <span className="font-medium text-orange-700">{stats.unresolved}</span>
        <span className="text-sm text-orange-600">未解决</span>
      </div>
    </div>
  );
};

// ============================================================
// Alert Card Component
// ============================================================

interface AlertCardProps {
  alert: Alert;
  onAction: (alertId: string, action: string) => void;
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string) => void;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert, onAction, onAcknowledge, onResolve }) => {
  const levelConfig = getLevelConfig(alert.level);
  const statusConfig = getStatusConfig(alert.status);

  return (
    <div className={`p-4 rounded-lg border ${levelConfig.color} mb-3`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span>{levelConfig.icon}</span>
          <span className="font-medium text-gray-900">{alert.title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded ${statusConfig.color}`}>
            {statusConfig.label}
          </span>
          <span className="text-xs text-gray-500">{alert.createdAt}</span>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-700 mb-3">{alert.description}</p>

      {/* Source and Category */}
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
        <span>来源: {alert.source}</span>
        <span>类型: {getCategoryLabel(alert.category)}</span>
        {alert.acknowledgedBy && (
          <span>确认人: {alert.acknowledgedBy}</span>
        )}
        {alert.resolvedBy && (
          <span>解决: {alert.resolvedBy}</span>
        )}
      </div>

      {/* Actions */}
      {alert.status !== 'resolved' && alert.status !== 'ignored' && (
        <div className="flex items-center gap-2 pt-3 border-t border-current border-opacity-20">
          {alert.status === 'active' && (
            <button
              onClick={() => onAcknowledge(alert.alertId)}
              className="px-3 py-1.5 bg-white text-gray-700 rounded border hover:bg-gray-50 text-sm"
            >
              ✓ 确认
            </button>
          )}
          <button
            onClick={() => onResolve(alert.alertId)}
            className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
          >
            ✓ 解决
          </button>
          {alert.actions?.map((action, i) => (
            <button
              key={i}
              onClick={() => onAction(alert.alertId, action)}
              className="px-3 py-1.5 bg-white text-gray-700 rounded border hover:bg-gray-50 text-sm"
            >
              {action}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================================
// Alert Filter Component
// ============================================================

interface AlertFilterProps {
  statusFilter: string;
  categoryFilter: string;
  searchQuery: string;
  onStatusChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onSearchChange: (value: string) => void;
}

const AlertFilter: React.FC<AlertFilterProps> = ({
  statusFilter,
  categoryFilter,
  searchQuery,
  onStatusChange,
  onCategoryChange,
  onSearchChange,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <select
        value={statusFilter}
        onChange={(e) => onStatusChange(e.target.value)}
        className="px-3 py-2 border rounded-lg text-sm"
      >
        <option value="">全部状态</option>
        <option value="active">待处理</option>
        <option value="acknowledged">已确认</option>
        <option value="resolved">已解决</option>
        <option value="ignored">已忽略</option>
      </select>

      <select
        value={categoryFilter}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="px-3 py-2 border rounded-lg text-sm"
      >
        <option value="">全部类型</option>
        <option value="robot">机器人</option>
        <option value="task">任务</option>
        <option value="system">系统</option>
        <option value="maintenance">维护</option>
      </select>

      <input
        type="text"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="搜索告警..."
        className="px-3 py-2 border rounded-lg text-sm w-48"
      />

      <div className="ml-auto flex gap-2">
        <button className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
          导出
        </button>
        <button className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg">
          告警规则
        </button>
      </div>
    </div>
  );
};

// ============================================================
// Batch Actions Component
// ============================================================

interface BatchActionsProps {
  selectedCount: number;
  onAcknowledgeAll: () => void;
  onResolveAll: () => void;
  onIgnoreAll: () => void;
  onClearSelection: () => void;
}

const BatchActions: React.FC<BatchActionsProps> = ({
  selectedCount,
  onAcknowledgeAll,
  onResolveAll,
  onIgnoreAll,
  onClearSelection,
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg mb-4">
      <span className="text-sm text-blue-700">
        已选择 {selectedCount} 条告警
      </span>
      <button
        onClick={onAcknowledgeAll}
        className="px-3 py-1.5 bg-white text-gray-700 rounded border hover:bg-gray-50 text-sm"
      >
        批量确认
      </button>
      <button
        onClick={onResolveAll}
        className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
      >
        批量解决
      </button>
      <button
        onClick={onIgnoreAll}
        className="px-3 py-1.5 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
      >
        批量忽略
      </button>
      <button
        onClick={onClearSelection}
        className="ml-auto text-sm text-gray-500 hover:text-gray-700"
      >
        取消选择
      </button>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const AlertManagement: React.FC<AlertManagementProps> = ({
  tenantId,
  onAlertClick: _onAlertClick,
}) => {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [stats, _setStats] = useState<AlertStats>(mockStats);
  const [loading, setLoading] = useState(false);
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([]);

  // Filters
  const [levelFilter, setLevelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API calls
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    loadData();
    // Auto refresh every minute
    const interval = setInterval(loadData, 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    if (levelFilter && alert.level !== levelFilter) return false;
    if (statusFilter && alert.status !== statusFilter) return false;
    if (categoryFilter && alert.category !== categoryFilter) return false;
    if (searchQuery && !alert.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const handleAction = (alertId: string, action: string) => {
    console.log(`Alert ${alertId} action: ${action}`);
    // TODO: Implement alert actions
  };

  const handleAcknowledge = (alertId: string) => {
    setAlerts(prev =>
      prev.map(a => a.alertId === alertId ? { ...a, status: 'acknowledged' as AlertStatus } : a)
    );
  };

  const handleResolve = (alertId: string) => {
    setAlerts(prev =>
      prev.map(a => a.alertId === alertId ? { ...a, status: 'resolved' as AlertStatus } : a)
    );
  };

  const handleBatchAcknowledge = () => {
    setAlerts(prev =>
      prev.map(a => selectedAlerts.includes(a.alertId) ? { ...a, status: 'acknowledged' as AlertStatus } : a)
    );
    setSelectedAlerts([]);
  };

  const handleBatchResolve = () => {
    setAlerts(prev =>
      prev.map(a => selectedAlerts.includes(a.alertId) ? { ...a, status: 'resolved' as AlertStatus } : a)
    );
    setSelectedAlerts([]);
  };

  const handleBatchIgnore = () => {
    setAlerts(prev =>
      prev.map(a => selectedAlerts.includes(a.alertId) ? { ...a, status: 'ignored' as AlertStatus } : a)
    );
    setSelectedAlerts([]);
  };

  // Group alerts by status
  const activeAlerts = filteredAlerts.filter(a => a.status === 'active');
  const acknowledgedAlerts = filteredAlerts.filter(a => a.status === 'acknowledged');
  const resolvedAlerts = filteredAlerts.filter(a => a.status === 'resolved' || a.status === 'ignored');

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">告警管理</h1>
          <p className="text-gray-500">查看和处理系统告警</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
        >
          🔄 刷新
        </button>
      </div>

      {/* Stats */}
      <AlertStatsComponent
        stats={stats}
        onFilterChange={setLevelFilter}
        currentFilter={levelFilter}
      />

      {/* Filter */}
      <AlertFilter
        statusFilter={statusFilter}
        categoryFilter={categoryFilter}
        searchQuery={searchQuery}
        onStatusChange={setStatusFilter}
        onCategoryChange={setCategoryFilter}
        onSearchChange={setSearchQuery}
      />

      {/* Batch Actions */}
      <BatchActions
        selectedCount={selectedAlerts.length}
        onAcknowledgeAll={handleBatchAcknowledge}
        onResolveAll={handleBatchResolve}
        onIgnoreAll={handleBatchIgnore}
        onClearSelection={() => setSelectedAlerts([])}
      />

      {/* Alert Lists */}
      <div className="space-y-6">
        {/* Active Alerts */}
        {activeAlerts.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              待处理 ({activeAlerts.length})
            </h3>
            {activeAlerts.map(alert => (
              <AlertCard
                key={alert.alertId}
                alert={alert}
                onAction={handleAction}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
              />
            ))}
          </div>
        )}

        {/* Acknowledged Alerts */}
        {acknowledgedAlerts.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">
              已确认 ({acknowledgedAlerts.length})
            </h3>
            {acknowledgedAlerts.map(alert => (
              <AlertCard
                key={alert.alertId}
                alert={alert}
                onAction={handleAction}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
              />
            ))}
          </div>
        )}

        {/* Resolved Alerts */}
        {resolvedAlerts.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-500 mb-3">
              已处理 ({resolvedAlerts.length})
            </h3>
            {resolvedAlerts.map(alert => (
              <AlertCard
                key={alert.alertId}
                alert={alert}
                onAction={handleAction}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {filteredAlerts.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">✅</div>
            <div>暂无告警</div>
          </div>
        )}
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

export default AlertManagement;
