/**
 * ActivityFeed Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ActivityFeed } from './ActivityFeed';
import { AgentActivity } from '../types/index';

// Mock API
vi.mock('../services/api', () => ({
  getActivities: vi.fn(),
  createActivityWebSocket: vi.fn(() => ({
    close: vi.fn(),
    send: vi.fn(),
  })),
}));

import { getActivities } from '../services/api';

const mockActivities: AgentActivity[] = [
  {
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
  },
  {
    activityId: 'act_002',
    agentType: 'cleaning_scheduler',
    agentId: 'agent_001',
    activityType: 'escalation',
    level: 'warning',
    title: '电量异常检测',
    description: 'robot_002电量骤降15%',
    details: {},
    requiresAttention: true,
    timestamp: '2026-01-21T10:28:45Z',
  },
];

describe('ActivityFeed', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getActivities as ReturnType<typeof vi.fn>).mockResolvedValue({
      activities: mockActivities,
      hasMore: false,
      nextCursor: undefined,
    });
  });

  it('renders the component header', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    expect(screen.getByText('Agent活动流')).toBeInTheDocument();
  });

  it('loads and displays activities', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('任务分配决策')).toBeInTheDocument();
      expect(screen.getByText('电量异常检测')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('displays "需关注" badge for activities requiring attention', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('需关注')).toBeInTheDocument();
    });
  });

  it('shows refresh button and handles click', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    const refreshButton = screen.getByText('刷新');
    expect(refreshButton).toBeInTheDocument();

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(getActivities).toHaveBeenCalledTimes(2);
    });
  });

  it('displays real-time indicator when realtime is enabled', () => {
    render(<ActivityFeed tenantId="test-tenant" realtime={true} />);

    expect(screen.getByText('实时')).toBeInTheDocument();
  });

  it('shows empty state when no activities', async () => {
    (getActivities as ReturnType<typeof vi.fn>).mockResolvedValue({
      activities: [],
      hasMore: false,
    });

    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('暂无活动记录')).toBeInTheDocument();
    });
  });

  it('calls onActivityClick when activity is clicked', async () => {
    const onActivityClick = vi.fn();
    render(
      <ActivityFeed
        tenantId="test-tenant"
        onActivityClick={onActivityClick}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('任务分配决策')).toBeInTheDocument();
    });

    const activityCard = screen.getByText('任务分配决策').closest('div[class*="cursor-pointer"]');
    if (activityCard) {
      fireEvent.click(activityCard);
      expect(onActivityClick).toHaveBeenCalledWith(mockActivities[0]);
    }
  });

  it('shows load more button when hasMore is true', async () => {
    (getActivities as ReturnType<typeof vi.fn>).mockResolvedValue({
      activities: mockActivities,
      hasMore: true,
      nextCursor: 'cursor_123',
    });

    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('加载更多')).toBeInTheDocument();
    });
  });

  it('filters can be changed', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('任务分配决策')).toBeInTheDocument();
    });

    // Find agent type filter
    const agentTypeSelect = screen.getByDisplayValue('全部');
    fireEvent.change(agentTypeSelect, { target: { value: 'cleaning_scheduler' } });

    await waitFor(() => {
      expect(getActivities).toHaveBeenCalledWith(
        expect.objectContaining({
          agentType: 'cleaning_scheduler',
        })
      );
    });
  });
});

describe('ActivityCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getActivities as ReturnType<typeof vi.fn>).mockResolvedValue({
      activities: mockActivities,
      hasMore: false,
    });
  });

  it('expands to show details when clicked', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('任务分配决策')).toBeInTheDocument();
    });

    const activityCard = screen.getByText('任务分配决策').closest('div[class*="cursor-pointer"]');
    if (activityCard) {
      fireEvent.click(activityCard);

      await waitFor(() => {
        expect(screen.getByText('详细信息')).toBeInTheDocument();
      });
    }
  });

  it('shows approve and correct buttons for decision activities', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('👍 认可')).toBeInTheDocument();
      expect(screen.getByText('✏️ 纠正')).toBeInTheDocument();
    });
  });

  it('displays correct level icon', async () => {
    render(<ActivityFeed tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('🔵')).toBeInTheDocument(); // info
      expect(screen.getByText('🟡')).toBeInTheDocument(); // warning
    });
  });
});
