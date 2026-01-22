/**
 * T3: Feedback Panel Component
 * 提供对Agent决策的反馈功能
 */

import React, { useState } from 'react';
import {
  AgentActivity,
  FeedbackType,
  FeedbackRequest,
} from '../types/index';
import { submitFeedback } from '../services/api';

// ============================================================
// Types
// ============================================================

interface FeedbackPanelProps {
  activity: AgentActivity;
  onClose: () => void;
  onSubmitted?: (feedbackType: FeedbackType) => void;
}

// ============================================================
// Rating Stars Component
// ============================================================

interface RatingStarsProps {
  value: number;
  onChange: (value: number) => void;
}

const RatingStars: React.FC<RatingStarsProps> = ({ value, onChange }) => {
  const [hovered, setHovered] = useState(0);

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange(star)}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          className="text-2xl transition-transform hover:scale-110"
        >
          {star <= (hovered || value) ? '⭐' : '☆'}
        </button>
      ))}
    </div>
  );
};

// ============================================================
// Feedback Type Selector
// ============================================================

interface FeedbackTypeSelectorProps {
  value: FeedbackType;
  onChange: (value: FeedbackType) => void;
}

const FeedbackTypeSelector: React.FC<FeedbackTypeSelectorProps> = ({
  value,
  onChange,
}) => {
  const types: { type: FeedbackType; label: string; icon: string; description: string }[] = [
    {
      type: 'approval',
      label: '认可',
      icon: '👍',
      description: '决策正确，符合预期',
    },
    {
      type: 'correction',
      label: '纠正',
      icon: '✏️',
      description: '需要调整或改进',
    },
    {
      type: 'rejection',
      label: '拒绝',
      icon: '👎',
      description: '决策错误，不可接受',
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {types.map((t) => (
        <button
          key={t.type}
          type="button"
          onClick={() => onChange(t.type)}
          className={`p-4 rounded-lg border-2 text-center transition-all ${
            value === t.type
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-2xl mb-1">{t.icon}</div>
          <div className="font-medium">{t.label}</div>
          <div className="text-xs text-gray-500 mt-1">{t.description}</div>
        </button>
      ))}
    </div>
  );
};

// ============================================================
// Main Component
// ============================================================

export const FeedbackPanel: React.FC<FeedbackPanelProps> = ({
  activity,
  onClose,
  onSubmitted,
}) => {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('approval');
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [correctionData, setCorrectionData] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const request: FeedbackRequest = {
        activityId: activity.activityId,
        feedbackType,
        rating,
        comment: comment || undefined,
        correctionData: feedbackType === 'correction' ? correctionData : undefined,
      };

      await submitFeedback(request);
      onSubmitted?.(feedbackType);
      onClose();
    } catch (err) {
      setError('提交失败，请重试');
      console.error('Failed to submit feedback:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h3 className="text-lg font-semibold">提交反馈</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Activity Summary */}
        <div className="px-6 py-4 bg-gray-50">
          <div className="text-sm text-gray-500">关于此决策：</div>
          <div className="font-medium mt-1">{activity.title}</div>
          <div className="text-sm text-gray-600 mt-1">{activity.description}</div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {/* Feedback Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              反馈类型
            </label>
            <FeedbackTypeSelector
              value={feedbackType}
              onChange={setFeedbackType}
            />
          </div>

          {/* Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              评分
            </label>
            <RatingStars value={rating} onChange={setRating} />
          </div>

          {/* Correction Data (for correction type) */}
          {feedbackType === 'correction' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                建议调整
              </label>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    建议的机器人
                  </label>
                  <input
                    type="text"
                    value={correctionData.suggestedRobotId || ''}
                    onChange={(e) =>
                      setCorrectionData((prev) => ({
                        ...prev,
                        suggestedRobotId: e.target.value,
                      }))
                    }
                    placeholder="例如: robot_003"
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    调整原因
                  </label>
                  <input
                    type="text"
                    value={correctionData.reason || ''}
                    onChange={(e) =>
                      setCorrectionData((prev) => ({
                        ...prev,
                        reason: e.target.value,
                      }))
                    }
                    placeholder="例如: 距离更近、电量更充足"
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              补充说明（可选）
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="请输入您的反馈意见..."
              rows={3}
              className="w-full px-3 py-2 border rounded-lg text-sm resize-none"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              disabled={submitting}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? '提交中...' : '提交反馈'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FeedbackPanel;
