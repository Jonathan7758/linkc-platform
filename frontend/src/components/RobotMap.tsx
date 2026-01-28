/**
 * T4: Robot Map Component
 * 在地图上展示机器人位置和状态
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Robot } from '../types/index';

const API_BASE = '/api/v1';

// ============================================================
// Types
// ============================================================

interface RobotMapProps {
  buildingId: string;
  floorId?: string;
  onRobotSelect?: (robot: Robot) => void;
  refreshInterval?: number;
}

interface MapDimensions {
  width: number;
  height: number;
  scale: number;
}

// ============================================================
// Helper Functions
// ============================================================

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    idle: '#22c55e',      // green
    working: '#3b82f6',   // blue
    charging: '#eab308',  // yellow
    error: '#ef4444',     // red
    offline: '#9ca3af',   // gray
  };
  return colors[status] || colors.offline;
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    idle: '空闲',
    working: '工作中',
    charging: '充电中',
    error: '故障',
    offline: '离线',
  };
  return labels[status] || status;
};

const getBatteryColor = (level: number): string => {
  if (level > 60) return '#22c55e';
  if (level > 20) return '#eab308';
  return '#ef4444';
};

// ============================================================
// Robot Marker Component
// ============================================================

interface RobotMarkerProps {
  robot: Robot;
  mapDimensions: MapDimensions;
  isSelected: boolean;
  onClick: () => void;
}

const RobotMarker: React.FC<RobotMarkerProps> = ({
  robot,
  mapDimensions,
  isSelected,
  onClick,
}) => {
  const position = robot.position || { x: 0, y: 0, orientation: 0 };

  // Convert robot position to map coordinates (with 50px margin on each side)
  const x = (position.x / 100) * (mapDimensions.width - 100) + 50;
  const y = (position.y / 100) * (mapDimensions.height - 100) + 50;
  const rotation = position.orientation || 0;

  return (
    <g
      transform={`translate(${x}, ${y})`}
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      {/* Selection ring */}
      {isSelected && (
        <circle
          r="20"
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          strokeDasharray="4 2"
          className="animate-pulse"
        />
      )}

      {/* Robot body */}
      <g transform={`rotate(${rotation})`}>
        <circle
          r="12"
          fill={getStatusColor(robot.status)}
          stroke="#fff"
          strokeWidth="2"
        />
        {/* Direction indicator */}
        <path
          d="M 0 -8 L 4 -2 L -4 -2 Z"
          fill="#fff"
        />
      </g>

      {/* Robot name label */}
      <text
        y="25"
        textAnchor="middle"
        className="text-xs fill-gray-700"
        style={{ fontSize: '10px' }}
      >
        {robot.name}
      </text>

      {/* Battery indicator */}
      <g transform="translate(15, -10)">
        <rect
          x="0"
          y="0"
          width="20"
          height="8"
          rx="1"
          fill="#e5e7eb"
          stroke="#9ca3af"
          strokeWidth="0.5"
        />
        <rect
          x="1"
          y="1"
          width={(robot.batteryLevel / 100) * 18}
          height="6"
          rx="0.5"
          fill={getBatteryColor(robot.batteryLevel)}
        />
        <rect
          x="20"
          y="2"
          width="2"
          height="4"
          fill="#9ca3af"
        />
      </g>
    </g>
  );
};

// ============================================================
// Robot Info Panel Component
// ============================================================

interface RobotInfoPanelProps {
  robot: Robot;
  onClose: () => void;
  onControl?: (action: string) => void;
}

const RobotInfoPanel: React.FC<RobotInfoPanelProps> = ({
  robot,
  onClose,
  onControl,
}) => {
  return (
    <div className="absolute right-4 top-4 w-64 bg-white rounded-lg shadow-lg border p-4">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-semibold text-gray-900">{robot.name}</h4>
          <p className="text-xs text-gray-500">{robot.robotId}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* Status */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">状态</span>
          <span
            className="px-2 py-0.5 text-xs rounded"
            style={{
              backgroundColor: getStatusColor(robot.status) + '20',
              color: getStatusColor(robot.status),
            }}
          >
            {getStatusLabel(robot.status)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">电量</span>
          <div className="flex items-center gap-2">
            <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${robot.batteryLevel}%`,
                  backgroundColor: getBatteryColor(robot.batteryLevel),
                }}
              />
            </div>
            <span className="text-sm">{robot.batteryLevel}%</span>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">型号</span>
          <span className="text-sm text-gray-700">{robot.brand} {robot.model}</span>
        </div>

        {robot.currentTaskId && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">当前任务</span>
            <span className="text-sm text-blue-600">{robot.currentTaskId}</span>
          </div>
        )}

        {robot.position && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">位置</span>
            <span className="text-sm text-gray-700">
              ({robot.position.x.toFixed(1)}, {robot.position.y.toFixed(1)})
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      {onControl && (
        <div className="flex gap-2 pt-3 border-t">
          <button
            onClick={() => onControl('recall')}
            className="flex-1 px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            召回
          </button>
          <button
            onClick={() => onControl('pause')}
            className="flex-1 px-3 py-1.5 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
          >
            暂停
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================
// Legend Component
// ============================================================

const MapLegend: React.FC = () => {
  const statuses = [
    { status: 'idle', label: '空闲' },
    { status: 'working', label: '工作中' },
    { status: 'charging', label: '充电中' },
    { status: 'error', label: '故障' },
    { status: 'offline', label: '离线' },
  ];

  return (
    <div className="absolute left-4 bottom-4 bg-white rounded-lg shadow border p-3">
      <div className="text-xs font-medium text-gray-700 mb-2">图例</div>
      <div className="space-y-1">
        {statuses.map(({ status, label }) => (
          <div key={status} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getStatusColor(status) }}
            />
            <span className="text-xs text-gray-600">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

// Floor options
const FLOORS = [
  { id: 'floor_001', name: '1F 大堂' },
  { id: 'floor_002', name: '2F 办公区' },
  { id: 'floor_003', name: '3F 办公区' },
];

// Map simulation floor IDs to display floor IDs
const mapFloorId = (floorId: string): string => {
  if (!floorId) return 'floor_001';
  const floorNum = parseInt(floorId.replace('floor_', ''), 10);
  if (floorNum <= 5) return 'floor_001';      // 1F 大堂
  if (floorNum <= 15) return 'floor_002';     // 2F 办公区
  return 'floor_003';                          // 3F 办公区
};

export const RobotMap: React.FC<RobotMapProps> = ({
  buildingId,
  floorId: initialFloorId,
  onRobotSelect,
  refreshInterval = 2000,
}) => {
  const [robots, setRobots] = useState<Robot[]>([]);
  const [selectedRobot, setSelectedRobot] = useState<Robot | null>(null);
  const [selectedFloor, setSelectedFloor] = useState<string>(initialFloorId || 'floor_001');
  const [loading, setLoading] = useState(true);
  const [mapDimensions, setMapDimensions] = useState<MapDimensions>({
    width: 800,
    height: 600,
    scale: 1,
  });
  const containerRef = useRef<HTMLDivElement>(null);

  // Load robots from simulation API
  const loadRobots = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/simulation/robots`);
      if (res.ok) {
        const data = await res.json();
        if (data.robots && Array.isArray(data.robots)) {
          // Map simulation robots to Robot interface with floor mapping
          const mappedRobots: Robot[] = data.robots.map((r: any) => ({
            robotId: r.robot_id,
            name: r.name,
            brand: 'Gaussian',
            model: 'GS-50 Pro',
            status: r.status || 'idle',
            batteryLevel: r.battery || 100,
            position: {
              x: Math.min(100, Math.max(0, (r.position?.x || 0) / 3)),
              y: Math.min(100, Math.max(0, (r.position?.y || 0) / 3)),
              orientation: r.position?.orientation || 0,
              floorId: mapFloorId(r.position?.floor_id),
            },
            currentTaskId: r.task_id,
          }));
          setRobots(mappedRobots);
        }
      }
    } catch (error) {
      console.error('Failed to load robots:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadRobots();
  }, [loadRobots]);

  // Auto refresh
  useEffect(() => {
    const interval = setInterval(loadRobots, refreshInterval);
    return () => clearInterval(interval);
  }, [loadRobots, refreshInterval]);

  // Handle container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setMapDimensions({
          width: width - 32, // padding
          height: height - 32,
          scale: Math.min(width / 800, height / 600),
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const handleRobotClick = (robot: Robot) => {
    setSelectedRobot(robot);
    onRobotSelect?.(robot);
  };

  const handleControl = (action: string) => {
    if (selectedRobot) {
      console.log('Control robot:', selectedRobot.robotId, action);
      // TODO: Implement robot control API call
    }
  };

  // Filter robots by selected floor
  const filteredRobots = robots.filter((r) => r.position?.floorId === selectedFloor);

  // Calculate stats based on filtered robots
  const stats = {
    total: filteredRobots.length,
    working: filteredRobots.filter((r) => r.status === 'working').length,
    idle: filteredRobots.filter((r) => r.status === 'idle').length,
    charging: filteredRobots.filter((r) => r.status === 'charging').length,
    error: filteredRobots.filter((r) => r.status === 'error').length,
    maintenance: filteredRobots.filter((r) => r.status === 'maintenance').length,
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">机器人地图</h2>
          {/* Floor Selector */}
          <select
            value={selectedFloor}
            onChange={(e) => setSelectedFloor(e.target.value)}
            className="px-3 py-1 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {FLOORS.map((floor) => (
              <option key={floor.id} value={floor.id}>
                {floor.name}
              </option>
            ))}
          </select>
          <div className="flex gap-3 text-sm">
            <span className="text-gray-500">
              总数: <span className="font-medium text-gray-900">{stats.total}</span>
            </span>
            <span className="text-blue-600">
              工作: {stats.working}
            </span>
            <span className="text-green-600">
              空闲: {stats.idle}
            </span>
            <span className="text-yellow-600">
              充电: {stats.charging}
            </span>
            {stats.maintenance > 0 && (
              <span className="text-orange-600">
                维护: {stats.maintenance}
              </span>
            )}
            {stats.error > 0 && (
              <span className="text-red-600">
                故障: {stats.error}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={loadRobots}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        >
          刷新
        </button>
      </div>

      {/* Map Container */}
      <div
        ref={containerRef}
        className="flex-1 relative bg-gray-100 rounded-lg overflow-hidden"
      >
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-gray-500">加载中...</div>
          </div>
        ) : (
          <>
            {/* SVG Map */}
            <svg
              width={mapDimensions.width}
              height={mapDimensions.height}
              className="absolute inset-4"
            >
              {/* Grid */}
              <defs>
                <pattern
                  id="grid"
                  width="50"
                  height="50"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 50 0 L 0 0 0 50"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="0.5"
                  />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />

              {/* Floor outline (placeholder) */}
              <rect
                x="50"
                y="50"
                width={mapDimensions.width - 100}
                height={mapDimensions.height - 100}
                fill="none"
                stroke="#9ca3af"
                strokeWidth="2"
                strokeDasharray="8 4"
              />

              {/* Robot markers */}
              {filteredRobots.map((robot) => (
                <RobotMarker
                  key={robot.robotId}
                  robot={robot}
                  mapDimensions={mapDimensions}
                  isSelected={selectedRobot?.robotId === robot.robotId}
                  onClick={() => handleRobotClick(robot)}
                />
              ))}
            </svg>

            {/* Legend */}
            <MapLegend />

            {/* Robot Info Panel */}
            {selectedRobot && (
              <RobotInfoPanel
                robot={selectedRobot}
                onClose={() => setSelectedRobot(null)}
                onControl={handleControl}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default RobotMap;
