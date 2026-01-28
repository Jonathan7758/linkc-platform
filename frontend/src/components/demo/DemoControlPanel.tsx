/**
 * DM3: Demo Control Panel
 * 演示控制面板 - 提供演示控制界面
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============================================================
// Types
// ============================================================

interface DemoStatus {
  is_active: boolean;
  current_scenario: string | null;
  scenario_name: string | null;
  started_at: string | null;
  simulation_speed: number;
  auto_events_enabled: boolean;
  pending_events_count: number;
  triggered_events_count: number;
  uptime_seconds: number;
}

interface SimulationStatus {
  running: boolean;
  paused: boolean;
  speed: number;
  robots_count: number;
  robots_by_status: Record<string, number>;
}

interface DemoControlPanelProps {
  visible?: boolean;
  onClose?: () => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

type Scenario = 'executive' | 'ops_normal' | 'ops_alert' | 'agent_chat' | 'full';
type DemoEvent = 'low_battery' | 'obstacle' | 'task_done' | 'urgent_task' | 'robot_error' | 'charging_done';

// ============================================================
// API Functions
// ============================================================

const API_BASE = '/api/v1';

async function fetchDemoStatus(): Promise<DemoStatus> {
  const res = await fetch(`${API_BASE}/demo/status`);
  const data = await res.json();
  return data.status;
}

async function fetchSimulationStatus(): Promise<SimulationStatus> {
  const res = await fetch(`${API_BASE}/simulation/status`);
  const data = await res.json();
  return data.status;
}

async function initDemo(scenario: Scenario): Promise<void> {
  await fetch(`${API_BASE}/demo/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  });
}

async function resetDemo(): Promise<void> {
  await fetch(`${API_BASE}/demo/reset`, { method: 'POST' });
}

async function switchScenario(scenario: Scenario): Promise<void> {
  await fetch(`${API_BASE}/demo/scenario`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  });
}

async function triggerEvent(event: DemoEvent, robotId?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event, robot_id: robotId }),
  });
  return res.json();
}

async function startSimulation(): Promise<void> {
  await fetch(`${API_BASE}/simulation/start`, { method: 'POST' });
}

async function stopSimulation(): Promise<void> {
  await fetch(`${API_BASE}/simulation/stop`, { method: 'POST' });
}

async function pauseSimulation(): Promise<void> {
  await fetch(`${API_BASE}/simulation/pause`, { method: 'POST' });
}

async function resumeSimulation(): Promise<void> {
  await fetch(`${API_BASE}/simulation/resume`, { method: 'POST' });
}

async function setSimulationSpeed(speed: number): Promise<void> {
  await fetch(`${API_BASE}/simulation/speed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ speed }),
  });
}

// ============================================================
// Helper Components
// ============================================================

interface ButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md';
  disabled?: boolean;
  active?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  onClick,
  children,
  variant = 'secondary',
  size = 'md',
  disabled = false,
  active = false,
}) => {
  const baseClasses = 'rounded font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1';

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  };

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-400',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
  };

  const activeClasses = active ? 'ring-2 ring-blue-500' : '';
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${activeClasses} ${disabledClasses}`}
    >
      {children}
    </button>
  );
};

// ============================================================
// Main Component
// ============================================================

const DemoControlPanel: React.FC<DemoControlPanelProps> = ({
  visible = true,
  onClose,
  position = 'bottom-right',
}) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [demoStatus, setDemoStatus] = useState<DemoStatus | null>(null);
  const [simStatus, setSimStatus] = useState<SimulationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastEvent, setLastEvent] = useState<string | null>(null);

  // Position classes
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
  };

  // Fetch status
  const refreshStatus = useCallback(async () => {
    try {
      const [demo, sim] = await Promise.all([
        fetchDemoStatus(),
        fetchSimulationStatus(),
      ]);
      setDemoStatus(demo);
      setSimStatus(sim);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  }, []);

  useEffect(() => {
    if (visible) {
      refreshStatus();
      const interval = setInterval(refreshStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [visible, refreshStatus]);

  // Scenario to URL mapping
  const scenarioRoutes: Record<Scenario, string> = {
    executive: '/executive',
    ops_normal: '/operations',
    ops_alert: '/alerts',
    agent_chat: '/trainer',
    full: '/demo/map',
  };

  // Handlers
  const handleSwitchScenario = async (scenario: Scenario) => {
    setLoading(true);
    try {
      // If not active, init first; otherwise switch
      if (!demoStatus?.is_active) {
        await initDemo(scenario);
        // Also start simulation
        await startSimulation();
      } else {
        await switchScenario(scenario);
      }
      await refreshStatus();
      setLastEvent(`场景: ${scenario}`);

      // Navigate to the corresponding page
      const targetRoute = scenarioRoutes[scenario];
      if (targetRoute && window.location.pathname !== targetRoute) {
        window.location.href = targetRoute;
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await resetDemo();
      await refreshStatus();
      setLastEvent('Demo reset');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerEvent = async (event: DemoEvent) => {
    setLoading(true);
    try {
      const result = await triggerEvent(event);
      setLastEvent(result.message || `Triggered: ${event}`);
      await refreshStatus();
    } finally {
      setLoading(false);
    }
  };

  const handleSimulationControl = async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    setLoading(true);
    try {
      switch (action) {
        case 'start':
          await startSimulation();
          break;
        case 'stop':
          await stopSimulation();
          break;
        case 'pause':
          await pauseSimulation();
          break;
        case 'resume':
          await resumeSimulation();
          break;
      }
      await refreshStatus();
      setLastEvent(`Simulation: ${action}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (speed: number) => {
    setLoading(true);
    try {
      await setSimulationSpeed(speed);
      await refreshStatus();
      setLastEvent(`Speed: ${speed}x`);
    } finally {
      setLoading(false);
    }
  };

  if (!visible) return null;

  // Minimized view
  if (isMinimized) {
    return (
      <div className={`fixed ${positionClasses[position]} z-50`}>
        <button
          onClick={() => setIsMinimized(false)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <span className="text-lg">🎬</span>
          <span className="font-medium">演示控制</span>
          {simStatus?.running && (
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          )}
        </button>
      </div>
    );
  }

  // Full panel
  return (
    <div
      className={`fixed ${positionClasses[position]} z-50 w-80 bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎬</span>
          <span className="font-semibold">演示控制面板</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(true)}
            className="p-1 hover:bg-blue-500 rounded transition-colors"
            title="最小化"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" />
            </svg>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-blue-500 rounded transition-colors"
              title="关闭"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {/* Status Indicator */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                simStatus?.running
                  ? simStatus?.paused
                    ? 'bg-yellow-500'
                    : 'bg-green-500 animate-pulse'
                  : 'bg-gray-400'
              }`}
            />
            <span className="text-gray-600">
              {simStatus?.running
                ? simStatus?.paused
                  ? '已暂停'
                  : '运行中'
                : '已停止'}
            </span>
          </div>
          <span className="text-gray-500">
            {demoStatus?.current_scenario
              ? `场景: ${demoStatus.scenario_name || demoStatus.current_scenario}`
              : '未初始化'}
          </span>
        </div>

        {/* Scenario Selection */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-2">场景切换</label>
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={() => handleSwitchScenario('executive')}
              variant={demoStatus?.current_scenario === 'executive' ? 'primary' : 'secondary'}
              size="sm"
              disabled={loading}
            >
              📊 高管视角
            </Button>
            <Button
              onClick={() => handleSwitchScenario('ops_normal')}
              variant={demoStatus?.current_scenario === 'ops_normal' ? 'primary' : 'secondary'}
              size="sm"
              disabled={loading}
            >
              🔧 运营视角
            </Button>
            <Button
              onClick={() => handleSwitchScenario('agent_chat')}
              variant={demoStatus?.current_scenario === 'agent_chat' ? 'primary' : 'secondary'}
              size="sm"
              disabled={loading}
            >
              🤖 AI协作
            </Button>
            <Button
              onClick={() => handleSwitchScenario('full')}
              variant={demoStatus?.current_scenario === 'full' ? 'primary' : 'secondary'}
              size="sm"
              disabled={loading}
            >
              🎯 完整演示
            </Button>
          </div>
        </div>

        {/* Event Triggers */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-2">触发事件</label>
          <div className="grid grid-cols-3 gap-2">
            <Button
              onClick={() => handleTriggerEvent('low_battery')}
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              🔋 低电量
            </Button>
            <Button
              onClick={() => handleTriggerEvent('obstacle')}
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              🚧 障碍物
            </Button>
            <Button
              onClick={() => handleTriggerEvent('urgent_task')}
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              🆘 紧急任务
            </Button>
            <Button
              onClick={() => handleTriggerEvent('task_done')}
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              ✅ 任务完成
            </Button>
            <Button
              onClick={() => handleTriggerEvent('robot_error')}
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              ⚠️ 故障
            </Button>
            <Button
              onClick={() => handleTriggerEvent('charging_done')}
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              🔌 充电完成
            </Button>
          </div>
        </div>

        {/* Simulation Speed */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-2">
            模拟速度: {simStatus?.speed || 1}x
          </label>
          <div className="flex gap-2">
            {[0.5, 1, 2, 5].map((speed) => (
              <Button
                key={speed}
                onClick={() => handleSpeedChange(speed)}
                variant={simStatus?.speed === speed ? 'primary' : 'secondary'}
                size="sm"
                disabled={loading}
              >
                {speed}x
              </Button>
            ))}
          </div>
        </div>

        {/* Simulation Controls */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-2">模拟控制</label>
          <div className="flex gap-2">
            {!simStatus?.running ? (
              <Button
                onClick={() => handleSimulationControl('start')}
                variant="success"
                size="sm"
                disabled={loading}
              >
                ▶️ 启动
              </Button>
            ) : (
              <>
                {simStatus?.paused ? (
                  <Button
                    onClick={() => handleSimulationControl('resume')}
                    variant="success"
                    size="sm"
                    disabled={loading}
                  >
                    ▶️ 继续
                  </Button>
                ) : (
                  <Button
                    onClick={() => handleSimulationControl('pause')}
                    variant="secondary"
                    size="sm"
                    disabled={loading}
                  >
                    ⏸️ 暂停
                  </Button>
                )}
                <Button
                  onClick={() => handleSimulationControl('stop')}
                  variant="danger"
                  size="sm"
                  disabled={loading}
                >
                  ⏹️ 停止
                </Button>
              </>
            )}
            <Button
              onClick={handleReset}
              variant="secondary"
              size="sm"
              disabled={loading || !demoStatus?.is_active}
            >
              🔄 重置
            </Button>
          </div>
        </div>

        {/* Stats */}
        {simStatus?.running && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500">机器人:</span>
                <span className="ml-1 font-medium">{simStatus.robots_count}</span>
              </div>
              <div>
                <span className="text-gray-500">事件:</span>
                <span className="ml-1 font-medium">{demoStatus?.triggered_events_count || 0}</span>
              </div>
              {Object.entries(simStatus.robots_by_status || {}).map(([status, count]) => (
                <div key={status}>
                  <span className="text-gray-500">{status}:</span>
                  <span className="ml-1 font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Last Event */}
        {lastEvent && (
          <div className="text-xs text-gray-500 bg-gray-50 rounded px-2 py-1">
            最近: {lastEvent}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-50 px-4 py-2 text-xs text-gray-500 flex justify-between border-t">
        <span>LinkC Demo v1.0</span>
        <button
          onClick={refreshStatus}
          className="hover:text-blue-600 transition-colors"
          disabled={loading}
        >
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div>
    </div>
  );
};

export default DemoControlPanel;
