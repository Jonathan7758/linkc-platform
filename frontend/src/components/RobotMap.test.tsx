/**
 * RobotMap Component Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RobotMap } from './RobotMap';
import { Robot } from '../types/index';

// Mock API
vi.mock('../services/api', () => ({
  getRobots: vi.fn(),
}));

import { getRobots } from '../services/api';

const mockRobots: Robot[] = [
  {
    robotId: 'robot_001',
    name: 'R-001',
    brand: 'Gaussian',
    model: 'GS-100',
    status: 'working',
    batteryLevel: 75,
    position: { x: 30, y: 40, orientation: 90 },
    currentTaskId: 'task_001',
    lastActiveAt: '2026-01-21T10:30:00Z',
  },
  {
    robotId: 'robot_002',
    name: 'R-002',
    brand: 'Gaussian',
    model: 'GS-100',
    status: 'idle',
    batteryLevel: 95,
    position: { x: 60, y: 70, orientation: 180 },
    lastActiveAt: '2026-01-21T10:25:00Z',
  },
  {
    robotId: 'robot_003',
    name: 'R-003',
    brand: 'Gaussian',
    model: 'GS-100',
    status: 'charging',
    batteryLevel: 45,
    position: { x: 10, y: 10, orientation: 0 },
    lastActiveAt: '2026-01-21T10:20:00Z',
  },
  {
    robotId: 'robot_004',
    name: 'R-004',
    brand: 'Gaussian',
    model: 'GS-100',
    status: 'error',
    batteryLevel: 60,
    position: { x: 50, y: 50, orientation: 270 },
    lastActiveAt: '2026-01-21T10:15:00Z',
  },
];

describe('RobotMap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getRobots as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: mockRobots,
      total: 4,
      page: 1,
      pageSize: 20,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the component header', async () => {
    render(<RobotMap buildingId="test-building" />);

    expect(screen.getByText('机器人地图')).toBeInTheDocument();
  });

  it('loads and displays robot stats', async () => {
    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      expect(screen.getByText(/总数: 4/)).toBeInTheDocument();
    });

    expect(screen.getByText(/工作: 1/)).toBeInTheDocument();
    expect(screen.getByText(/空闲: 1/)).toBeInTheDocument();
    expect(screen.getByText(/充电: 1/)).toBeInTheDocument();
    expect(screen.getByText(/故障: 1/)).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(<RobotMap buildingId="test-building" />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('displays legend', async () => {
    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      expect(screen.getByText('图例')).toBeInTheDocument();
    });

    expect(screen.getByText('空闲')).toBeInTheDocument();
    expect(screen.getByText('工作中')).toBeInTheDocument();
    expect(screen.getByText('充电中')).toBeInTheDocument();
    expect(screen.getByText('故障')).toBeInTheDocument();
    expect(screen.getByText('离线')).toBeInTheDocument();
  });

  it('shows refresh button and handles click', async () => {
    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      expect(screen.getByText(/总数:/)).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('刷新');
    expect(refreshButton).toBeInTheDocument();

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(getRobots).toHaveBeenCalledTimes(2);
    });
  });

  it('displays SVG map container', async () => {
    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      const svg = document.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  it('renders robot name labels', async () => {
    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      expect(screen.getByText('R-001')).toBeInTheDocument();
    });

    expect(screen.getByText('R-002')).toBeInTheDocument();
    expect(screen.getByText('R-003')).toBeInTheDocument();
    expect(screen.getByText('R-004')).toBeInTheDocument();
  });

  it('handles empty robot list', async () => {
    (getRobots as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
    });

    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      expect(screen.getByText(/总数: 0/)).toBeInTheDocument();
    });
  });

  it('filters robots by floor when floorId is provided', async () => {
    const robotsWithFloor: Robot[] = mockRobots.map((r, i) => ({
      ...r,
      position: { ...r.position!, floorId: i % 2 === 0 ? 'floor_1' : 'floor_2' },
    }));

    (getRobots as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: robotsWithFloor,
      total: 4,
      page: 1,
      pageSize: 20,
    });

    render(<RobotMap buildingId="test-building" floorId="floor_1" />);

    await waitFor(() => {
      expect(screen.getByText('R-001')).toBeInTheDocument();
    });

    expect(screen.getByText('R-003')).toBeInTheDocument();
    expect(screen.queryByText('R-002')).not.toBeInTheDocument();
    expect(screen.queryByText('R-004')).not.toBeInTheDocument();
  });

  it('calls API with correct buildingId', async () => {
    render(<RobotMap buildingId="building-123" />);

    await waitFor(() => {
      expect(getRobots).toHaveBeenCalledWith({ buildingId: 'building-123' });
    });
  });

  it('renders robot circles in SVG', async () => {
    render(<RobotMap buildingId="test-building" />);

    await waitFor(() => {
      const circles = document.querySelectorAll('circle');
      expect(circles.length).toBeGreaterThan(0);
    });
  });
});

describe('RobotMap Auto Refresh', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (getRobots as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: mockRobots,
      total: 4,
      page: 1,
      pageSize: 20,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('auto refreshes at specified interval', async () => {
    render(<RobotMap buildingId="test-building" refreshInterval={5000} />);

    // Initial call
    expect(getRobots).toHaveBeenCalledTimes(1);

    // Advance time by 5 seconds
    await vi.advanceTimersByTimeAsync(5000);

    expect(getRobots).toHaveBeenCalledTimes(2);

    // Advance again
    await vi.advanceTimersByTimeAsync(5000);

    expect(getRobots).toHaveBeenCalledTimes(3);
  });
});
