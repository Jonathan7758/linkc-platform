/**
 * P1 Mobile Monitor - Mobile-First Monitoring Dashboard
 * 移动端监控页面
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============ Type Definitions ============

type RobotStatus = 'working' | 'idle' | 'charging' | 'error' | 'offline';
type AlertLevel = 'critical' | 'high' | 'medium' | 'low';
type ViewMode = 'list' | 'map';
type TabType = 'dashboard' | 'fleet' | 'notifications' | 'settings';

interface DashboardData {
  healthScore: number;
  healthTrend: 'up' | 'down' | 'stable';
  stats: {
    total: number;
    working: number;
    idle: number;
    charging: number;
    error: number;
    offline: number;
  };
  todaySummary: {
    tasksCompleted: number;
    tasksTotal: number;
    coverageRate: number;
    efficiency: number;
  };
  alerts: {
    critical: number;
    warning: number;
    info: number;
  };
  recentAlerts: AlertSummary[];
  lastUpdated: string;
}

interface AlertSummary {
  id: string;
  robotId: string;
  robotName: string;
  level: AlertLevel;
  message: string;
  timestamp: string;
}

interface RobotSummary {
  id: string;
  name: string;
  status: RobotStatus;
  battery: number;
  building: string;
  floor: string;
  currentTask?: string;
  lastActive: string;
}

interface Notification {
  id: string;
  type: 'alert' | 'task' | 'system';
  level: AlertLevel;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  robotId?: string;
  taskId?: string;
}

interface MobileMonitorProps {
  tenantId: string;
  onRobotSelect?: (robotId: string) => void;
  onAlertSelect?: (alertId: string) => void;
}

// ============ Mock Data ============

const mockDashboard: DashboardData = {
  healthScore: 85,
  healthTrend: 'up',
  stats: {
    total: 25,
    working: 12,
    idle: 5,
    charging: 6,
    error: 2,
    offline: 0,
  },
  todaySummary: {
    tasksCompleted: 42,
    tasksTotal: 48,
    coverageRate: 94.2,
    efficiency: 1.2,
  },
  alerts: {
    critical: 2,
    warning: 5,
    info: 3,
  },
  recentAlerts: [
    { id: '1', robotId: 'R-005', robotName: 'R-005', level: 'critical', message: '清洁机器人卡住', timestamp: '2分钟前' },
    { id: '2', robotId: 'R-012', robotName: 'R-012', level: 'high', message: '电量过低警告', timestamp: '10分钟前' },
    { id: '3', robotId: 'R-003', robotName: 'R-003', level: 'medium', message: '清洁效率下降', timestamp: '25分钟前' },
  ],
  lastUpdated: new Date().toLocaleTimeString('zh-CN'),
};

const mockRobots: RobotSummary[] = [
  { id: 'R-001', name: 'R-001', status: 'working', battery: 75, building: 'A栋', floor: '1F', currentTask: '大堂清洁', lastActive: '刚刚' },
  { id: 'R-002', name: 'R-002', status: 'working', battery: 62, building: 'A栋', floor: '2F', currentTask: '走廊清洁', lastActive: '刚刚' },
  { id: 'R-003', name: 'R-003', status: 'idle', battery: 95, building: 'B栋', floor: '1F', lastActive: '5分钟前' },
  { id: 'R-004', name: 'R-004', status: 'charging', battery: 45, building: 'B栋', floor: '充电站', lastActive: '30分钟前' },
  { id: 'R-005', name: 'R-005', status: 'error', battery: 68, building: 'C栋', floor: '3F', currentTask: '会议室清洁', lastActive: '2分钟前' },
  { id: 'R-006', name: 'R-006', status: 'working', battery: 82, building: 'A栋', floor: '3F', currentTask: '办公区清洁', lastActive: '刚刚' },
  { id: 'R-007', name: 'R-007', status: 'charging', battery: 28, building: 'C栋', floor: '充电站', lastActive: '1小时前' },
  { id: 'R-008', name: 'R-008', status: 'idle', battery: 88, building: 'D栋', floor: '2F', lastActive: '15分钟前' },
];

const mockNotifications: Notification[] = [
  { id: 'n1', type: 'alert', level: 'critical', title: '机器人故障', message: 'R-005 在C栋3F卡住，需要人工介入', timestamp: '2分钟前', read: false, robotId: 'R-005' },
  { id: 'n2', type: 'alert', level: 'high', title: '电量警告', message: 'R-012 电量低于20%，即将自动返回充电', timestamp: '10分钟前', read: false, robotId: 'R-012' },
  { id: 'n3', type: 'task', level: 'medium', title: '任务完成', message: 'A栋1F大堂清洁任务已完成，覆盖率98%', timestamp: '15分钟前', read: true, taskId: 'T-001' },
  { id: 'n4', type: 'alert', level: 'medium', title: '效率下降', message: 'R-003 清洁效率较平均值下降15%', timestamp: '25分钟前', read: true, robotId: 'R-003' },
  { id: 'n5', type: 'system', level: 'low', title: '系统更新', message: '系统将在今晚3:00进行维护升级', timestamp: '1小时前', read: true },
];

// ============ Sub Components ============

// Health Score Ring
const HealthScoreRing: React.FC<{ score: number; trend: 'up' | 'down' | 'stable'; size?: number }> = ({
  score, trend, size = 120
}) => {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (score >= 90) return '#22c55e';
    if (score >= 75) return '#3b82f6';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const getLabel = () => {
    if (score >= 90) return '优秀';
    if (score >= 75) return '良好';
    if (score >= 60) return '一般';
    return '较差';
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth="8"
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor()}
          strokeWidth="8"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color: getColor() }}>{score}</span>
        <span className="text-sm text-gray-500">{getLabel()}</span>
        <span className="text-xs text-gray-400">
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
        </span>
      </div>
    </div>
  );
};

// Status Badge
const StatusBadge: React.FC<{ status: RobotStatus }> = ({ status }) => {
  const config: Record<RobotStatus, { bg: string; text: string; label: string }> = {
    working: { bg: 'bg-green-100', text: 'text-green-700', label: '工作中' },
    idle: { bg: 'bg-blue-100', text: 'text-blue-700', label: '空闲' },
    charging: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '充电' },
    error: { bg: 'bg-red-100', text: 'text-red-700', label: '故障' },
    offline: { bg: 'bg-gray-100', text: 'text-gray-700', label: '离线' },
  };
  const { bg, text, label } = config[status];
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full ${bg} ${text}`}>{label}</span>
  );
};

// Battery Indicator
const BatteryIndicator: React.FC<{ level: number }> = ({ level }) => {
  const getColor = () => {
    if (level >= 60) return 'bg-green-500';
    if (level >= 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="flex items-center space-x-1">
      <div className="w-6 h-3 border border-gray-400 rounded-sm relative">
        <div className={`absolute left-0 top-0 bottom-0 rounded-sm ${getColor()}`} style={{ width: `${level}%` }} />
      </div>
      <span className="text-xs text-gray-500">{level}%</span>
    </div>
  );
};

// Alert Level Icon
const AlertLevelIcon: React.FC<{ level: AlertLevel }> = ({ level }) => {
  const config: Record<AlertLevel, { icon: string; color: string }> = {
    critical: { icon: '🔴', color: 'text-red-500' },
    high: { icon: '🟠', color: 'text-orange-500' },
    medium: { icon: '🟡', color: 'text-yellow-500' },
    low: { icon: '🟢', color: 'text-green-500' },
  };
  return <span className={config[level].color}>{config[level].icon}</span>;
};

// Quick Stats Grid
const QuickStatsGrid: React.FC<{ stats: DashboardData['stats']; onStatClick?: (key: string) => void }> = ({
  stats, onStatClick
}) => {
  const items = [
    { key: 'working', label: '工作中', value: stats.working, color: 'bg-green-500' },
    { key: 'idle', label: '空闲', value: stats.idle, color: 'bg-blue-500' },
    { key: 'charging', label: '充电', value: stats.charging, color: 'bg-yellow-500' },
    { key: 'error', label: '故障', value: stats.error, color: 'bg-red-500' },
  ];

  return (
    <div className="grid grid-cols-4 gap-2">
      {items.map(item => (
        <div
          key={item.key}
          onClick={() => onStatClick?.(item.key)}
          className="bg-white rounded-lg p-3 text-center shadow-sm active:bg-gray-50"
        >
          <div className={`w-2 h-2 rounded-full ${item.color} mx-auto mb-1`} />
          <div className="text-xl font-bold text-gray-900">{item.value}</div>
          <div className="text-xs text-gray-500">{item.label}</div>
        </div>
      ))}
    </div>
  );
};

// Robot List Item
const RobotListItem: React.FC<{ robot: RobotSummary; onClick: () => void }> = ({ robot, onClick }) => (
  <div
    onClick={onClick}
    className="bg-white rounded-lg p-4 shadow-sm flex items-center justify-between active:bg-gray-50"
  >
    <div className="flex items-center space-x-3">
      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
        robot.status === 'error' ? 'bg-red-100' : 'bg-gray-100'
      }`}>
        <span className="text-lg">🤖</span>
      </div>
      <div>
        <div className="flex items-center space-x-2">
          <span className="font-medium text-gray-900">{robot.name}</span>
          <StatusBadge status={robot.status} />
        </div>
        <div className="text-sm text-gray-500">
          {robot.building} {robot.floor}
          {robot.currentTask && ` · ${robot.currentTask}`}
        </div>
      </div>
    </div>
    <div className="text-right">
      <BatteryIndicator level={robot.battery} />
      <div className="text-xs text-gray-400 mt-1">{robot.lastActive}</div>
    </div>
  </div>
);

// Notification Item
const NotificationItem: React.FC<{ notification: Notification; onClick: () => void }> = ({
  notification, onClick
}) => (
  <div
    onClick={onClick}
    className={`p-4 border-b border-gray-100 active:bg-gray-50 ${
      notification.read ? 'bg-white' : 'bg-blue-50'
    }`}
  >
    <div className="flex items-start space-x-3">
      <AlertLevelIcon level={notification.level} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className={`font-medium ${notification.read ? 'text-gray-700' : 'text-gray-900'}`}>
            {notification.title}
          </span>
          <span className="text-xs text-gray-400">{notification.timestamp}</span>
        </div>
        <p className="text-sm text-gray-500 mt-1 line-clamp-2">{notification.message}</p>
      </div>
    </div>
  </div>
);

// Robot Detail Panel
const RobotDetailPanel: React.FC<{
  robot: RobotSummary;
  onClose: () => void;
  onControl: (action: string) => void;
}> = ({ robot, onClose, onControl }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
    <div className="bg-white w-full rounded-t-2xl max-h-[80vh] overflow-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🤖</span>
          <div>
            <div className="font-medium text-gray-900">{robot.name}</div>
            <StatusBadge status={robot.status} />
          </div>
        </div>
        <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600">✕</button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Battery & Location */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">电量</div>
            <div className="flex items-center space-x-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full">
                <div
                  className={`h-full rounded-full ${robot.battery >= 60 ? 'bg-green-500' : robot.battery >= 30 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${robot.battery}%` }}
                />
              </div>
              <span className="text-sm font-medium">{robot.battery}%</span>
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">位置</div>
            <div className="text-sm font-medium">{robot.building} {robot.floor}</div>
          </div>
        </div>

        {/* Current Task */}
        {robot.currentTask && (
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-xs text-blue-600 mb-1">当前任务</div>
            <div className="text-sm font-medium text-blue-900">{robot.currentTask}</div>
          </div>
        )}

        {/* Control Buttons */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">快捷操作</div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onControl('stop')}
              className="py-3 px-4 bg-red-500 text-white rounded-lg text-sm font-medium active:bg-red-600"
            >
              🛑 紧急停止
            </button>
            <button
              onClick={() => onControl('home')}
              className="py-3 px-4 bg-yellow-500 text-white rounded-lg text-sm font-medium active:bg-yellow-600"
            >
              🏠 返回充电
            </button>
            <button
              onClick={() => onControl('resume')}
              className="py-3 px-4 bg-green-500 text-white rounded-lg text-sm font-medium active:bg-green-600"
            >
              ▶️ 恢复工作
            </button>
            <button
              onClick={() => onControl('locate')}
              className="py-3 px-4 bg-blue-500 text-white rounded-lg text-sm font-medium active:bg-blue-600"
            >
              📍 定位机器人
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// ============ Tab Panels ============

// Dashboard Panel
const DashboardPanel: React.FC<{ data: DashboardData; onNavigate: (target: string) => void }> = ({
  data, onNavigate
}) => (
  <div className="space-y-4">
    {/* Health Score */}
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm text-gray-500">运营健康度</h3>
          <p className="text-xs text-gray-400 mt-1">较昨日 {data.healthTrend === 'up' ? '+2.3%' : '-1.2%'}</p>
        </div>
        <HealthScoreRing score={data.healthScore} trend={data.healthTrend} size={100} />
      </div>
    </div>

    {/* Quick Stats */}
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium text-gray-700">机器人状态</h3>
        <span className="text-xs text-gray-500">共 {data.stats.total} 台</span>
      </div>
      <QuickStatsGrid stats={data.stats} onStatClick={() => onNavigate('fleet')} />
    </div>

    {/* Today Summary */}
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <h3 className="text-sm font-medium text-gray-700 mb-3">今日概览</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-2xl font-bold text-gray-900">
            {data.todaySummary.tasksCompleted}/{data.todaySummary.tasksTotal}
          </div>
          <div className="text-xs text-gray-500">任务完成</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {data.todaySummary.coverageRate}%
          </div>
          <div className="text-xs text-gray-500">覆盖率</div>
        </div>
      </div>
    </div>

    {/* Alerts Summary */}
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-medium text-gray-700">待处理异常</h3>
        <button onClick={() => onNavigate('notifications')} className="text-xs text-blue-600">
          查看全部 →
        </button>
      </div>

      <div className="flex space-x-4 mb-3">
        <div className="flex items-center space-x-1">
          <span className="text-red-500">🔴</span>
          <span className="text-sm font-medium">{data.alerts.critical}</span>
          <span className="text-xs text-gray-500">紧急</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-yellow-500">🟡</span>
          <span className="text-sm font-medium">{data.alerts.warning}</span>
          <span className="text-xs text-gray-500">警告</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-blue-500">🔵</span>
          <span className="text-sm font-medium">{data.alerts.info}</span>
          <span className="text-xs text-gray-500">提示</span>
        </div>
      </div>

      <div className="space-y-2">
        {data.recentAlerts.slice(0, 2).map(alert => (
          <div key={alert.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
            <div className="flex items-center space-x-2">
              <AlertLevelIcon level={alert.level} />
              <span className="text-sm">{alert.robotName} {alert.message}</span>
            </div>
            <span className="text-xs text-gray-400">{alert.timestamp}</span>
          </div>
        ))}
      </div>
    </div>

    {/* Last Updated */}
    <div className="text-center text-xs text-gray-400">
      最后更新: {data.lastUpdated}
    </div>
  </div>
);

// Fleet Panel
const FleetPanel: React.FC<{
  robots: RobotSummary[];
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onRobotSelect: (robot: RobotSummary) => void;
  filter: string;
  onFilterChange: (filter: string) => void;
}> = ({ robots, viewMode, onViewModeChange, onRobotSelect, filter, onFilterChange }) => {
  const filteredRobots = filter === 'all' ? robots : robots.filter(r => r.status === filter);

  return (
    <div className="space-y-4">
      {/* Filter & View Toggle */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {['all', 'working', 'idle', 'charging', 'error'].map(f => (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`px-3 py-1.5 text-sm rounded-full whitespace-nowrap ${
                filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
              }`}
            >
              {f === 'all' ? '全部' : f === 'working' ? '工作中' : f === 'idle' ? '空闲' : f === 'charging' ? '充电' : '故障'}
            </button>
          ))}
        </div>
        <div className="flex space-x-1">
          <button
            onClick={() => onViewModeChange('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-400'}`}
          >
            ☰
          </button>
          <button
            onClick={() => onViewModeChange('map')}
            className={`p-2 rounded ${viewMode === 'map' ? 'bg-blue-100 text-blue-600' : 'text-gray-400'}`}
          >
            🗺
          </button>
        </div>
      </div>

      {/* Robot List/Map */}
      {viewMode === 'list' ? (
        <div className="space-y-2">
          {filteredRobots.map(robot => (
            <RobotListItem key={robot.id} robot={robot} onClick={() => onRobotSelect(robot)} />
          ))}
          {filteredRobots.length === 0 && (
            <div className="text-center py-8 text-gray-500">暂无机器人</div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm h-80 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-4xl mb-2">🗺</div>
            <div>地图视图</div>
            <div className="text-xs text-gray-400 mt-1">显示 {filteredRobots.length} 台机器人</div>
          </div>
        </div>
      )}
    </div>
  );
};

// Notifications Panel
const NotificationsPanel: React.FC<{
  notifications: Notification[];
  onNotificationClick: (notification: Notification) => void;
  onMarkAllRead: () => void;
}> = ({ notifications, onNotificationClick, onMarkAllRead }) => {
  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <span className="text-sm text-gray-500">
            {unreadCount > 0 ? `${unreadCount} 条未读` : '没有未读通知'}
          </span>
        </div>
        {unreadCount > 0 && (
          <button onClick={onMarkAllRead} className="text-sm text-blue-600">
            全部已读
          </button>
        )}
      </div>

      {/* Notification List */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {notifications.map(notification => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onClick={() => onNotificationClick(notification)}
          />
        ))}
        {notifications.length === 0 && (
          <div className="text-center py-8 text-gray-500">暂无通知</div>
        )}
      </div>
    </div>
  );
};

// Settings Panel
const SettingsPanel: React.FC = () => (
  <div className="space-y-4">
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-medium text-gray-900">通知设置</h3>
      </div>
      <div className="divide-y divide-gray-100">
        {[
          { label: '紧急告警推送', desc: '机器人故障等紧急情况', enabled: true },
          { label: '任务完成通知', desc: '任务完成时推送通知', enabled: true },
          { label: '电量警告', desc: '机器人电量低于20%时提醒', enabled: true },
          { label: '系统通知', desc: '系统更新和维护通知', enabled: false },
        ].map((item, index) => (
          <div key={index} className="p-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-900">{item.label}</div>
              <div className="text-xs text-gray-500">{item.desc}</div>
            </div>
            <div className={`w-10 h-6 rounded-full relative ${item.enabled ? 'bg-blue-600' : 'bg-gray-300'}`}>
              <div className={`absolute w-4 h-4 bg-white rounded-full top-1 transition-all ${item.enabled ? 'right-1' : 'left-1'}`} />
            </div>
          </div>
        ))}
      </div>
    </div>

    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-medium text-gray-900">账户信息</h3>
      </div>
      <div className="p-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-xl">👤</span>
          </div>
          <div>
            <div className="font-medium text-gray-900">运维管理员</div>
            <div className="text-sm text-gray-500">admin@linkc.com</div>
          </div>
        </div>
      </div>
    </div>

    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 text-center">
        <div className="text-sm text-gray-500">LinkC Platform Mobile</div>
        <div className="text-xs text-gray-400 mt-1">版本 1.0.0</div>
      </div>
    </div>
  </div>
);

// ============ Main Component ============

export const MobileMonitor: React.FC<MobileMonitorProps> = ({
  tenantId,
  onRobotSelect,
  onAlertSelect,
}) => {
  // State
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [dashboard, _setDashboard] = useState<DashboardData>(mockDashboard);
  const [robots, _setRobots] = useState<RobotSummary[]>(mockRobots);
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [robotFilter, setRobotFilter] = useState('all');
  const [selectedRobot, setSelectedRobot] = useState<RobotSummary | null>(null);
  const [loading, setLoading] = useState(false);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handlers
  const handleRobotControl = (action: string) => {
    console.log('Robot control:', selectedRobot?.id, action);
    alert(`执行操作: ${action}`);
    setSelectedRobot(null);
  };

  const handleMarkAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  // Tab config
  const tabs: { key: TabType; label: string; icon: string; badge?: number }[] = [
    { key: 'dashboard', label: '首页', icon: '🏠' },
    { key: 'fleet', label: '车队', icon: '🤖' },
    { key: 'notifications', label: '通知', icon: '🔔', badge: unreadCount },
    { key: 'settings', label: '设置', icon: '⚙️' },
  ];

  return (
    <div className="min-h-screen bg-gray-100 pb-16">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">
            {activeTab === 'dashboard' && '运营监控'}
            {activeTab === 'fleet' && '机器人车队'}
            {activeTab === 'notifications' && '通知中心'}
            {activeTab === 'settings' && '设置'}
          </h1>
          <button onClick={loadData} disabled={loading} className="p-2 text-gray-500">
            {loading ? '⏳' : '🔄'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'dashboard' && (
          <DashboardPanel data={dashboard} onNavigate={target => setActiveTab(target as TabType)} />
        )}
        {activeTab === 'fleet' && (
          <FleetPanel
            robots={robots}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            onRobotSelect={robot => {
              setSelectedRobot(robot);
              onRobotSelect?.(robot.id);
            }}
            filter={robotFilter}
            onFilterChange={setRobotFilter}
          />
        )}
        {activeTab === 'notifications' && (
          <NotificationsPanel
            notifications={notifications}
            onNotificationClick={n => {
              if (n.robotId) onRobotSelect?.(n.robotId);
              if (n.type === 'alert') onAlertSelect?.(n.id);
            }}
            onMarkAllRead={handleMarkAllRead}
          />
        )}
        {activeTab === 'settings' && <SettingsPanel />}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around py-2">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex flex-col items-center py-1 px-4 relative ${
              activeTab === tab.key ? 'text-blue-600' : 'text-gray-500'
            }`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="text-xs mt-0.5">{tab.label}</span>
            {tab.badge && tab.badge > 0 && (
              <span className="absolute -top-1 right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Robot Detail Panel */}
      {selectedRobot && (
        <RobotDetailPanel
          robot={selectedRobot}
          onClose={() => setSelectedRobot(null)}
          onControl={handleRobotControl}
        />
      )}
    </div>
  );
};

export default MobileMonitor;
