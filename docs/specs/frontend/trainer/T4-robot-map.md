# 模块开发规格书：T4 机器人地图组件

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | T4 |
| 模块名称 | RobotMap - 机器人地图组件 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 规划中 |
| 前置依赖 | G4机器人API、F1数据模型 |

---

## 1. 模块概述

### 1.1 职责描述

RobotMap组件负责在二维地图上实时展示机器人位置、状态和运动轨迹，支持楼层切换、区域标注、机器人选中交互等功能。是训练工作台的核心可视化组件。

### 1.2 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                    训练工作台 (Trainer Workbench)            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ T1: Agent   │  │ T2: 待处理  │  │ T3: 反馈面板        │ │
│  │ 活动流      │  │ 队列        │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              ★ T4: 机器人地图组件 ★                    │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │  楼层平面图                                     │   │ │
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐                 │   │ │
│  │  │  │🤖 R1 │  │🤖 R2 │  │🤖 R3 │ ← 机器人图标    │   │ │
│  │  │  └──────┘  └──────┘  └──────┘                 │   │ │
│  │  │  ════════════════════════════ ← 运动轨迹       │   │ │
│  │  │  [区域A] [区域B] [区域C]      ← 区域标注       │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  │  [楼层选择] [图层控制] [缩放控制]                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 功能概述

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 地图渲染 | 加载并渲染楼层平面图 | P0 |
| 机器人位置 | 实时显示机器人位置图标 | P0 |
| 状态指示 | 通过颜色/动画显示机器人状态 | P0 |
| 楼层切换 | 切换不同楼层视图 | P0 |
| 区域标注 | 显示清洁区域边界 | P1 |
| 运动轨迹 | 显示机器人移动路径 | P1 |
| 机器人选中 | 点击选中机器人查看详情 | P1 |
| 缩放平移 | 地图缩放和拖拽 | P1 |
| 图层控制 | 控制显示/隐藏图层 | P2 |
| 热力图 | 清洁覆盖热力图 | P2 |

---

## 2. UI设计

### 2.1 组件布局

```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 工具栏                                                          │ │
│ │ [楼层: 1F ▼] [图层 ▼] [轨迹: ON] [热力图: OFF]    [🔍+] [🔍-] │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┬───┐ │
│ │                                                             │   │ │
│ │                      地图画布                               │ 图│ │
│ │   ┌──────────────────────────────────────────────────┐     │ 例│ │
│ │   │                                                  │     │   │ │
│ │   │    ┌────────┐                                    │     │ 🟢│ │
│ │   │    │ 区域A  │         🤖←──────────              │     │工作│ │
│ │   │    │        │              机器人轨迹             │     │   │ │
│ │   │    └────────┘                                    │     │ 🟡│ │
│ │   │                    🤖                            │     │暂停│ │
│ │   │         ┌────────────────┐                      │     │   │ │
│ │   │         │    区域B       │                      │     │ 🔴│ │
│ │   │         │                │        🤖            │     │故障│ │
│ │   │         └────────────────┘                      │     │   │ │
│ │   │                                                  │     │ ⚪│ │
│ │   │    ┌───────┐                                    │     │离线│ │
│ │   │    │ 区域C │                                    │     │   │ │
│ │   │    └───────┘                      🔌            │     │ 🔵│ │
│ │   │                              充电站              │     │充电│ │
│ │   └──────────────────────────────────────────────────┘     │   │ │
│ │                                                             │   │ │
│ └─────────────────────────────────────────────────────────────┴───┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 状态栏: 在线机器人: 5/6 | 工作中: 3 | 充电中: 2 | 故障: 0      │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 机器人图标设计

```
机器人图标（SVG）:
┌─────────────────────────────────────────────┐
│                                             │
│  工作中 (working):     暂停 (paused):       │
│  ┌─────┐               ┌─────┐              │
│  │ 🤖  │ + 旋转动画    │ 🤖  │ + 脉冲动画  │
│  │ ▂▂▂ │ (边框)       │ ▁▁▁ │ (边框)      │
│  └─────┘ 绿色          └─────┘ 黄色         │
│                                             │
│  故障 (error):         离线 (offline):      │
│  ┌─────┐               ┌─────┐              │
│  │ 🤖  │ + 闪烁动画    │ 🤖  │ 无动画      │
│  │ ⚠️  │ (警告图标)    │     │ 灰色半透明  │
│  └─────┘ 红色          └─────┘              │
│                                             │
│  充电中 (charging):    选中状态:            │
│  ┌─────┐               ┌─────┐              │
│  │ 🤖  │ + 充电动画    │ 🤖  │ 放大1.2倍   │
│  │ 🔋  │ (电池图标)    │████│ 高亮边框    │
│  └─────┘ 蓝色          └─────┘              │
│                                             │
└─────────────────────────────────────────────┘
```

### 2.3 区域样式

```css
/* 区域样式定义 */
.zone {
  /* 默认样式 */
  fill: rgba(59, 130, 246, 0.1);      /* 浅蓝填充 */
  stroke: rgba(59, 130, 246, 0.5);    /* 蓝色边框 */
  stroke-width: 2;
}

.zone:hover {
  fill: rgba(59, 130, 246, 0.2);      /* 悬停加深 */
}

.zone.cleaning {
  fill: rgba(34, 197, 94, 0.2);       /* 清洁中 - 绿色 */
  stroke: rgba(34, 197, 94, 0.7);
}

.zone.completed {
  fill: rgba(34, 197, 94, 0.1);       /* 已完成 - 浅绿 */
  stroke: rgba(34, 197, 94, 0.3);
}

.zone.pending {
  fill: rgba(250, 204, 21, 0.1);      /* 待清洁 - 黄色 */
  stroke: rgba(250, 204, 21, 0.5);
}
```

### 2.4 轨迹样式

```css
/* 轨迹样式 */
.trajectory {
  stroke: rgba(99, 102, 241, 0.6);    /* 紫色 */
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}

.trajectory.recent {
  stroke: rgba(99, 102, 241, 0.8);    /* 最近轨迹更深 */
  stroke-width: 3;
}

.trajectory.historical {
  stroke: rgba(99, 102, 241, 0.3);    /* 历史轨迹更浅 */
  stroke-width: 1;
  stroke-dasharray: 4 2;              /* 虚线 */
}
```

---

## 3. 组件接口

### 3.1 Props定义

```typescript
// components/RobotMap/types.ts

interface RobotMapProps {
  /** 楼宇ID */
  buildingId: string;
  
  /** 默认楼层ID */
  defaultFloorId?: string;
  
  /** 机器人列表（实时更新） */
  robots: Robot[];
  
  /** 区域列表 */
  zones: Zone[];
  
  /** 是否显示轨迹 */
  showTrajectory?: boolean;
  
  /** 是否显示热力图 */
  showHeatmap?: boolean;
  
  /** 选中的机器人ID */
  selectedRobotId?: string;
  
  /** 机器人点击回调 */
  onRobotClick?: (robot: Robot) => void;
  
  /** 区域点击回调 */
  onZoneClick?: (zone: Zone) => void;
  
  /** 楼层切换回调 */
  onFloorChange?: (floorId: string) => void;
  
  /** 地图加载完成回调 */
  onMapLoad?: () => void;
  
  /** 容器样式 */
  className?: string;
  
  /** 容器高度 */
  height?: number | string;
  
  /** 刷新间隔（毫秒） */
  refreshInterval?: number;
  
  /** 是否启用WebSocket实时更新 */
  enableRealtime?: boolean;
}

interface Robot {
  id: string;
  name: string;
  brand: 'gaoxian' | 'ecovacs' | 'other';
  status: RobotStatus;
  position: Position | null;
  battery_level: number;
  current_task_id?: string;
}

interface RobotStatus {
  state: 'idle' | 'working' | 'charging' | 'paused' | 'error' | 'offline';
  sub_state?: string;
  error_code?: string;
  error_message?: string;
}

interface Position {
  x: number;          // 地图坐标X
  y: number;          // 地图坐标Y
  heading: number;    // 朝向角度（0-360）
  floor_id: string;
  timestamp: string;
}

interface Zone {
  id: string;
  name: string;
  floor_id: string;
  zone_type: 'cleaning' | 'restricted' | 'charging';
  polygon: Point[];   // 多边形顶点
  status?: 'pending' | 'cleaning' | 'completed';
  assigned_robot_id?: string;
}

interface Point {
  x: number;
  y: number;
}

interface Floor {
  id: string;
  name: string;
  building_id: string;
  floor_number: number;
  map_url: string;    // 楼层平面图URL
  map_width: number;  // 地图宽度（像素）
  map_height: number; // 地图高度（像素）
  scale: number;      // 比例尺（像素/米）
}

interface Trajectory {
  robot_id: string;
  points: TrajectoryPoint[];
}

interface TrajectoryPoint {
  x: number;
  y: number;
  timestamp: string;
}

interface HeatmapData {
  floor_id: string;
  cells: HeatmapCell[];
}

interface HeatmapCell {
  x: number;
  y: number;
  value: number;      // 0-1, 清洁覆盖度
}
```

### 3.2 暴露的方法（Ref）

```typescript
interface RobotMapRef {
  /** 切换楼层 */
  switchFloor: (floorId: string) => void;
  
  /** 聚焦到指定机器人 */
  focusRobot: (robotId: string) => void;
  
  /** 聚焦到指定区域 */
  focusZone: (zoneId: string) => void;
  
  /** 设置缩放级别 */
  setZoom: (level: number) => void;
  
  /** 重置视图 */
  resetView: () => void;
  
  /** 获取当前视图状态 */
  getViewState: () => ViewState;
  
  /** 导出地图截图 */
  exportImage: () => Promise<Blob>;
}

interface ViewState {
  floorId: string;
  zoom: number;
  center: Point;
  bounds: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
  };
}
```

### 3.3 API调用

```typescript
// 获取楼层列表
GET /api/v1/spaces/buildings/{building_id}/floors

// 获取楼层地图详情
GET /api/v1/spaces/floors/{floor_id}

// 获取机器人位置（实时）
GET /api/v1/robots?floor_id={floor_id}&include_position=true

// WebSocket实时位置推送
WS /api/v1/robots/ws/status

// 获取机器人轨迹
GET /api/v1/robots/{robot_id}/positions?start_time={}&end_time={}

// 获取区域列表
GET /api/v1/spaces/floors/{floor_id}/zones

// 获取热力图数据
GET /api/v1/data/coverage-heatmap?floor_id={floor_id}&date={}
```

---

## 4. 数据模型

### 4.1 地图状态

```typescript
interface MapState {
  /** 当前楼层 */
  currentFloor: Floor | null;
  
  /** 所有楼层 */
  floors: Floor[];
  
  /** 当前楼层的机器人 */
  robots: Robot[];
  
  /** 当前楼层的区域 */
  zones: Zone[];
  
  /** 机器人轨迹 */
  trajectories: Map<string, Trajectory>;
  
  /** 热力图数据 */
  heatmap: HeatmapData | null;
  
  /** 选中的机器人 */
  selectedRobotId: string | null;
  
  /** 视图状态 */
  viewState: ViewState;
  
  /** 图层显示控制 */
  layers: LayerVisibility;
  
  /** 加载状态 */
  loading: boolean;
  
  /** 错误信息 */
  error: string | null;
}

interface LayerVisibility {
  zones: boolean;
  robots: boolean;
  trajectories: boolean;
  heatmap: boolean;
  labels: boolean;
  chargingStations: boolean;
}
```

### 4.2 WebSocket消息

```typescript
// 机器人位置更新消息
interface RobotPositionUpdate {
  type: 'position_update';
  robot_id: string;
  position: Position;
  status: RobotStatus;
  battery_level: number;
  timestamp: string;
}

// 机器人状态变化消息
interface RobotStatusChange {
  type: 'status_change';
  robot_id: string;
  old_status: RobotStatus;
  new_status: RobotStatus;
  timestamp: string;
}

// 区域状态更新消息
interface ZoneStatusUpdate {
  type: 'zone_update';
  zone_id: string;
  status: 'pending' | 'cleaning' | 'completed';
  assigned_robot_id?: string;
  timestamp: string;
}

type WebSocketMessage = RobotPositionUpdate | RobotStatusChange | ZoneStatusUpdate;
```

---

## 5. 实现要求

### 5.1 技术栈

| 技术 | 版本 | 用途 |
|-----|------|------|
| React | 18+ | UI框架 |
| TypeScript | 5.0+ | 类型安全 |
| Canvas/SVG | - | 地图渲染 |
| React-Konva | 18.2+ | Canvas抽象层 |
| TailwindCSS | 3.4+ | 样式 |
| React Query | 5.0+ | 数据获取 |
| Zustand | 4.0+ | 状态管理 |

### 5.2 核心实现

#### 5.2.1 地图渲染引擎

```typescript
// components/RobotMap/MapCanvas.tsx
import React, { useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Image, Group } from 'react-konva';
import useImage from 'use-image';
import { useMapStore } from './store';
import { RobotMarker } from './RobotMarker';
import { ZoneOverlay } from './ZoneOverlay';
import { TrajectoryLine } from './TrajectoryLine';
import { HeatmapOverlay } from './HeatmapOverlay';

interface MapCanvasProps {
  floor: Floor;
  robots: Robot[];
  zones: Zone[];
  trajectories: Map<string, Trajectory>;
  heatmap: HeatmapData | null;
  selectedRobotId: string | null;
  layers: LayerVisibility;
  onRobotClick: (robot: Robot) => void;
  onZoneClick: (zone: Zone) => void;
}

export const MapCanvas: React.FC<MapCanvasProps> = ({
  floor,
  robots,
  zones,
  trajectories,
  heatmap,
  selectedRobotId,
  layers,
  onRobotClick,
  onZoneClick,
}) => {
  const stageRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [mapImage] = useImage(floor.map_url);
  
  const {
    zoom,
    position,
    setZoom,
    setPosition,
  } = useMapStore();

  // 计算容器尺寸
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setContainerSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // 缩放处理
  const handleWheel = useCallback((e: any) => {
    e.evt.preventDefault();
    
    const stage = stageRef.current;
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();
    
    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };
    
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const newScale = direction > 0 
      ? Math.min(oldScale * 1.1, 5)   // 最大5倍
      : Math.max(oldScale / 1.1, 0.5); // 最小0.5倍
    
    setZoom(newScale);
    
    const newPos = {
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale,
    };
    setPosition(newPos);
  }, [setZoom, setPosition]);

  // 拖拽处理
  const handleDragEnd = useCallback((e: any) => {
    setPosition({
      x: e.target.x(),
      y: e.target.y(),
    });
  }, [setPosition]);

  // 过滤当前楼层的数据
  const floorRobots = robots.filter(r => r.position?.floor_id === floor.id);
  const floorZones = zones.filter(z => z.floor_id === floor.id);

  return (
    <div ref={containerRef} className="w-full h-full">
      <Stage
        ref={stageRef}
        width={containerSize.width}
        height={containerSize.height}
        scaleX={zoom}
        scaleY={zoom}
        x={position.x}
        y={position.y}
        draggable
        onWheel={handleWheel}
        onDragEnd={handleDragEnd}
      >
        {/* 底图层 */}
        <Layer>
          {mapImage && (
            <Image
              image={mapImage}
              width={floor.map_width}
              height={floor.map_height}
            />
          )}
        </Layer>

        {/* 热力图层 */}
        {layers.heatmap && heatmap && (
          <Layer opacity={0.5}>
            <HeatmapOverlay data={heatmap} scale={floor.scale} />
          </Layer>
        )}

        {/* 区域层 */}
        {layers.zones && (
          <Layer>
            {floorZones.map(zone => (
              <ZoneOverlay
                key={zone.id}
                zone={zone}
                onClick={() => onZoneClick(zone)}
              />
            ))}
          </Layer>
        )}

        {/* 轨迹层 */}
        {layers.trajectories && (
          <Layer>
            {Array.from(trajectories.entries()).map(([robotId, trajectory]) => (
              <TrajectoryLine
                key={robotId}
                trajectory={trajectory}
                isSelected={robotId === selectedRobotId}
              />
            ))}
          </Layer>
        )}

        {/* 机器人层 */}
        {layers.robots && (
          <Layer>
            {floorRobots.map(robot => (
              <RobotMarker
                key={robot.id}
                robot={robot}
                isSelected={robot.id === selectedRobotId}
                onClick={() => onRobotClick(robot)}
              />
            ))}
          </Layer>
        )}
      </Stage>
    </div>
  );
};
```

#### 5.2.2 机器人标记组件

```typescript
// components/RobotMap/RobotMarker.tsx
import React, { useMemo } from 'react';
import { Group, Circle, Text, Arrow } from 'react-konva';
import { Robot } from './types';

interface RobotMarkerProps {
  robot: Robot;
  isSelected: boolean;
  onClick: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  idle: '#9CA3AF',      // 灰色
  working: '#22C55E',   // 绿色
  charging: '#3B82F6',  // 蓝色
  paused: '#EAB308',    // 黄色
  error: '#EF4444',     // 红色
  offline: '#D1D5DB',   // 浅灰
};

const MARKER_SIZE = 24;
const SELECTED_SCALE = 1.3;

export const RobotMarker: React.FC<RobotMarkerProps> = ({
  robot,
  isSelected,
  onClick,
}) => {
  const position = robot.position;
  if (!position) return null;

  const color = STATUS_COLORS[robot.status.state] || STATUS_COLORS.offline;
  const scale = isSelected ? SELECTED_SCALE : 1;

  // 计算方向箭头
  const arrowPoints = useMemo(() => {
    const angle = (position.heading * Math.PI) / 180;
    const length = MARKER_SIZE * 0.8;
    return [
      0, 0,
      Math.sin(angle) * length,
      -Math.cos(angle) * length,
    ];
  }, [position.heading]);

  return (
    <Group
      x={position.x}
      y={position.y}
      scaleX={scale}
      scaleY={scale}
      onClick={onClick}
      onTap={onClick}
    >
      {/* 选中光环 */}
      {isSelected && (
        <Circle
          radius={MARKER_SIZE * 0.8}
          stroke={color}
          strokeWidth={3}
          dash={[5, 5]}
          opacity={0.5}
        />
      )}

      {/* 主体圆 */}
      <Circle
        radius={MARKER_SIZE / 2}
        fill={color}
        stroke={isSelected ? '#FFFFFF' : color}
        strokeWidth={isSelected ? 3 : 1}
        shadowColor="black"
        shadowBlur={5}
        shadowOpacity={0.3}
      />

      {/* 方向箭头 */}
      <Arrow
        points={arrowPoints}
        fill="#FFFFFF"
        stroke="#FFFFFF"
        strokeWidth={2}
        pointerLength={6}
        pointerWidth={6}
      />

      {/* 机器人名称 */}
      <Text
        text={robot.name}
        fontSize={10}
        fill="#FFFFFF"
        fontStyle="bold"
        y={MARKER_SIZE / 2 + 4}
        offsetX={robot.name.length * 2.5}
      />

      {/* 电量指示（低电量时显示） */}
      {robot.battery_level < 20 && (
        <Text
          text={`🔋${robot.battery_level}%`}
          fontSize={8}
          fill="#EF4444"
          y={MARKER_SIZE / 2 + 16}
          offsetX={15}
        />
      )}

      {/* 状态动画 */}
      <StatusAnimation status={robot.status.state} />
    </Group>
  );
};

// 状态动画组件
const StatusAnimation: React.FC<{ status: string }> = ({ status }) => {
  // 工作中：旋转动画
  // 充电中：脉冲动画
  // 错误：闪烁动画
  // 使用Konva的Animation实现
  return null; // 简化实现，实际需要使用Konva.Animation
};
```

#### 5.2.3 区域覆盖层

```typescript
// components/RobotMap/ZoneOverlay.tsx
import React from 'react';
import { Line, Text, Group } from 'react-konva';
import { Zone } from './types';

interface ZoneOverlayProps {
  zone: Zone;
  onClick: () => void;
}

const ZONE_COLORS: Record<string, { fill: string; stroke: string }> = {
  pending: {
    fill: 'rgba(250, 204, 21, 0.1)',
    stroke: 'rgba(250, 204, 21, 0.5)',
  },
  cleaning: {
    fill: 'rgba(34, 197, 94, 0.2)',
    stroke: 'rgba(34, 197, 94, 0.7)',
  },
  completed: {
    fill: 'rgba(34, 197, 94, 0.1)',
    stroke: 'rgba(34, 197, 94, 0.3)',
  },
  default: {
    fill: 'rgba(59, 130, 246, 0.1)',
    stroke: 'rgba(59, 130, 246, 0.5)',
  },
};

export const ZoneOverlay: React.FC<ZoneOverlayProps> = ({ zone, onClick }) => {
  const colors = ZONE_COLORS[zone.status || 'default'] || ZONE_COLORS.default;
  
  // 将多边形顶点转换为Konva格式
  const points = zone.polygon.flatMap(p => [p.x, p.y]);
  
  // 计算中心点用于显示标签
  const centerX = zone.polygon.reduce((sum, p) => sum + p.x, 0) / zone.polygon.length;
  const centerY = zone.polygon.reduce((sum, p) => sum + p.y, 0) / zone.polygon.length;

  return (
    <Group onClick={onClick} onTap={onClick}>
      {/* 区域多边形 */}
      <Line
        points={points}
        fill={colors.fill}
        stroke={colors.stroke}
        strokeWidth={2}
        closed
        hitStrokeWidth={10}
      />
      
      {/* 区域名称标签 */}
      <Text
        x={centerX}
        y={centerY}
        text={zone.name}
        fontSize={12}
        fill="#374151"
        fontStyle="bold"
        offsetX={zone.name.length * 3}
        offsetY={6}
      />
    </Group>
  );
};
```

#### 5.2.4 WebSocket实时更新

```typescript
// hooks/useRobotPositionUpdates.ts
import { useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketMessage } from '../types';

export function useRobotPositionUpdates(floorId: string) {
  const queryClient = useQueryClient();
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'position_update':
        // 更新机器人位置缓存
        queryClient.setQueryData(
          ['robots', { floor_id: floorId }],
          (oldData: Robot[] | undefined) => {
            if (!oldData) return oldData;
            return oldData.map(robot => 
              robot.id === message.robot_id
                ? {
                    ...robot,
                    position: message.position,
                    status: message.status,
                    battery_level: message.battery_level,
                  }
                : robot
            );
          }
        );
        break;
        
      case 'status_change':
        // 更新机器人状态
        queryClient.setQueryData(
          ['robots', { floor_id: floorId }],
          (oldData: Robot[] | undefined) => {
            if (!oldData) return oldData;
            return oldData.map(robot =>
              robot.id === message.robot_id
                ? { ...robot, status: message.new_status }
                : robot
            );
          }
        );
        break;
        
      case 'zone_update':
        // 更新区域状态
        queryClient.setQueryData(
          ['zones', { floor_id: floorId }],
          (oldData: Zone[] | undefined) => {
            if (!oldData) return oldData;
            return oldData.map(zone =>
              zone.id === message.zone_id
                ? {
                    ...zone,
                    status: message.status,
                    assigned_robot_id: message.assigned_robot_id,
                  }
                : zone
            );
          }
        );
        break;
    }
  }, [queryClient, floorId]);

  useEffect(() => {
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/api/v1/robots/ws/status`
    );
    
    ws.onopen = () => {
      // 订阅指定楼层
      ws.send(JSON.stringify({
        action: 'subscribe',
        floor_id: floorId,
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        handleMessage(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [floorId, handleMessage]);
}
```

#### 5.2.5 主组件

```typescript
// components/RobotMap/index.tsx
import React, { useRef, useImperativeHandle, forwardRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MapCanvas } from './MapCanvas';
import { MapToolbar } from './MapToolbar';
import { MapLegend } from './MapLegend';
import { MapStatusBar } from './MapStatusBar';
import { useMapStore } from './store';
import { useRobotPositionUpdates } from '../../hooks/useRobotPositionUpdates';
import { RobotMapProps, RobotMapRef, Floor, Robot, Zone, Trajectory } from './types';
import { fetchFloors, fetchRobots, fetchZones, fetchTrajectory, fetchHeatmap } from '../../api';

export const RobotMap = forwardRef<RobotMapRef, RobotMapProps>(({
  buildingId,
  defaultFloorId,
  robots: externalRobots,
  zones: externalZones,
  showTrajectory = false,
  showHeatmap = false,
  selectedRobotId,
  onRobotClick,
  onZoneClick,
  onFloorChange,
  onMapLoad,
  className,
  height = 600,
  refreshInterval = 5000,
  enableRealtime = true,
}, ref) => {
  const mapCanvasRef = useRef<any>(null);
  
  const {
    currentFloorId,
    setCurrentFloorId,
    layers,
    setLayers,
    zoom,
    setZoom,
    resetView,
  } = useMapStore();

  // 获取楼层列表
  const { data: floors = [] } = useQuery({
    queryKey: ['floors', buildingId],
    queryFn: () => fetchFloors(buildingId),
    onSuccess: (data) => {
      if (!currentFloorId && data.length > 0) {
        const floor = defaultFloorId 
          ? data.find(f => f.id === defaultFloorId) 
          : data[0];
        if (floor) {
          setCurrentFloorId(floor.id);
        }
      }
    },
  });

  const currentFloor = floors.find(f => f.id === currentFloorId);

  // 获取机器人（如果没有外部传入）
  const { data: fetchedRobots = [] } = useQuery({
    queryKey: ['robots', { floor_id: currentFloorId }],
    queryFn: () => fetchRobots({ floor_id: currentFloorId, include_position: true }),
    enabled: !externalRobots && !!currentFloorId,
    refetchInterval: refreshInterval,
  });

  // 获取区域（如果没有外部传入）
  const { data: fetchedZones = [] } = useQuery({
    queryKey: ['zones', { floor_id: currentFloorId }],
    queryFn: () => fetchZones(currentFloorId!),
    enabled: !externalZones && !!currentFloorId,
  });

  const robots = externalRobots || fetchedRobots;
  const zones = externalZones || fetchedZones;

  // WebSocket实时更新
  if (enableRealtime && currentFloorId) {
    useRobotPositionUpdates(currentFloorId);
  }

  // 获取轨迹数据
  const { data: trajectories = new Map() } = useQuery({
    queryKey: ['trajectories', selectedRobotId],
    queryFn: async () => {
      if (!selectedRobotId) return new Map<string, Trajectory>();
      const trajectory = await fetchTrajectory(selectedRobotId, {
        start_time: new Date(Date.now() - 3600000).toISOString(), // 最近1小时
        end_time: new Date().toISOString(),
      });
      return new Map([[selectedRobotId, trajectory]]);
    },
    enabled: showTrajectory && !!selectedRobotId,
  });

  // 获取热力图数据
  const { data: heatmap } = useQuery({
    queryKey: ['heatmap', currentFloorId],
    queryFn: () => fetchHeatmap(currentFloorId!, new Date().toISOString().split('T')[0]),
    enabled: showHeatmap && !!currentFloorId,
  });

  // 暴露方法给父组件
  useImperativeHandle(ref, () => ({
    switchFloor: (floorId: string) => {
      setCurrentFloorId(floorId);
      onFloorChange?.(floorId);
    },
    focusRobot: (robotId: string) => {
      const robot = robots.find(r => r.id === robotId);
      if (robot?.position) {
        // 平移到机器人位置
        mapCanvasRef.current?.centerOn(robot.position.x, robot.position.y);
      }
    },
    focusZone: (zoneId: string) => {
      const zone = zones.find(z => z.id === zoneId);
      if (zone && zone.polygon.length > 0) {
        const centerX = zone.polygon.reduce((s, p) => s + p.x, 0) / zone.polygon.length;
        const centerY = zone.polygon.reduce((s, p) => s + p.y, 0) / zone.polygon.length;
        mapCanvasRef.current?.centerOn(centerX, centerY);
      }
    },
    setZoom,
    resetView,
    getViewState: () => ({
      floorId: currentFloorId!,
      zoom,
      center: { x: 0, y: 0 },
      bounds: { minX: 0, maxX: 0, minY: 0, maxY: 0 },
    }),
    exportImage: async () => {
      const stage = mapCanvasRef.current?.getStage();
      if (!stage) throw new Error('Stage not ready');
      const dataUrl = stage.toDataURL({ pixelRatio: 2 });
      const res = await fetch(dataUrl);
      return res.blob();
    },
  }));

  // 统计数据
  const stats = {
    total: robots.length,
    online: robots.filter(r => r.status.state !== 'offline').length,
    working: robots.filter(r => r.status.state === 'working').length,
    charging: robots.filter(r => r.status.state === 'charging').length,
    error: robots.filter(r => r.status.state === 'error').length,
  };

  return (
    <div className={`flex flex-col ${className}`} style={{ height }}>
      {/* 工具栏 */}
      <MapToolbar
        floors={floors}
        currentFloorId={currentFloorId}
        onFloorChange={(id) => {
          setCurrentFloorId(id);
          onFloorChange?.(id);
        }}
        layers={layers}
        onLayersChange={setLayers}
        zoom={zoom}
        onZoomChange={setZoom}
        onReset={resetView}
      />

      {/* 地图主体 */}
      <div className="flex-1 relative bg-gray-100">
        {currentFloor ? (
          <MapCanvas
            ref={mapCanvasRef}
            floor={currentFloor}
            robots={robots}
            zones={zones}
            trajectories={trajectories}
            heatmap={heatmap || null}
            selectedRobotId={selectedRobotId || null}
            layers={layers}
            onRobotClick={(robot) => onRobotClick?.(robot)}
            onZoneClick={(zone) => onZoneClick?.(zone)}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            请选择楼层
          </div>
        )}

        {/* 图例 */}
        <MapLegend className="absolute top-4 right-4" />
      </div>

      {/* 状态栏 */}
      <MapStatusBar stats={stats} />
    </div>
  );
});

RobotMap.displayName = 'RobotMap';

export default RobotMap;
```

---

## 6. 测试要求

### 6.1 单元测试

```typescript
// components/RobotMap/__tests__/RobotMap.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RobotMap } from '../index';

const mockFloors: Floor[] = [
  {
    id: 'floor-1',
    name: '1F',
    building_id: 'building-1',
    floor_number: 1,
    map_url: '/maps/floor1.png',
    map_width: 1000,
    map_height: 800,
    scale: 100,
  },
];

const mockRobots: Robot[] = [
  {
    id: 'robot-1',
    name: 'R1',
    brand: 'gaoxian',
    status: { state: 'working' },
    position: { x: 100, y: 200, heading: 45, floor_id: 'floor-1', timestamp: '' },
    battery_level: 85,
  },
  {
    id: 'robot-2',
    name: 'R2',
    brand: 'ecovacs',
    status: { state: 'charging' },
    position: { x: 300, y: 400, heading: 90, floor_id: 'floor-1', timestamp: '' },
    battery_level: 45,
  },
];

const mockZones: Zone[] = [
  {
    id: 'zone-1',
    name: 'Area A',
    floor_id: 'floor-1',
    zone_type: 'cleaning',
    polygon: [{ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 100, y: 100 }, { x: 0, y: 100 }],
    status: 'cleaning',
  },
];

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('RobotMap', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  test('renders map with robots', async () => {
    render(
      <RobotMap
        buildingId="building-1"
        robots={mockRobots}
        zones={mockZones}
      />,
      { wrapper }
    );

    // 等待地图加载
    await waitFor(() => {
      expect(screen.getByText('在线机器人:')).toBeInTheDocument();
    });
  });

  test('handles floor change', async () => {
    const onFloorChange = jest.fn();
    
    render(
      <RobotMap
        buildingId="building-1"
        robots={mockRobots}
        zones={mockZones}
        onFloorChange={onFloorChange}
      />,
      { wrapper }
    );

    // 模拟楼层切换
    // ...
  });

  test('handles robot click', async () => {
    const onRobotClick = jest.fn();
    
    render(
      <RobotMap
        buildingId="building-1"
        robots={mockRobots}
        zones={mockZones}
        onRobotClick={onRobotClick}
      />,
      { wrapper }
    );

    // 由于使用Canvas，需要模拟Konva事件
    // ...
  });

  test('displays correct robot status colors', () => {
    // 测试不同状态的机器人显示正确的颜色
  });

  test('displays zone overlays', () => {
    // 测试区域覆盖层正确显示
  });

  test('handles zoom controls', () => {
    // 测试缩放控制
  });

  test('handles layer visibility toggle', () => {
    // 测试图层显示/隐藏
  });
});
```

### 6.2 集成测试

```typescript
// components/RobotMap/__tests__/RobotMap.integration.test.tsx
describe('RobotMap Integration', () => {
  test('receives WebSocket updates and updates robot positions', async () => {
    // 测试WebSocket实时更新
  });

  test('loads trajectory when robot is selected', async () => {
    // 测试选中机器人时加载轨迹
  });

  test('loads heatmap data when enabled', async () => {
    // 测试热力图加载
  });
});
```

---

## 7. 验收标准

### 7.1 功能验收

| 验收项 | 验收标准 | 优先级 |
|-------|---------|-------|
| 地图渲染 | 楼层平面图正确加载并显示 | P0 |
| 机器人显示 | 所有在线机器人正确显示在地图上 | P0 |
| 状态颜色 | 机器人状态通过颜色正确区分 | P0 |
| 实时更新 | 机器人位置实时更新（延迟<1秒） | P0 |
| 楼层切换 | 点击楼层选择器可切换楼层 | P0 |
| 缩放平移 | 鼠标滚轮缩放、拖拽平移正常工作 | P1 |
| 机器人点击 | 点击机器人触发回调并高亮显示 | P1 |
| 区域显示 | 区域边界和状态正确显示 | P1 |
| 轨迹显示 | 选中机器人时显示运动轨迹 | P1 |
| 热力图 | 热力图正确叠加在地图上 | P2 |

### 7.2 性能要求

| 指标 | 要求 | 测量方法 |
|-----|------|---------|
| 首次渲染 | < 500ms | Performance API |
| 位置更新帧率 | ≥ 30fps | 动画帧计数 |
| WebSocket延迟 | < 100ms | 端到端时间戳 |
| 内存占用 | < 100MB | Chrome DevTools |
| 支持机器人数 | ≥ 50台 | 压力测试 |

### 7.3 代码质量

| 要求 | 标准 |
|-----|------|
| TypeScript | 严格模式，无any类型 |
| 测试覆盖 | 核心逻辑 > 80% |
| 组件拆分 | 单组件 < 300行 |
| 性能优化 | 使用React.memo、useMemo、useCallback |

---

## 8. 依赖说明

### 8.1 npm依赖

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-konva": "^18.2.10",
    "konva": "^9.2.0",
    "use-image": "^1.1.1",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "jest-canvas-mock": "^2.5.0"
  }
}
```

### 8.2 API依赖

- G4: 机器人API（位置、状态）
- G2: 空间API（楼层、区域）
- G6: 数据API（热力图）
- WebSocket: 实时位置推送

---

*文档结束*
