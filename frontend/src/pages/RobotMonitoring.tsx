/**
 * O3: Robot Monitoring Interface
 * 机器人监控界面 - 机器人车队的实时监控和管理
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============================================================
// Types
// ============================================================

type RobotStatus = 'online' | 'working' | 'idle' | 'charging' | 'error' | 'offline' | 'maintenance';

interface Robot {
  robotId: string;
  name: string;
  brand: string;
  model: string;
  status: RobotStatus;
  batteryLevel: number;
  buildingName: string;
  floorName: string;
  position: { x: number; y: number };
  currentTask?: string;
  lastActive: string;
  errorMessage?: string;
  consumables: {
    brushWear: number;
    filterStatus: number;
    waterLevel: number;
  };
}

interface FleetStats {
  total: number;
  online: number;
  working: number;
  idle: number;
  charging: number;
  error: number;
  offline: number;
}

interface RobotMonitoringProps {
  tenantId: string;
  buildingId?: string;
  onRobotSelect?: (robotId: string) => void;
}

// ============================================================
// Mock Data
// ============================================================

const mockRobots: Robot[] = [
  {
    robotId: 'robot_001',
    name: 'GX-001',
    brand: '高仙',
    model: 'X100',
    status: 'working',
    batteryLevel: 78,
    buildingName: 'A栋',
    floorName: '1F',
    position: { x: 35, y: 45 },
    currentTask: 'T-001 大堂清洁',
    lastActive: '2分钟前',
    consumables: { brushWear: 75, filterStatus: 80, waterLevel: 60 },
  },
  {
    robotId: 'robot_002',
    name: 'GX-002',
    brand: '高仙',
    model: 'X100',
    status: 'idle',
    batteryLevel: 95,
    buildingName: 'A栋',
    floorName: '2F',
    position: { x: 60, y: 30 },
    lastActive: '刚刚',
    consumables: { brushWear: 90, filterStatus: 85, waterLevel: 100 },
  },
  {
    robotId: 'robot_003',
    name: 'GX-003',
    brand: '高仙',
    model: 'X100',
    status: 'error',
    batteryLevel: 45,
    buildingName: 'B栋',
    floorName: '1F',
    position: { x: 25, y: 70 },
    errorMessage: '传感器故障 - 已卡住',
    lastActive: '5分钟前',
    consumables: { brushWear: 40, filterStatus: 50, waterLevel: 30 },
  },
  {
    robotId: 'robot_004',
    name: 'EC-001',
    brand: '科沃斯',
    model: 'Pro',
    status: 'charging',
    batteryLevel: 35,
    buildingName: 'A栋',
    floorName: '1F',
    position: { x: 10, y: 10 },
    lastActive: '10分钟前',
    consumables: { brushWear: 60, filterStatus: 70, waterLevel: 80 },
  },
  {
    robotId: 'robot_005',
    name: 'GX-004',
    brand: '高仙',
    model: 'X100',
    status: 'offline',
    batteryLevel: 0,
    buildingName: 'B栋',
    floorName: '2F',
    position: { x: 50, y: 50 },
    lastActive: '2小时前',
    consumables: { brushWear: 55, filterStatus: 65, waterLevel: 0 },
  },
];

const mockStats: FleetStats = {
  total: 15,
  online: 13,
  working: 8,
  idle: 3,
  charging: 2,
  error: 2,
  offline: 2,
};

// ============================================================
// Helper Functions
// ============================================================

const getStatusConfig = (status: RobotStatus) => {
  const configs = {
    online: { label: '在线', color: 'bg-green-500', textColor: 'text-green-600', icon: '●' },
    working: { label: '工作中', color: 'bg-blue-500', textColor: 'text-blue-600', icon: '◉' },
    idle: { label: '空闲', color: 'bg-gray-400', textColor: 'text-gray-500', icon: '○' },
    charging: { label: '充电中', color: 'bg-yellow-500', textColor: 'text-yellow-600', icon: '⚡' },
    error: { label: '异常', color: 'bg-red-500', textColor: 'text-red-600', icon: '⚠' },
    offline: { label: '离线', color: 'bg-gray-300', textColor: 'text-gray-400', icon: '◌' },
    maintenance: { label: '维护中', color: 'bg-orange-500', textColor: 'text-orange-600', icon: '🔧' },
  };
  return configs[status];
};

const getBatteryColor = (level: number) => {
  if (level > 60) return 'text-green-600';
  if (level > 20) return 'text-yellow-600';
  return 'text-red-600';
};

// ============================================================
// Fleet Stats Component
// ============================================================

interface FleetStatsProps {
  stats: FleetStats;
}

const FleetStatsComponent: React.FC<FleetStatsProps> = ({ stats }) => {
  const items = [
    { key: 'total', label: '总数', value: stats.total, unit: '台', color: 'bg-gray-100' },
    { key: 'online', label: '在线', value: stats.online, icon: '●', iconColor: 'text-green-500', color: 'bg-green-50' },
    { key: 'working', label: '工作中', value: stats.working, icon: '●', iconColor: 'text-blue-500', color: 'bg-blue-50' },
    { key: 'idle', label: '空闲', value: stats.idle, icon: '○', iconColor: 'text-gray-400', color: 'bg-gray-50' },
    { key: 'error', label: '异常', value: stats.error, icon: '●', iconColor: 'text-red-500', color: 'bg-red-50' },
  ];

  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm mb-4">
      <h3 className="font-semibold text-gray-900 mb-3">车队概览</h3>
      <div className="flex gap-4">
        {items.map(item => (
          <div
            key={item.key}
            className={`flex-1 p-3 rounded-lg ${item.color}`}
          >
            <div className="text-2xl font-bold text-gray-900">{item.value}</div>
            <div className="flex items-center gap-1 text-sm text-gray-600">
              {item.icon && <span className={item.iconColor}>{item.icon}</span>}
              {item.label}
              {item.unit && <span>{item.unit}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================
// Robot List Item Component
// ============================================================

interface RobotListItemProps {
  robot: Robot;
  isSelected: boolean;
  onClick: () => void;
}

const RobotListItem: React.FC<RobotListItemProps> = ({ robot, isSelected, onClick }) => {
  const statusConfig = getStatusConfig(robot.status);

  return (
    <div
      onClick={onClick}
      className={`p-3 border-b cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className={statusConfig.textColor}>{statusConfig.icon}</span>
          <span className="font-medium text-gray-900">{robot.name}</span>
        </div>
        <span className={`px-2 py-0.5 text-xs rounded ${
          robot.status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
        }`}>
          {statusConfig.label}
        </span>
      </div>

      <div className="mt-1 text-sm text-gray-500">
        {robot.brand} {robot.model} | {robot.buildingName} {robot.floorName}
      </div>

      <div className="mt-1 flex items-center gap-3 text-sm">
        <span className={getBatteryColor(robot.batteryLevel)}>
          🔋 {robot.batteryLevel}%
        </span>
        {robot.currentTask && (
          <span className="text-blue-600 truncate">
            📋 {robot.currentTask}
          </span>
        )}
        {robot.errorMessage && (
          <span className="text-red-600 truncate">
            ⚠ {robot.errorMessage}
          </span>
        )}
      </div>
    </div>
  );
};

// ============================================================
// Robot Detail Panel Component
// ============================================================

interface RobotDetailPanelProps {
  robot: Robot;
  onControl: (action: string) => void;
  onClose: () => void;
}

const RobotDetailPanel: React.FC<RobotDetailPanelProps> = ({ robot, onControl, onClose }) => {
  const statusConfig = getStatusConfig(robot.status);

  return (
    <div className="bg-white border-l h-full overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <span className={statusConfig.textColor}>{statusConfig.icon}</span>
            <h3 className="text-lg font-semibold">{robot.name}</h3>
          </div>
          <p className="text-sm text-gray-500">{robot.brand} {robot.model}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>

      {/* Status */}
      <div className="p-4 border-b">
        <h4 className="font-medium text-gray-700 mb-3">状态信息</h4>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-500">状态</span>
            <span className={`px-2 py-0.5 text-xs rounded ${
              robot.status === 'error' ? 'bg-red-100 text-red-700' :
              robot.status === 'working' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {statusConfig.label}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">电量</span>
            <span className={getBatteryColor(robot.batteryLevel)}>
              {robot.batteryLevel}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">位置</span>
            <span className="text-gray-700">{robot.buildingName} {robot.floorName}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">最后活动</span>
            <span className="text-gray-700">{robot.lastActive}</span>
          </div>
          {robot.currentTask && (
            <div className="flex justify-between">
              <span className="text-gray-500">当前任务</span>
              <span className="text-blue-600">{robot.currentTask}</span>
            </div>
          )}
          {robot.errorMessage && (
            <div className="mt-2 p-2 bg-red-50 text-red-700 text-sm rounded">
              ⚠ {robot.errorMessage}
            </div>
          )}
        </div>
      </div>

      {/* Consumables */}
      <div className="p-4 border-b">
        <h4 className="font-medium text-gray-700 mb-3">耗材状态</h4>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-500">刷盘磨损</span>
              <span>{robot.consumables.brushWear}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  robot.consumables.brushWear > 50 ? 'bg-green-500' :
                  robot.consumables.brushWear > 20 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${robot.consumables.brushWear}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-500">滤芯状态</span>
              <span>{robot.consumables.filterStatus}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  robot.consumables.filterStatus > 50 ? 'bg-green-500' :
                  robot.consumables.filterStatus > 20 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${robot.consumables.filterStatus}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-500">水箱水位</span>
              <span>{robot.consumables.waterLevel}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  robot.consumables.waterLevel > 50 ? 'bg-blue-500' :
                  robot.consumables.waterLevel > 20 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${robot.consumables.waterLevel}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="p-4">
        <h4 className="font-medium text-gray-700 mb-3">远程控制</h4>
        <div className="grid grid-cols-2 gap-2">
          {robot.status === 'idle' && (
            <button
              onClick={() => onControl('start')}
              className="px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm"
            >
              ▶ 开始工作
            </button>
          )}
          {robot.status === 'working' && (
            <>
              <button
                onClick={() => onControl('pause')}
                className="px-3 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 text-sm"
              >
                ⏸ 暂停
              </button>
              <button
                onClick={() => onControl('stop')}
                className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
              >
                ⏹ 停止
              </button>
            </>
          )}
          <button
            onClick={() => onControl('recall')}
            className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm"
          >
            🏠 召回
          </button>
          <button
            onClick={() => onControl('charge')}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
          >
            ⚡ 去充电
          </button>
          {robot.status === 'error' && (
            <button
              onClick={() => onControl('reset')}
              className="px-3 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 text-sm col-span-2"
            >
              🔄 重置故障
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================
// Simple Map Component
// ============================================================

interface SimpleMapProps {
  robots: Robot[];
  selectedRobotId?: string;
  onRobotClick: (robotId: string) => void;
}

const SimpleMap: React.FC<SimpleMapProps> = ({ robots, selectedRobotId, onRobotClick }) => {
  return (
    <div className="bg-gray-100 rounded-lg p-4 h-full relative">
      <svg width="100%" height="300" viewBox="0 0 100 100" className="bg-white rounded border">
        {/* Grid */}
        <defs>
          <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#e5e7eb" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#grid)" />

        {/* Robot Markers */}
        {robots.map(robot => {
          const statusConfig = getStatusConfig(robot.status);
          const isSelected = robot.robotId === selectedRobotId;

          return (
            <g
              key={robot.robotId}
              transform={`translate(${robot.position.x}, ${robot.position.y})`}
              onClick={() => onRobotClick(robot.robotId)}
              className="cursor-pointer"
            >
              {isSelected && (
                <circle r="8" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="2 1" />
              )}
              <circle
                r="5"
                fill={statusConfig.color.replace('bg-', '#').replace('-500', '')}
                className={statusConfig.color}
              />
              <text
                y="12"
                textAnchor="middle"
                className="text-xs fill-gray-700"
                style={{ fontSize: '3px' }}
              >
                {robot.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Map Controls */}
      <div className="absolute bottom-6 right-6 flex gap-1">
        <button className="p-2 bg-white border rounded shadow-sm hover:bg-gray-50">+</button>
        <button className="p-2 bg-white border rounded shadow-sm hover:bg-gray-50">-</button>
      </div>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const RobotMonitoring: React.FC<RobotMonitoringProps> = ({
  tenantId,
  buildingId,
  onRobotSelect,
}) => {
  const [robots, _setRobots] = useState<Robot[]>(mockRobots);
  const [stats, _setStats] = useState<FleetStats>(mockStats);
  const [selectedRobotId, setSelectedRobotId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Filters
  const [brandFilter, setBrandFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API calls
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('Failed to load robots:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId, buildingId]);

  useEffect(() => {
    loadData();
    // Auto refresh every 30 seconds
    const interval = setInterval(loadData, 30 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Filter robots
  const filteredRobots = robots.filter(robot => {
    if (brandFilter && robot.brand !== brandFilter) return false;
    if (statusFilter && robot.status !== statusFilter) return false;
    if (searchQuery && !robot.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const selectedRobot = robots.find(r => r.robotId === selectedRobotId);

  const handleRobotClick = (robotId: string) => {
    setSelectedRobotId(robotId);
    onRobotSelect?.(robotId);
  };

  const handleControl = (action: string) => {
    console.log(`Control robot ${selectedRobotId}: ${action}`);
    // TODO: Implement robot control
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">机器人监控</h1>
          <p className="text-gray-500">实时监控和管理机器人车队</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
        >
          🔄 刷新
        </button>
      </div>

      {/* Fleet Stats */}
      <FleetStatsComponent stats={stats} />

      {/* Main Content */}
      <div className="flex gap-4">
        {/* Left: Robot List */}
        <div className="w-80 bg-white rounded-lg border shadow-sm flex flex-col">
          {/* Filters */}
          <div className="p-3 border-b space-y-2">
            <div className="flex gap-2">
              <select
                value={brandFilter}
                onChange={(e) => setBrandFilter(e.target.value)}
                className="flex-1 px-2 py-1.5 border rounded text-sm"
              >
                <option value="">全部品牌</option>
                <option value="高仙">高仙</option>
                <option value="科沃斯">科沃斯</option>
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex-1 px-2 py-1.5 border rounded text-sm"
              >
                <option value="">全部状态</option>
                <option value="working">工作中</option>
                <option value="idle">空闲</option>
                <option value="charging">充电中</option>
                <option value="error">异常</option>
                <option value="offline">离线</option>
              </select>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索机器人..."
              className="w-full px-2 py-1.5 border rounded text-sm"
            />
          </div>

          {/* Robot List */}
          <div className="flex-1 overflow-y-auto">
            {filteredRobots.map(robot => (
              <RobotListItem
                key={robot.robotId}
                robot={robot}
                isSelected={robot.robotId === selectedRobotId}
                onClick={() => handleRobotClick(robot.robotId)}
              />
            ))}
            {filteredRobots.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                无匹配的机器人
              </div>
            )}
          </div>

          <div className="p-2 border-t text-sm text-gray-500 text-center">
            显示 {filteredRobots.length}/{robots.length} 台
          </div>
        </div>

        {/* Center: Map */}
        <div className="flex-1 bg-white rounded-lg border shadow-sm p-4">
          <h3 className="font-semibold text-gray-900 mb-3">实时地图</h3>
          <SimpleMap
            robots={filteredRobots}
            selectedRobotId={selectedRobotId || undefined}
            onRobotClick={handleRobotClick}
          />
        </div>

        {/* Right: Detail Panel */}
        {selectedRobot && (
          <div className="w-80">
            <RobotDetailPanel
              robot={selectedRobot}
              onControl={handleControl}
              onClose={() => setSelectedRobotId(null)}
            />
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

export default RobotMonitoring;
