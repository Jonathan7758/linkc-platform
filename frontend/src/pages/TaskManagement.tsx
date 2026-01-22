/**
 * O2: Task Management Interface
 * 任务管理界面 - 清洁任务的全生命周期管理
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============================================================
// Types
// ============================================================

type TaskStatus = 'pending' | 'assigned' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
type TaskType = 'daily' | 'deep' | 'spot' | 'emergency';
type TabType = 'today' | 'schedules' | 'templates' | 'history';

interface Task {
  taskId: string;
  name: string;
  zoneId: string;
  zoneName: string;
  type: TaskType;
  status: TaskStatus;
  robotId?: string;
  robotName?: string;
  scheduledTime: string;
  startTime?: string;
  endTime?: string;
  progress: number;
  priority: number;
  estimatedDuration: number;
  actualDuration?: number;
}

interface Schedule {
  scheduleId: string;
  name: string;
  zoneName: string;
  frequency: string;
  time: string;
  enabled: boolean;
  nextRun?: string;
  lastRun?: string;
}

interface TaskStats {
  pending: number;
  inProgress: number;
  completed: number;
  failed: number;
  cancelled: number;
}

interface TaskManagementProps {
  tenantId: string;
  onTaskClick?: (taskId: string) => void;
}

// ============================================================
// Mock Data
// ============================================================

const mockTasks: Task[] = [
  {
    taskId: 'T-001',
    name: 'A栋1F大堂清洁',
    zoneId: 'zone_001',
    zoneName: 'A栋1F大堂',
    type: 'daily',
    status: 'in_progress',
    robotId: 'robot_001',
    robotName: 'GX-001',
    scheduledTime: '08:00',
    startTime: '08:02',
    progress: 65,
    priority: 1,
    estimatedDuration: 45,
  },
  {
    taskId: 'T-002',
    name: 'A栋2F走廊清洁',
    zoneId: 'zone_002',
    zoneName: 'A栋2F走廊',
    type: 'daily',
    status: 'pending',
    scheduledTime: '09:00',
    progress: 0,
    priority: 2,
    estimatedDuration: 30,
  },
  {
    taskId: 'T-003',
    name: 'B栋1F大堂清洁',
    zoneId: 'zone_003',
    zoneName: 'B栋1F大堂',
    type: 'spot',
    status: 'failed',
    robotId: 'robot_003',
    robotName: 'GX-003',
    scheduledTime: '08:30',
    startTime: '08:32',
    progress: 40,
    priority: 1,
    estimatedDuration: 40,
  },
  {
    taskId: 'T-004',
    name: 'A栋3F办公区深度清洁',
    zoneId: 'zone_004',
    zoneName: 'A栋3F办公区',
    type: 'deep',
    status: 'completed',
    robotId: 'robot_002',
    robotName: 'EC-001',
    scheduledTime: '07:00',
    startTime: '07:00',
    endTime: '08:15',
    progress: 100,
    priority: 3,
    estimatedDuration: 75,
    actualDuration: 75,
  },
];

const mockSchedules: Schedule[] = [
  {
    scheduleId: 'S-001',
    name: '每日大堂清洁',
    zoneName: 'A栋1F大堂',
    frequency: '每日',
    time: '08:00',
    enabled: true,
    nextRun: '明天 08:00',
    lastRun: '今天 08:00',
  },
  {
    scheduleId: 'S-002',
    name: '周末深度清洁',
    zoneName: 'A栋全楼',
    frequency: '每周六',
    time: '06:00',
    enabled: true,
    nextRun: '周六 06:00',
    lastRun: '上周六 06:00',
  },
  {
    scheduleId: 'S-003',
    name: 'B栋走廊清洁',
    zoneName: 'B栋走廊',
    frequency: '每日',
    time: '09:00',
    enabled: false,
    lastRun: '3天前 09:00',
  },
];

const mockStats: TaskStats = {
  pending: 12,
  inProgress: 5,
  completed: 28,
  failed: 2,
  cancelled: 1,
};

// ============================================================
// Helper Functions
// ============================================================

const getStatusConfig = (status: TaskStatus) => {
  const configs = {
    pending: { label: '待执行', color: 'bg-gray-100 text-gray-800', icon: '⏳' },
    assigned: { label: '已分配', color: 'bg-blue-100 text-blue-800', icon: '📋' },
    in_progress: { label: '执行中', color: 'bg-green-100 text-green-800', icon: '🔄' },
    completed: { label: '已完成', color: 'bg-emerald-100 text-emerald-800', icon: '✅' },
    failed: { label: '异常', color: 'bg-red-100 text-red-800', icon: '⚠️' },
    cancelled: { label: '已取消', color: 'bg-gray-100 text-gray-500', icon: '🚫' },
  };
  return configs[status];
};

const getTypeLabel = (type: TaskType) => {
  const labels = {
    daily: '日常',
    deep: '深度',
    spot: '临时',
    emergency: '紧急',
  };
  return labels[type];
};

// ============================================================
// Task Stats Bar Component
// ============================================================

interface TaskStatsBarProps {
  stats: TaskStats;
}

const TaskStatsBar: React.FC<TaskStatsBarProps> = ({ stats }) => {
  const items = [
    { key: 'pending', label: '待执行', value: stats.pending, color: 'text-gray-600' },
    { key: 'inProgress', label: '执行中', value: stats.inProgress, color: 'text-green-600' },
    { key: 'completed', label: '已完成', value: stats.completed, color: 'text-emerald-600' },
    { key: 'failed', label: '异常', value: stats.failed, color: 'text-red-600' },
    { key: 'cancelled', label: '取消', value: stats.cancelled, color: 'text-gray-400' },
  ];

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-gray-50 rounded-lg text-sm">
      {items.map(item => (
        <span key={item.key} className={item.color}>
          {item.label}: <span className="font-medium">{item.value}</span>
        </span>
      ))}
    </div>
  );
};

// ============================================================
// Task Filter Component
// ============================================================

interface TaskFilterProps {
  statusFilter: string;
  typeFilter: string;
  searchQuery: string;
  onStatusChange: (value: string) => void;
  onTypeChange: (value: string) => void;
  onSearchChange: (value: string) => void;
}

const TaskFilter: React.FC<TaskFilterProps> = ({
  statusFilter,
  typeFilter,
  searchQuery,
  onStatusChange,
  onTypeChange,
  onSearchChange,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={statusFilter}
        onChange={(e) => onStatusChange(e.target.value)}
        className="px-3 py-2 border rounded-lg text-sm"
      >
        <option value="">全部状态</option>
        <option value="pending">待执行</option>
        <option value="in_progress">执行中</option>
        <option value="completed">已完成</option>
        <option value="failed">异常</option>
        <option value="cancelled">已取消</option>
      </select>

      <select
        value={typeFilter}
        onChange={(e) => onTypeChange(e.target.value)}
        className="px-3 py-2 border rounded-lg text-sm"
      >
        <option value="">全部类型</option>
        <option value="daily">日常清洁</option>
        <option value="deep">深度清洁</option>
        <option value="spot">临时清洁</option>
        <option value="emergency">紧急清洁</option>
      </select>

      <input
        type="text"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="搜索任务..."
        className="px-3 py-2 border rounded-lg text-sm w-48"
      />
    </div>
  );
};

// ============================================================
// Task Table Component
// ============================================================

interface TaskTableProps {
  tasks: Task[];
  selectedTasks: string[];
  onSelectTask: (taskId: string) => void;
  onSelectAll: () => void;
  onTaskClick: (taskId: string) => void;
  onTaskAction: (taskId: string, action: string) => void;
}

const TaskTable: React.FC<TaskTableProps> = ({
  tasks,
  selectedTasks,
  onSelectTask,
  onSelectAll,
  onTaskClick,
  onTaskAction,
}) => {
  const [openMenu, setOpenMenu] = useState<string | null>(null);

  const allSelected = tasks.length > 0 && selectedTasks.length === tasks.length;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-y">
          <tr>
            <th className="px-4 py-3 text-left">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onSelectAll}
                className="rounded"
              />
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">任务ID</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">区域</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">类型</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">状态</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">机器人</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">计划时间</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">进度</th>
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">操作</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => {
            const statusConfig = getStatusConfig(task.status);
            return (
              <tr
                key={task.taskId}
                className="border-b hover:bg-gray-50 cursor-pointer"
                onClick={() => onTaskClick(task.taskId)}
              >
                <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selectedTasks.includes(task.taskId)}
                    onChange={() => onSelectTask(task.taskId)}
                    className="rounded"
                  />
                </td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {task.taskId}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {task.zoneName}
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                    {getTypeLabel(task.type)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs rounded ${statusConfig.color}`}>
                    {statusConfig.icon} {statusConfig.label}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {task.robotName || '--'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {task.scheduledTime}
                </td>
                <td className="px-4 py-3">
                  {task.status === 'pending' ? (
                    <span className="text-gray-400">--</span>
                  ) : (
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            task.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{task.progress}%</span>
                    </div>
                  )}
                </td>
                <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                  <div className="relative">
                    <button
                      onClick={() => setOpenMenu(openMenu === task.taskId ? null : task.taskId)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      ⋮
                    </button>
                    {openMenu === task.taskId && (
                      <div className="absolute right-0 mt-1 w-32 bg-white border rounded-lg shadow-lg z-10">
                        <button
                          onClick={() => {
                            onTaskAction(task.taskId, 'view');
                            setOpenMenu(null);
                          }}
                          className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50"
                        >
                          查看详情
                        </button>
                        {task.status === 'in_progress' && (
                          <button
                            onClick={() => {
                              onTaskAction(task.taskId, 'pause');
                              setOpenMenu(null);
                            }}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50"
                          >
                            暂停任务
                          </button>
                        )}
                        {task.status === 'pending' && (
                          <button
                            onClick={() => {
                              onTaskAction(task.taskId, 'cancel');
                              setOpenMenu(null);
                            }}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 text-red-600"
                          >
                            取消任务
                          </button>
                        )}
                        {task.status === 'failed' && (
                          <button
                            onClick={() => {
                              onTaskAction(task.taskId, 'retry');
                              setOpenMenu(null);
                            }}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50"
                          >
                            重试任务
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {tasks.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          暂无任务数据
        </div>
      )}
    </div>
  );
};

// ============================================================
// Schedule List Component
// ============================================================

interface ScheduleListProps {
  schedules: Schedule[];
  onToggle: (scheduleId: string) => void;
  onEdit: (scheduleId: string) => void;
  onDelete: (scheduleId: string) => void;
}

const ScheduleList: React.FC<ScheduleListProps> = ({
  schedules,
  onToggle,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="space-y-3">
      {schedules.map((schedule) => (
        <div
          key={schedule.scheduleId}
          className={`p-4 border rounded-lg ${schedule.enabled ? 'bg-white' : 'bg-gray-50'}`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => onToggle(schedule.scheduleId)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  schedule.enabled ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    schedule.enabled ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
              <div>
                <h4 className="font-medium text-gray-900">{schedule.name}</h4>
                <p className="text-sm text-gray-500">{schedule.zoneName}</p>
              </div>
            </div>

            <div className="flex items-center gap-6 text-sm">
              <div className="text-gray-600">
                <span className="font-medium">{schedule.frequency}</span>
                <span className="mx-2">·</span>
                <span>{schedule.time}</span>
              </div>
              <div className="text-gray-400">
                {schedule.nextRun ? `下次: ${schedule.nextRun}` : '已暂停'}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => onEdit(schedule.scheduleId)}
                  className="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded"
                >
                  编辑
                </button>
                <button
                  onClick={() => onDelete(schedule.scheduleId)}
                  className="px-3 py-1 text-red-600 hover:bg-red-50 rounded"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}

      {schedules.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          暂无排程配置
        </div>
      )}
    </div>
  );
};

// ============================================================
// Create Task Modal Component
// ============================================================

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (task: Partial<Task>) => void;
}

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  onCreate,
}) => {
  const [formData, setFormData] = useState({
    zoneName: '',
    type: 'daily' as TaskType,
    scheduledTime: '',
    priority: 2,
  });

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate(formData);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h3 className="text-lg font-semibold">新建任务</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              清洁区域
            </label>
            <select
              value={formData.zoneName}
              onChange={(e) => setFormData({ ...formData, zoneName: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              required
            >
              <option value="">选择区域</option>
              <option value="A栋1F大堂">A栋1F大堂</option>
              <option value="A栋2F走廊">A栋2F走廊</option>
              <option value="B栋1F大堂">B栋1F大堂</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              任务类型
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as TaskType })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="daily">日常清洁</option>
              <option value="deep">深度清洁</option>
              <option value="spot">临时清洁</option>
              <option value="emergency">紧急清洁</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              计划时间
            </label>
            <input
              type="time"
              value={formData.scheduledTime}
              onChange={(e) => setFormData({ ...formData, scheduledTime: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              优先级
            </label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: Number(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value={1}>高</option>
              <option value={2}>中</option>
              <option value={3}>低</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              创建任务
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const TaskManagement: React.FC<TaskManagementProps> = ({
  tenantId,
  onTaskClick,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('today');
  const [tasks, _setTasks] = useState<Task[]>(mockTasks);
  const [schedules, setSchedules] = useState<Schedule[]>(mockSchedules);
  const [stats, _setStats] = useState<TaskStats>(mockStats);
  const [loading, setLoading] = useState(false);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API calls
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filter tasks
  const filteredTasks = tasks.filter(task => {
    if (statusFilter && task.status !== statusFilter) return false;
    if (typeFilter && task.type !== typeFilter) return false;
    if (searchQuery && !task.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const handleSelectTask = (taskId: string) => {
    setSelectedTasks(prev =>
      prev.includes(taskId) ? prev.filter(id => id !== taskId) : [...prev, taskId]
    );
  };

  const handleSelectAll = () => {
    if (selectedTasks.length === filteredTasks.length) {
      setSelectedTasks([]);
    } else {
      setSelectedTasks(filteredTasks.map(t => t.taskId));
    }
  };

  const handleTaskAction = (taskId: string, action: string) => {
    console.log(`Task ${taskId} action: ${action}`);
    // TODO: Implement task actions
  };

  const handleCreateTask = (taskData: Partial<Task>) => {
    console.log('Create task:', taskData);
    // TODO: Implement task creation
  };

  const handleScheduleToggle = (scheduleId: string) => {
    setSchedules(prev =>
      prev.map(s => s.scheduleId === scheduleId ? { ...s, enabled: !s.enabled } : s)
    );
  };

  const tabs = [
    { key: 'today', label: '今日任务' },
    { key: 'schedules', label: '排程管理' },
    { key: 'templates', label: '任务模板' },
    { key: 'history', label: '历史记录' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">任务管理</h1>
          <p className="text-gray-500">管理和监控清洁任务</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            + 新建任务
          </button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            批量操作
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm mb-4">
        <div className="border-b">
          <div className="flex">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as TabType)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {activeTab === 'today' && (
            <>
              {/* Filter and Stats */}
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <TaskFilter
                  statusFilter={statusFilter}
                  typeFilter={typeFilter}
                  searchQuery={searchQuery}
                  onStatusChange={setStatusFilter}
                  onTypeChange={setTypeFilter}
                  onSearchChange={setSearchQuery}
                />
                <TaskStatsBar stats={stats} />
              </div>

              {/* Task Table */}
              <TaskTable
                tasks={filteredTasks}
                selectedTasks={selectedTasks}
                onSelectTask={handleSelectTask}
                onSelectAll={handleSelectAll}
                onTaskClick={(id) => onTaskClick?.(id)}
                onTaskAction={handleTaskAction}
              />

              {/* Pagination */}
              <div className="flex justify-between items-center mt-4 text-sm text-gray-500">
                <span>共 {filteredTasks.length} 条任务</span>
                <div className="flex items-center gap-2">
                  <button className="px-3 py-1 border rounded hover:bg-gray-50">上一页</button>
                  <span>1 / 1</span>
                  <button className="px-3 py-1 border rounded hover:bg-gray-50">下一页</button>
                </div>
              </div>
            </>
          )}

          {activeTab === 'schedules' && (
            <ScheduleList
              schedules={schedules}
              onToggle={handleScheduleToggle}
              onEdit={(id) => console.log('Edit schedule:', id)}
              onDelete={(id) => console.log('Delete schedule:', id)}
            />
          )}

          {activeTab === 'templates' && (
            <div className="text-center py-12 text-gray-500">
              任务模板功能开发中...
            </div>
          )}

          {activeTab === 'history' && (
            <div className="text-center py-12 text-gray-500">
              历史记录功能开发中...
            </div>
          )}
        </div>
      </div>

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateTask}
      />

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

export default TaskManagement;
