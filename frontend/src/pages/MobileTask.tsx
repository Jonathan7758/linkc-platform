/**
 * P2 Mobile Task - Mobile-First Task Management
 * 移动端任务页面
 */

import React, { useState, useCallback } from 'react';

// ============ Type Definitions ============

type TaskStatus = 'pending' | 'in_progress' | 'paused' | 'completed' | 'failed' | 'cancelled';
type TaskType = 'routine' | 'deep' | 'spot' | 'emergency';
type TaskPriority = 'high' | 'normal' | 'low';
type TabKey = 'today' | 'active' | 'scheduled' | 'completed' | 'failed';

interface TaskSummary {
  id: string;
  name: string;
  type: TaskType;
  status: TaskStatus;
  priority: TaskPriority;
  location: {
    building: string;
    floor?: string;
    zone?: string;
  };
  scheduledTime: string;
  startTime?: string;
  progress: number;
  robots: {
    total: number;
    active: number;
    names: string[];
  };
  hasAlert: boolean;
}

interface TaskDetail extends TaskSummary {
  description?: string;
  config: {
    cleaningMode: string;
    intensity: string;
  };
  execution: {
    totalArea: number;
    cleanedArea: number;
    coverageRate: number;
    estimatedCompletion?: string;
  };
  timeline: TimelineEvent[];
  createdBy: string;
  createdAt: string;
}

interface TimelineEvent {
  id: string;
  type: string;
  message: string;
  timestamp: string;
}

interface CreateTaskData {
  building: string;
  floor?: string;
  zone?: string;
  type: TaskType;
  priority: TaskPriority;
  scheduledTime: 'now' | 'scheduled';
  notes?: string;
}

interface MobileTaskProps {
  tenantId: string;
  onBack?: () => void;
}

// ============ Mock Data ============

const mockTasks: TaskSummary[] = [
  {
    id: 'T-001', name: 'A栋大堂清洁', type: 'routine', status: 'in_progress', priority: 'high',
    location: { building: 'A栋', floor: '1F', zone: '大堂' },
    scheduledTime: '08:00', startTime: '08:05', progress: 65,
    robots: { total: 2, active: 2, names: ['R-001', 'R-002'] }, hasAlert: false
  },
  {
    id: 'T-002', name: 'B栋走廊清洁', type: 'routine', status: 'in_progress', priority: 'normal',
    location: { building: 'B栋', floor: '1-3F', zone: '走廊' },
    scheduledTime: '08:30', startTime: '08:35', progress: 42,
    robots: { total: 3, active: 2, names: ['R-003', 'R-004', 'R-005'] }, hasAlert: true
  },
  {
    id: 'T-003', name: 'C栋会议室深度清洁', type: 'deep', status: 'paused', priority: 'normal',
    location: { building: 'C栋', floor: '5F', zone: '会议室' },
    scheduledTime: '09:00', startTime: '09:05', progress: 28,
    robots: { total: 1, active: 0, names: ['R-006'] }, hasAlert: true
  },
  {
    id: 'T-004', name: 'D栋办公区清洁', type: 'routine', status: 'pending', priority: 'low',
    location: { building: 'D栋', floor: '2F', zone: '办公区' },
    scheduledTime: '10:00', progress: 0,
    robots: { total: 2, active: 0, names: ['R-007', 'R-008'] }, hasAlert: false
  },
  {
    id: 'T-005', name: 'A栋卫生间清洁', type: 'routine', status: 'completed', priority: 'high',
    location: { building: 'A栋', floor: '1-5F', zone: '卫生间' },
    scheduledTime: '07:00', startTime: '07:00', progress: 100,
    robots: { total: 2, active: 0, names: ['R-009', 'R-010'] }, hasAlert: false
  },
  {
    id: 'T-006', name: 'B栋地下车库清洁', type: 'routine', status: 'completed', priority: 'normal',
    location: { building: 'B栋', floor: 'B1', zone: '停车场' },
    scheduledTime: '06:00', startTime: '06:00', progress: 100,
    robots: { total: 1, active: 0, names: ['R-011'] }, hasAlert: false
  },
  {
    id: 'T-007', name: 'C栋紧急清洁', type: 'emergency', status: 'failed', priority: 'high',
    location: { building: 'C栋', floor: '3F', zone: '茶水间' },
    scheduledTime: '11:00', startTime: '11:05', progress: 15,
    robots: { total: 1, active: 0, names: ['R-012'] }, hasAlert: true
  },
];

const mockTaskDetail: TaskDetail = {
  ...mockTasks[0],
  description: '每日例行大堂清洁任务，包括地面清洁、垃圾收集',
  config: { cleaningMode: '标准模式', intensity: '中等' },
  execution: {
    totalArea: 500,
    cleanedArea: 325,
    coverageRate: 94.2,
    estimatedCompletion: '09:15',
  },
  timeline: [
    { id: '1', type: 'start', message: '任务开始执行', timestamp: '08:05' },
    { id: '2', type: 'robot', message: 'R-001 开始清洁A区', timestamp: '08:06' },
    { id: '3', type: 'robot', message: 'R-002 开始清洁B区', timestamp: '08:06' },
    { id: '4', type: 'progress', message: '完成50%', timestamp: '08:35' },
    { id: '5', type: 'progress', message: '完成65%', timestamp: '08:50' },
  ],
  createdBy: '系统自动',
  createdAt: '2026-01-21 07:00',
};

// ============ Sub Components ============

// Status Badge
const TaskStatusBadge: React.FC<{ status: TaskStatus }> = ({ status }) => {
  const config: Record<TaskStatus, { bg: string; text: string; label: string }> = {
    pending: { bg: 'bg-gray-100', text: 'text-gray-700', label: '待执行' },
    in_progress: { bg: 'bg-blue-100', text: 'text-blue-700', label: '进行中' },
    paused: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '已暂停' },
    completed: { bg: 'bg-green-100', text: 'text-green-700', label: '已完成' },
    failed: { bg: 'bg-red-100', text: 'text-red-700', label: '失败' },
    cancelled: { bg: 'bg-gray-100', text: 'text-gray-500', label: '已取消' },
  };
  const { bg, text, label } = config[status];
  return <span className={`px-2 py-0.5 text-xs rounded-full ${bg} ${text}`}>{label}</span>;
};

// Priority Badge
const PriorityBadge: React.FC<{ priority: TaskPriority }> = ({ priority }) => {
  const config: Record<TaskPriority, { color: string; label: string }> = {
    high: { color: 'text-red-500', label: '⬆️ 高' },
    normal: { color: 'text-gray-500', label: '➡️ 中' },
    low: { color: 'text-green-500', label: '⬇️ 低' },
  };
  return <span className={`text-xs ${config[priority].color}`}>{config[priority].label}</span>;
};

// Type Badge
const TypeBadge: React.FC<{ type: TaskType }> = ({ type }) => {
  const labels: Record<TaskType, string> = {
    routine: '日常',
    deep: '深度',
    spot: '定点',
    emergency: '紧急',
  };
  return <span className="text-xs text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded">{labels[type]}</span>;
};

// Progress Bar
const ProgressBar: React.FC<{ progress: number; status: TaskStatus }> = ({ progress, status }) => {
  const getColor = () => {
    if (status === 'completed') return 'bg-green-500';
    if (status === 'failed') return 'bg-red-500';
    if (status === 'paused') return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${getColor()} transition-all`} style={{ width: `${progress}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-10 text-right">{progress}%</span>
    </div>
  );
};

// Task Card
const TaskCard: React.FC<{ task: TaskSummary; onClick: () => void }> = ({ task, onClick }) => (
  <div
    onClick={onClick}
    className={`bg-white rounded-lg p-4 shadow-sm active:bg-gray-50 ${
      task.hasAlert ? 'border-l-4 border-red-500' : ''
    }`}
  >
    <div className="flex items-start justify-between mb-2">
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2 mb-1">
          <span className="font-medium text-gray-900 truncate">{task.name}</span>
          {task.hasAlert && <span className="text-red-500">⚠️</span>}
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <TypeBadge type={task.type} />
          <PriorityBadge priority={task.priority} />
        </div>
      </div>
      <TaskStatusBadge status={task.status} />
    </div>

    <div className="text-sm text-gray-500 mb-2">
      📍 {task.location.building} {task.location.floor} {task.location.zone}
    </div>

    <ProgressBar progress={task.progress} status={task.status} />

    <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
      <span>
        🤖 {task.robots.active}/{task.robots.total} · {task.robots.names.slice(0, 2).join(', ')}
        {task.robots.names.length > 2 && '...'}
      </span>
      <span>⏰ {task.startTime || task.scheduledTime}</span>
    </div>
  </div>
);

// Task Detail Panel
const TaskDetailPanel: React.FC<{
  task: TaskDetail;
  onClose: () => void;
  onAction: (action: string) => void;
}> = ({ task, onClose, onAction }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
    <div className="bg-white w-full rounded-t-2xl max-h-[90vh] overflow-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-100 p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <span className="font-bold text-gray-900">{task.name}</span>
              {task.hasAlert && <span className="text-red-500">⚠️</span>}
            </div>
            <div className="flex items-center space-x-2">
              <TaskStatusBadge status={task.status} />
              <TypeBadge type={task.type} />
              <PriorityBadge priority={task.priority} />
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-gray-400">✕</button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Progress */}
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-blue-700">执行进度</span>
            <span className="text-lg font-bold text-blue-900">{task.progress}%</span>
          </div>
          <ProgressBar progress={task.progress} status={task.status} />
          <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
            <div>
              <div className="text-blue-900 font-medium">{task.execution.cleanedArea}㎡</div>
              <div className="text-blue-600">已清洁</div>
            </div>
            <div>
              <div className="text-blue-900 font-medium">{task.execution.totalArea}㎡</div>
              <div className="text-blue-600">总面积</div>
            </div>
            <div>
              <div className="text-blue-900 font-medium">{task.execution.coverageRate}%</div>
              <div className="text-blue-600">覆盖率</div>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="bg-white rounded-lg border border-gray-100">
          <div className="p-3 border-b border-gray-50">
            <div className="text-xs text-gray-500">位置</div>
            <div className="text-sm font-medium">{task.location.building} {task.location.floor} {task.location.zone}</div>
          </div>
          <div className="p-3 border-b border-gray-50">
            <div className="text-xs text-gray-500">配置</div>
            <div className="text-sm font-medium">{task.config.cleaningMode} · {task.config.intensity}</div>
          </div>
          <div className="p-3">
            <div className="text-xs text-gray-500">机器人</div>
            <div className="text-sm font-medium">{task.robots.names.join(', ')}</div>
          </div>
        </div>

        {/* Timeline */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">执行时间线</h4>
          <div className="space-y-2">
            {task.timeline.map((event, index) => (
              <div key={event.id} className="flex items-start space-x-3">
                <div className={`w-2 h-2 rounded-full mt-1.5 ${
                  index === task.timeline.length - 1 ? 'bg-blue-500' : 'bg-gray-300'
                }`} />
                <div className="flex-1">
                  <div className="text-sm text-gray-700">{event.message}</div>
                  <div className="text-xs text-gray-400">{event.timestamp}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        {(task.status === 'in_progress' || task.status === 'paused' || task.status === 'pending') && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">任务操作</h4>
            <div className="grid grid-cols-2 gap-2">
              {task.status === 'in_progress' && (
                <>
                  <button
                    onClick={() => onAction('pause')}
                    className="py-3 bg-yellow-500 text-white rounded-lg text-sm font-medium"
                  >
                    ⏸ 暂停
                  </button>
                  <button
                    onClick={() => onAction('cancel')}
                    className="py-3 bg-red-500 text-white rounded-lg text-sm font-medium"
                  >
                    ✕ 取消
                  </button>
                </>
              )}
              {task.status === 'paused' && (
                <>
                  <button
                    onClick={() => onAction('resume')}
                    className="py-3 bg-green-500 text-white rounded-lg text-sm font-medium"
                  >
                    ▶️ 恢复
                  </button>
                  <button
                    onClick={() => onAction('cancel')}
                    className="py-3 bg-red-500 text-white rounded-lg text-sm font-medium"
                  >
                    ✕ 取消
                  </button>
                </>
              )}
              {task.status === 'pending' && (
                <>
                  <button
                    onClick={() => onAction('start')}
                    className="py-3 bg-green-500 text-white rounded-lg text-sm font-medium"
                  >
                    ▶️ 立即执行
                  </button>
                  <button
                    onClick={() => onAction('cancel')}
                    className="py-3 bg-gray-500 text-white rounded-lg text-sm font-medium"
                  >
                    ✕ 取消
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  </div>
);

// Create Task Panel
const CreateTaskPanel: React.FC<{
  onClose: () => void;
  onCreate: (data: CreateTaskData) => void;
}> = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState<CreateTaskData>({
    building: '',
    type: 'spot',
    priority: 'normal',
    scheduledTime: 'now',
  });

  const handleSubmit = () => {
    if (!formData.building) {
      alert('请选择清洁位置');
      return;
    }
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
      <div className="bg-white w-full rounded-t-2xl max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
          <h2 className="font-bold text-gray-900">快速创建任务</h2>
          <button onClick={onClose} className="p-2 text-gray-400">✕</button>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4">
          {/* Building Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">清洁位置 *</label>
            <div className="grid grid-cols-2 gap-2">
              {['A栋', 'B栋', 'C栋', 'D栋'].map(building => (
                <button
                  key={building}
                  onClick={() => setFormData(prev => ({ ...prev, building }))}
                  className={`py-3 rounded-lg text-sm font-medium ${
                    formData.building === building
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {building}
                </button>
              ))}
            </div>
          </div>

          {/* Floor Selection */}
          {formData.building && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">楼层</label>
              <div className="flex flex-wrap gap-2">
                {['1F', '2F', '3F', '4F', '5F', 'B1'].map(floor => (
                  <button
                    key={floor}
                    onClick={() => setFormData(prev => ({ ...prev, floor }))}
                    className={`px-4 py-2 rounded-lg text-sm ${
                      formData.floor === floor
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {floor}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Task Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">任务类型</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { key: 'spot', label: '定点清洁', desc: '指定区域清洁' },
                { key: 'emergency', label: '紧急清洁', desc: '突发情况处理' },
              ].map(type => (
                <button
                  key={type.key}
                  onClick={() => setFormData(prev => ({ ...prev, type: type.key as TaskType }))}
                  className={`p-3 rounded-lg text-left ${
                    formData.type === type.key
                      ? 'bg-blue-50 border-2 border-blue-600'
                      : 'bg-gray-50 border-2 border-transparent'
                  }`}
                >
                  <div className="text-sm font-medium">{type.label}</div>
                  <div className="text-xs text-gray-500">{type.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">优先级</label>
            <div className="flex space-x-2">
              {[
                { key: 'high', label: '高', color: 'red' },
                { key: 'normal', label: '中', color: 'gray' },
                { key: 'low', label: '低', color: 'green' },
              ].map(p => (
                <button
                  key={p.key}
                  onClick={() => setFormData(prev => ({ ...prev, priority: p.key as TaskPriority }))}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium ${
                    formData.priority === p.key
                      ? p.color === 'red' ? 'bg-red-500 text-white' :
                        p.color === 'green' ? 'bg-green-500 text-white' : 'bg-gray-500 text-white'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Schedule */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">执行时间</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setFormData(prev => ({ ...prev, scheduledTime: 'now' }))}
                className={`py-3 rounded-lg text-sm font-medium ${
                  formData.scheduledTime === 'now'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                立即执行
              </button>
              <button
                onClick={() => setFormData(prev => ({ ...prev, scheduledTime: 'scheduled' }))}
                className={`py-3 rounded-lg text-sm font-medium ${
                  formData.scheduledTime === 'scheduled'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                定时执行
              </button>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">备注</label>
            <textarea
              value={formData.notes || ''}
              onChange={e => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="可选：添加任务说明..."
              className="w-full p-3 border border-gray-200 rounded-lg text-sm"
              rows={3}
            />
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            className="w-full py-4 bg-blue-600 text-white rounded-lg text-sm font-medium"
          >
            创建任务
          </button>
        </div>
      </div>
    </div>
  );
};

// ============ Main Component ============

export const MobileTask: React.FC<MobileTaskProps> = ({ tenantId: _tenantId, onBack }) => {
  // State
  const [activeTab, setActiveTab] = useState<TabKey>('today');
  const [tasks, setTasks] = useState<TaskSummary[]>(mockTasks);
  const [selectedTask, setSelectedTask] = useState<TaskDetail | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // Filter tasks by tab
  const getFilteredTasks = useCallback(() => {
    switch (activeTab) {
      case 'today':
        return tasks;
      case 'active':
        return tasks.filter(t => t.status === 'in_progress' || t.status === 'paused');
      case 'scheduled':
        return tasks.filter(t => t.status === 'pending');
      case 'completed':
        return tasks.filter(t => t.status === 'completed');
      case 'failed':
        return tasks.filter(t => t.status === 'failed' || t.status === 'cancelled');
      default:
        return tasks;
    }
  }, [activeTab, tasks]);

  // Tab config
  const tabs: { key: TabKey; label: string; badge?: number }[] = [
    { key: 'today', label: '今日' },
    { key: 'active', label: '进行中', badge: tasks.filter(t => t.status === 'in_progress' || t.status === 'paused').length },
    { key: 'scheduled', label: '待执行' },
    { key: 'completed', label: '已完成' },
    { key: 'failed', label: '异常', badge: tasks.filter(t => t.status === 'failed').length },
  ];

  // Handlers
  const handleTaskClick = (task: TaskSummary) => {
    // In production, fetch full detail from API
    setSelectedTask({ ...mockTaskDetail, ...task });
  };

  const handleTaskAction = (action: string) => {
    console.log('Task action:', selectedTask?.id, action);
    alert(`执行操作: ${action}`);
    setSelectedTask(null);
  };

  const handleCreateTask = (data: CreateTaskData) => {
    console.log('Create task:', data);
    const newTask: TaskSummary = {
      id: `T-${Date.now()}`,
      name: `${data.building}${data.floor || ''} ${data.type === 'emergency' ? '紧急' : '定点'}清洁`,
      type: data.type,
      status: data.scheduledTime === 'now' ? 'in_progress' : 'pending',
      priority: data.priority,
      location: { building: data.building, floor: data.floor, zone: data.zone },
      scheduledTime: data.scheduledTime === 'now' ? '立即' : '待定',
      progress: 0,
      robots: { total: 1, active: data.scheduledTime === 'now' ? 1 : 0, names: ['待分配'] },
      hasAlert: false,
    };
    setTasks(prev => [newTask, ...prev]);
    setShowCreate(false);
    alert('任务创建成功');
  };

  const filteredTasks = getFilteredTasks();

  // Summary stats
  const todayStats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    inProgress: tasks.filter(t => t.status === 'in_progress').length,
    alerts: tasks.filter(t => t.hasAlert).length,
  };

  return (
    <div className="min-h-screen bg-gray-100 pb-4">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3 flex items-center justify-between">
          {onBack && (
            <button onClick={onBack} className="p-2 -ml-2 text-gray-500">←</button>
          )}
          <h1 className="text-lg font-bold text-gray-900 flex-1 text-center">任务管理</h1>
          <button
            onClick={() => setShowCreate(true)}
            className="p-2 -mr-2 text-blue-600"
          >
            +
          </button>
        </div>

        {/* Today Summary */}
        <div className="px-4 pb-3">
          <div className="bg-blue-50 rounded-lg p-3 flex justify-around">
            <div className="text-center">
              <div className="text-xl font-bold text-blue-900">{todayStats.completed}/{todayStats.total}</div>
              <div className="text-xs text-blue-600">完成/总数</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-900">{todayStats.inProgress}</div>
              <div className="text-xs text-blue-600">进行中</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-red-600">{todayStats.alerts}</div>
              <div className="text-xs text-red-500">需关注</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex overflow-x-auto border-t border-gray-100">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-shrink-0 px-4 py-3 text-sm font-medium relative ${
                activeTab === tab.key
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500'
              }`}
            >
              {tab.label}
              {tab.badge && tab.badge > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Task List */}
      <div className="p-4 space-y-3">
        {filteredTasks.length > 0 ? (
          filteredTasks.map(task => (
            <TaskCard key={task.id} task={task} onClick={() => handleTaskClick(task)} />
          ))
        ) : (
          <div className="text-center py-12 text-gray-500">
            暂无任务
          </div>
        )}
      </div>

      {/* Floating Action Button */}
      <button
        onClick={() => setShowCreate(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center text-2xl"
      >
        +
      </button>

      {/* Task Detail Panel */}
      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onAction={handleTaskAction}
        />
      )}

      {/* Create Task Panel */}
      {showCreate && (
        <CreateTaskPanel
          onClose={() => setShowCreate(false)}
          onCreate={handleCreateTask}
        />
      )}
    </div>
  );
};

export default MobileTask;
