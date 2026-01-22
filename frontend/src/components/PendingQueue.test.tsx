/**
 * PendingQueue Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PendingQueue } from './PendingQueue';
import { PendingItem } from '../types/index';

// Mock API
vi.mock('../services/api', () => ({
  getPendingItems: vi.fn(),
  resolvePendingItem: vi.fn(),
}));

import { getPendingItems, resolvePendingItem } from '../services/api';

const mockPendingItems: PendingItem[] = [
  {
    itemId: 'pending_001',
    type: 'task_assignment',
    priority: 'high',
    status: 'pending',
    title: '需要确认机器人分配',
    description: '系统无法自动决定最佳机器人',
    agentType: 'cleaning_scheduler',
    relatedEntities: { taskId: 'task_001', zoneId: 'zone_001' },
    suggestedActions: [
      { action: 'approve', label: '批准', params: { robotId: 'robot_001' } },
      { action: 'reject', label: '拒绝' },
      { action: 'ignore', label: '忽略' },
    ],
    createdAt: '2026-01-21T10:30:00Z',
  },
  {
    itemId: 'pending_002',
    type: 'error_handling',
    priority: 'critical',
    status: 'pending',
    title: '机器人故障需处理',
    description: 'robot_002报告传感器故障',
    agentType: 'cleaning_scheduler',
    relatedEntities: { robotId: 'robot_002' },
    suggestedActions: [
      { action: 'dispatch_technician', label: '派遣技术员' },
      { action: 'ignore', label: '忽略' },
    ],
    createdAt: '2026-01-21T10:25:00Z',
    expiresAt: '2026-01-21T12:00:00Z',
  },
];

describe('PendingQueue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getPendingItems as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: mockPendingItems,
      total: 2,
      byPriority: { critical: 1, high: 1, medium: 0, low: 0 },
    });
    (resolvePendingItem as ReturnType<typeof vi.fn>).mockResolvedValue({ success: true });
  });

  it('renders the component header', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    expect(screen.getByText('待处理事项')).toBeInTheDocument();
  });

  it('loads and displays pending items', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('需要确认机器人分配')).toBeInTheDocument();
      expect(screen.getByText('机器人故障需处理')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    render(<PendingQueue tenantId="test-tenant" />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('displays priority badges correctly', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('高')).toBeInTheDocument();
      expect(screen.getByText('紧急')).toBeInTheDocument();
    });
  });

  it('shows priority summary', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText(/紧急: 1/)).toBeInTheDocument();
      expect(screen.getByText(/高: 1/)).toBeInTheDocument();
    });
  });

  it('displays total pending count badge', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('shows refresh button and handles click', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    const refreshButton = screen.getByText('刷新');
    expect(refreshButton).toBeInTheDocument();

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(getPendingItems).toHaveBeenCalledTimes(2);
    });
  });

  it('shows empty state when no pending items', async () => {
    (getPendingItems as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      total: 0,
      byPriority: {},
    });

    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('没有待处理事项')).toBeInTheDocument();
      expect(screen.getByText('✅')).toBeInTheDocument();
    });
  });

  it('displays action buttons for pending items', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('批准')).toBeInTheDocument();
      expect(screen.getByText('拒绝')).toBeInTheDocument();
    });
  });

  it('handles action button click', async () => {
    const onItemResolved = vi.fn();
    render(
      <PendingQueue
        tenantId="test-tenant"
        onItemResolved={onItemResolved}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('批准')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('批准'));

    await waitFor(() => {
      expect(resolvePendingItem).toHaveBeenCalledWith(
        'pending_001',
        expect.objectContaining({ action: 'approve' })
      );
      expect(onItemResolved).toHaveBeenCalled();
    });
  });

  it('displays expiration warning when item has expiresAt', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText(/将于.*过期/)).toBeInTheDocument();
    });
  });

  it('displays related entities as tags', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText(/taskId: task_001/)).toBeInTheDocument();
      expect(screen.getByText(/zoneId: zone_001/)).toBeInTheDocument();
    });
  });

  it('can filter by priority', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('需要确认机器人分配')).toBeInTheDocument();
    });

    const prioritySelect = screen.getByDisplayValue('全部优先级');
    fireEvent.change(prioritySelect, { target: { value: 'critical' } });

    await waitFor(() => {
      expect(getPendingItems).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: 'critical',
        })
      );
    });
  });

  it('removes item from list after resolution', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('需要确认机器人分配')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('批准'));

    await waitFor(() => {
      expect(screen.queryByText('需要确认机器人分配')).not.toBeInTheDocument();
    });
  });
});

describe('PendingItemCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getPendingItems as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: mockPendingItems,
      total: 2,
      byPriority: { critical: 1, high: 1 },
    });
  });

  it('shows processing state when action is in progress', async () => {
    (resolvePendingItem as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 100))
    );

    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getByText('批准')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('批准'));

    await waitFor(() => {
      expect(screen.getByText('处理中...')).toBeInTheDocument();
    });
  });

  it('displays agent type label', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      expect(screen.getAllByText('清洁调度').length).toBeGreaterThan(0);
    });
  });

  it('shows time ago format', async () => {
    render(<PendingQueue tenantId="test-tenant" />);

    await waitFor(() => {
      // Should show relative time format
      expect(screen.getByText(/分钟前|小时前|刚刚/)).toBeInTheDocument();
    });
  });
});
