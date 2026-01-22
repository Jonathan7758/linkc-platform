/**
 * T2: Pending Queue Component
 * 展示需要人工处理的待办事项
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  PendingItem,
  PendingItemPriority,
  SuggestedAction,
} from '../types/index';
import { getPendingItems, resolvePendingItem } from '../services/api';

// ============================================================
// Types
// ============================================================

interface PendingQueueProps {
  tenantId: string;
  onItemResolved?: (item: PendingItem, action: string) => void;
  onItemClick?: (item: PendingItem) => void;
}

// ============================================================
// Helper Functions
// ============================================================

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`;
  return date.toLocaleDateString('zh-CN');
};

const getPriorityStyles = (priority: PendingItemPriority): string => {
  const styles: Record<PendingItemPriority, string> = {
    critical: 'border-red-500 bg-red-50',
    high: 'border-orange-500 bg-orange-50',
    medium: 'border-yellow-500 bg-yellow-50',
    low: 'border-gray-300 bg-gray-50',
  };
  return styles[priority] || styles.medium;
};

const getPriorityLabel = (priority: PendingItemPriority): string => {
  const labels: Record<PendingItemPriority, string> = {
    critical: '紧急',
    high: '高',
    medium: '中',
    low: '低',
  };
  return labels[priority] || '中';
};

const getPriorityBadgeStyles = (priority: PendingItemPriority): string => {
  const styles: Record<PendingItemPriority, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  };
  return styles[priority] || styles.medium;
};

const getAgentName = (agentType: string): string => {
  const names: Record<string, string> = {
    cleaning_scheduler: '清洁调度',
    conversation: '对话助手',
    data_collector: '数据采集',
  };
  return names[agentType] || agentType;
};

// ============================================================
// Pending Item Card Component
// ============================================================

interface PendingItemCardProps {
  item: PendingItem;
  onAction: (action: SuggestedAction) => void;
  onClick?: () => void;
}

const PendingItemCard: React.FC<PendingItemCardProps> = ({
  item,
  onAction,
  onClick,
}) => {
  const [processing, setProcessing] = useState(false);

  const handleAction = async (action: SuggestedAction) => {
    setProcessing(true);
    try {
      await onAction(action);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div
      className={`p-4 mb-3 border-l-4 rounded-r-lg ${getPriorityStyles(item.priority)}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded ${getPriorityBadgeStyles(item.priority)}`}>
            {getPriorityLabel(item.priority)}
          </span>
          <span className="text-gray-500 text-sm">
            {formatTime(item.createdAt)}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {getAgentName(item.agentType)}
        </span>
      </div>

      {/* Content */}
      <h4 className="font-medium mt-2 text-gray-900">{item.title}</h4>
      <p className="text-gray-600 text-sm mt-1">{item.description}</p>

      {/* Related Entities */}
      {Object.keys(item.relatedEntities).length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.entries(item.relatedEntities).map(([key, value]) => (
            <span
              key={key}
              className="px-2 py-1 text-xs bg-white rounded border cursor-pointer hover:bg-gray-50"
            >
              {key}: {value}
            </span>
          ))}
        </div>
      )}

      {/* Expiration Warning */}
      {item.expiresAt && (
        <div className="mt-2 text-xs text-orange-600">
          ⏰ 将于 {new Date(item.expiresAt).toLocaleString('zh-CN')} 过期
        </div>
      )}

      {/* Actions */}
      <div className="mt-3 flex flex-wrap gap-2">
        {item.suggestedActions.map((action) => (
          <button
            key={action.action}
            onClick={(e) => {
              e.stopPropagation();
              handleAction(action);
            }}
            disabled={processing}
            className={`px-3 py-1.5 text-sm rounded transition-colors ${
              action.action === 'ignore'
                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {processing ? '处理中...' : action.label}
          </button>
        ))}
      </div>
    </div>
  );
};

// ============================================================
// Priority Summary Component
// ============================================================

interface PrioritySummaryProps {
  byPriority: Record<string, number>;
}

const PrioritySummary: React.FC<PrioritySummaryProps> = ({ byPriority }) => {
  const priorities: PendingItemPriority[] = ['critical', 'high', 'medium', 'low'];

  return (
    <div className="flex gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
      {priorities.map((priority) => (
        <div key={priority} className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full ${
            priority === 'critical' ? 'bg-red-500' :
            priority === 'high' ? 'bg-orange-500' :
            priority === 'medium' ? 'bg-yellow-500' : 'bg-gray-400'
          }`}></span>
          <span className="text-sm text-gray-600">
            {getPriorityLabel(priority)}: {byPriority[priority] || 0}
          </span>
        </div>
      ))}
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const PendingQueue: React.FC<PendingQueueProps> = ({
  tenantId,
  onItemResolved,
  onItemClick,
}) => {
  const [items, setItems] = useState<PendingItem[]>([]);
  const [byPriority, setByPriority] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState<PendingItemPriority | ''>('');

  // Load pending items
  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getPendingItems({
        tenantId,
        priority: priorityFilter || undefined,
        status: 'pending',
        limit: 50,
      });
      setItems(response.items);
      setByPriority(response.byPriority);
    } catch (error) {
      console.error('Failed to load pending items:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId, priorityFilter]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const handleAction = async (item: PendingItem, action: SuggestedAction) => {
    try {
      await resolvePendingItem(item.itemId, {
        action: action.action,
        params: action.params,
      });
      // Remove from list
      setItems((prev) => prev.filter((i) => i.itemId !== item.itemId));
      // Update counts
      setByPriority((prev) => ({
        ...prev,
        [item.priority]: Math.max(0, (prev[item.priority] || 0) - 1),
      }));
      onItemResolved?.(item, action.action);
    } catch (error) {
      console.error('Failed to resolve item:', error);
    }
  };

  const totalPending = Object.values(byPriority).reduce((a, b) => a + b, 0);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold">待处理事项</h2>
          {totalPending > 0 && (
            <span className="px-2 py-1 text-sm bg-red-100 text-red-800 rounded-full">
              {totalPending}
            </span>
          )}
        </div>
        <button
          onClick={loadItems}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        >
          刷新
        </button>
      </div>

      {/* Priority Summary */}
      <PrioritySummary byPriority={byPriority} />

      {/* Filter */}
      <div className="mb-4">
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as PendingItemPriority | '')}
          className="px-3 py-1.5 border rounded text-sm"
        >
          <option value="">全部优先级</option>
          <option value="critical">紧急</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </div>

      {/* Item List */}
      <div className="flex-1 overflow-y-auto">
        {items.map((item) => (
          <PendingItemCard
            key={item.itemId}
            item={item}
            onAction={(action) => handleAction(item, action)}
            onClick={() => onItemClick?.(item)}
          />
        ))}

        {loading && (
          <div className="text-center py-4 text-gray-500">加载中...</div>
        )}

        {!loading && items.length === 0 && (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">✅</div>
            <div className="text-gray-500">没有待处理事项</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PendingQueue;
