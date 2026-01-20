# E3 报表中心规格书

## 文档信息
- **模块ID**: E3
- **模块名称**: 报表中心 (Report Center)
- **版本**: 1.0
- **日期**: 2026年1月
- **状态**: 规划中
- **前置依赖**: G6数据API, E1战略总览, E2数据分析

---

## 1. 模块概述

### 1.1 职责描述

报表中心是战略驾驶舱的报表生成和管理模块，负责：
- 周期性报表自动生成和分发
- 自定义报表模板管理
- 报表订阅和通知
- 历史报表存档和查询
- 多格式报表导出（PDF/Excel/PPT）

### 1.2 核心功能

| 功能 | 描述 | 优先级 |
|-----|------|-------|
| 报表模板 | 预定义和自定义报表模板管理 | P0 |
| 报表生成 | 手动和定时生成报表 | P0 |
| 报表列表 | 查看和管理所有报表 | P0 |
| 报表预览 | 在线预览报表内容 | P0 |
| 报表导出 | 多格式导出（PDF/Excel/PPT） | P0 |
| 报表订阅 | 定期自动发送报表到邮箱 | P1 |
| 报表分享 | 生成分享链接或发送给同事 | P1 |
| 报表对比 | 多期报表对比分析 | P2 |

### 1.3 目标用户

| 角色 | 使用场景 | 关注重点 |
|-----|---------|---------|
| 高管 | 查看定期运营报告 | 关键指标、趋势、异常 |
| 运营经理 | 生成部门周报 | 详细数据、执行情况 |
| 客户 | 接收服务报告 | SLA达成、服务质量 |

---

## 2. 报表类型定义

### 2.1 标准报表模板

```typescript
// 报表模板定义
interface ReportTemplate {
  id: string;
  name: string;
  type: ReportType;
  description: string;
  category: ReportCategory;
  
  // 报表内容配置
  sections: ReportSection[];
  
  // 数据配置
  dataConfig: ReportDataConfig;
  
  // 样式配置
  styleConfig: ReportStyleConfig;
  
  // 调度配置
  scheduleConfig?: ReportScheduleConfig;
  
  // 元数据
  isSystem: boolean;       // 系统模板
  isActive: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

type ReportType = 
  | 'daily'           // 日报
  | 'weekly'          // 周报
  | 'monthly'         // 月报
  | 'quarterly'       // 季报
  | 'annual'          // 年报
  | 'custom';         // 自定义

type ReportCategory = 
  | 'operations'      // 运营报表
  | 'financial'       // 财务报表
  | 'performance'     // 绩效报表
  | 'customer'        // 客户报表
  | 'equipment'       // 设备报表
  | 'custom';         // 自定义

// 报表章节
interface ReportSection {
  id: string;
  type: SectionType;
  title: string;
  order: number;
  config: SectionConfig;
}

type SectionType = 
  | 'summary'         // 摘要
  | 'kpi_metrics'     // KPI指标
  | 'trend_chart'     // 趋势图表
  | 'comparison'      // 对比分析
  | 'table'           // 数据表格
  | 'heatmap'         // 热力图
  | 'text'            // 文本说明
  | 'recommendations' // 建议
  | 'appendix';       // 附录

interface SectionConfig {
  // 数据源
  dataSource: {
    type: 'api' | 'query' | 'static';
    endpoint?: string;
    query?: string;
    staticData?: any;
  };
  
  // 可视化配置
  visualization?: {
    chartType?: ChartType;
    dimensions?: string[];
    metrics?: string[];
    colors?: string[];
  };
  
  // 布局配置
  layout?: {
    width?: 'full' | 'half' | 'third';
    height?: number;
    pageBreakBefore?: boolean;
  };
}
```

### 2.2 系统预置模板

```typescript
// 系统预置报表模板
const SYSTEM_TEMPLATES: ReportTemplate[] = [
  {
    id: 'daily-operations',
    name: '日常运营报告',
    type: 'daily',
    category: 'operations',
    description: '每日运营情况汇总，包含任务完成、机器人状态、异常事件',
    sections: [
      { id: 's1', type: 'summary', title: '今日概览', order: 1, config: {...} },
      { id: 's2', type: 'kpi_metrics', title: '核心指标', order: 2, config: {...} },
      { id: 's3', type: 'table', title: '任务执行明细', order: 3, config: {...} },
      { id: 's4', type: 'table', title: '异常事件列表', order: 4, config: {...} },
      { id: 's5', type: 'recommendations', title: '改进建议', order: 5, config: {...} },
    ],
    isSystem: true,
    isActive: true,
  },
  {
    id: 'weekly-summary',
    name: '周度运营总结',
    type: 'weekly',
    category: 'operations',
    description: '每周运营总结，包含趋势分析和周环比',
    sections: [
      { id: 's1', type: 'summary', title: '本周概览', order: 1, config: {...} },
      { id: 's2', type: 'kpi_metrics', title: '核心指标（环比）', order: 2, config: {...} },
      { id: 's3', type: 'trend_chart', title: '日度趋势', order: 3, config: {...} },
      { id: 's4', type: 'comparison', title: '楼宇对比', order: 4, config: {...} },
      { id: 's5', type: 'table', title: '本周亮点', order: 5, config: {...} },
      { id: 's6', type: 'table', title: '待改进项', order: 6, config: {...} },
      { id: 's7', type: 'recommendations', title: '下周计划', order: 7, config: {...} },
    ],
    isSystem: true,
    isActive: true,
  },
  {
    id: 'monthly-report',
    name: '月度运营报告',
    type: 'monthly',
    category: 'operations',
    description: '完整的月度运营分析报告',
    sections: [
      { id: 's1', type: 'summary', title: '执行摘要', order: 1, config: {...} },
      { id: 's2', type: 'kpi_metrics', title: 'KPI达成情况', order: 2, config: {...} },
      { id: 's3', type: 'trend_chart', title: '月度趋势分析', order: 3, config: {...} },
      { id: 's4', type: 'comparison', title: '同比环比分析', order: 4, config: {...} },
      { id: 's5', type: 'heatmap', title: '效率热力图', order: 5, config: {...} },
      { id: 's6', type: 'table', title: '楼宇绩效排名', order: 6, config: {...} },
      { id: 's7', type: 'table', title: '机器人利用率', order: 7, config: {...} },
      { id: 's8', type: 'table', title: '成本分析', order: 8, config: {...} },
      { id: 's9', type: 'recommendations', title: '优化建议', order: 9, config: {...} },
      { id: 's10', type: 'appendix', title: '附录：详细数据', order: 10, config: {...} },
    ],
    isSystem: true,
    isActive: true,
  },
  {
    id: 'customer-sla-report',
    name: '客户SLA报告',
    type: 'monthly',
    category: 'customer',
    description: '面向客户的服务水平报告',
    sections: [
      { id: 's1', type: 'summary', title: '服务概览', order: 1, config: {...} },
      { id: 's2', type: 'kpi_metrics', title: 'SLA达成率', order: 2, config: {...} },
      { id: 's3', type: 'table', title: '服务覆盖详情', order: 3, config: {...} },
      { id: 's4', type: 'trend_chart', title: '服务质量趋势', order: 4, config: {...} },
      { id: 's5', type: 'table', title: '事件响应记录', order: 5, config: {...} },
    ],
    isSystem: true,
    isActive: true,
  },
  {
    id: 'equipment-health',
    name: '设备健康报告',
    type: 'weekly',
    category: 'equipment',
    description: '机器人设备状态和维护报告',
    sections: [
      { id: 's1', type: 'summary', title: '设备概览', order: 1, config: {...} },
      { id: 's2', type: 'kpi_metrics', title: '可用率指标', order: 2, config: {...} },
      { id: 's3', type: 'table', title: '设备状态清单', order: 3, config: {...} },
      { id: 's4', type: 'table', title: '维护记录', order: 4, config: {...} },
      { id: 's5', type: 'table', title: '耗材更换计划', order: 5, config: {...} },
      { id: 's6', type: 'recommendations', title: '维护建议', order: 6, config: {...} },
    ],
    isSystem: true,
    isActive: true,
  },
];
```

---

## 3. 页面结构

### 3.1 整体布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📊 报表中心                                           [+ 新建报表]     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─ 标签页 ─────────────────────────────────────────────────────────┐  │
│  │  [我的报表]  [报表模板]  [订阅管理]  [生成历史]                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ 筛选栏 ─────────────────────────────────────────────────────────┐  │
│  │  类型: [全部▼]  周期: [全部▼]  时间: [最近30天▼]  🔍 搜索报表   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ 报表列表/网格 ───────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│  │
│  │  │ 📄          │ │ 📄          │ │ 📄          │ │ 📄          ││  │
│  │  │ 12月运营报告│ │ 第51周周报 │ │ 11月SLA报告│ │ 设备健康报告││  │
│  │  │             │ │             │ │             │ │             ││  │
│  │  │ 月报        │ │ 周报        │ │ 客户报表    │ │ 设备报表    ││  │
│  │  │ 2026-01-01  │ │ 2025-12-23  │ │ 2025-12-15  │ │ 2025-12-20  ││  │
│  │  │ [预览][下载]│ │ [预览][下载]│ │ [预览][下载]│ │ [预览][下载]││  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│  │
│  │                                                                   │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│  │
│  │  │ ...         │ │ ...         │ │ ...         │ │ ...         ││  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  分页: [< 1 2 3 4 5 >]                            显示: [12▼] 条/页   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 报表预览弹窗

```
┌─────────────────────────────────────────────────────────────────────────┐
│  12月运营月报                                    [导出▼] [分享] [×]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─ 工具栏 ─────────────────────────────────────────────────────────┐  │
│  │  [缩小] [100%] [放大]  |  [上一页] 1/10 [下一页]  |  [全屏]      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ 报表内容预览 ────────────────────────────────────────────────────┐  │
│  │  ╔═══════════════════════════════════════════════════════════════╗ │  │
│  │  ║                                                               ║ │  │
│  │  ║                    LinkC 月度运营报告                         ║ │  │
│  │  ║                      2025年12月                               ║ │  │
│  │  ║                                                               ║ │  │
│  │  ║  ─────────────────────────────────────────────────────────── ║ │  │
│  │  ║                                                               ║ │  │
│  │  ║  1. 执行摘要                                                  ║ │  │
│  │  ║                                                               ║ │  │
│  │  ║  本月清洁任务完成率达到98.5%，较上月提升2.3个百分点。       ║ │  │
│  │  ║  机器人可用率保持在99.2%，成本节约达到HK$45,000。           ║ │  │
│  │  ║                                                               ║ │  │
│  │  ║  2. 核心指标                                                  ║ │  │
│  │  ║  ┌─────────┬─────────┬─────────┬─────────┐                   ║ │  │
│  │  ║  │ 完成率  │ 覆盖率  │ 可用率  │ 节约    │                   ║ │  │
│  │  ║  │ 98.5%  │ 95.2%  │ 99.2%  │ $45K    │                   ║ │  │
│  │  ║  └─────────┴─────────┴─────────┴─────────┘                   ║ │  │
│  │  ║                                                               ║ │  │
│  │  ╚═══════════════════════════════════════════════════════════════╝ │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  报表信息: 生成时间 2026-01-01 08:00 | 生成者: 系统自动 | 大小: 2.3MB │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 组件定义

### 4.1 报表列表组件

```typescript
// ReportList.tsx
interface ReportListProps {
  // 当前标签页
  activeTab: 'my_reports' | 'templates' | 'subscriptions' | 'history';
  
  // 筛选条件
  filters: ReportFilters;
  onFiltersChange: (filters: ReportFilters) => void;
  
  // 视图模式
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
  
  // 回调
  onPreview: (report: Report) => void;
  onDownload: (report: Report, format: ExportFormat) => void;
  onShare: (report: Report) => void;
  onDelete: (report: Report) => void;
}

interface ReportFilters {
  type?: ReportType[];
  category?: ReportCategory[];
  dateRange?: [string, string];
  keyword?: string;
  status?: ReportStatus[];
}

type ReportStatus = 'generated' | 'generating' | 'failed' | 'scheduled';

// 报表实例
interface Report {
  id: string;
  templateId: string;
  name: string;
  type: ReportType;
  category: ReportCategory;
  
  // 时间范围
  periodStart: string;
  periodEnd: string;
  
  // 生成信息
  status: ReportStatus;
  generatedAt?: string;
  generatedBy: 'system' | 'user';
  
  // 文件信息
  fileUrl?: string;
  fileSize?: number;
  pageCount?: number;
  
  // 元数据
  tags?: string[];
  notes?: string;
}
```

### 4.2 报表模板管理组件

```typescript
// TemplateManager.tsx
interface TemplateManagerProps {
  templates: ReportTemplate[];
  onCreateTemplate: () => void;
  onEditTemplate: (template: ReportTemplate) => void;
  onDuplicateTemplate: (template: ReportTemplate) => void;
  onDeleteTemplate: (template: ReportTemplate) => void;
  onGenerateReport: (template: ReportTemplate, config: GenerateConfig) => void;
}

interface GenerateConfig {
  // 时间范围
  periodType: 'last_day' | 'last_week' | 'last_month' | 'custom';
  customRange?: [string, string];
  
  // 数据范围
  buildingIds?: string[];
  robotIds?: string[];
  
  // 输出配置
  format: ExportFormat;
  includeRawData?: boolean;
  
  // 通知配置
  notifyOnComplete?: boolean;
  recipients?: string[];
}

type ExportFormat = 'pdf' | 'excel' | 'pptx' | 'html';
```

### 4.3 报表编辑器组件

```typescript
// ReportEditor.tsx
interface ReportEditorProps {
  template?: ReportTemplate;   // 编辑现有模板或新建
  onSave: (template: ReportTemplate) => void;
  onCancel: () => void;
  onPreview: (template: ReportTemplate) => void;
}

interface ReportEditorState {
  // 基本信息
  name: string;
  type: ReportType;
  category: ReportCategory;
  description: string;
  
  // 章节列表
  sections: ReportSection[];
  selectedSectionId?: string;
  
  // 拖拽状态
  isDragging: boolean;
  dragIndex?: number;
  
  // 预览状态
  isPreviewOpen: boolean;
  previewData?: any;
}
```

### 4.4 章节编辑组件

```typescript
// SectionEditor.tsx
interface SectionEditorProps {
  section: ReportSection;
  onChange: (section: ReportSection) => void;
  onDelete: () => void;
  availableDataSources: DataSource[];
}

interface DataSource {
  id: string;
  name: string;
  type: 'metric' | 'timeseries' | 'table' | 'distribution';
  description: string;
  parameters?: DataSourceParameter[];
}

interface DataSourceParameter {
  name: string;
  type: 'string' | 'number' | 'date' | 'select' | 'multi_select';
  label: string;
  required: boolean;
  defaultValue?: any;
  options?: { value: string; label: string }[];
}
```

### 4.5 订阅管理组件

```typescript
// SubscriptionManager.tsx
interface SubscriptionManagerProps {
  subscriptions: ReportSubscription[];
  onCreateSubscription: () => void;
  onEditSubscription: (subscription: ReportSubscription) => void;
  onDeleteSubscription: (subscription: ReportSubscription) => void;
  onToggleSubscription: (subscription: ReportSubscription, enabled: boolean) => void;
}

interface ReportSubscription {
  id: string;
  name: string;
  templateId: string;
  templateName: string;
  
  // 调度配置
  schedule: ScheduleConfig;
  
  // 发送配置
  delivery: DeliveryConfig;
  
  // 状态
  isActive: boolean;
  lastRunAt?: string;
  lastRunStatus?: 'success' | 'failed';
  nextRunAt?: string;
  
  // 元数据
  createdBy: string;
  createdAt: string;
}

interface ScheduleConfig {
  type: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  
  // 每日配置
  dailyTime?: string;  // HH:mm
  
  // 每周配置
  weeklyDay?: number;  // 0-6
  weeklyTime?: string;
  
  // 每月配置
  monthlyDay?: number;  // 1-31
  monthlyTime?: string;
  
  // 时区
  timezone: string;
}

interface DeliveryConfig {
  // 邮件配置
  emailRecipients: string[];
  emailSubject?: string;
  emailBody?: string;
  
  // 附件格式
  attachmentFormat: ExportFormat;
  
  // 内联预览
  includeInlinePreview?: boolean;
}
```

### 4.6 报表预览组件

```typescript
// ReportPreview.tsx
interface ReportPreviewProps {
  report: Report;
  onClose: () => void;
  onDownload: (format: ExportFormat) => void;
  onShare: () => void;
}

interface ReportPreviewState {
  // 加载状态
  isLoading: boolean;
  error?: string;
  
  // 预览内容
  content?: ReportContent;
  
  // 分页
  currentPage: number;
  totalPages: number;
  
  // 缩放
  zoom: number;
  
  // 全屏
  isFullscreen: boolean;
}

interface ReportContent {
  pages: ReportPage[];
  metadata: {
    title: string;
    period: string;
    generatedAt: string;
    totalPages: number;
  };
}

interface ReportPage {
  pageNumber: number;
  content: string;  // HTML content
  charts?: ChartData[];
  tables?: TableData[];
}
```

---

## 5. 数据流设计

### 5.1 状态管理

```typescript
// stores/reportStore.ts
import { create } from 'zustand';

interface ReportStore {
  // 报表列表
  reports: Report[];
  reportsLoading: boolean;
  reportsError?: string;
  
  // 模板列表
  templates: ReportTemplate[];
  templatesLoading: boolean;
  
  // 订阅列表
  subscriptions: ReportSubscription[];
  subscriptionsLoading: boolean;
  
  // 当前报表
  currentReport?: Report;
  currentReportContent?: ReportContent;
  
  // 报表生成
  generatingReports: Map<string, GenerationProgress>;
  
  // Actions
  fetchReports: (filters?: ReportFilters) => Promise<void>;
  fetchTemplates: () => Promise<void>;
  fetchSubscriptions: () => Promise<void>;
  
  generateReport: (templateId: string, config: GenerateConfig) => Promise<string>;
  downloadReport: (reportId: string, format: ExportFormat) => Promise<void>;
  deleteReport: (reportId: string) => Promise<void>;
  
  createTemplate: (template: Partial<ReportTemplate>) => Promise<ReportTemplate>;
  updateTemplate: (id: string, updates: Partial<ReportTemplate>) => Promise<void>;
  deleteTemplate: (id: string) => Promise<void>;
  
  createSubscription: (subscription: Partial<ReportSubscription>) => Promise<ReportSubscription>;
  updateSubscription: (id: string, updates: Partial<ReportSubscription>) => Promise<void>;
  deleteSubscription: (id: string) => Promise<void>;
  toggleSubscription: (id: string, enabled: boolean) => Promise<void>;
  
  previewReport: (reportId: string) => Promise<void>;
}

interface GenerationProgress {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;  // 0-100
  currentStep?: string;
  error?: string;
}

export const useReportStore = create<ReportStore>((set, get) => ({
  // 初始状态
  reports: [],
  reportsLoading: false,
  templates: [],
  templatesLoading: false,
  subscriptions: [],
  subscriptionsLoading: false,
  generatingReports: new Map(),
  
  // 获取报表列表
  fetchReports: async (filters) => {
    set({ reportsLoading: true, reportsError: undefined });
    try {
      const response = await api.get('/api/v1/reports', { params: filters });
      set({ reports: response.data.reports, reportsLoading: false });
    } catch (error) {
      set({ reportsError: error.message, reportsLoading: false });
    }
  },
  
  // 生成报表
  generateReport: async (templateId, config) => {
    const taskId = crypto.randomUUID();
    
    // 初始化进度
    set(state => ({
      generatingReports: new Map(state.generatingReports).set(taskId, {
        status: 'pending',
        progress: 0,
      })
    }));
    
    try {
      const response = await api.post('/api/v1/reports/generate', {
        templateId,
        ...config,
      });
      
      // 轮询生成进度
      const pollProgress = async () => {
        const status = await api.get(`/api/v1/reports/generate/${response.data.taskId}/status`);
        
        set(state => ({
          generatingReports: new Map(state.generatingReports).set(taskId, {
            status: status.data.status,
            progress: status.data.progress,
            currentStep: status.data.currentStep,
          })
        }));
        
        if (status.data.status === 'processing') {
          setTimeout(pollProgress, 1000);
        } else if (status.data.status === 'completed') {
          // 刷新报表列表
          get().fetchReports();
        }
      };
      
      pollProgress();
      return response.data.taskId;
    } catch (error) {
      set(state => ({
        generatingReports: new Map(state.generatingReports).set(taskId, {
          status: 'failed',
          progress: 0,
          error: error.message,
        })
      }));
      throw error;
    }
  },
  
  // 下载报表
  downloadReport: async (reportId, format) => {
    const response = await api.get(`/api/v1/reports/${reportId}/download`, {
      params: { format },
      responseType: 'blob',
    });
    
    // 触发浏览器下载
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `report-${reportId}.${format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  },
  
  // ... 其他actions实现
}));
```

### 5.2 API调用

```typescript
// api/reports.ts

// 获取报表列表
export const getReports = async (params: {
  type?: ReportType[];
  category?: ReportCategory[];
  dateRange?: [string, string];
  keyword?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ reports: Report[]; total: number }> => {
  const response = await api.get('/api/v1/reports', { params });
  return response.data;
};

// 获取报表详情
export const getReport = async (reportId: string): Promise<Report> => {
  const response = await api.get(`/api/v1/reports/${reportId}`);
  return response.data;
};

// 获取报表内容（预览）
export const getReportContent = async (reportId: string): Promise<ReportContent> => {
  const response = await api.get(`/api/v1/reports/${reportId}/content`);
  return response.data;
};

// 生成报表
export const generateReport = async (params: {
  templateId: string;
  config: GenerateConfig;
}): Promise<{ taskId: string }> => {
  const response = await api.post('/api/v1/reports/generate', params);
  return response.data;
};

// 获取生成进度
export const getGenerationStatus = async (taskId: string): Promise<GenerationProgress> => {
  const response = await api.get(`/api/v1/reports/generate/${taskId}/status`);
  return response.data;
};

// 下载报表
export const downloadReport = async (
  reportId: string, 
  format: ExportFormat
): Promise<Blob> => {
  const response = await api.get(`/api/v1/reports/${reportId}/download`, {
    params: { format },
    responseType: 'blob',
  });
  return response.data;
};

// 分享报表
export const shareReport = async (reportId: string, params: {
  type: 'link' | 'email';
  expiresIn?: number;  // 小时
  recipients?: string[];
}): Promise<{ shareUrl?: string }> => {
  const response = await api.post(`/api/v1/reports/${reportId}/share`, params);
  return response.data;
};

// 删除报表
export const deleteReport = async (reportId: string): Promise<void> => {
  await api.delete(`/api/v1/reports/${reportId}`);
};

// === 模板API ===

// 获取模板列表
export const getTemplates = async (): Promise<ReportTemplate[]> => {
  const response = await api.get('/api/v1/reports/templates');
  return response.data;
};

// 创建模板
export const createTemplate = async (
  template: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  const response = await api.post('/api/v1/reports/templates', template);
  return response.data;
};

// 更新模板
export const updateTemplate = async (
  id: string, 
  updates: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  const response = await api.put(`/api/v1/reports/templates/${id}`, updates);
  return response.data;
};

// 删除模板
export const deleteTemplate = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/reports/templates/${id}`);
};

// 预览模板
export const previewTemplate = async (
  template: Partial<ReportTemplate>,
  sampleData?: any
): Promise<ReportContent> => {
  const response = await api.post('/api/v1/reports/templates/preview', {
    template,
    sampleData,
  });
  return response.data;
};

// === 订阅API ===

// 获取订阅列表
export const getSubscriptions = async (): Promise<ReportSubscription[]> => {
  const response = await api.get('/api/v1/reports/subscriptions');
  return response.data;
};

// 创建订阅
export const createSubscription = async (
  subscription: Partial<ReportSubscription>
): Promise<ReportSubscription> => {
  const response = await api.post('/api/v1/reports/subscriptions', subscription);
  return response.data;
};

// 更新订阅
export const updateSubscription = async (
  id: string, 
  updates: Partial<ReportSubscription>
): Promise<ReportSubscription> => {
  const response = await api.put(`/api/v1/reports/subscriptions/${id}`, updates);
  return response.data;
};

// 删除订阅
export const deleteSubscription = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/reports/subscriptions/${id}`);
};

// 切换订阅状态
export const toggleSubscription = async (
  id: string, 
  enabled: boolean
): Promise<void> => {
  await api.patch(`/api/v1/reports/subscriptions/${id}`, { isActive: enabled });
};
```

---

## 6. 报表生成流程

### 6.1 生成流程设计

```typescript
// 报表生成流程
/*
1. 用户选择模板和配置
2. 发起生成请求
3. 后端创建生成任务
4. 分步执行：
   a. 数据收集 - 从各API获取数据
   b. 数据处理 - 计算指标、生成图表
   c. 内容渲染 - 根据模板生成内容
   d. 格式转换 - 转换为目标格式
   e. 文件存储 - 保存到存储服务
5. 返回生成结果
6. 用户下载或预览
*/

// 生成配置表单
interface GenerateReportFormProps {
  template: ReportTemplate;
  onSubmit: (config: GenerateConfig) => void;
  onCancel: () => void;
}

const GenerateReportForm: React.FC<GenerateReportFormProps> = ({
  template,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const { buildings } = useBuildingStore();
  const { robots } = useRobotStore();
  
  const periodOptions = [
    { value: 'last_day', label: '昨天' },
    { value: 'last_week', label: '上周' },
    { value: 'last_month', label: '上月' },
    { value: 'custom', label: '自定义' },
  ];
  
  const formatOptions = [
    { value: 'pdf', label: 'PDF文档', icon: <FilePdfOutlined /> },
    { value: 'excel', label: 'Excel表格', icon: <FileExcelOutlined /> },
    { value: 'pptx', label: 'PowerPoint', icon: <FilePptOutlined /> },
  ];
  
  const handleSubmit = (values: any) => {
    const config: GenerateConfig = {
      periodType: values.periodType,
      customRange: values.periodType === 'custom' 
        ? [values.dateRange[0].toISOString(), values.dateRange[1].toISOString()]
        : undefined,
      buildingIds: values.buildingIds,
      robotIds: values.robotIds,
      format: values.format,
      includeRawData: values.includeRawData,
      notifyOnComplete: values.notifyOnComplete,
      recipients: values.recipients,
    };
    onSubmit(config);
  };
  
  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Form.Item
        name="periodType"
        label="报表周期"
        initialValue="last_month"
        rules={[{ required: true }]}
      >
        <Radio.Group options={periodOptions} />
      </Form.Item>
      
      <Form.Item
        noStyle
        shouldUpdate={(prev, curr) => prev.periodType !== curr.periodType}
      >
        {({ getFieldValue }) =>
          getFieldValue('periodType') === 'custom' && (
            <Form.Item
              name="dateRange"
              label="自定义时间范围"
              rules={[{ required: true }]}
            >
              <DatePicker.RangePicker />
            </Form.Item>
          )
        }
      </Form.Item>
      
      <Form.Item
        name="buildingIds"
        label="楼宇范围"
      >
        <Select
          mode="multiple"
          placeholder="全部楼宇"
          allowClear
        >
          {buildings.map(b => (
            <Select.Option key={b.id} value={b.id}>{b.name}</Select.Option>
          ))}
        </Select>
      </Form.Item>
      
      <Form.Item
        name="format"
        label="输出格式"
        initialValue="pdf"
        rules={[{ required: true }]}
      >
        <Radio.Group>
          {formatOptions.map(opt => (
            <Radio.Button key={opt.value} value={opt.value}>
              {opt.icon} {opt.label}
            </Radio.Button>
          ))}
        </Radio.Group>
      </Form.Item>
      
      <Form.Item
        name="includeRawData"
        valuePropName="checked"
      >
        <Checkbox>包含原始数据附录</Checkbox>
      </Form.Item>
      
      <Form.Item
        name="notifyOnComplete"
        valuePropName="checked"
      >
        <Checkbox>生成完成后发送通知</Checkbox>
      </Form.Item>
      
      <Form.Item
        noStyle
        shouldUpdate={(prev, curr) => prev.notifyOnComplete !== curr.notifyOnComplete}
      >
        {({ getFieldValue }) =>
          getFieldValue('notifyOnComplete') && (
            <Form.Item
              name="recipients"
              label="通知接收人"
            >
              <Select mode="tags" placeholder="输入邮箱地址" />
            </Form.Item>
          )
        }
      </Form.Item>
      
      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit">
            生成报表
          </Button>
          <Button onClick={onCancel}>取消</Button>
        </Space>
      </Form.Item>
    </Form>
  );
};
```

### 6.2 生成进度展示

```typescript
// GenerationProgress.tsx
interface GenerationProgressProps {
  taskId: string;
  onComplete: (report: Report) => void;
  onError: (error: string) => void;
}

const GenerationProgress: React.FC<GenerationProgressProps> = ({
  taskId,
  onComplete,
  onError,
}) => {
  const { generatingReports } = useReportStore();
  const progress = generatingReports.get(taskId);
  
  const steps = [
    { key: 'collecting', title: '数据收集', description: '从系统收集数据' },
    { key: 'processing', title: '数据处理', description: '计算指标和统计' },
    { key: 'rendering', title: '内容生成', description: '生成报表内容' },
    { key: 'converting', title: '格式转换', description: '转换输出格式' },
    { key: 'saving', title: '保存文件', description: '保存到存储' },
  ];
  
  const getCurrentStep = () => {
    if (!progress?.currentStep) return 0;
    return steps.findIndex(s => s.key === progress.currentStep);
  };
  
  if (!progress) {
    return <Spin tip="准备中..." />;
  }
  
  if (progress.status === 'failed') {
    return (
      <Result
        status="error"
        title="生成失败"
        subTitle={progress.error}
        extra={<Button onClick={() => onError(progress.error!)}>关闭</Button>}
      />
    );
  }
  
  if (progress.status === 'completed') {
    return (
      <Result
        status="success"
        title="生成完成"
        subTitle="报表已生成，可以下载或预览"
        extra={
          <Space>
            <Button type="primary">下载报表</Button>
            <Button>预览</Button>
          </Space>
        }
      />
    );
  }
  
  return (
    <div className="generation-progress">
      <Progress
        percent={progress.progress}
        status="active"
        strokeColor={{ from: '#108ee9', to: '#87d068' }}
      />
      
      <Steps
        current={getCurrentStep()}
        size="small"
        className="mt-4"
      >
        {steps.map(step => (
          <Steps.Step
            key={step.key}
            title={step.title}
            description={step.description}
          />
        ))}
      </Steps>
    </div>
  );
};
```

---

## 7. 测试要求

### 7.1 单元测试

```typescript
// __tests__/ReportList.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReportList } from '../components/ReportList';

describe('ReportList', () => {
  const mockReports: Report[] = [
    {
      id: 'r1',
      templateId: 't1',
      name: '12月运营报告',
      type: 'monthly',
      category: 'operations',
      periodStart: '2025-12-01',
      periodEnd: '2025-12-31',
      status: 'generated',
      generatedAt: '2026-01-01T08:00:00Z',
      generatedBy: 'system',
      fileUrl: '/reports/r1.pdf',
      fileSize: 2400000,
      pageCount: 15,
    },
    // ... more mock reports
  ];
  
  it('should render report cards', () => {
    render(
      <ReportList
        activeTab="my_reports"
        filters={{}}
        onFiltersChange={jest.fn()}
        viewMode="grid"
        onViewModeChange={jest.fn()}
        onPreview={jest.fn()}
        onDownload={jest.fn()}
        onShare={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    
    expect(screen.getByText('12月运营报告')).toBeInTheDocument();
  });
  
  it('should filter reports by type', async () => {
    const onFiltersChange = jest.fn();
    
    render(
      <ReportList
        activeTab="my_reports"
        filters={{}}
        onFiltersChange={onFiltersChange}
        viewMode="grid"
        onViewModeChange={jest.fn()}
        onPreview={jest.fn()}
        onDownload={jest.fn()}
        onShare={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    
    // 选择筛选类型
    fireEvent.click(screen.getByText('全部'));
    fireEvent.click(screen.getByText('月报'));
    
    expect(onFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ type: ['monthly'] })
    );
  });
  
  it('should open preview modal on click', () => {
    const onPreview = jest.fn();
    
    render(
      <ReportList
        activeTab="my_reports"
        filters={{}}
        onFiltersChange={jest.fn()}
        viewMode="grid"
        onViewModeChange={jest.fn()}
        onPreview={onPreview}
        onDownload={jest.fn()}
        onShare={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    
    fireEvent.click(screen.getByText('预览'));
    
    expect(onPreview).toHaveBeenCalledWith(mockReports[0]);
  });
  
  it('should trigger download with correct format', () => {
    const onDownload = jest.fn();
    
    render(
      <ReportList
        activeTab="my_reports"
        filters={{}}
        onFiltersChange={jest.fn()}
        viewMode="grid"
        onViewModeChange={jest.fn()}
        onPreview={jest.fn()}
        onDownload={onDownload}
        onShare={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    
    // 点击下载按钮
    fireEvent.click(screen.getByText('下载'));
    // 选择格式
    fireEvent.click(screen.getByText('PDF'));
    
    expect(onDownload).toHaveBeenCalledWith(mockReports[0], 'pdf');
  });
});

// __tests__/TemplateEditor.test.tsx
describe('TemplateEditor', () => {
  it('should allow adding sections', () => {
    render(<ReportEditor onSave={jest.fn()} onCancel={jest.fn()} />);
    
    fireEvent.click(screen.getByText('添加章节'));
    fireEvent.click(screen.getByText('KPI指标'));
    
    expect(screen.getByText('KPI指标')).toBeInTheDocument();
  });
  
  it('should allow reordering sections via drag and drop', async () => {
    // Test drag and drop functionality
  });
  
  it('should validate template before saving', async () => {
    const onSave = jest.fn();
    
    render(<ReportEditor onSave={onSave} onCancel={jest.fn()} />);
    
    fireEvent.click(screen.getByText('保存'));
    
    // Should show validation error for empty template
    expect(screen.getByText('请至少添加一个章节')).toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });
});

// __tests__/SubscriptionManager.test.tsx
describe('SubscriptionManager', () => {
  const mockSubscriptions: ReportSubscription[] = [
    {
      id: 'sub1',
      name: '每周运营报告',
      templateId: 't1',
      templateName: '周度运营总结',
      schedule: { type: 'weekly', weeklyDay: 1, weeklyTime: '08:00', timezone: 'Asia/Hong_Kong' },
      delivery: { emailRecipients: ['test@example.com'], attachmentFormat: 'pdf' },
      isActive: true,
      lastRunAt: '2025-12-30T08:00:00Z',
      lastRunStatus: 'success',
      nextRunAt: '2026-01-06T08:00:00Z',
      createdBy: 'user1',
      createdAt: '2025-12-01T00:00:00Z',
    },
  ];
  
  it('should display subscriptions', () => {
    render(
      <SubscriptionManager
        subscriptions={mockSubscriptions}
        onCreateSubscription={jest.fn()}
        onEditSubscription={jest.fn()}
        onDeleteSubscription={jest.fn()}
        onToggleSubscription={jest.fn()}
      />
    );
    
    expect(screen.getByText('每周运营报告')).toBeInTheDocument();
    expect(screen.getByText('周度运营总结')).toBeInTheDocument();
  });
  
  it('should toggle subscription status', () => {
    const onToggle = jest.fn();
    
    render(
      <SubscriptionManager
        subscriptions={mockSubscriptions}
        onCreateSubscription={jest.fn()}
        onEditSubscription={jest.fn()}
        onDeleteSubscription={jest.fn()}
        onToggleSubscription={onToggle}
      />
    );
    
    fireEvent.click(screen.getByRole('switch'));
    
    expect(onToggle).toHaveBeenCalledWith(mockSubscriptions[0], false);
  });
});
```

### 7.2 集成测试

```typescript
// __tests__/integration/ReportCenter.test.tsx
describe('Report Center Integration', () => {
  beforeEach(() => {
    // Setup mock API
    server.use(
      rest.get('/api/v1/reports', (req, res, ctx) => {
        return res(ctx.json({ reports: mockReports, total: 10 }));
      }),
      rest.get('/api/v1/reports/templates', (req, res, ctx) => {
        return res(ctx.json(mockTemplates));
      }),
      rest.post('/api/v1/reports/generate', (req, res, ctx) => {
        return res(ctx.json({ taskId: 'task-123' }));
      }),
    );
  });
  
  it('should complete full report generation flow', async () => {
    render(<ReportCenter />);
    
    // 1. 切换到模板标签
    fireEvent.click(screen.getByText('报表模板'));
    
    // 2. 选择模板并生成
    fireEvent.click(screen.getByText('月度运营报告'));
    fireEvent.click(screen.getByText('生成报表'));
    
    // 3. 填写生成配置
    fireEvent.click(screen.getByText('上月'));
    fireEvent.click(screen.getByText('PDF文档'));
    fireEvent.click(screen.getByText('生成报表'));
    
    // 4. 等待生成完成
    await waitFor(() => {
      expect(screen.getByText('生成完成')).toBeInTheDocument();
    }, { timeout: 10000 });
    
    // 5. 预览报表
    fireEvent.click(screen.getByText('预览'));
    expect(screen.getByText('LinkC 月度运营报告')).toBeInTheDocument();
  });
  
  it('should manage subscriptions correctly', async () => {
    render(<ReportCenter />);
    
    // 切换到订阅管理
    fireEvent.click(screen.getByText('订阅管理'));
    
    // 创建新订阅
    fireEvent.click(screen.getByText('新建订阅'));
    
    // 填写订阅信息
    fireEvent.change(screen.getByLabelText('订阅名称'), {
      target: { value: '每日运营报告' }
    });
    
    // 选择模板
    fireEvent.click(screen.getByLabelText('报表模板'));
    fireEvent.click(screen.getByText('日常运营报告'));
    
    // 设置调度
    fireEvent.click(screen.getByText('每日'));
    
    // 保存
    fireEvent.click(screen.getByText('创建'));
    
    await waitFor(() => {
      expect(screen.getByText('每日运营报告')).toBeInTheDocument();
    });
  });
});
```

---

## 8. 验收标准

### 8.1 功能验收

| 功能 | 验收标准 | 优先级 |
|-----|---------|-------|
| 报表列表 | 能够分页展示报表，支持筛选和搜索 | P0 |
| 报表预览 | 能够在线预览报表内容，支持翻页和缩放 | P0 |
| 报表下载 | 支持PDF、Excel、PPT三种格式下载 | P0 |
| 报表生成 | 能够选择模板和配置生成报表，显示进度 | P0 |
| 模板管理 | 能够创建、编辑、删除自定义模板 | P1 |
| 订阅管理 | 能够创建订阅，定时自动生成和发送报表 | P1 |
| 报表分享 | 能够生成分享链接或发送给他人 | P2 |

### 8.2 性能要求

| 指标 | 要求 |
|-----|------|
| 列表加载 | < 1秒 |
| 预览加载 | < 3秒（首页） |
| 报表生成 | < 30秒（月报）/ < 60秒（季报） |
| 导出下载 | < 5秒（10MB以内） |

### 8.3 可用性要求

- 支持响应式布局
- 生成过程可中断
- 支持离线下载（生成完成后）
- 订阅失败自动重试

---

## 9. 文件结构

```
src/pages/executive/reports/
├── index.tsx                    # 报表中心主页面
├── ReportCenter.tsx             # 主容器组件
├── components/
│   ├── ReportList/
│   │   ├── index.tsx            # 报表列表
│   │   ├── ReportCard.tsx       # 报表卡片
│   │   ├── ReportFilters.tsx    # 筛选组件
│   │   └── styles.less
│   ├── ReportPreview/
│   │   ├── index.tsx            # 报表预览
│   │   ├── PreviewToolbar.tsx   # 预览工具栏
│   │   ├── PageNavigator.tsx    # 页面导航
│   │   └── styles.less
│   ├── TemplateManager/
│   │   ├── index.tsx            # 模板管理
│   │   ├── TemplateCard.tsx     # 模板卡片
│   │   └── styles.less
│   ├── ReportEditor/
│   │   ├── index.tsx            # 报表编辑器
│   │   ├── SectionEditor.tsx    # 章节编辑器
│   │   ├── SectionList.tsx      # 章节列表
│   │   ├── DataSourcePicker.tsx # 数据源选择
│   │   └── styles.less
│   ├── SubscriptionManager/
│   │   ├── index.tsx            # 订阅管理
│   │   ├── SubscriptionForm.tsx # 订阅表单
│   │   ├── ScheduleConfig.tsx   # 调度配置
│   │   └── styles.less
│   ├── GenerateModal/
│   │   ├── index.tsx            # 生成配置弹窗
│   │   ├── GenerateForm.tsx     # 配置表单
│   │   ├── GenerationProgress.tsx # 生成进度
│   │   └── styles.less
│   └── ShareModal/
│       ├── index.tsx            # 分享弹窗
│       └── styles.less
├── hooks/
│   ├── useReports.ts            # 报表数据hook
│   ├── useTemplates.ts          # 模板数据hook
│   └── useSubscriptions.ts      # 订阅数据hook
├── stores/
│   └── reportStore.ts           # 报表状态管理
├── api/
│   └── reports.ts               # 报表API
├── types/
│   └── index.ts                 # 类型定义
└── __tests__/
    ├── ReportList.test.tsx
    ├── ReportEditor.test.tsx
    └── SubscriptionManager.test.tsx
```

---

## 附录

### A. 报表样式规范

```less
// 报表颜色主题
@report-primary: #1890ff;
@report-success: #52c41a;
@report-warning: #faad14;
@report-error: #ff4d4f;

// 报表字体
@report-title-font: 24px;
@report-section-font: 18px;
@report-body-font: 14px;

// 报表间距
@report-page-margin: 40px;
@report-section-margin: 24px;
@report-element-margin: 16px;
```

### B. 导出格式说明

| 格式 | 适用场景 | 特点 |
|-----|---------|------|
| PDF | 正式报告、打印 | 格式固定，不可编辑 |
| Excel | 数据分析、进一步处理 | 包含原始数据，可编辑 |
| PPT | 会议汇报、展示 | 适合投影展示 |

---

*文档结束*
