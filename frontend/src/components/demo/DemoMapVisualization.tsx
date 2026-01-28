/**
 * DM5: 地图动态可视化组件 (Demo Map Visualization)
 *
 * 功能:
 * - 机器人实时位置显示与平滑移动动画
 * - 任务状态可视化 (清洁路径、工作区域)
 * - 区域热力图 (清洁频率/状态)
 * - WebSocket实时数据更新
 * - 楼层切换与缩放控制
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';

// ============================================================
// Types
// ============================================================

interface Position {
  x: number;
  y: number;
  orientation: number;
  floor_id?: string;
}

interface RobotSimState {
  robot_id: string;
  name: string;
  status: string;
  position: Position;
  target_position?: Position;
  battery_level: number;
  current_task_id?: string;
  path?: Position[];
  speed: number;
}

interface Zone {
  id: string;
  name: string;
  zone_type: string;
  floor_id: string;
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  cleaning_status?: 'clean' | 'in_progress' | 'pending' | 'dirty';
  last_cleaned?: string;
  cleaning_frequency?: number;
}

interface Floor {
  id: string;
  name: string;
  floor_number: number;
  building_id: string;
}

interface Task {
  task_id: string;
  zone_id: string;
  status: string;
  robot_id?: string;
  task_type: string;
  progress?: number;
}

interface DemoMapVisualizationProps {
  buildingId?: string;
  floorId?: string;
  onRobotSelect?: (robot: RobotSimState) => void;
  onZoneSelect?: (zone: Zone) => void;
  showHeatmap?: boolean;
  showPaths?: boolean;
  showTasks?: boolean;
  refreshInterval?: number;
}

interface MapDimensions {
  width: number;
  height: number;
  scale: number;
  offsetX: number;
  offsetY: number;
}

// ============================================================
// Constants
// ============================================================

const STATUS_COLORS: Record<string, string> = {
  idle: '#22c55e',
  working: '#3b82f6',
  charging: '#eab308',
  returning: '#8b5cf6',
  error: '#ef4444',
  offline: '#9ca3af',
};

const ZONE_STATUS_COLORS: Record<string, string> = {
  clean: 'rgba(34, 197, 94, 0.2)',
  in_progress: 'rgba(59, 130, 246, 0.3)',
  pending: 'rgba(234, 179, 8, 0.2)',
  dirty: 'rgba(239, 68, 68, 0.2)',
};

const HEATMAP_COLORS = [
  'rgba(34, 197, 94, 0.1)',   // Low frequency - green
  'rgba(34, 197, 94, 0.3)',
  'rgba(234, 179, 8, 0.3)',   // Medium - yellow
  'rgba(234, 179, 8, 0.5)',
  'rgba(239, 68, 68, 0.3)',   // High frequency - red
  'rgba(239, 68, 68, 0.5)',
];

// ============================================================
// Helper Functions
// ============================================================

const getStatusColor = (status: string): string => STATUS_COLORS[status] || STATUS_COLORS.offline;

const getBatteryColor = (level: number): string => {
  if (level > 60) return '#22c55e';
  if (level > 20) return '#eab308';
  return '#ef4444';
};

const getHeatmapColor = (frequency: number, maxFrequency: number): string => {
  if (maxFrequency === 0) return HEATMAP_COLORS[0];
  const index = Math.min(
    Math.floor((frequency / maxFrequency) * HEATMAP_COLORS.length),
    HEATMAP_COLORS.length - 1
  );
  return HEATMAP_COLORS[index];
};

// ============================================================
// Animated Robot Marker Component
// ============================================================

interface AnimatedRobotMarkerProps {
  robot: RobotSimState;
  mapDimensions: MapDimensions;
  isSelected: boolean;
  onClick: () => void;
  showPath: boolean;
}

const AnimatedRobotMarkerComponent: React.FC<AnimatedRobotMarkerProps> = ({
  robot,
  mapDimensions,
  isSelected,
  onClick,
  showPath,
}) => {
  const [animatedPos, setAnimatedPos] = useState({ x: 0, y: 0 });
  const prevPosRef = useRef({ x: 0, y: 0 });
  const animationRef = useRef<number>();

  // Convert position to map coordinates
  const toMapCoords = useCallback((pos: Position) => ({
    x: (pos.x / 100) * (mapDimensions.width - 100) + 50,
    y: (pos.y / 100) * (mapDimensions.height - 100) + 50,
  }), [mapDimensions]);

  // Smooth animation
  useEffect(() => {
    const targetPos = toMapCoords(robot.position);
    const startPos = { ...prevPosRef.current };
    const startTime = performance.now();
    const duration = 500; // 500ms animation

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3);

      setAnimatedPos({
        x: startPos.x + (targetPos.x - startPos.x) * easeOut,
        y: startPos.y + (targetPos.y - startPos.y) * easeOut,
      });

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        prevPosRef.current = targetPos;
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [robot.position, toMapCoords]);

  // Initialize position
  useEffect(() => {
    const pos = toMapCoords(robot.position);
    setAnimatedPos(pos);
    prevPosRef.current = pos;
  }, []);

  const rotation = robot.position.orientation || 0;

  // Render path if available
  const pathPoints = useMemo(() => {
    if (!showPath || !robot.path || robot.path.length < 2) return null;
    return robot.path.map(p => toMapCoords(p)).map(p => `${p.x},${p.y}`).join(' ');
  }, [robot.path, showPath, toMapCoords]);

  return (
    <g>
      {/* Path line */}
      {pathPoints && (
        <polyline
          points={pathPoints}
          fill="none"
          stroke={getStatusColor(robot.status)}
          strokeWidth="2"
          strokeDasharray="5 3"
          opacity="0.5"
        />
      )}

      {/* Target position indicator */}
      {robot.target_position && robot.status === 'working' && (
        <g transform={`translate(${toMapCoords(robot.target_position).x}, ${toMapCoords(robot.target_position).y})`}>
          <circle
            r="8"
            fill="none"
            stroke={getStatusColor(robot.status)}
            strokeWidth="2"
            strokeDasharray="3 2"
            className="animate-pulse"
          />
          <circle r="3" fill={getStatusColor(robot.status)} opacity="0.5" />
        </g>
      )}

      {/* Robot marker */}
      <g
        transform={`translate(${animatedPos.x}, ${animatedPos.y})`}
        onClick={onClick}
        style={{ cursor: 'pointer' }}
      >
        {/* Selection ring */}
        {isSelected && (
          <circle
            r="24"
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
            strokeDasharray="6 3"
            className="animate-spin"
            style={{ animationDuration: '3s' }}
          />
        )}

        {/* Status glow effect */}
        <circle
          r="18"
          fill={getStatusColor(robot.status)}
          opacity="0.2"
          className={robot.status === 'working' ? 'animate-pulse' : ''}
        />

        {/* Robot body */}
        <g transform={`rotate(${rotation})`}>
          <circle
            r="14"
            fill={getStatusColor(robot.status)}
            stroke="#fff"
            strokeWidth="2"
          />
          {/* Direction indicator */}
          <path
            d="M 0 -10 L 5 -3 L -5 -3 Z"
            fill="#fff"
          />
          {/* Working animation */}
          {robot.status === 'working' && (
            <circle
              r="10"
              fill="none"
              stroke="#fff"
              strokeWidth="1"
              strokeDasharray="2 2"
              className="animate-spin"
              style={{ animationDuration: '1s' }}
            />
          )}
        </g>

        {/* Robot name */}
        <text
          y="30"
          textAnchor="middle"
          className="text-xs font-medium"
          fill="#374151"
          style={{ fontSize: '11px' }}
        >
          {robot.name}
        </text>

        {/* Battery indicator */}
        <g transform="translate(18, -12)">
          <rect
            x="0" y="0"
            width="24" height="10"
            rx="2"
            fill="#e5e7eb"
            stroke="#9ca3af"
            strokeWidth="0.5"
          />
          <rect
            x="1" y="1"
            width={(robot.battery_level / 100) * 22}
            height="8"
            rx="1"
            fill={getBatteryColor(robot.battery_level)}
          />
          <rect x="24" y="3" width="3" height="4" fill="#9ca3af" rx="0.5" />
          <text
            x="12" y="7.5"
            textAnchor="middle"
            fill="#374151"
            style={{ fontSize: '6px', fontWeight: 'bold' }}
          >
            {robot.battery_level}%
          </text>
        </g>

        {/* Task progress indicator */}
        {robot.current_task_id && robot.status === 'working' && (
          <g transform="translate(0, 40)">
            <rect x="-20" y="0" width="40" height="4" rx="2" fill="#e5e7eb" />
            <rect
              x="-20" y="0"
              width="40"
              height="4"
              rx="2"
              fill={getStatusColor(robot.status)}
              className="animate-pulse"
            />
          </g>
        )}
      </g>
    </g>
  );
};

// Memoize to prevent unnecessary re-renders
const AnimatedRobotMarker = React.memo(AnimatedRobotMarkerComponent);

// ============================================================
// Zone Overlay Component
// ============================================================

interface ZoneOverlayProps {
  zone: Zone;
  mapDimensions: MapDimensions;
  showHeatmap: boolean;
  maxFrequency: number;
  isSelected: boolean;
  onClick: () => void;
}

const ZoneOverlayComponent: React.FC<ZoneOverlayProps> = ({
  zone,
  mapDimensions,
  showHeatmap,
  maxFrequency,
  isSelected,
  onClick,
}) => {
  const bounds = zone.bounds;
  const x = (bounds.x / 100) * (mapDimensions.width - 100) + 50;
  const y = (bounds.y / 100) * (mapDimensions.height - 100) + 50;
  const width = (bounds.width / 100) * (mapDimensions.width - 100);
  const height = (bounds.height / 100) * (mapDimensions.height - 100);

  const fillColor = showHeatmap
    ? getHeatmapColor(zone.cleaning_frequency || 0, maxFrequency)
    : ZONE_STATUS_COLORS[zone.cleaning_status || 'clean'];

  return (
    <g onClick={onClick} style={{ cursor: 'pointer' }}>
      <rect
        x={x} y={y}
        width={width} height={height}
        fill={fillColor}
        stroke={isSelected ? '#3b82f6' : '#9ca3af'}
        strokeWidth={isSelected ? 2 : 1}
        strokeDasharray={isSelected ? '0' : '4 2'}
        rx="4"
      />
      {/* Zone label */}
      <text
        x={x + width / 2}
        y={y + height / 2}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#6b7280"
        style={{ fontSize: '10px' }}
      >
        {zone.name}
      </text>
      {/* Cleaning status indicator */}
      {zone.cleaning_status === 'in_progress' && (
        <rect
          x={x} y={y}
          width={width} height={height}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          rx="4"
          className="animate-pulse"
        />
      )}
    </g>
  );
};

// Memoize to prevent unnecessary re-renders
const ZoneOverlay = React.memo(ZoneOverlayComponent);

// ============================================================
// Task Visualization Component
// ============================================================

interface TaskVisualizationProps {
  task: Task;
  zone?: Zone;
  mapDimensions: MapDimensions;
}

const TaskVisualization: React.FC<TaskVisualizationProps> = ({
  task,
  zone,
  mapDimensions,
}) => {
  if (!zone) return null;

  const bounds = zone.bounds;
  const x = (bounds.x / 100) * (mapDimensions.width - 100) + 50;
  const y = (bounds.y / 100) * (mapDimensions.height - 100) + 50;
  const width = (bounds.width / 100) * (mapDimensions.width - 100);

  const getTaskColor = (status: string) => {
    switch (status) {
      case 'in_progress': return '#3b82f6';
      case 'pending': return '#eab308';
      case 'completed': return '#22c55e';
      default: return '#9ca3af';
    }
  };

  return (
    <g>
      {/* Task progress bar */}
      {task.status === 'in_progress' && task.progress !== undefined && (
        <g transform={`translate(${x}, ${y - 10})`}>
          <rect
            x="0" y="0"
            width={width} height="6"
            rx="3"
            fill="#e5e7eb"
          />
          <rect
            x="0" y="0"
            width={width * (task.progress / 100)}
            height="6"
            rx="3"
            fill={getTaskColor(task.status)}
          />
          <text
            x={width / 2} y="-2"
            textAnchor="middle"
            fill="#374151"
            style={{ fontSize: '9px' }}
          >
            {task.progress}%
          </text>
        </g>
      )}
      {/* Task type indicator */}
      <text
        x={x + 4} y={y + 12}
        fill={getTaskColor(task.status)}
        style={{ fontSize: '9px', fontWeight: 'bold' }}
      >
        ● {task.task_type}
      </text>
    </g>
  );
};

// ============================================================
// Map Controls Component
// ============================================================

interface MapControlsProps {
  scale: number;
  onScaleChange: (scale: number) => void;
  floors: Floor[];
  selectedFloor?: string;
  onFloorChange: (floorId: string) => void;
  showHeatmap: boolean;
  onToggleHeatmap: () => void;
  showPaths: boolean;
  onTogglePaths: () => void;
}

const MapControls: React.FC<MapControlsProps> = ({
  scale,
  onScaleChange,
  floors,
  selectedFloor,
  onFloorChange,
  showHeatmap,
  onToggleHeatmap,
  showPaths,
  onTogglePaths,
}) => {
  return (
    <div className="absolute top-4 left-4 flex flex-col gap-2">
      {/* Floor selector */}
      <div className="bg-white rounded-lg shadow-md p-2">
        <div className="text-xs text-gray-500 mb-1">楼层</div>
        <select
          value={selectedFloor || ''}
          onChange={(e) => onFloorChange(e.target.value)}
          className="text-sm border rounded px-2 py-1 w-full"
        >
          {floors.map((floor) => (
            <option key={floor.id} value={floor.id}>
              {floor.name}
            </option>
          ))}
        </select>
      </div>

      {/* Zoom controls */}
      <div className="bg-white rounded-lg shadow-md p-2">
        <div className="text-xs text-gray-500 mb-1">缩放</div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onScaleChange(Math.max(0.5, scale - 0.25))}
            className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded"
          >
            −
          </button>
          <span className="text-sm w-12 text-center">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => onScaleChange(Math.min(2, scale + 0.25))}
            className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded"
          >
            +
          </button>
        </div>
      </div>

      {/* View toggles */}
      <div className="bg-white rounded-lg shadow-md p-2">
        <div className="text-xs text-gray-500 mb-1">显示</div>
        <div className="space-y-1">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showHeatmap}
              onChange={onToggleHeatmap}
              className="rounded"
            />
            热力图
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showPaths}
              onChange={onTogglePaths}
              className="rounded"
            />
            移动路径
          </label>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// Robot Info Sidebar Component
// ============================================================

interface RobotInfoSidebarProps {
  robot: RobotSimState;
  onClose: () => void;
  onAction?: (action: string) => void;
}

const RobotInfoSidebar: React.FC<RobotInfoSidebarProps> = ({
  robot,
  onClose,
  onAction,
}) => {
  return (
    <div className="absolute right-4 top-4 w-72 bg-white rounded-lg shadow-lg border overflow-hidden">
      {/* Header */}
      <div
        className="px-4 py-3 border-b"
        style={{ backgroundColor: getStatusColor(robot.status) + '15' }}
      >
        <div className="flex justify-between items-start">
          <div>
            <h4 className="font-semibold text-gray-900">{robot.name}</h4>
            <p className="text-xs text-gray-500">{robot.robot_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="p-4 space-y-3">
        {/* Status badge */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">状态</span>
          <span
            className="px-3 py-1 text-xs font-medium rounded-full"
            style={{
              backgroundColor: getStatusColor(robot.status) + '20',
              color: getStatusColor(robot.status),
            }}
          >
            {robot.status === 'idle' && '空闲'}
            {robot.status === 'working' && '工作中'}
            {robot.status === 'charging' && '充电中'}
            {robot.status === 'returning' && '返回中'}
            {robot.status === 'error' && '故障'}
          </span>
        </div>

        {/* Battery */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">电量</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${robot.battery_level}%`,
                  backgroundColor: getBatteryColor(robot.battery_level),
                }}
              />
            </div>
            <span className="text-sm font-medium w-10">{robot.battery_level}%</span>
          </div>
        </div>

        {/* Position */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">位置</span>
          <span className="text-sm text-gray-700">
            ({robot.position.x.toFixed(1)}, {robot.position.y.toFixed(1)})
          </span>
        </div>

        {/* Speed */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">速度</span>
          <span className="text-sm text-gray-700">{robot.speed.toFixed(1)} m/s</span>
        </div>

        {/* Current task */}
        {robot.current_task_id && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">当前任务</span>
            <span className="text-sm text-blue-600 font-medium">
              {robot.current_task_id}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      {onAction && (
        <div className="px-4 py-3 border-t bg-gray-50 flex gap-2">
          <button
            onClick={() => onAction('recall')}
            className="flex-1 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
          >
            召回
          </button>
          <button
            onClick={() => onAction('pause')}
            className="flex-1 px-3 py-2 text-sm bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors"
          >
            暂停
          </button>
          <button
            onClick={() => onAction('charge')}
            className="flex-1 px-3 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
          >
            充电
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================
// Map Legend Component
// ============================================================

interface MapLegendProps {
  showHeatmap: boolean;
}

const MapLegend: React.FC<MapLegendProps> = ({ showHeatmap }) => {
  const robotStatuses = [
    { status: 'idle', label: '空闲' },
    { status: 'working', label: '工作中' },
    { status: 'charging', label: '充电中' },
    { status: 'returning', label: '返回中' },
    { status: 'error', label: '故障' },
  ];

  const zoneStatuses = [
    { status: 'clean', label: '已清洁' },
    { status: 'in_progress', label: '清洁中' },
    { status: 'pending', label: '待清洁' },
    { status: 'dirty', label: '需清洁' },
  ];

  return (
    <div className="absolute left-4 bottom-4 bg-white rounded-lg shadow-md border p-3">
      <div className="text-xs font-medium text-gray-700 mb-2">图例</div>

      {/* Robot statuses */}
      <div className="mb-3">
        <div className="text-xs text-gray-500 mb-1">机器人状态</div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {robotStatuses.map(({ status, label }) => (
            <div key={status} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getStatusColor(status) }}
              />
              <span className="text-xs text-gray-600">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Zone statuses / Heatmap */}
      <div>
        <div className="text-xs text-gray-500 mb-1">
          {showHeatmap ? '清洁频率' : '区域状态'}
        </div>
        {showHeatmap ? (
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-500">低</span>
            <div className="flex-1 h-3 rounded" style={{
              background: 'linear-gradient(to right, rgba(34,197,94,0.2), rgba(234,179,8,0.4), rgba(239,68,68,0.4))'
            }} />
            <span className="text-xs text-gray-500">高</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {zoneStatuses.map(({ status, label }) => (
              <div key={status} className="flex items-center gap-1.5">
                <div
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: ZONE_STATUS_COLORS[status] }}
                />
                <span className="text-xs text-gray-600">{label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================
// Stats Bar Component
// ============================================================

interface StatsBarProps {
  robots: RobotSimState[];
  tasks: Task[];
}

const StatsBar: React.FC<StatsBarProps> = ({ robots, tasks }) => {
  const stats = useMemo(() => ({
    total: robots.length,
    working: robots.filter(r => r.status === 'working').length,
    idle: robots.filter(r => r.status === 'idle').length,
    charging: robots.filter(r => r.status === 'charging').length,
    error: robots.filter(r => r.status === 'error').length,
    avgBattery: robots.length > 0
      ? Math.round(robots.reduce((sum, r) => sum + r.battery_level, 0) / robots.length)
      : 0,
    activeTasks: tasks.filter(t => t.status === 'in_progress').length,
    pendingTasks: tasks.filter(t => t.status === 'pending').length,
  }), [robots, tasks]);

  return (
    <div className="bg-white border-b px-4 py-2 flex items-center gap-6 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-gray-500">机器人:</span>
        <span className="font-medium">{stats.total}</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-blue-600">● 工作 {stats.working}</span>
        <span className="text-green-600">● 空闲 {stats.idle}</span>
        <span className="text-yellow-600">● 充电 {stats.charging}</span>
        {stats.error > 0 && (
          <span className="text-red-600">● 故障 {stats.error}</span>
        )}
      </div>
      <div className="h-4 border-l" />
      <div className="flex items-center gap-2">
        <span className="text-gray-500">平均电量:</span>
        <span className="font-medium" style={{ color: getBatteryColor(stats.avgBattery) }}>
          {stats.avgBattery}%
        </span>
      </div>
      <div className="h-4 border-l" />
      <div className="flex items-center gap-4">
        <span className="text-gray-500">任务:</span>
        <span className="text-blue-600">进行中 {stats.activeTasks}</span>
        <span className="text-yellow-600">待处理 {stats.pendingTasks}</span>
      </div>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const DemoMapVisualization: React.FC<DemoMapVisualizationProps> = ({
  buildingId = 'building_001',
  floorId: initialFloorId,
  onRobotSelect,
  onZoneSelect,
  showHeatmap: initialShowHeatmap = false,
  showPaths: initialShowPaths = true,
  showTasks: initialShowTasks = true,
  refreshInterval = 1000,
}) => {
  // State
  const [robots, setRobots] = useState<RobotSimState[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [floors, setFloors] = useState<Floor[]>([]);
  const [tasks] = useState<Task[]>([]);
  const [selectedFloor, setSelectedFloor] = useState<string>(initialFloorId || '');
  const [selectedRobot, setSelectedRobot] = useState<RobotSimState | null>(null);
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(initialShowHeatmap);
  const [showPaths, setShowPaths] = useState(initialShowPaths);
  const [scale, setScale] = useState(1);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const lastUpdateTime = useRef(0);

  const [mapDimensions, setMapDimensions] = useState<MapDimensions>({
    width: 800,
    height: 600,
    scale: 1,
    offsetX: 0,
    offsetY: 0,
  });

  // API base URL
  const API_BASE = '/api/v1';

  // Load initial data
  const loadInitialData = useCallback(async () => {
    try {
      // Load floors
      const floorsRes = await fetch(`${API_BASE}/demo/status`);
      if (floorsRes.ok) {
        await floorsRes.json(); // Verify response is valid
        // Mock floors data for demo
        setFloors([
          { id: 'floor_001', name: '1F 大堂', floor_number: 1, building_id: buildingId },
          { id: 'floor_002', name: '2F 办公区', floor_number: 2, building_id: buildingId },
          { id: 'floor_003', name: '3F 办公区', floor_number: 3, building_id: buildingId },
        ]);
        if (!selectedFloor) {
          setSelectedFloor('floor_001');
        }
      }

      // Load robots from simulation
      console.log('DemoMapVisualization: Loading initial robots from', `${API_BASE}/simulation/robots`);
      const simRes = await fetch(`${API_BASE}/simulation/robots`);
      console.log('DemoMapVisualization: Response status', simRes.status);
      if (simRes.ok) {
        const simData = await simRes.json();
        console.log('DemoMapVisualization: Got data', simData);
        if (simData.robots && Array.isArray(simData.robots)) {
          // Map simulation floor IDs to display floor IDs
          const mapFloorId = (floorId: string): string => {
            if (!floorId) return 'floor_001';
            const floorNum = parseInt(floorId.replace('floor_', ''), 10);
            if (floorNum <= 5) return 'floor_001';      // 1F 大堂
            if (floorNum <= 15) return 'floor_002';     // 2F 办公区
            return 'floor_003';                          // 3F 办公区
          };

          const mappedRobots = simData.robots.map((r: any) => ({
            robot_id: r.robot_id,
            name: r.name,
            status: r.status,
            position: {
              // Normalize coordinates from 0-300 range to 0-100 range
              x: Math.min(100, Math.max(0, (r.position?.x || 0) / 3)),
              y: Math.min(100, Math.max(0, (r.position?.y || 0) / 3)),
              orientation: r.position?.orientation || 0,
              floor_id: mapFloorId(r.position?.floor_id),
            },
            target_position: r.target_position ? {
              x: Math.min(100, Math.max(0, r.target_position.x / 3)),
              y: Math.min(100, Math.max(0, r.target_position.y / 3)),
              orientation: r.target_position.orientation || 0,
              floor_id: mapFloorId(r.target_position.floor_id),
            } : undefined,
            battery_level: r.battery || 100,
            current_task_id: r.task_id,
            path: r.path,
            speed: r.speed || 0.5,
          }));
          console.log('DemoMapVisualization: Setting', mappedRobots.length, 'robots');
          setRobots(mappedRobots);
        }
      } else {
        console.error('DemoMapVisualization: Failed to load robots, status', simRes.status);
      }

      // Create realistic floor plan zones for all floors
      const floorPlanZones: Zone[] = [
        // ============ 1F 大堂层 ============
        {
          id: 'f1_lobby',
          name: '大堂',
          zone_type: 'lobby',
          floor_id: 'floor_001',
          bounds: { x: 25, y: 30, width: 50, height: 40 },
          cleaning_status: 'clean',
          cleaning_frequency: 15,
        },
        {
          id: 'f1_corridor_west',
          name: '西侧走廊',
          zone_type: 'corridor',
          floor_id: 'floor_001',
          bounds: { x: 2, y: 20, width: 20, height: 60 },
          cleaning_status: 'in_progress',
          cleaning_frequency: 12,
        },
        {
          id: 'f1_corridor_east',
          name: '东侧走廊',
          zone_type: 'corridor',
          floor_id: 'floor_001',
          bounds: { x: 78, y: 20, width: 20, height: 60 },
          cleaning_status: 'pending',
          cleaning_frequency: 10,
        },
        {
          id: 'f1_elevator',
          name: '电梯厅',
          zone_type: 'elevator',
          floor_id: 'floor_001',
          bounds: { x: 40, y: 2, width: 20, height: 25 },
          cleaning_status: 'clean',
          cleaning_frequency: 18,
        },
        {
          id: 'f1_reception',
          name: '接待区',
          zone_type: 'reception',
          floor_id: 'floor_001',
          bounds: { x: 2, y: 2, width: 35, height: 15 },
          cleaning_status: 'clean',
          cleaning_frequency: 8,
        },
        {
          id: 'f1_security',
          name: '安保区',
          zone_type: 'security',
          floor_id: 'floor_001',
          bounds: { x: 63, y: 2, width: 35, height: 15 },
          cleaning_status: 'pending',
          cleaning_frequency: 6,
        },
        {
          id: 'f1_entrance',
          name: '主入口',
          zone_type: 'entrance',
          floor_id: 'floor_001',
          bounds: { x: 35, y: 75, width: 30, height: 23 },
          cleaning_status: 'in_progress',
          cleaning_frequency: 20,
        },
        {
          id: 'f1_restroom',
          name: '洗手间',
          zone_type: 'restroom',
          floor_id: 'floor_001',
          bounds: { x: 2, y: 83, width: 30, height: 15 },
          cleaning_status: 'clean',
          cleaning_frequency: 25,
        },
        {
          id: 'f1_utility',
          name: '设备间',
          zone_type: 'utility',
          floor_id: 'floor_001',
          bounds: { x: 68, y: 83, width: 30, height: 15 },
          cleaning_status: 'clean',
          cleaning_frequency: 3,
        },

        // ============ 2F 办公区 ============
        {
          id: 'f2_office_a',
          name: '办公区A',
          zone_type: 'office',
          floor_id: 'floor_002',
          bounds: { x: 2, y: 2, width: 45, height: 45 },
          cleaning_status: 'clean',
          cleaning_frequency: 10,
        },
        {
          id: 'f2_office_b',
          name: '办公区B',
          zone_type: 'office',
          floor_id: 'floor_002',
          bounds: { x: 53, y: 2, width: 45, height: 45 },
          cleaning_status: 'pending',
          cleaning_frequency: 10,
        },
        {
          id: 'f2_corridor',
          name: '主走廊',
          zone_type: 'corridor',
          floor_id: 'floor_002',
          bounds: { x: 2, y: 50, width: 96, height: 12 },
          cleaning_status: 'in_progress',
          cleaning_frequency: 15,
        },
        {
          id: 'f2_meeting_large',
          name: '大会议室',
          zone_type: 'meeting',
          floor_id: 'floor_002',
          bounds: { x: 2, y: 65, width: 35, height: 33 },
          cleaning_status: 'clean',
          cleaning_frequency: 8,
        },
        {
          id: 'f2_meeting_small',
          name: '小会议室',
          zone_type: 'meeting',
          floor_id: 'floor_002',
          bounds: { x: 40, y: 65, width: 25, height: 15 },
          cleaning_status: 'clean',
          cleaning_frequency: 6,
        },
        {
          id: 'f2_pantry',
          name: '茶水间',
          zone_type: 'pantry',
          floor_id: 'floor_002',
          bounds: { x: 40, y: 83, width: 25, height: 15 },
          cleaning_status: 'pending',
          cleaning_frequency: 20,
        },
        {
          id: 'f2_restroom',
          name: '洗手间',
          zone_type: 'restroom',
          floor_id: 'floor_002',
          bounds: { x: 68, y: 65, width: 30, height: 33 },
          cleaning_status: 'clean',
          cleaning_frequency: 25,
        },

        // ============ 3F 办公区 ============
        {
          id: 'f3_open_office',
          name: '开放办公区',
          zone_type: 'office',
          floor_id: 'floor_003',
          bounds: { x: 2, y: 2, width: 70, height: 55 },
          cleaning_status: 'in_progress',
          cleaning_frequency: 12,
        },
        {
          id: 'f3_executive',
          name: '高管办公室',
          zone_type: 'executive',
          floor_id: 'floor_003',
          bounds: { x: 75, y: 2, width: 23, height: 35 },
          cleaning_status: 'clean',
          cleaning_frequency: 5,
        },
        {
          id: 'f3_server_room',
          name: '机房',
          zone_type: 'server',
          floor_id: 'floor_003',
          bounds: { x: 75, y: 40, width: 23, height: 17 },
          cleaning_status: 'clean',
          cleaning_frequency: 2,
        },
        {
          id: 'f3_corridor',
          name: '走廊',
          zone_type: 'corridor',
          floor_id: 'floor_003',
          bounds: { x: 2, y: 60, width: 96, height: 10 },
          cleaning_status: 'clean',
          cleaning_frequency: 14,
        },
        {
          id: 'f3_training',
          name: '培训室',
          zone_type: 'training',
          floor_id: 'floor_003',
          bounds: { x: 2, y: 73, width: 45, height: 25 },
          cleaning_status: 'pending',
          cleaning_frequency: 7,
        },
        {
          id: 'f3_lounge',
          name: '员工休息区',
          zone_type: 'lounge',
          floor_id: 'floor_003',
          bounds: { x: 50, y: 73, width: 30, height: 25 },
          cleaning_status: 'clean',
          cleaning_frequency: 18,
        },
        {
          id: 'f3_restroom',
          name: '洗手间',
          zone_type: 'restroom',
          floor_id: 'floor_003',
          bounds: { x: 83, y: 60, width: 15, height: 38 },
          cleaning_status: 'clean',
          cleaning_frequency: 25,
        },
      ];
      setZones(floorPlanZones);
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  }, [buildingId, selectedFloor]);

  // Connect WebSocket for real-time updates
  const connectWebSocket = useCallback(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}${API_BASE}/simulation/ws`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0; // Reset backoff on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'state_update' && message.robot_states) {
            // Throttle updates to max 30fps for smooth performance
            const now = Date.now();
            if (now - lastUpdateTime.current >= 33) { // ~30fps
              setRobots(Object.values(message.robot_states));
              setLastUpdate(new Date());
              lastUpdateTime.current = now;
            }
          } else if (message.type === 'event') {
            // Handle events (low battery, task complete, etc.)
            console.log('Received event:', message.event);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Exponential backoff reconnection (max 30s)
        const retryDelay = Math.min(3000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;
        setTimeout(connectWebSocket, retryDelay);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  }, []);

  // Polling for updates
  const pollUpdates = useCallback(async () => {
    // Always poll (WebSocket disabled for demo stability)
    try {
      const res = await fetch(`${API_BASE}/simulation/robots`);
      if (res.ok) {
        const data = await res.json();
        if (data.robots && Array.isArray(data.robots)) {
          // Map simulation floor IDs to display floor IDs
          const mapFloorId = (floorId: string): string => {
            if (!floorId) return 'floor_001';
            const floorNum = parseInt(floorId.replace('floor_', ''), 10);
            if (floorNum <= 5) return 'floor_001';      // 1F 大堂
            if (floorNum <= 15) return 'floor_002';     // 2F 办公区
            return 'floor_003';                          // 3F 办公区
          };

          const mappedRobots = data.robots.map((r: any) => ({
            robot_id: r.robot_id,
            name: r.name,
            status: r.status,
            position: {
              // Normalize coordinates from 0-300 range to 0-100 range
              x: Math.min(100, Math.max(0, (r.position?.x || 0) / 3)),
              y: Math.min(100, Math.max(0, (r.position?.y || 0) / 3)),
              orientation: r.position?.orientation || 0,
              floor_id: mapFloorId(r.position?.floor_id),
            },
            target_position: r.target_position ? {
              x: Math.min(100, Math.max(0, r.target_position.x / 3)),
              y: Math.min(100, Math.max(0, r.target_position.y / 3)),
              orientation: r.target_position.orientation || 0,
              floor_id: mapFloorId(r.target_position.floor_id),
            } : undefined,
            battery_level: r.battery || 100,
            current_task_id: r.task_id,
            path: r.path,
            speed: r.speed || 0.5,
          }));
          setRobots(mappedRobots);
          setLastUpdate(new Date());
        }
      }
    } catch (error) {
      console.error('Failed to poll updates:', error);
    }
  }, []);

  // Initialize
  useEffect(() => {
    console.log('DemoMapVisualization: Initializing...');
    loadInitialData();
    // Skip WebSocket for now, use polling only
    // connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [loadInitialData]);

  // Polling fallback
  useEffect(() => {
    const interval = setInterval(pollUpdates, refreshInterval);
    return () => clearInterval(interval);
  }, [pollUpdates, refreshInterval]);

  // Handle container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setMapDimensions({
          width: width - 16,
          height: height - 16,
          scale,
          offsetX: 0,
          offsetY: 0,
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, [scale]);

  // Filter robots by selected floor
  const filteredRobots = useMemo(() => {
    if (!selectedFloor) return robots;
    return robots.filter(r => r.position.floor_id === selectedFloor);
  }, [robots, selectedFloor]);

  // Filter zones by floor
  const filteredZones = useMemo(() => {
    if (!selectedFloor) return zones;
    return zones.filter(z => z.floor_id === selectedFloor);
  }, [zones, selectedFloor]);

  // Max cleaning frequency for heatmap
  const maxFrequency = useMemo(() => {
    return Math.max(...zones.map(z => z.cleaning_frequency || 0), 1);
  }, [zones]);

  // Handlers
  const handleRobotClick = (robot: RobotSimState) => {
    setSelectedRobot(robot);
    setSelectedZone(null);
    onRobotSelect?.(robot);
  };

  const handleZoneClick = (zone: Zone) => {
    setSelectedZone(zone);
    setSelectedRobot(null);
    onZoneSelect?.(zone);
  };

  const handleRobotAction = async (action: string) => {
    if (!selectedRobot) return;

    try {
      const res = await fetch(`${API_BASE}/simulation/robots/${selectedRobot.robot_id}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (res.ok) {
        console.log(`Action ${action} executed for robot ${selectedRobot.robot_id}`);
      }
    } catch (error) {
      console.error(`Failed to execute action ${action}:`, error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Stats Bar */}
      <StatsBar robots={robots} tasks={tasks} />

      {/* Map Container */}
      <div className="flex-1 relative overflow-hidden" ref={containerRef}>
        {/* SVG Map */}
        <svg
          width={mapDimensions.width * scale}
          height={mapDimensions.height * scale}
          className="absolute inset-2"
          style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}
        >
          {/* Grid */}
          <defs>
            <pattern id="demo-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e7eb" strokeWidth="0.5" />
            </pattern>
            <pattern id="demo-grid-large" width="200" height="200" patternUnits="userSpaceOnUse">
              <path d="M 200 0 L 0 0 0 200" fill="none" stroke="#d1d5db" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#demo-grid)" />
          <rect width="100%" height="100%" fill="url(#demo-grid-large)" />

          {/* Floor boundary */}
          <rect
            x="40"
            y="40"
            width={mapDimensions.width - 80}
            height={mapDimensions.height - 80}
            fill="none"
            stroke="#9ca3af"
            strokeWidth="2"
            rx="8"
          />

          {/* Zone overlays */}
          {filteredZones.map((zone) => (
            <ZoneOverlay
              key={zone.id}
              zone={zone}
              mapDimensions={mapDimensions}
              showHeatmap={showHeatmap}
              maxFrequency={maxFrequency}
              isSelected={selectedZone?.id === zone.id}
              onClick={() => handleZoneClick(zone)}
            />
          ))}

          {/* Task visualizations */}
          {initialShowTasks && tasks.map((task) => (
            <TaskVisualization
              key={task.task_id}
              task={task}
              zone={zones.find(z => z.id === task.zone_id)}
              mapDimensions={mapDimensions}
            />
          ))}

          {/* Robot markers */}
          {filteredRobots.map((robot) => (
            <AnimatedRobotMarker
              key={robot.robot_id}
              robot={robot}
              mapDimensions={mapDimensions}
              isSelected={selectedRobot?.robot_id === robot.robot_id}
              onClick={() => handleRobotClick(robot)}
              showPath={showPaths}
            />
          ))}
        </svg>

        {/* Map Controls */}
        <MapControls
          scale={scale}
          onScaleChange={setScale}
          floors={floors}
          selectedFloor={selectedFloor}
          onFloorChange={setSelectedFloor}
          showHeatmap={showHeatmap}
          onToggleHeatmap={() => setShowHeatmap(!showHeatmap)}
          showPaths={showPaths}
          onTogglePaths={() => setShowPaths(!showPaths)}
        />

        {/* Legend */}
        <MapLegend showHeatmap={showHeatmap} />

        {/* Robot Info Sidebar */}
        {selectedRobot && (
          <RobotInfoSidebar
            robot={selectedRobot}
            onClose={() => setSelectedRobot(null)}
            onAction={handleRobotAction}
          />
        )}

        {/* Connection status */}
        <div className="absolute bottom-4 right-4 flex items-center gap-2 bg-white rounded-lg shadow px-3 py-1.5">
          <div
            className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
          />
          <span className="text-xs text-gray-600">
            {isConnected ? '实时连接' : '轮询模式'}
          </span>
          {lastUpdate && (
            <span className="text-xs text-gray-400">
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default DemoMapVisualization;
