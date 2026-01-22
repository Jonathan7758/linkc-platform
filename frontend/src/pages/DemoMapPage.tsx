/**
 * DM5: Demo Map Page
 * 地图动态可视化演示页面
 *
 * 集成:
 * - 实时地图可视化
 * - 机器人状态监控
 * - 演示控制面板
 */

import React, { useState, useCallback } from 'react';
import { DemoMapVisualization, DemoControlPanel, DemoModeIndicator } from '../components/demo';

// Types
interface RobotSimState {
  robot_id: string;
  name: string;
  status: string;
  position: { x: number; y: number; orientation: number };
  battery_level: number;
  current_task_id?: string;
}

interface Zone {
  id: string;
  name: string;
  zone_type: string;
}

const DemoMapPage: React.FC = () => {
  const [selectedRobot, setSelectedRobot] = useState<RobotSimState | null>(null);
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showPaths, setShowPaths] = useState(true);

  const handleRobotSelect = useCallback((robot: RobotSimState) => {
    setSelectedRobot(robot);
    setSelectedZone(null);
  }, []);

  const handleZoneSelect = useCallback((zone: Zone) => {
    setSelectedZone(zone);
    setSelectedRobot(null);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Demo Mode Indicator */}
      <DemoModeIndicator />

      {/* Header */}
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold text-gray-900">实时地图监控</h1>
          <span className="text-sm text-gray-500">DM5 地图动态可视化</span>
        </div>

        <div className="flex items-center gap-4">
          {/* View toggles */}
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setShowHeatmap(false)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                !showHeatmap ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              状态视图
            </button>
            <button
              onClick={() => setShowHeatmap(true)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                showHeatmap ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              热力图
            </button>
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showPaths}
              onChange={(e) => setShowPaths(e.target.checked)}
              className="rounded"
            />
            显示路径
          </label>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Map visualization */}
        <div className="flex-1">
          <DemoMapVisualization
            buildingId="building_001"
            onRobotSelect={handleRobotSelect}
            onZoneSelect={handleZoneSelect}
            showHeatmap={showHeatmap}
            showPaths={showPaths}
            refreshInterval={500}
          />
        </div>

        {/* Side panel for selection details */}
        {(selectedRobot || selectedZone) && (
          <aside className="w-80 bg-white border-l overflow-y-auto">
            {selectedRobot && (
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-900">机器人详情</h2>
                  <button
                    onClick={() => setSelectedRobot(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-500">名称</div>
                    <div className="font-medium">{selectedRobot.name}</div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-500">ID</div>
                    <div className="font-mono text-sm">{selectedRobot.robot_id}</div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-500">状态</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{
                          backgroundColor:
                            selectedRobot.status === 'working' ? '#3b82f6' :
                            selectedRobot.status === 'idle' ? '#22c55e' :
                            selectedRobot.status === 'charging' ? '#eab308' :
                            '#ef4444'
                        }}
                      />
                      <span className="capitalize">{selectedRobot.status}</span>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-500">电量</div>
                    <div className="mt-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${selectedRobot.battery_level}%`,
                              backgroundColor:
                                selectedRobot.battery_level > 60 ? '#22c55e' :
                                selectedRobot.battery_level > 20 ? '#eab308' : '#ef4444'
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium">{selectedRobot.battery_level}%</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-500">位置</div>
                    <div className="font-mono text-sm">
                      X: {selectedRobot.position.x.toFixed(1)}, Y: {selectedRobot.position.y.toFixed(1)}
                    </div>
                  </div>

                  {selectedRobot.current_task_id && (
                    <div>
                      <div className="text-sm text-gray-500">当前任务</div>
                      <div className="font-mono text-sm text-blue-600">
                        {selectedRobot.current_task_id}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t flex gap-2">
                    <button className="flex-1 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                      召回
                    </button>
                    <button className="flex-1 px-3 py-2 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200">
                      暂停
                    </button>
                  </div>
                </div>
              </div>
            )}

            {selectedZone && (
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-900">区域详情</h2>
                  <button
                    onClick={() => setSelectedZone(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-500">名称</div>
                    <div className="font-medium">{selectedZone.name}</div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-500">类型</div>
                    <div className="capitalize">{selectedZone.zone_type}</div>
                  </div>

                  <div className="pt-4 border-t">
                    <button className="w-full px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                      创建清洁任务
                    </button>
                  </div>
                </div>
              </div>
            )}
          </aside>
        )}
      </main>

      {/* Demo Control Panel */}
      <DemoControlPanel />
    </div>
  );
};

export default DemoMapPage;
