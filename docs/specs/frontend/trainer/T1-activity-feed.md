# 模块开发规格书：T1 Agent活动流组件

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | T1 |
| 模块名称 | Agent活动流组件 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | G5 Agent交互API |

---

## 1. 模块概述

### 1.1 职责描述
Agent活动流组件实时展示AI Agent的决策、行动和状态变化，让训练师能够监控Agent行为并及时介入。

### 1.2 在系统中的位置
```
训练工作台 (Trainer Workbench)
├── T1: Agent活动流组件  ← 本模块
├── T2: 待处理队列组件
├── T3: 反馈面板组件
└── T4: 机器人地图组件
```

### 1.3 功能概述
- 实时展示Agent活动日志
- 支持按类型、级别筛选
- 展示决策详情和推理过程
- 支持一键跳转到相关实体
- WebSocket实时推送新活动

---

## 2. UI设计

### 2.1 组件布局
```
┌─────────────────────────────────────────────────────────────┐
│ Agent活动流                                    [筛选] [刷新] │
├─────────────────────────────────────────────────────────────┤
│ ┌─ 筛选栏 ─────────────────────────────────────────────────┐│
│ │ Agent: [全部 ▼]  级别: [全部 ▼]  类型: [全部 ▼]        ││
│ └──────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ ┌─ 活动列表 ───────────────────────────────────────────────┐│
│ │ 🟢 10:30:15  清洁调度Agent                               ││
│ │    ├─ 任务分配决策                                       ││
│ │    │  将任务task_001分配给robot_001                      ││
│ │    │  匹配得分: 0.85  推理: 距离最近且电量充足           ││
│ │    └─ [查看详情] [查看机器人] [查看任务]                 ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ 🟡 10:28:45  清洁调度Agent                    ⚠️ 需关注   ││
│ │    ├─ 电量异常检测                                       ││
│ │    │  robot_002电量骤降15%，可能存在问题                 ││
│ │    └─ [处理] [忽略] [查看机器人]                         ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ 🔵 10:25:30  对话助手Agent                               ││
│ │    ├─ 用户查询                                           ││
│ │    │  回答了关于机器人状态的查询                         ││
│ │    └─ [查看对话]                                         ││
│ └──────────────────────────────────────────────────────────┘│
│ [加载更多...]                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 活动卡片设计
```
┌────────────────────────────────────────────────────────────┐
│ 🟢 10:30:15                              清洁调度Agent     │
├────────────────────────────────────────────────────────────┤
│ 📋 任务分配决策                                            │
│                                                            │
│ 将任务 task_001 分配给 robot_001                           │
│                                                            │
│ ┌─ 决策详情 ─────────────────────────────────────────────┐ │
│ │ 匹配得分: 0.85                                         │ │
│ │ 推理: robot_001距离最近(15m)，电量充足(85%)，          │ │
│ │      历史表现良好(4.5分)                               │ │
│ │ 备选方案:                                              │ │
│ │  - robot_002: 得分0.72 (距离较远)                      │ │
│ │  - robot_003: 得分0.65 (电量偏低)                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [👍 认可] [✏️ 纠正] [🔗 查看任务] [🤖 查看机器人]          │
└────────────────────────────────────────────────────────────┘
```

### 2.3 颜色和图标规范
| 级别 | 颜色 | 图标 | 说明 |
|-----|------|------|------|
| info | 蓝色 #3B82F6 | 🔵 | 常规信息 |
| success | 绿色 #22C55E | 🟢 | 成功操作 |
| warning | 黄色 #EAB308 | 🟡 | 需要关注 |
| error | 红色 #EF4444 | 🔴 | 错误/异常 |

---

## 3. 组件接口

### 3.1 Props定义
```typescript
interface AgentActivityFeedProps {
  tenantId: string;
  // 筛选条件
  initialFilters?: {
    agentType?: AgentType;
    level?: ActivityLevel;
    activityType?: ActivityType;
  };
  // 每页数量
  pageSize?: number;  // default: 20
  // 是否启用实时更新
  realtime?: boolean;  // default: true
  // 点击活动回调
  onActivityClick?: (activity: AgentActivity) => void;
  // 需要处理回调
  onActionRequired?: (activity: AgentActivity) => void;
}

type AgentType = 'cleaning_scheduler' | 'conversation' | 'data_collector';
type ActivityLevel = 'info' | 'warning' | 'error' | 'critical';
type ActivityType = 'decision' | 'tool_call' | 'escalation' | 'state_change';
```

### 3.2 数据类型
```typescript
interface AgentActivity {
  activityId: string;
  agentType: AgentType;
  agentId: string;
  activityType: ActivityType;
  level: ActivityLevel;
  title: string;
  description: string;
  details: Record<string, any>;
  requiresAttention: boolean;
  escalationId?: string;
  timestamp: string;
}

interface ActivityFilters {
  agentType?: AgentType;
  level?: ActivityLevel;
  activityType?: ActivityType;
}
```

### 3.3 API调用
```typescript
// 获取活动列表
GET /api/v1/agents/activities
  ?tenant_id={tenantId}
  &agent_type={agentType}
  &level={level}
  &limit={pageSize}
  &cursor={cursor}

// WebSocket实时推送
WS /api/v1/agents/ws/activities
  ?token={token}&tenant_id={tenantId}
```

---

## 4. 实现要求

### 4.1 技术栈
- React 18+
- TypeScript
- TailwindCSS
- React Query (数据获取)
- WebSocket (实时更新)

### 4.2 核心实现

#### 组件结构
```typescript
// components/AgentActivityFeed/index.tsx
export const AgentActivityFeed: React.FC<AgentActivityFeedProps> = ({
  tenantId,
  initialFilters,
  pageSize = 20,
  realtime = true,
  onActivityClick,
  onActionRequired
}) => {
  const [filters, setFilters] = useState<ActivityFilters>(initialFilters || {});
  
  // 数据获取
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isLoading
  } = useInfiniteQuery({
    queryKey: ['activities', tenantId, filters],
    queryFn: ({ pageParam }) => fetchActivities(tenantId, filters, pageSize, pageParam),
    getNextPageParam: (lastPage) => lastPage.nextCursor
  });
  
  // WebSocket实时更新
  useActivityWebSocket(tenantId, filters, realtime);
  
  return (
    <div className="flex flex-col h-full">
      <ActivityFilters filters={filters} onChange={setFilters} />
      <ActivityList 
        activities={data?.pages.flatMap(p => p.activities) || []}
        onActivityClick={onActivityClick}
        onActionRequired={onActionRequired}
      />
      {hasNextPage && (
        <LoadMoreButton onClick={() => fetchNextPage()} />
      )}
    </div>
  );
};
```

#### 活动卡片组件
```typescript
// components/AgentActivityFeed/ActivityCard.tsx
interface ActivityCardProps {
  activity: AgentActivity;
  onClick?: () => void;
  onAction?: (action: string) => void;
}

export const ActivityCard: React.FC<ActivityCardProps> = ({
  activity,
  onClick,
  onAction
}) => {
  const levelColors = {
    info: 'border-blue-500 bg-blue-50',
    warning: 'border-yellow-500 bg-yellow-50',
    error: 'border-red-500 bg-red-50',
    critical: 'border-red-700 bg-red-100'
  };
  
  return (
    <div 
      className={`p-4 border-l-4 rounded-r-lg ${levelColors[activity.level]}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <span className="text-gray-500 text-sm">
            {formatTime(activity.timestamp)}
          </span>
          <span className="ml-2 text-gray-700">
            {getAgentName(activity.agentType)}
          </span>
        </div>
        {activity.requiresAttention && (
          <Badge variant="warning">需关注</Badge>
        )}
      </div>
      
      <h4 className="font-medium mt-2">{activity.title}</h4>
      <p className="text-gray-600 text-sm">{activity.description}</p>
      
      {activity.details && (
        <ActivityDetails details={activity.details} />
      )}
      
      <ActivityActions 
        activity={activity} 
        onAction={onAction}
      />
    </div>
  );
};
```

#### WebSocket Hook
```typescript
// hooks/useActivityWebSocket.ts
export const useActivityWebSocket = (
  tenantId: string,
  filters: ActivityFilters,
  enabled: boolean
) => {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    if (!enabled) return;
    
    const ws = new WebSocket(
      `${WS_BASE_URL}/api/v1/agents/ws/activities?token=${getToken()}&tenant_id=${tenantId}`
    );
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        filters: {
          agent_types: filters.agentType ? [filters.agentType] : undefined,
          levels: filters.level ? [filters.level] : undefined
        }
      }));
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'activity') {
        // 更新缓存，将新活动添加到列表顶部
        queryClient.setQueryData(
          ['activities', tenantId, filters],
          (old: any) => {
            if (!old) return old;
            return {
              ...old,
              pages: [
                {
                  ...old.pages[0],
                  activities: [message.data, ...old.pages[0].activities]
                },
                ...old.pages.slice(1)
              ]
            };
          }
        );
      }
    };
    
    return () => ws.close();
  }, [tenantId, filters, enabled, queryClient]);
};
```

### 4.3 状态管理
```typescript
// 使用React Query管理服务端状态
// 使用useState管理本地UI状态（筛选条件、展开状态等）

// 活动缓存策略
const queryConfig = {
  staleTime: 30 * 1000,      // 30秒后标记为stale
  cacheTime: 5 * 60 * 1000,  // 5分钟后清除缓存
  refetchOnWindowFocus: true, // 窗口聚焦时刷新
};
```

---

## 5. 测试要求

### 5.1 单元测试
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentActivityFeed } from './AgentActivityFeed';

describe('AgentActivityFeed', () => {
  it('renders activity list', async () => {
    render(<AgentActivityFeed tenantId="tenant_001" />);
    
    await waitFor(() => {
      expect(screen.getByText('任务分配决策')).toBeInTheDocument();
    });
  });
  
  it('filters by agent type', async () => {
    render(<AgentActivityFeed tenantId="tenant_001" />);
    
    await userEvent.click(screen.getByRole('combobox', { name: /agent/i }));
    await userEvent.click(screen.getByText('清洁调度'));
    
    // 验证筛选结果
  });
  
  it('handles websocket updates', async () => {
    // Mock WebSocket
    const mockWs = new MockWebSocket();
    
    render(<AgentActivityFeed tenantId="tenant_001" realtime={true} />);
    
    // 模拟新活动推送
    mockWs.triggerMessage({
      type: 'activity',
      data: mockActivity
    });
    
    await waitFor(() => {
      expect(screen.getByText(mockActivity.title)).toBeInTheDocument();
    });
  });
});
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] 活动列表正常加载
- [ ] 筛选功能正常
- [ ] 无限滚动加载正常
- [ ] WebSocket实时更新正常
- [ ] 活动详情展开收起正常
- [ ] 快捷操作按钮可用
- [ ] 跳转链接正确

### 6.2 性能要求
- 首屏渲染 < 500ms
- 滚动加载 < 200ms
- WebSocket消息处理 < 50ms

### 6.3 兼容性
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
