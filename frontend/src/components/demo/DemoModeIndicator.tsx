/**
 * DM3: Demo Mode Indicator
 * 演示模式指示器 - 在页面顶部显示演示模式状态
 */

import React, { useState, useEffect } from 'react';

interface DemoModeIndicatorProps {
  onClick?: () => void;
}

interface DemoStatus {
  is_active: boolean;
  current_scenario: string | null;
  scenario_name: string | null;
  simulation_speed: number;
}

const DemoModeIndicator: React.FC<DemoModeIndicatorProps> = ({ onClick }) => {
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [demoRes, simRes] = await Promise.all([
          fetch('/api/v1/demo/status'),
          fetch('/api/v1/simulation/status'),
        ]);
        const demoData = await demoRes.json();
        const simData = await simRes.json();
        setStatus(demoData.status);
        setIsRunning(simData.status?.running || false);
      } catch (error) {
        console.error('Failed to fetch demo status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!status?.is_active) return null;

  return (
    <div
      className="fixed top-0 left-1/2 transform -translate-x-1/2 z-50 cursor-pointer"
      onClick={onClick}
    >
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1.5 rounded-b-lg shadow-lg flex items-center gap-3 text-sm">
        <span className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              isRunning ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'
            }`}
          />
          <span className="font-medium">演示模式</span>
        </span>
        <span className="text-blue-200">|</span>
        <span className="text-blue-100">
          {status.scenario_name || status.current_scenario || '未知场景'}
        </span>
        {status.simulation_speed !== 1 && (
          <>
            <span className="text-blue-200">|</span>
            <span className="text-yellow-300">{status.simulation_speed}x</span>
          </>
        )}
        <span className="text-blue-200">|</span>
        <span className="text-blue-100 hover:text-white transition-colors">
          点击打开控制面板
        </span>
      </div>
    </div>
  );
};

export default DemoModeIndicator;
