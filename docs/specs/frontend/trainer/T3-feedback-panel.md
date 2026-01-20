# 模块开发规格书：T3 反馈面板组件

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | T3 |
| 模块名称 | 反馈面板组件 |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | G5 Agent交互API |

---

## 1. 模块概述

### 1.1 职责描述
反馈面板组件用于训练师对Agent决策提交反馈，支持认可、纠正、拒绝三种类型，帮助Agent持续学习和改进。

### 1.2 功能概述
- 查看Agent决策详情
- 提交评分和评价
- 提供纠正建议
- 查看反馈历史
- 反馈统计分析

---

## 2. UI设计

### 2.1 反馈表单
```
┌─────────────────────────────────────────────────────────────┐
│ 决策反馈                                              [关闭] │
├─────────────────────────────────────────────────────────────┤
│ ┌─ 决策信息 ───────────────────────────────────────────────┐│
│ │ 决策类型: 任务分配                                        ││
│ │ 时间: 2026-01-20 10:30:15                                ││
│ │ Agent: 清洁调度Agent                                     ││
│ │                                                          ││
│ │ 决策内容:                                                ││
│ │ 将任务 task_001(大堂清洁) 分配给 robot_001               ││
│ │                                                          ││
│ │ 推理过程:                                                ││
│ │ robot_001距离最近(15m)，电量充足(85%)，历史表现4.5分     ││
│ └──────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ ┌─ 您的反馈 ───────────────────────────────────────────────┐│
│ │                                                          ││
│ │ 反馈类型:                                                ││
│ │ ○ 👍 认可 - 决策正确                                     ││
│ │ ● ✏️ 纠正 - 有更好选择                                   ││
│ │ ○ ❌ 拒绝 - 决策错误                                     ││
│ │                                                          ││
│ │ 评分: ⭐⭐⭐⭐☆  (4/5)                                    ││
│ │                                                          ││
│ │ ┌─ 纠正建议 ─────────────────────────────────────────┐   ││
│ │ │ 建议分配给: [robot_003 ▼]                          │   ││
│ │ │ 原因: [大面积清洁更适合 ▼]                         │   ││
│ │ │                                                    │   ││
│ │ │ 补充说明:                                          │   ││
│ │ │ ┌────────────────────────────────────────────────┐ │   ││
│ │ │ │robot_003擅长大面积清洁，效率更高              │ │   ││
│ │ │ └────────────────────────────────────────────────┘ │   ││
│ │ └────────────────────────────────────────────────────┘   ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│                              [取消]  [提交反馈]              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 反馈历史列表
```
┌─────────────────────────────────────────────────────────────┐
│ 我的反馈历史                                        [筛选]   │
├─────────────────────────────────────────────────────────────┤
│ 今天                                                        │
│ ├─ 10:30  任务分配  ✏️纠正  ⭐⭐⭐⭐☆  [查看]               │
│ ├─ 09:15  异常处理  👍认可  ⭐⭐⭐⭐⭐  [查看]               │
│ └─ 08:45  调度优化  👍认可  ⭐⭐⭐⭐⭐  [查看]               │
│                                                             │
│ 昨天                                                        │
│ ├─ 16:20  任务分配  ❌拒绝  ⭐⭐☆☆☆  [查看]                │
│ └─ ...                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 组件接口

### 3.1 Props定义
```typescript
interface FeedbackPanelProps {
  activity: AgentActivity;
  onSubmit: (feedback: FeedbackData) => Promise<void>;
  onCancel: () => void;
}

interface FeedbackHistoryProps {
  tenantId: string;
  userId?: string;
  dateRange?: { start: Date; end: Date };
}
```

### 3.2 数据类型
```typescript
type FeedbackType = 'approval' | 'correction' | 'rejection';

interface FeedbackData {
  activityId: string;
  feedbackType: FeedbackType;
  rating: number;  // 1-5
  comment?: string;
  correctionData?: {
    suggestedRobotId?: string;
    reason?: string;
    additionalNotes?: string;
  };
}

interface FeedbackRecord {
  feedbackId: string;
  activityId: string;
  feedbackType: FeedbackType;
  rating: number;
  comment?: string;
  correctionData?: object;
  createdAt: string;
  activity: {
    title: string;
    agentType: string;
  };
}
```

### 3.3 API调用
```typescript
// 提交反馈
POST /api/v1/agents/feedback
  body: FeedbackData

// 获取反馈历史
GET /api/v1/agents/feedback/history
  ?tenant_id={tenantId}
  &user_id={userId}
  &start_date={startDate}
  &end_date={endDate}
```

---

## 4. 实现要求

### 4.1 核心组件
```typescript
// components/FeedbackPanel/index.tsx
export const FeedbackPanel: React.FC<FeedbackPanelProps> = ({
  activity,
  onSubmit,
  onCancel
}) => {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('approval');
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [correction, setCorrection] = useState<CorrectionData | null>(null);
  
  const handleSubmit = async () => {
    const feedback: FeedbackData = {
      activityId: activity.activityId,
      feedbackType,
      rating,
      comment: comment || undefined,
      correctionData: feedbackType === 'correction' ? correction : undefined
    };
    
    await onSubmit(feedback);
  };
  
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <DecisionInfo activity={activity} />
      
      <div className="mt-6">
        <FeedbackTypeSelector 
          value={feedbackType} 
          onChange={setFeedbackType} 
        />
        
        <RatingInput value={rating} onChange={setRating} />
        
        {feedbackType === 'correction' && (
          <CorrectionForm 
            activity={activity}
            value={correction}
            onChange={setCorrection}
          />
        )}
        
        <CommentInput value={comment} onChange={setComment} />
      </div>
      
      <div className="flex justify-end gap-3 mt-6">
        <Button variant="secondary" onClick={onCancel}>取消</Button>
        <Button variant="primary" onClick={handleSubmit}>提交反馈</Button>
      </div>
    </div>
  );
};
```

### 4.2 评分组件
```typescript
// components/FeedbackPanel/RatingInput.tsx
export const RatingInput: React.FC<{
  value: number;
  onChange: (value: number) => void;
}> = ({ value, onChange }) => {
  return (
    <div className="flex items-center gap-1">
      <span className="text-sm text-gray-600 mr-2">评分:</span>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onChange(star)}
          className="text-2xl focus:outline-none"
        >
          {star <= value ? '⭐' : '☆'}
        </button>
      ))}
      <span className="ml-2 text-gray-500">({value}/5)</span>
    </div>
  );
};
```

### 4.3 纠正建议表单
```typescript
// components/FeedbackPanel/CorrectionForm.tsx
export const CorrectionForm: React.FC<{
  activity: AgentActivity;
  value: CorrectionData | null;
  onChange: (data: CorrectionData) => void;
}> = ({ activity, value, onChange }) => {
  const { data: robots } = useQuery({
    queryKey: ['available-robots', activity.details?.buildingId],
    queryFn: () => fetchAvailableRobots(activity.details?.buildingId)
  });
  
  const reasons = [
    { value: 'large_area_preference', label: '大面积清洁更适合' },
    { value: 'battery_consideration', label: '电量考虑' },
    { value: 'location_better', label: '位置更优' },
    { value: 'performance_history', label: '历史表现更好' },
    { value: 'other', label: '其他原因' }
  ];
  
  return (
    <div className="border rounded-lg p-4 mt-4 bg-gray-50">
      <h4 className="font-medium mb-3">纠正建议</h4>
      
      <div className="space-y-3">
        <Select
          label="建议分配给"
          options={robots?.map(r => ({ value: r.robotId, label: r.name }))}
          value={value?.suggestedRobotId}
          onChange={(v) => onChange({ ...value, suggestedRobotId: v })}
        />
        
        <Select
          label="原因"
          options={reasons}
          value={value?.reason}
          onChange={(v) => onChange({ ...value, reason: v })}
        />
        
        <Textarea
          label="补充说明"
          value={value?.additionalNotes || ''}
          onChange={(v) => onChange({ ...value, additionalNotes: v })}
          rows={3}
        />
      </div>
    </div>
  );
};
```

---

## 5. 测试要求

### 5.1 单元测试
```typescript
describe('FeedbackPanel', () => {
  it('submits approval feedback', async () => {
    const onSubmit = jest.fn();
    render(<FeedbackPanel activity={mockActivity} onSubmit={onSubmit} onCancel={() => {}} />);
    
    await userEvent.click(screen.getByText('👍 认可'));
    await userEvent.click(screen.getByText('提交反馈'));
    
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ feedbackType: 'approval' })
    );
  });
  
  it('shows correction form when correction selected', async () => {
    render(<FeedbackPanel activity={mockActivity} onSubmit={() => {}} onCancel={() => {}} />);
    
    await userEvent.click(screen.getByText('✏️ 纠正'));
    
    expect(screen.getByText('纠正建议')).toBeInTheDocument();
  });
});
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] 三种反馈类型正常切换
- [ ] 评分输入正常
- [ ] 纠正表单显示和隐藏正确
- [ ] 反馈提交成功
- [ ] 反馈历史显示正确

### 6.2 性能要求
- 表单渲染 < 100ms
- 提交响应 < 500ms
