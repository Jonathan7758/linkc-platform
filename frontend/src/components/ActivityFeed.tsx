/**
 * T1: Agent Activity Feed Component
 * 实时展示Agent的决策、行动和状态变化
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  AgentActivity,
  AgentType,
  ActivityLevel,
} from '../types/index';
import { getActivities, createActivityWebSocket } from '../services/api';

// ============================================================
// Types
// ============================================================

interface ActivityFeedProps {
  tenantId: string;
  initialFilters?: {
    agentType?: AgentType;
    level?: ActivityLevel;
  };
  pageSize?: number;
  realtime?: boolean;
  onActivityClick?: (activity: AgentActivity) => void;
  onActionRequired?: (activity: AgentActivity) => void;
}

interface Filters {
  agentType?: AgentType;
  level?: ActivityLevel;
}

// ============================================================
// Helper Functions
// ============================================================

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const getAgentName = (agentType: AgentType): string => {
  const names: Record<AgentType, string> = {
    cleaning_scheduler: '清洁调度Agent',
    conversation: '对话助手Agent',
    data_collector: '数据采集Agent',
  };
  return names[agentType] || agentType;
};

const getLevelStyles = (level: ActivityLevel): string => {
  const styles: Record<ActivityLevel, string> = {
    info: 'border-blue-500 bg-blue-50',
    warning: 'border-yellow-500 bg-yellow-50',
    error: 'border-red-500 bg-red-50',
    critical: 'border-red-700 bg-red-100',
  };
  return styles[level] || styles.info;
};

const getLevelIcon = (level: ActivityLevel): string => {
  const icons: Record<ActivityLevel, string> = {
    info: '🔵',
    warning: '🟡',
    error: '🔴',
    critical: '🔴',
  };
  return icons[level] || '🔵';
};

// ============================================================
// Activity Card Component
// ============================================================

interface ActivityCardProps {
  activity: AgentActivity;
  onClick?: () => void;
  onApprove?: () => void;
  onCorrect?: () => void;
}

const ActivityCard: React.FC<ActivityCardProps> = ({
  activity,
  onClick,
  onApprove,
  onCorrect,
}) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`p-4 mb-3 border-l-4 rounded-r-lg cursor-pointer hover:shadow-md transition-shadow ${getLevelStyles(activity.level)}`}
      onClick={() => {
        setExpanded(!expanded);
        onClick?.();
      }}
    >
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2">
          <span>{getLevelIcon(activity.level)}</span>
          <span className="text-gray-500 text-sm">
            {formatTime(activity.timestamp)}
          </span>
          <span className="text-gray-700 font-medium">
            {getAgentName(activity.agentType)}
          </span>
        </div>
        {activity.requiresAttention && (
          <span className="px-2 py-1 text-xs bg-yellow-200 text-yellow-800 rounded">
            需关注
          </span>
        )}
      </div>

      {/* Content */}
      <h4 className="font-medium mt-2 text-gray-900">{activity.title}</h4>
      <p className="text-gray-600 text-sm mt-1">{activity.description}</p>

      {/* Details (expandable) */}
      {expanded && activity.details && (
        <div className="mt-3 p-3 bg-white rounded border">
          <h5 className="text-sm font-medium text-gray-700 mb-2">详细信息</h5>
          <pre className="text-xs text-gray-600 overflow-auto">
            {JSON.stringify(activity.details, null, 2)}
          </pre>
        </div>
      )}

      {/* Actions */}
      <div className="mt-3 flex gap-2">
        {activity.activityType === 'decision' && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onApprove?.();
              }}
              className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
            >
              👍 认可
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCorrect?.();
              }}
              className="px-3 py-1 text-sm bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
            >
              ✏️ 纠正
            </button>
          </>
        )}
        <button
          onClick={(e) => e.stopPropagation()}
          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          🔗 详情
        </button>
      </div>
    </div>
  );
};

// ============================================================
// Filter Bar Component
// ============================================================

interface FilterBarProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onChange }) => {
  return (
    <div className="flex gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
      <div>
        <label className="block text-xs text-gray-500 mb-1">Agent类型</label>
        <select
          value={filters.agentType || ''}
          onChange={(e) =>
            onChange({ ...filters, agentType: e.target.value as AgentType || undefined })
          }
          className="px-3 py-1.5 border rounded text-sm"
        >
          <option value="">全部</option>
          <option value="cleaning_scheduler">清洁调度</option>
          <option value="conversation">对话助手</option>
          <option value="data_collector">数据采集</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1">级别</label>
        <select
          value={filters.level || ''}
          onChange={(e) =>
            onChange({ ...filters, level: e.target.value as ActivityLevel || undefined })
          }
          className="px-3 py-1.5 border rounded text-sm"
        >
          <option value="">全部</option>
          <option value="info">信息</option>
          <option value="warning">警告</option>
          <option value="error">错误</option>
          <option value="critical">严重</option>
        </select>
      </div>
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  tenantId,
  initialFilters = {},
  pageSize = 20,
  realtime = true,
  onActivityClick,
  onActionRequired,
}) => {
  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [loading, setLoading] = useState(true);
  const [cursor, setCursor] = useState<string | undefined>();
  const [hasMore, setHasMore] = useState(true);

  // Load activities
  const loadActivities = useCallback(async (reset = false) => {
    setLoading(true);
    try {
      const response = await getActivities({
        tenantId,
        agentType: filters.agentType,
        level: filters.level,
        limit: pageSize,
        cursor: reset ? undefined : cursor,
      });

      setActivities((prev) =>
        reset ? response.activities : [...prev, ...response.activities]
      );
      setCursor(response.nextCursor);
      setHasMore(response.hasMore);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId, filters, pageSize, cursor]);

  // Initial load and filter changes
  useEffect(() => {
    loadActivities(true);
  }, [tenantId, filters]);

  // WebSocket for realtime updates
  useEffect(() => {
    if (!realtime) return;

    const ws = createActivityWebSocket(
      tenantId,
      (activity) => {
        setActivities((prev) => [activity, ...prev]);
        if (activity.requiresAttention) {
          onActionRequired?.(activity);
        }
      },
      {
        agentTypes: filters.agentType ? [filters.agentType] : undefined,
        levels: filters.level ? [filters.level] : undefined,
      }
    );

    return () => ws.close();
  }, [tenantId, filters, realtime, onActionRequired]);

  const handleApprove = (activity: AgentActivity) => {
    // TODO: Submit approval feedback
    console.log('Approve:', activity.activityId);
  };

  const handleCorrect = (activity: AgentActivity) => {
    // TODO: Open correction dialog
    console.log('Correct:', activity.activityId);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Agent活动流</h2>
        <div className="flex gap-2">
          {realtime && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              实时
            </span>
          )}
          <button
            onClick={() => loadActivities(true)}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            刷新
          </button>
        </div>
      </div>

      {/* Filters */}
      <FilterBar filters={filters} onChange={setFilters} />

      {/* Activity List */}
      <div className="flex-1 overflow-y-auto">
        {activities.map((activity) => (
          <ActivityCard
            key={activity.activityId}
            activity={activity}
            onClick={() => onActivityClick?.(activity)}
            onApprove={() => handleApprove(activity)}
            onCorrect={() => handleCorrect(activity)}
          />
        ))}

        {loading && (
          <div className="text-center py-4 text-gray-500">加载中...</div>
        )}

        {!loading && activities.length === 0 && (
          <div className="text-center py-8 text-gray-500">暂无活动记录</div>
        )}

        {hasMore && !loading && (
          <button
            onClick={() => loadActivities()}
            className="w-full py-3 text-center text-blue-600 hover:bg-blue-50 rounded"
          >
            加载更多
          </button>
        )}
      </div>
    </div>
  );
};

export default ActivityFeed;
