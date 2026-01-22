/**
 * P3 Mobile Alert - Mobile-First Alert Management
 * 移动端告警页面
 */

import React, { useState, useCallback } from 'react';

// ============ Type Definitions ============

type AlertLevel = 'critical' | 'high' | 'medium' | 'low';
type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'closed';
type AlertType = 'robot_error' | 'robot_stuck' | 'low_battery' | 'task_failed' | 'efficiency_low' | 'connection_lost' | 'system';
type TabKey = 'active' | 'acknowledged' | 'resolved' | 'all';

interface AlertSummary {
  id: string;
  code: string;
  level: AlertLevel;
  type: AlertType;
  status: AlertStatus;
  title: string;
  message: string;
  source: {
    type: 'robot' | 'task' | 'system';
    id: string;
    name: string;
    location?: {
      building: string;
      floor?: string;
    };
  };
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  isOverdue: boolean;
}

interface AlertDetail extends AlertSummary {
  description: string;
  suggestedActions: SuggestedAction[];
  relatedData: {
    robot?: {
      id: string;
      name: string;
      status: string;
      battery: number;
    };
    task?: {
      id: string;
      name: string;
      status: string;
      progress: number;
    };
  };
  history: AlertHistoryEvent[];
}

interface SuggestedAction {
  id: string;
  type: string;
  label: string;
  description: string;
  isPrimary: boolean;
}

interface AlertHistoryEvent {
  id: string;
  type: string;
  timestamp: string;
  actor: string;
  description: string;
}

interface MobileAlertProps {
  tenantId: string;
  onBack?: () => void;
  onRobotSelect?: (robotId: string) => void;
  onTaskSelect?: (taskId: string) => void;
}

// ============ Mock Data ============

const mockAlerts: AlertSummary[] = [
  {
    id: 'A-001', code: 'ROBOT_STUCK', level: 'critical', type: 'robot_stuck', status: 'active',
    title: '机器人卡住', message: 'R-005 在C栋3F走廊处卡住，无法继续移动',
    source: { type: 'robot', id: 'R-005', name: 'R-005', location: { building: 'C栋', floor: '3F' } },
    createdAt: '2分钟前', isOverdue: false
  },
  {
    id: 'A-002', code: 'LOW_BATTERY', level: 'high', type: 'low_battery', status: 'active',
    title: '电量过低', message: 'R-012 电量仅剩18%，任务可能无法完成',
    source: { type: 'robot', id: 'R-012', name: 'R-012', location: { building: 'A栋', floor: '2F' } },
    createdAt: '10分钟前', isOverdue: false
  },
  {
    id: 'A-003', code: 'TASK_FAILED', level: 'high', type: 'task_failed', status: 'active',
    title: '任务执行失败', message: 'B栋深度清洁任务异常终止',
    source: { type: 'task', id: 'T-007', name: 'B栋深度清洁', location: { building: 'B栋', floor: '1F' } },
    createdAt: '15分钟前', isOverdue: true
  },
  {
    id: 'A-004', code: 'EFFICIENCY_LOW', level: 'medium', type: 'efficiency_low', status: 'acknowledged',
    title: '效率下降', message: 'R-003 清洁效率较平均值下降20%',
    source: { type: 'robot', id: 'R-003', name: 'R-003', location: { building: 'A栋', floor: '1F' } },
    createdAt: '30分钟前', acknowledgedAt: '25分钟前', isOverdue: false
  },
  {
    id: 'A-005', code: 'CONNECTION_LOST', level: 'medium', type: 'connection_lost', status: 'acknowledged',
    title: '连接中断', message: 'R-008 与服务器断开连接超过5分钟',
    source: { type: 'robot', id: 'R-008', name: 'R-008', location: { building: 'D栋', floor: '2F' } },
    createdAt: '45分钟前', acknowledgedAt: '40分钟前', isOverdue: false
  },
  {
    id: 'A-006', code: 'ROBOT_ERROR', level: 'high', type: 'robot_error', status: 'resolved',
    title: '传感器异常', message: 'R-002 激光雷达传感器数据异常',
    source: { type: 'robot', id: 'R-002', name: 'R-002', location: { building: 'A栋', floor: '2F' } },
    createdAt: '2小时前', acknowledgedAt: '1小时前', resolvedAt: '30分钟前', isOverdue: false
  },
  {
    id: 'A-007', code: 'LOW_BATTERY', level: 'medium', type: 'low_battery', status: 'resolved',
    title: '电量警告', message: 'R-007 电量低于30%已自动返回充电',
    source: { type: 'robot', id: 'R-007', name: 'R-007', location: { building: 'C栋', floor: '充电站' } },
    createdAt: '3小时前', resolvedAt: '2小时前', isOverdue: false
  },
];

const mockAlertDetail: AlertDetail = {
  ...mockAlerts[0],
  description: '机器人R-005在执行C栋3F走廊清洁任务时，检测到前方障碍物无法绕过，已停止移动等待处理。可能原因包括：临时放置的物品、地面异物或传感器误判。',
  suggestedActions: [
    { id: '1', type: 'view_robot', label: '查看机器人', description: '查看机器人详细状态', isPrimary: false },
    { id: '2', type: 'remote_control', label: '远程控制', description: '远程移动机器人', isPrimary: true },
    { id: '3', type: 'dispatch_staff', label: '派遣人员', description: '通知现场人员处理', isPrimary: false },
    { id: '4', type: 'restart_task', label: '重启任务', description: '清除障碍后重新执行', isPrimary: false },
  ],
  relatedData: {
    robot: { id: 'R-005', name: 'R-005', status: 'error', battery: 68 },
    task: { id: 'T-003', name: 'C栋会议室清洁', status: 'paused', progress: 28 },
  },
  history: [
    { id: '1', type: 'created', timestamp: '14:32:15', actor: '系统', description: '告警生成' },
    { id: '2', type: 'detected', timestamp: '14:32:10', actor: 'R-005', description: '检测到障碍物' },
    { id: '3', type: 'stopped', timestamp: '14:32:12', actor: 'R-005', description: '机器人停止移动' },
  ],
};

// ============ Sub Components ============

// Level Badge
const LevelBadge: React.FC<{ level: AlertLevel; size?: 'sm' | 'md' }> = ({ level, size = 'sm' }) => {
  const config: Record<AlertLevel, { bg: string; text: string; icon: string; label: string }> = {
    critical: { bg: 'bg-red-100', text: 'text-red-700', icon: '🔴', label: '紧急' },
    high: { bg: 'bg-orange-100', text: 'text-orange-700', icon: '🟠', label: '高' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '🟡', label: '中' },
    low: { bg: 'bg-green-100', text: 'text-green-700', icon: '🟢', label: '低' },
  };
  const { bg, text, icon, label } = config[level];

  if (size === 'md') {
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full ${bg} ${text}`}>
        <span className="mr-1">{icon}</span>
        <span className="text-sm font-medium">{label}</span>
      </span>
    );
  }

  return <span className="text-sm">{icon}</span>;
};

// Status Badge
const StatusBadge: React.FC<{ status: AlertStatus }> = ({ status }) => {
  const config: Record<AlertStatus, { bg: string; text: string; label: string }> = {
    active: { bg: 'bg-red-100', text: 'text-red-700', label: '待处理' },
    acknowledged: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '已确认' },
    resolved: { bg: 'bg-green-100', text: 'text-green-700', label: '已解决' },
    closed: { bg: 'bg-gray-100', text: 'text-gray-700', label: '已关闭' },
  };
  const { bg, text, label } = config[status];
  return <span className={`px-2 py-0.5 text-xs rounded-full ${bg} ${text}`}>{label}</span>;
};

// Alert Card
const AlertCard: React.FC<{ alert: AlertSummary; onClick: () => void }> = ({ alert, onClick }) => (
  <div
    onClick={onClick}
    className={`bg-white rounded-lg p-4 shadow-sm active:bg-gray-50 ${
      alert.level === 'critical' ? 'border-l-4 border-red-500' :
      alert.level === 'high' ? 'border-l-4 border-orange-500' : ''
    } ${alert.isOverdue ? 'ring-2 ring-red-200' : ''}`}
  >
    <div className="flex items-start space-x-3">
      <LevelBadge level={alert.level} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="font-medium text-gray-900 truncate">{alert.title}</span>
          <StatusBadge status={alert.status} />
        </div>
        <p className="text-sm text-gray-500 line-clamp-2 mb-2">{alert.message}</p>
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>📍 {alert.source.name} · {alert.source.location?.building} {alert.source.location?.floor}</span>
          <span className={alert.isOverdue ? 'text-red-500 font-medium' : ''}>
            {alert.isOverdue && '⏰ '}
            {alert.createdAt}
          </span>
        </div>
      </div>
    </div>
  </div>
);

// Alert Detail Panel
const AlertDetailPanel: React.FC<{
  alert: AlertDetail;
  onClose: () => void;
  onAction: (action: string) => void;
  onAcknowledge: () => void;
  onResolve: () => void;
}> = ({ alert, onClose, onAction, onAcknowledge, onResolve }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
    <div className="bg-white w-full rounded-t-2xl max-h-[90vh] overflow-auto">
      {/* Header */}
      <div className={`sticky top-0 p-4 border-b border-gray-100 ${
        alert.level === 'critical' ? 'bg-red-50' :
        alert.level === 'high' ? 'bg-orange-50' : 'bg-white'
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <LevelBadge level={alert.level} size="md" />
              <StatusBadge status={alert.status} />
              {alert.isOverdue && (
                <span className="text-xs text-red-500 font-medium">⏰ 超时</span>
              )}
            </div>
            <h2 className="font-bold text-gray-900">{alert.title}</h2>
          </div>
          <button onClick={onClose} className="p-2 text-gray-400">✕</button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Description */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-700">{alert.description}</p>
        </div>

        {/* Source Info */}
        <div className="bg-white rounded-lg border border-gray-100">
          <div className="p-3 border-b border-gray-50">
            <div className="text-xs text-gray-500">来源</div>
            <div className="text-sm font-medium">{alert.source.name}</div>
          </div>
          <div className="p-3 border-b border-gray-50">
            <div className="text-xs text-gray-500">位置</div>
            <div className="text-sm font-medium">
              {alert.source.location?.building} {alert.source.location?.floor}
            </div>
          </div>
          <div className="p-3">
            <div className="text-xs text-gray-500">发生时间</div>
            <div className="text-sm font-medium">{alert.createdAt}</div>
          </div>
        </div>

        {/* Related Data */}
        {alert.relatedData.robot && (
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-xs text-blue-600 mb-2">关联机器人</div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-blue-900">{alert.relatedData.robot.name}</div>
                <div className="text-sm text-blue-700">状态: {alert.relatedData.robot.status}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-blue-700">电量</div>
                <div className="font-medium text-blue-900">{alert.relatedData.robot.battery}%</div>
              </div>
            </div>
          </div>
        )}

        {alert.relatedData.task && (
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="text-xs text-purple-600 mb-2">关联任务</div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-purple-900">{alert.relatedData.task.name}</div>
                <div className="text-sm text-purple-700">状态: {alert.relatedData.task.status}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-purple-700">进度</div>
                <div className="font-medium text-purple-900">{alert.relatedData.task.progress}%</div>
              </div>
            </div>
          </div>
        )}

        {/* Suggested Actions */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">建议操作</h4>
          <div className="space-y-2">
            {alert.suggestedActions.map(action => (
              <button
                key={action.id}
                onClick={() => onAction(action.type)}
                className={`w-full p-3 rounded-lg text-left ${
                  action.isPrimary
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                <div className={`text-sm font-medium ${action.isPrimary ? 'text-white' : 'text-gray-900'}`}>
                  {action.label}
                </div>
                <div className={`text-xs ${action.isPrimary ? 'text-blue-100' : 'text-gray-500'}`}>
                  {action.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* History */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">处理历史</h4>
          <div className="space-y-2">
            {alert.history.map((event, index) => (
              <div key={event.id} className="flex items-start space-x-3">
                <div className={`w-2 h-2 rounded-full mt-1.5 ${
                  index === 0 ? 'bg-blue-500' : 'bg-gray-300'
                }`} />
                <div className="flex-1">
                  <div className="text-sm text-gray-700">{event.description}</div>
                  <div className="text-xs text-gray-400">{event.timestamp} · {event.actor}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        {alert.status === 'active' && (
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={onAcknowledge}
              className="py-3 bg-yellow-500 text-white rounded-lg text-sm font-medium"
            >
              ✓ 确认告警
            </button>
            <button
              onClick={onResolve}
              className="py-3 bg-green-500 text-white rounded-lg text-sm font-medium"
            >
              ✓ 标记已解决
            </button>
          </div>
        )}
        {alert.status === 'acknowledged' && (
          <button
            onClick={onResolve}
            className="w-full py-3 bg-green-500 text-white rounded-lg text-sm font-medium"
          >
            ✓ 标记已解决
          </button>
        )}
      </div>
    </div>
  </div>
);

// Stats Summary
const StatsSummary: React.FC<{ alerts: AlertSummary[] }> = ({ alerts }) => {
  const critical = alerts.filter(a => a.level === 'critical' && a.status === 'active').length;
  const high = alerts.filter(a => a.level === 'high' && a.status === 'active').length;
  const pending = alerts.filter(a => a.status === 'active').length;
  const overdue = alerts.filter(a => a.isOverdue).length;

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <div className="grid grid-cols-4 gap-2 text-center">
        <div>
          <div className="text-2xl font-bold text-red-600">{critical}</div>
          <div className="text-xs text-gray-500">紧急</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-orange-600">{high}</div>
          <div className="text-xs text-gray-500">高优先</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{pending}</div>
          <div className="text-xs text-gray-500">待处理</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-500">{overdue}</div>
          <div className="text-xs text-gray-500">超时</div>
        </div>
      </div>
    </div>
  );
};

// ============ Main Component ============

export const MobileAlert: React.FC<MobileAlertProps> = ({
  tenantId: _tenantId,
  onBack,
  onRobotSelect,
  onTaskSelect,
}) => {
  // State
  const [activeTab, setActiveTab] = useState<TabKey>('active');
  const [alerts, setAlerts] = useState<AlertSummary[]>(mockAlerts);
  const [selectedAlert, setSelectedAlert] = useState<AlertDetail | null>(null);
  const [levelFilter, setLevelFilter] = useState<AlertLevel | 'all'>('all');

  // Filter alerts
  const getFilteredAlerts = useCallback(() => {
    let filtered = alerts;

    // Filter by tab
    switch (activeTab) {
      case 'active':
        filtered = filtered.filter(a => a.status === 'active');
        break;
      case 'acknowledged':
        filtered = filtered.filter(a => a.status === 'acknowledged');
        break;
      case 'resolved':
        filtered = filtered.filter(a => a.status === 'resolved' || a.status === 'closed');
        break;
      default:
        break;
    }

    // Filter by level
    if (levelFilter !== 'all') {
      filtered = filtered.filter(a => a.level === levelFilter);
    }

    return filtered;
  }, [activeTab, alerts, levelFilter]);

  // Tab config
  const tabs: { key: TabKey; label: string; badge?: number }[] = [
    { key: 'active', label: '待处理', badge: alerts.filter(a => a.status === 'active').length },
    { key: 'acknowledged', label: '已确认', badge: alerts.filter(a => a.status === 'acknowledged').length },
    { key: 'resolved', label: '已解决' },
    { key: 'all', label: '全部' },
  ];

  // Handlers
  const handleAlertClick = (alert: AlertSummary) => {
    setSelectedAlert({ ...mockAlertDetail, ...alert });
  };

  const handleAction = (action: string) => {
    console.log('Alert action:', selectedAlert?.id, action);
    if (action === 'view_robot' && selectedAlert?.relatedData?.robot) {
      onRobotSelect?.(selectedAlert.relatedData.robot.id);
    } else if (action === 'view_task' && selectedAlert?.relatedData?.task) {
      onTaskSelect?.(selectedAlert.relatedData.task.id);
    } else {
      alert(`执行操作: ${action}`);
    }
  };

  const handleAcknowledge = () => {
    if (selectedAlert) {
      setAlerts(prev => prev.map(a =>
        a.id === selectedAlert.id ? { ...a, status: 'acknowledged' as AlertStatus, acknowledgedAt: '刚刚' } : a
      ));
      setSelectedAlert(null);
    }
  };

  const handleResolve = () => {
    if (selectedAlert) {
      setAlerts(prev => prev.map(a =>
        a.id === selectedAlert.id ? { ...a, status: 'resolved' as AlertStatus, resolvedAt: '刚刚' } : a
      ));
      setSelectedAlert(null);
    }
  };

  const filteredAlerts = getFilteredAlerts();

  return (
    <div className="min-h-screen bg-gray-100 pb-4">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3 flex items-center justify-between">
          {onBack && (
            <button onClick={onBack} className="p-2 -ml-2 text-gray-500">←</button>
          )}
          <h1 className="text-lg font-bold text-gray-900 flex-1 text-center">告警中心</h1>
          <button className="p-2 -mr-2 text-gray-500">⚙️</button>
        </div>
      </div>

      {/* Stats */}
      <div className="p-4 pb-2">
        <StatsSummary alerts={alerts} />
      </div>

      {/* Level Filter */}
      <div className="px-4 py-2">
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {[
            { key: 'all', label: '全部', icon: '' },
            { key: 'critical', label: '紧急', icon: '🔴' },
            { key: 'high', label: '高', icon: '🟠' },
            { key: 'medium', label: '中', icon: '🟡' },
            { key: 'low', label: '低', icon: '🟢' },
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setLevelFilter(f.key as AlertLevel | 'all')}
              className={`px-3 py-1.5 text-sm rounded-full whitespace-nowrap flex items-center space-x-1 ${
                levelFilter === f.key ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 shadow-sm'
              }`}
            >
              {f.icon && <span>{f.icon}</span>}
              <span>{f.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-100">
        <div className="flex">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-3 text-sm font-medium relative ${
                activeTab === tab.key
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500'
              }`}
            >
              {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${
                  activeTab === tab.key ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Alert List */}
      <div className="p-4 space-y-3">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map(alert => (
            <AlertCard key={alert.id} alert={alert} onClick={() => handleAlertClick(alert)} />
          ))
        ) : (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">✓</div>
            <div>暂无告警</div>
          </div>
        )}
      </div>

      {/* Alert Detail Panel */}
      {selectedAlert && (
        <AlertDetailPanel
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onAction={handleAction}
          onAcknowledge={handleAcknowledge}
          onResolve={handleResolve}
        />
      )}
    </div>
  );
};

export default MobileAlert;
