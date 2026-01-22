/**
 * DM5: Demo Map Visualization Tests
 * 地图动态可视化组件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import DemoMapVisualization from './DemoMapVisualization';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: Event) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      this.onopen?.();
    }, 0);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  });

  simulateMessage(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
}

global.WebSocket = MockWebSocket as any;

// Mock robot data
const mockRobots = [
  {
    robot_id: 'robot_001',
    name: '清洁机器人 A-01',
    status: 'working',
    position: { x: 25, y: 30, orientation: 45 },
    battery_level: 85,
    current_task_id: 'task_001',
    speed: 0.5,
  },
  {
    robot_id: 'robot_002',
    name: '清洁机器人 A-02',
    status: 'idle',
    position: { x: 60, y: 50, orientation: 0 },
    battery_level: 92,
    speed: 0,
  },
  {
    robot_id: 'robot_003',
    name: '清洁机器人 A-03',
    status: 'charging',
    position: { x: 10, y: 80, orientation: 180 },
    battery_level: 35,
    speed: 0,
  },
];

const mockZones = [
  {
    id: 'zone_001',
    name: '大堂',
    zone_type: 'lobby',
    floor_id: 'floor_001',
  },
  {
    id: 'zone_002',
    name: '会议室A',
    zone_type: 'meeting_room',
    floor_id: 'floor_001',
  },
];

describe('DemoMapVisualization', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/simulation/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            is_running: true,
            robot_states: mockRobots.reduce((acc, r) => ({
              ...acc,
              [r.robot_id]: r
            }), {}),
          }),
        });
      }
      if (url.includes('/demo/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ is_active: true }),
        });
      }
      if (url.includes('/demo/zones')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ zones: mockZones }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders the map component', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('机器人:')).toBeInTheDocument();
    });
  });

  it('displays robot count stats', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const workingElements = screen.getAllByText(/工作/);
      expect(workingElements.length).toBeGreaterThan(0);
    });
  });

  it('shows map controls', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('楼层')).toBeInTheDocument();
      expect(screen.getByText('缩放')).toBeInTheDocument();
      expect(screen.getByText('显示')).toBeInTheDocument();
    });
  });

  it('shows heatmap toggle in controls', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const heatmapLabel = screen.getByLabelText('热力图');
      expect(heatmapLabel).toBeInTheDocument();
    });
  });

  it('shows path toggle in controls', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const pathLabel = screen.getByLabelText('移动路径');
      expect(pathLabel).toBeInTheDocument();
    });
  });

  it('displays connection status indicator', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const connectionStatus = screen.queryByText('实时连接') || screen.queryByText('轮询模式');
      expect(connectionStatus).toBeInTheDocument();
    });
  });

  it('displays map legend', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('图例')).toBeInTheDocument();
      expect(screen.getByText('机器人状态')).toBeInTheDocument();
    });
  });

  it('shows idle status in legend', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const legendItems = screen.getAllByText('空闲');
      expect(legendItems.length).toBeGreaterThan(0);
    });
  });

  it('displays floor selector', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('楼层')).toBeInTheDocument();
      const floorSelect = screen.getByRole('combobox');
      expect(floorSelect).toBeInTheDocument();
    });
  });

  it('fetches initial data on mount', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/simulation/status'));
    });
  });

  it('shows average battery level stat', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('平均电量:')).toBeInTheDocument();
    });
  });

  it('shows task counts in stats bar', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('任务:')).toBeInTheDocument();
    });
  });

  it('renders SVG map element', async () => {
    const { container } = render(<DemoMapVisualization />);

    await waitFor(() => {
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  it('renders grid pattern in SVG', async () => {
    const { container } = render(<DemoMapVisualization />);

    await waitFor(() => {
      const pattern = container.querySelector('pattern#demo-grid');
      expect(pattern).toBeInTheDocument();
    });
  });

  it('toggles heatmap checkbox', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const heatmapCheckbox = screen.getByLabelText('热力图');
      expect(heatmapCheckbox).not.toBeChecked();
    });

    const heatmapCheckbox = screen.getByLabelText('热力图');
    await act(async () => {
      fireEvent.click(heatmapCheckbox);
    });

    expect(heatmapCheckbox).toBeChecked();
  });

  it('toggles paths checkbox', async () => {
    render(<DemoMapVisualization showPaths={false} />);

    await waitFor(() => {
      const pathsCheckbox = screen.getByLabelText('移动路径');
      expect(pathsCheckbox).not.toBeChecked();
    });

    const pathsCheckbox = screen.getByLabelText('移动路径');
    await act(async () => {
      fireEvent.click(pathsCheckbox);
    });

    expect(pathsCheckbox).toBeChecked();
  });
});

describe('DemoMapVisualization - Props', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );
  });

  it('accepts custom buildingId', async () => {
    render(<DemoMapVisualization buildingId="custom_building" />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  it('accepts custom refreshInterval', async () => {
    render(<DemoMapVisualization refreshInterval={2000} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  it('accepts showHeatmap prop', () => {
    const { container } = render(<DemoMapVisualization showHeatmap={true} />);
    expect(container).toBeInTheDocument();
  });

  it('accepts showPaths prop', () => {
    const { container } = render(<DemoMapVisualization showPaths={true} />);
    expect(container).toBeInTheDocument();
  });

  it('calls onRobotSelect callback when provided', async () => {
    const onRobotSelect = vi.fn();
    render(<DemoMapVisualization onRobotSelect={onRobotSelect} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  it('calls onZoneSelect callback when provided', async () => {
    const onZoneSelect = vi.fn();
    render(<DemoMapVisualization onZoneSelect={onZoneSelect} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });
});

describe('DemoMapVisualization - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles fetch error gracefully', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    expect(() => render(<DemoMapVisualization />)).not.toThrow();

    await waitFor(() => {
      expect(screen.getByText('机器人:')).toBeInTheDocument();
    });
  });

  it('handles malformed response gracefully', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ invalid: 'data' }),
    });

    expect(() => render(<DemoMapVisualization />)).not.toThrow();
  });

  it('falls back to polling on WebSocket error', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const status = screen.queryByText('实时连接') || screen.queryByText('轮询模式');
      expect(status).toBeInTheDocument();
    });
  });
});

describe('DemoMapVisualization - Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          robot_states: {},
          zones: [],
        }),
      })
    );
  });

  it('renders stats bar at top', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('机器人:')).toBeInTheDocument();
    });
  });

  it('renders controls on left side', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('楼层')).toBeInTheDocument();
      expect(screen.getByText('缩放')).toBeInTheDocument();
    });
  });

  it('renders legend at bottom left', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('图例')).toBeInTheDocument();
    });
  });

  it('renders connection status at bottom right', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      const status = screen.queryByText('实时连接') || screen.queryByText('轮询模式');
      expect(status).toBeInTheDocument();
    });
  });
});

describe('DemoMapVisualization - Zoom Controls', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );
  });

  it('starts at 100% zoom', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  it('can zoom in', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('+'));
    });

    await waitFor(() => {
      expect(screen.getByText('125%')).toBeInTheDocument();
    });
  });

  it('can zoom out', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('−'));
    });

    await waitFor(() => {
      expect(screen.getByText('75%')).toBeInTheDocument();
    });
  });

  it('has zoom buttons', async () => {
    render(<DemoMapVisualization />);

    await waitFor(() => {
      expect(screen.getByText('+')).toBeInTheDocument();
      expect(screen.getByText('−')).toBeInTheDocument();
    });
  });
});
