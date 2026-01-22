/**
 * FeedbackPanel Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FeedbackPanel } from './FeedbackPanel';
import { AgentActivity } from '../types/index';

// Mock API
vi.mock('../services/api', () => ({
  submitFeedback: vi.fn(),
}));

import { submitFeedback } from '../services/api';

const mockActivity: AgentActivity = {
  activityId: 'act_001',
  agentType: 'cleaning_scheduler',
  agentId: 'agent_001',
  activityType: 'decision',
  level: 'info',
  title: '任务分配决策',
  description: '将任务task_001分配给robot_001',
  details: { matchScore: 0.85 },
  requiresAttention: false,
  timestamp: '2026-01-21T10:30:15Z',
};

describe('FeedbackPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (submitFeedback as ReturnType<typeof vi.fn>).mockResolvedValue({
      feedbackId: 'feedback_001',
      activityId: 'act_001',
      status: 'received',
      willAffectFuture: true,
    });
  });

  it('renders the modal with header', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('提交反馈')).toBeInTheDocument();
  });

  it('displays activity summary', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('关于此决策：')).toBeInTheDocument();
    expect(screen.getByText('任务分配决策')).toBeInTheDocument();
    expect(screen.getByText('将任务task_001分配给robot_001')).toBeInTheDocument();
  });

  it('displays feedback type options', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('认可')).toBeInTheDocument();
    expect(screen.getByText('纠正')).toBeInTheDocument();
    expect(screen.getByText('拒绝')).toBeInTheDocument();
  });

  it('allows selecting different feedback types', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const correctionButton = screen.getByText('纠正').closest('button');
    if (correctionButton) {
      fireEvent.click(correctionButton);
      expect(correctionButton).toHaveClass('border-blue-500');
    }
  });

  it('shows correction fields when correction type is selected', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const correctionButton = screen.getByText('纠正').closest('button');
    if (correctionButton) {
      fireEvent.click(correctionButton);

      expect(screen.getByText('建议调整')).toBeInTheDocument();
      expect(screen.getByText('建议的机器人')).toBeInTheDocument();
      expect(screen.getByText('调整原因')).toBeInTheDocument();
    }
  });

  it('displays rating stars', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('评分')).toBeInTheDocument();
    // Should have 5 star buttons
    const stars = screen.getAllByRole('button').filter(btn =>
      btn.textContent?.includes('⭐') || btn.textContent?.includes('☆')
    );
    expect(stars.length).toBe(5);
  });

  it('allows changing rating', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const starButtons = screen.getAllByRole('button').filter(btn =>
      btn.textContent?.includes('⭐') || btn.textContent?.includes('☆')
    );

    // Click on 3rd star
    fireEvent.click(starButtons[2]);

    // First 3 stars should be filled
    expect(starButtons[0].textContent).toBe('⭐');
    expect(starButtons[1].textContent).toBe('⭐');
    expect(starButtons[2].textContent).toBe('⭐');
  });

  it('has a comment textarea', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('补充说明（可选）')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('请输入您的反馈意见...')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={onClose}
      />
    );

    const closeButton = screen.getByText('✕');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when cancel button is clicked', () => {
    const onClose = vi.fn();
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={onClose}
      />
    );

    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('submits feedback when form is submitted', async () => {
    const onSubmitted = vi.fn();
    const onClose = vi.fn();

    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={onClose}
        onSubmitted={onSubmitted}
      />
    );

    // Fill in comment
    const commentTextarea = screen.getByPlaceholderText('请输入您的反馈意见...');
    fireEvent.change(commentTextarea, { target: { value: 'Good decision!' } });

    // Submit
    const submitButton = screen.getByText('提交反馈');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          activityId: 'act_001',
          feedbackType: 'approval',
          rating: 5,
          comment: 'Good decision!',
        })
      );
      expect(onSubmitted).toHaveBeenCalledWith('approval');
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('shows submitting state during submission', async () => {
    (submitFeedback as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 100))
    );

    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const submitButton = screen.getByText('提交反馈');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('提交中...')).toBeInTheDocument();
    });
  });

  it('disables buttons during submission', async () => {
    (submitFeedback as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 100))
    );

    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const submitButton = screen.getByText('提交反馈');
    fireEvent.click(submitButton);

    await waitFor(() => {
      const cancelButton = screen.getByText('取消');
      expect(cancelButton).toBeDisabled();
    });
  });

  it('shows error message on submission failure', async () => {
    (submitFeedback as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'));

    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const submitButton = screen.getByText('提交反馈');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('提交失败，请重试')).toBeInTheDocument();
    });
  });

  it('includes correction data when feedback type is correction', async () => {
    const onSubmitted = vi.fn();

    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
        onSubmitted={onSubmitted}
      />
    );

    // Select correction type
    const correctionButton = screen.getByText('纠正').closest('button');
    if (correctionButton) {
      fireEvent.click(correctionButton);
    }

    // Fill correction fields
    const robotInput = screen.getByPlaceholderText('例如: robot_003');
    fireEvent.change(robotInput, { target: { value: 'robot_002' } });

    const reasonInput = screen.getByPlaceholderText('例如: 距离更近、电量更充足');
    fireEvent.change(reasonInput, { target: { value: '电量更高' } });

    // Submit
    const submitButton = screen.getByText('提交反馈');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          feedbackType: 'correction',
          correctionData: {
            suggestedRobotId: 'robot_002',
            reason: '电量更高',
          },
        })
      );
    });
  });
});

describe('RatingStars', () => {
  it('highlights stars on hover', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const starButtons = screen.getAllByRole('button').filter(btn =>
      btn.textContent?.includes('⭐') || btn.textContent?.includes('☆')
    );

    // Hover on 4th star
    fireEvent.mouseEnter(starButtons[3]);

    // Stars 1-4 should be highlighted
    expect(starButtons[0].textContent).toBe('⭐');
    expect(starButtons[3].textContent).toBe('⭐');
    expect(starButtons[4].textContent).toBe('☆');
  });

  it('resets hover state on mouse leave', () => {
    render(
      <FeedbackPanel
        activity={mockActivity}
        onClose={vi.fn()}
      />
    );

    const starButtons = screen.getAllByRole('button').filter(btn =>
      btn.textContent?.includes('⭐') || btn.textContent?.includes('☆')
    );

    // Default value is 5, click on 3
    fireEvent.click(starButtons[2]);

    // Hover on 1st star then leave
    fireEvent.mouseEnter(starButtons[0]);
    fireEvent.mouseLeave(starButtons[0]);

    // Should show rating of 3
    expect(starButtons[0].textContent).toBe('⭐');
    expect(starButtons[2].textContent).toBe('⭐');
    expect(starButtons[3].textContent).toBe('☆');
  });
});
