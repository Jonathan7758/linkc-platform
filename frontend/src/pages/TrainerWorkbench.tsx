/**
 * Trainer Workbench Page
 * 训练工作台主页面 - 整合T1-T4组件
 */

import React, { useState, useCallback } from 'react';
import { AgentActivity, PendingItem, Robot } from '../types/index';
import { ActivityFeed } from '../components/ActivityFeed';
import { PendingQueue } from '../components/PendingQueue';
import { FeedbackPanel } from '../components/FeedbackPanel';
import { RobotMap } from '../components/RobotMap';

// ============================================================
// Types
// ============================================================

interface TrainerWorkbenchProps {
  tenantId: string;
  buildingId: string;
}

type ViewMode = 'split' | 'activities' | 'pending' | 'map';

// ============================================================
// View Mode Selector
// ============================================================

interface ViewModeSelectorProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

const ViewModeSelector: React.FC<ViewModeSelectorProps> = ({ mode, onChange }) => {
  const modes: { value: ViewMode; label: string; icon: string }[] = [
    { value: 'split', label: '分屏', icon: '⊞' },
    { value: 'activities', label: '活动流', icon: '📋' },
    { value: 'pending', label: '待处理', icon: '⏳' },
    { value: 'map', label: '地图', icon: '🗺️' },
  ];

  return (
    <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
      {modes.map((m) => (
        <button
          key={m.value}
          onClick={() => onChange(m.value)}
          className={`px-3 py-1.5 text-sm rounded transition-colors ${
            mode === m.value
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <span className="mr-1">{m.icon}</span>
          {m.label}
        </button>
      ))}
    </div>
  );
};

// ============================================================
// Notification Toast
// ============================================================

interface ToastProps {
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  const colors = {
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    error: 'bg-red-100 text-red-800 border-red-200',
  };

  return (
    <div
      className={`fixed bottom-4 right-4 px-4 py-3 rounded-lg border shadow-lg ${colors[type]} animate-slide-up`}
    >
      <div className="flex items-center gap-3">
        <span>{message}</span>
        <button onClick={onClose} className="text-current opacity-70 hover:opacity-100">
          ✕
        </button>
      </div>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const TrainerWorkbench: React.FC<TrainerWorkbenchProps> = ({
  tenantId,
  buildingId,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [selectedActivity, setSelectedActivity] = useState<AgentActivity | null>(null);
  const [showFeedbackPanel, setShowFeedbackPanel] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [toast, setToast] = useState<{ message: string; type: ToastProps['type'] } | null>(null);

  // Handle activity requiring attention
  const handleActionRequired = useCallback((activity: AgentActivity) => {
    setToast({
      message: `需要关注: ${activity.title}`,
      type: 'warning',
    });
    // Auto dismiss after 5 seconds
    setTimeout(() => setToast(null), 5000);
  }, []);

  // Handle activity click
  const handleActivityClick = useCallback((activity: AgentActivity) => {
    setSelectedActivity(activity);
  }, []);

  // Handle pending item resolved
  const handleItemResolved = useCallback((item: PendingItem, _action: string) => {
    setToast({
      message: `已处理: ${item.title}`,
      type: 'success',
    });
    setPendingCount((prev) => Math.max(0, prev - 1));
    setTimeout(() => setToast(null), 3000);
  }, []);

  // Handle feedback submitted
  const handleFeedbackSubmitted = useCallback((feedbackType: string) => {
    setToast({
      message: `反馈已提交: ${feedbackType}`,
      type: 'success',
    });
    setShowFeedbackPanel(false);
    setSelectedActivity(null);
    setTimeout(() => setToast(null), 3000);
  }, []);

  // Handle robot selection
  const handleRobotSelect = useCallback((robot: Robot) => {
    console.log('Robot selected:', robot.robotId);
  }, []);

  // Open feedback panel for selected activity
  const handleOpenFeedback = useCallback(() => {
    if (selectedActivity) {
      setShowFeedbackPanel(true);
    }
  }, [selectedActivity]);

  // Render content based on view mode
  const renderContent = () => {
    switch (viewMode) {
      case 'activities':
        return (
          <div className="h-full p-4">
            <ActivityFeed
              tenantId={tenantId}
              onActivityClick={handleActivityClick}
              onActionRequired={handleActionRequired}
            />
          </div>
        );

      case 'pending':
        return (
          <div className="h-full p-4">
            <PendingQueue
              tenantId={tenantId}
              onItemResolved={handleItemResolved}
            />
          </div>
        );

      case 'map':
        return (
          <div className="h-full p-4">
            <RobotMap
              buildingId={buildingId}
              onRobotSelect={handleRobotSelect}
            />
          </div>
        );

      case 'split':
      default:
        return (
          <div className="h-full grid grid-cols-2 grid-rows-2 gap-4 p-4">
            {/* Top Left: Activity Feed */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <ActivityFeed
                tenantId={tenantId}
                pageSize={10}
                onActivityClick={handleActivityClick}
                onActionRequired={handleActionRequired}
              />
            </div>

            {/* Top Right: Pending Queue */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <PendingQueue
                tenantId={tenantId}
                onItemResolved={handleItemResolved}
              />
            </div>

            {/* Bottom: Robot Map (spans full width) */}
            <div className="col-span-2 bg-white rounded-lg shadow overflow-hidden">
              <RobotMap
                buildingId={buildingId}
                onRobotSelect={handleRobotSelect}
              />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold text-gray-900">训练工作台</h1>
            <span className="text-sm text-gray-500">
              租户: {tenantId}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <ViewModeSelector mode={viewMode} onChange={setViewMode} />

            {/* Quick stats */}
            <div className="flex items-center gap-3 text-sm">
              {pendingCount > 0 && (
                <span className="px-2 py-1 bg-red-100 text-red-700 rounded">
                  {pendingCount} 待处理
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {renderContent()}
      </main>

      {/* Activity Detail Sidebar */}
      {selectedActivity && !showFeedbackPanel && (
        <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-xl border-l z-40">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="font-semibold">活动详情</h3>
            <button
              onClick={() => setSelectedActivity(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="p-4 space-y-4">
            <div>
              <span className="text-xs text-gray-500">标题</span>
              <p className="font-medium">{selectedActivity.title}</p>
            </div>

            <div>
              <span className="text-xs text-gray-500">描述</span>
              <p className="text-sm text-gray-700">{selectedActivity.description}</p>
            </div>

            <div>
              <span className="text-xs text-gray-500">Agent类型</span>
              <p className="text-sm">{selectedActivity.agentType}</p>
            </div>

            <div>
              <span className="text-xs text-gray-500">级别</span>
              <p className="text-sm">{selectedActivity.level}</p>
            </div>

            <div>
              <span className="text-xs text-gray-500">时间</span>
              <p className="text-sm">
                {new Date(selectedActivity.timestamp).toLocaleString('zh-CN')}
              </p>
            </div>

            {selectedActivity.details && (
              <div>
                <span className="text-xs text-gray-500">详细信息</span>
                <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto max-h-48">
                  {JSON.stringify(selectedActivity.details, null, 2)}
                </pre>
              </div>
            )}

            {/* Actions */}
            {selectedActivity.activityType === 'decision' && (
              <div className="pt-4 border-t flex gap-2">
                <button
                  onClick={handleOpenFeedback}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  提供反馈
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Feedback Panel Modal */}
      {showFeedbackPanel && selectedActivity && (
        <FeedbackPanel
          activity={selectedActivity}
          onClose={() => {
            setShowFeedbackPanel(false);
            setSelectedActivity(null);
          }}
          onSubmitted={handleFeedbackSubmitted}
        />
      )}

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default TrainerWorkbench;
