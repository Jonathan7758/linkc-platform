# 模块开发规格书：T2 待处理队列组件

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | T2 |
| 模块名称 | 待处理队列组件 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | G5 Agent交互API |

---

## 1. 模块概述

### 1.1 职责描述
待处理队列组件展示需要训练师人工处理的事项（异常升级、决策确认等），支持快速处理和批量操作。

### 1.2 功能概述
- 展示待处理事项列表
- 按优先级排序和筛选
- 一键处理/批量处理
- 过期提醒
- 处理历史记录

---

## 2. UI设计

### 2.1 组件布局
```
┌─────────────────────────────────────────────────────────────┐
│ 待处理队列                           [批量处理] [刷新] 🔔 3  │
├─────────────────────────────────────────────────────────────┤
│ ┌─ 统计栏 ──────────────────────────────────────────────────┐│
│ │ 🔴 紧急: 1    🟠 高: 2    🟡 中: 3    🟢 低: 1           ││
│ └──────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ ┌─ 待处理列表 ─────────────────────────────────────────────┐│
│ │ ☐ 🔴 机器人故障需处理                     ⏰ 还剩15分钟  ││
│ │    robot_003报告电机过热，需要人工确认                    ││
│ │    [立即返回充电] [派人检查] [暂时忽略]                   ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ ☐ 🟠 任务调度确认                         ⏰ 还剩45分钟  ││
│ │    Agent建议调整清洁顺序以优化电量使用                    ││
│ │    [批准调整] [保持原计划] [查看详情]                     ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ ☐ 🟡 覆盖率异常                           ⏰ 还剩2小时   ││
│ │    3F走廊区域本周覆盖率仅65%，低于目标                    ││
│ │    [增加清洁频次] [调整任务] [标记已知]                   ││
│ └──────────────────────────────────────────────────────────┘│
│ ┌─ 已处理 (今日) ─────────────────────────────────── [展开] ┐│
│ │ ✓ 已处理 5 项                                            ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 待处理卡片
```
┌────────────────────────────────────────────────────────────┐
│ ☐  🔴 紧急                                    ⏰ 还剩15分钟│
├────────────────────────────────────────────────────────────┤
│ 🤖 机器人故障需处理                                        │
│                                                            │
│ robot_003(清洁机器人3号)报告电机过热错误                    │
│ 当前位置: A座3F走廊                                        │
│ 发生时间: 10:25                                            │
│                                                            │
│ ┌─ Agent建议 ──────────────────────────────────────────┐  │
│ │ 建议立即停止工作并返回充电站进行检查                   │  │
│ │ 置信度: 92%                                           │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                            │
│ [🔙 立即返回充电]  [👷 派人检查]  [⏸️ 暂停观察]            │
└────────────────────────────────────────────────────────────┘
```

---

## 3. 组件接口

### 3.1 Props定义
```typescript
interface PendingQueueProps {
  tenantId: string;
  // 自动刷新间隔（秒），0表示禁用
  refreshInterval?: number;  // default: 30
  // 处理完成回调
  onItemResolved?: (item: PendingItem, action: string) => void;
  // 超时警告回调
  onExpirationWarning?: (item: PendingItem) => void;
}
```

### 3.2 数据类型
```typescript
interface PendingItem {
  itemId: string;
  type: 'escalation' | 'confirmation' | 'alert';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_progress' | 'resolved' | 'expired';
  title: string;
  description: string;
  agentType: string;
  relatedEntities: {
    robotId?: string;
    taskId?: string;
    zoneId?: string;
  };
  suggestedActions: SuggestedAction[];
  createdAt: string;
  expiresAt?: string;
}

interface SuggestedAction {
  action: string;
  label: string;
  variant?: 'primary' | 'secondary' | 'danger';
  params?: Record<string, any>;
}
```

### 3.3 API调用
```typescript
// 获取待处理列表
GET /api/v1/agents/pending-items
  ?tenant_id={tenantId}
  &status=pending
  &limit=50

// 处理事项
POST /api/v1/agents/pending-items/{itemId}/resolve
  body: { action: string, comment?: string, params?: object }
```

---

## 4. 实现要求

### 4.1 技术栈
- React 18+ / TypeScript
- TailwindCSS
- React Query
- date-fns (时间处理)

### 4.2 核心实现
```typescript
// components/PendingQueue/index.tsx
export const PendingQueue: React.FC<PendingQueueProps> = ({
  tenantId,
  refreshInterval = 30,
  onItemResolved,
  onExpirationWarning
}) => {
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  
  const { data, refetch } = useQuery({
    queryKey: ['pending-items', tenantId],
    queryFn: () => fetchPendingItems(tenantId),
    refetchInterval: refreshInterval * 1000
  });
  
  const resolveMutation = useMutation({
    mutationFn: resolveItem,
    onSuccess: (_, { itemId, action }) => {
      queryClient.invalidateQueries(['pending-items']);
      onItemResolved?.(data?.items.find(i => i.itemId === itemId)!, action);
    }
  });
  
  // 过期检查
  useEffect(() => {
    const checkExpiration = () => {
      data?.items.forEach(item => {
        if (item.expiresAt) {
          const remaining = new Date(item.expiresAt).getTime() - Date.now();
          if (remaining < 5 * 60 * 1000 && remaining > 0) {  // 5分钟内
            onExpirationWarning?.(item);
          }
        }
      });
    };
    const interval = setInterval(checkExpiration, 60000);
    return () => clearInterval(interval);
  }, [data]);
  
  return (
    <div className="flex flex-col h-full">
      <PriorityStats items={data?.items || []} />
      <PendingList 
        items={data?.items || []}
        selectedItems={selectedItems}
        onSelect={setSelectedItems}
        onResolve={(itemId, action) => resolveMutation.mutate({ itemId, action })}
      />
    </div>
  );
};
```

### 4.3 倒计时显示
```typescript
const ExpirationTimer: React.FC<{ expiresAt: string }> = ({ expiresAt }) => {
  const [remaining, setRemaining] = useState(
    new Date(expiresAt).getTime() - Date.now()
  );
  
  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining(new Date(expiresAt).getTime() - Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, [expiresAt]);
  
  if (remaining <= 0) return <span className="text-red-600">已过期</span>;
  
  const minutes = Math.floor(remaining / 60000);
  const hours = Math.floor(minutes / 60);
  
  const color = minutes < 15 ? 'text-red-600' : 
                minutes < 60 ? 'text-yellow-600' : 'text-gray-600';
  
  return (
    <span className={color}>
      ⏰ 还剩{hours > 0 ? `${hours}小时` : `${minutes}分钟`}
    </span>
  );
};
```

---

## 5. 测试要求

### 5.1 单元测试
```typescript
describe('PendingQueue', () => {
  it('displays pending items sorted by priority', async () => {
    render(<PendingQueue tenantId="tenant_001" />);
    await waitFor(() => {
      const items = screen.getAllByRole('listitem');
      // 验证critical在前
    });
  });
  
  it('resolves item on action click', async () => {
    const onResolved = jest.fn();
    render(<PendingQueue tenantId="tenant_001" onItemResolved={onResolved} />);
    
    await userEvent.click(screen.getByText('立即返回充电'));
    
    await waitFor(() => {
      expect(onResolved).toHaveBeenCalled();
    });
  });
  
  it('shows expiration warning', async () => {
    const onWarning = jest.fn();
    render(<PendingQueue tenantId="tenant_001" onExpirationWarning={onWarning} />);
    
    // 模拟时间流逝
    jest.advanceTimersByTime(60000);
    
    expect(onWarning).toHaveBeenCalled();
  });
});
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] 待处理列表正确显示
- [ ] 按优先级排序正确
- [ ] 倒计时显示正确
- [ ] 处理操作正常执行
- [ ] 批量处理功能正常
- [ ] 自动刷新正常

### 6.2 性能要求
- 列表渲染 < 100ms
- 处理响应 < 500ms
