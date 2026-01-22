/**
 * E3 Report Center - Report Management Interface
 * 报表中心
 */

import React, { useState, useCallback } from 'react';

// ============ Type Definitions ============

type ReportType = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual' | 'custom';
type ReportCategory = 'operations' | 'financial' | 'performance' | 'customer' | 'equipment' | 'custom';
type ReportStatus = 'generated' | 'generating' | 'failed' | 'scheduled';
type ExportFormat = 'pdf' | 'excel' | 'csv';
type TabType = 'my_reports' | 'templates' | 'subscriptions' | 'history';

interface ReportTemplate {
  id: string;
  name: string;
  type: ReportType;
  category: ReportCategory;
  description: string;
  isSystem: boolean;
  isActive: boolean;
  sections: string[];
  createdAt: string;
}

interface Report {
  id: string;
  templateId: string;
  templateName: string;
  name: string;
  type: ReportType;
  category: ReportCategory;
  periodStart: string;
  periodEnd: string;
  status: ReportStatus;
  generatedAt?: string;
  generatedBy: 'system' | 'user';
  fileUrl?: string;
  fileSize?: number;
  pageCount?: number;
}

interface Subscription {
  id: string;
  templateId: string;
  templateName: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  isActive: boolean;
  lastSent?: string;
  nextSend?: string;
}

interface ReportCenterProps {
  tenantId: string;
  onPreview?: (report: Report) => void;
  onDownload?: (report: Report, format: ExportFormat) => void;
}

// ============ Mock Data ============

const mockTemplates: ReportTemplate[] = [
  {
    id: 'daily-operations',
    name: '日常运营报告',
    type: 'daily',
    category: 'operations',
    description: '每日运营情况汇总，包含任务完成、机器人状态、异常事件',
    isSystem: true,
    isActive: true,
    sections: ['今日概览', '核心指标', '任务执行明细', '异常事件列表', '改进建议'],
    createdAt: '2025-01-01',
  },
  {
    id: 'weekly-summary',
    name: '周度运营总结',
    type: 'weekly',
    category: 'operations',
    description: '每周运营总结，包含趋势分析和周环比',
    isSystem: true,
    isActive: true,
    sections: ['本周概览', '核心指标（环比）', '日度趋势', '楼宇对比', '本周亮点', '待改进项', '下周计划'],
    createdAt: '2025-01-01',
  },
  {
    id: 'monthly-report',
    name: '月度运营报告',
    type: 'monthly',
    category: 'operations',
    description: '完整的月度运营分析报告',
    isSystem: true,
    isActive: true,
    sections: ['执行摘要', 'KPI达成情况', '月度趋势分析', '同比环比分析', '效率热力图', '楼宇绩效排名', '机器人利用率', '成本分析', '优化建议', '附录'],
    createdAt: '2025-01-01',
  },
  {
    id: 'customer-sla-report',
    name: '客户SLA报告',
    type: 'monthly',
    category: 'customer',
    description: '面向客户的服务水平报告',
    isSystem: true,
    isActive: true,
    sections: ['服务概览', 'SLA达成率', '服务覆盖详情', '服务质量趋势', '事件响应记录'],
    createdAt: '2025-01-01',
  },
  {
    id: 'equipment-health',
    name: '设备健康报告',
    type: 'weekly',
    category: 'equipment',
    description: '机器人设备状态和维护报告',
    isSystem: true,
    isActive: true,
    sections: ['设备概览', '可用率指标', '设备状态清单', '维护记录', '耗材更换计划', '维护建议'],
    createdAt: '2025-01-01',
  },
];

const mockReports: Report[] = [
  {
    id: 'report-001',
    templateId: 'monthly-report',
    templateName: '月度运营报告',
    name: '2025年12月运营报告',
    type: 'monthly',
    category: 'operations',
    periodStart: '2025-12-01',
    periodEnd: '2025-12-31',
    status: 'generated',
    generatedAt: '2026-01-01T08:00:00Z',
    generatedBy: 'system',
    fileSize: 2350000,
    pageCount: 18,
  },
  {
    id: 'report-002',
    templateId: 'weekly-summary',
    templateName: '周度运营总结',
    name: '第51周周报',
    type: 'weekly',
    category: 'operations',
    periodStart: '2025-12-16',
    periodEnd: '2025-12-22',
    status: 'generated',
    generatedAt: '2025-12-23T08:00:00Z',
    generatedBy: 'system',
    fileSize: 1250000,
    pageCount: 10,
  },
  {
    id: 'report-003',
    templateId: 'customer-sla-report',
    templateName: '客户SLA报告',
    name: '2025年11月SLA报告',
    type: 'monthly',
    category: 'customer',
    periodStart: '2025-11-01',
    periodEnd: '2025-11-30',
    status: 'generated',
    generatedAt: '2025-12-01T08:00:00Z',
    generatedBy: 'system',
    fileSize: 1800000,
    pageCount: 12,
  },
  {
    id: 'report-004',
    templateId: 'equipment-health',
    templateName: '设备健康报告',
    name: '设备健康周报',
    type: 'weekly',
    category: 'equipment',
    periodStart: '2025-12-16',
    periodEnd: '2025-12-22',
    status: 'generated',
    generatedAt: '2025-12-23T09:00:00Z',
    generatedBy: 'user',
    fileSize: 950000,
    pageCount: 8,
  },
  {
    id: 'report-005',
    templateId: 'daily-operations',
    templateName: '日常运营报告',
    name: '2026-01-20日报',
    type: 'daily',
    category: 'operations',
    periodStart: '2026-01-20',
    periodEnd: '2026-01-20',
    status: 'generated',
    generatedAt: '2026-01-21T06:00:00Z',
    generatedBy: 'system',
    fileSize: 580000,
    pageCount: 5,
  },
  {
    id: 'report-006',
    templateId: 'monthly-report',
    templateName: '月度运营报告',
    name: '2026年1月运营报告',
    type: 'monthly',
    category: 'operations',
    periodStart: '2026-01-01',
    periodEnd: '2026-01-31',
    status: 'generating',
    generatedBy: 'user',
  },
];

const mockSubscriptions: Subscription[] = [
  {
    id: 'sub-001',
    templateId: 'daily-operations',
    templateName: '日常运营报告',
    frequency: 'daily',
    recipients: ['ops-manager@linkc.com', 'team-lead@linkc.com'],
    isActive: true,
    lastSent: '2026-01-21T06:00:00Z',
    nextSend: '2026-01-22T06:00:00Z',
  },
  {
    id: 'sub-002',
    templateId: 'weekly-summary',
    templateName: '周度运营总结',
    frequency: 'weekly',
    recipients: ['coo@linkc.com', 'ops-director@linkc.com'],
    isActive: true,
    lastSent: '2026-01-20T08:00:00Z',
    nextSend: '2026-01-27T08:00:00Z',
  },
  {
    id: 'sub-003',
    templateId: 'monthly-report',
    templateName: '月度运营报告',
    frequency: 'monthly',
    recipients: ['ceo@linkc.com', 'cfo@linkc.com', 'coo@linkc.com'],
    isActive: true,
    lastSent: '2026-01-01T08:00:00Z',
    nextSend: '2026-02-01T08:00:00Z',
  },
];

// ============ Sub Components ============

// Tab Button
const TabButton: React.FC<{
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  badge?: number;
}> = ({ active, onClick, children, badge }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium relative ${
      active
        ? 'text-blue-600 border-b-2 border-blue-600'
        : 'text-gray-600 hover:text-gray-900'
    }`}
  >
    {children}
    {badge !== undefined && badge > 0 && (
      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
        {badge}
      </span>
    )}
  </button>
);

// Status Badge
const StatusBadge: React.FC<{ status: ReportStatus }> = ({ status }) => {
  const config = {
    generated: { bg: 'bg-green-100', text: 'text-green-800', label: '已生成' },
    generating: { bg: 'bg-blue-100', text: 'text-blue-800', label: '生成中' },
    failed: { bg: 'bg-red-100', text: 'text-red-800', label: '失败' },
    scheduled: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '已计划' },
  };
  const { bg, text, label } = config[status];
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${bg} ${text}`}>
      {label}
    </span>
  );
};

// Type Badge
const TypeBadge: React.FC<{ type: ReportType }> = ({ type }) => {
  const labels: Record<ReportType, string> = {
    daily: '日报',
    weekly: '周报',
    monthly: '月报',
    quarterly: '季报',
    annual: '年报',
    custom: '自定义',
  };
  return (
    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
      {labels[type]}
    </span>
  );
};

// Category Badge
const CategoryBadge: React.FC<{ category: ReportCategory }> = ({ category }) => {
  const config: Record<ReportCategory, { bg: string; text: string; label: string }> = {
    operations: { bg: 'bg-blue-50', text: 'text-blue-700', label: '运营' },
    financial: { bg: 'bg-green-50', text: 'text-green-700', label: '财务' },
    performance: { bg: 'bg-purple-50', text: 'text-purple-700', label: '绩效' },
    customer: { bg: 'bg-orange-50', text: 'text-orange-700', label: '客户' },
    equipment: { bg: 'bg-gray-50', text: 'text-gray-700', label: '设备' },
    custom: { bg: 'bg-pink-50', text: 'text-pink-700', label: '自定义' },
  };
  const { bg, text, label } = config[category];
  return (
    <span className={`px-2 py-1 text-xs rounded ${bg} ${text}`}>
      {label}
    </span>
  );
};

// Report Card (Grid View)
const ReportCard: React.FC<{
  report: Report;
  onPreview: () => void;
  onDownload: (format: ExportFormat) => void;
}> = ({ report, onPreview, onDownload }) => {
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="text-3xl">📄</div>
        <StatusBadge status={report.status} />
      </div>

      <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">{report.name}</h3>

      <div className="flex flex-wrap gap-1 mb-3">
        <TypeBadge type={report.type} />
        <CategoryBadge category={report.category} />
      </div>

      <div className="text-xs text-gray-500 mb-3">
        <div>期间: {report.periodStart} ~ {report.periodEnd}</div>
        {report.generatedAt && (
          <div>生成: {new Date(report.generatedAt).toLocaleDateString('zh-CN')}</div>
        )}
        {report.fileSize && (
          <div>大小: {(report.fileSize / 1024 / 1024).toFixed(1)}MB · {report.pageCount}页</div>
        )}
      </div>

      <div className="flex space-x-2">
        <button
          onClick={onPreview}
          disabled={report.status !== 'generated'}
          className="flex-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
        >
          预览
        </button>
        <div className="relative">
          <button
            onClick={() => setShowDownloadMenu(!showDownloadMenu)}
            disabled={report.status !== 'generated'}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            下载 ▼
          </button>
          {showDownloadMenu && (
            <div className="absolute right-0 mt-1 bg-white border rounded shadow-lg z-10">
              <button
                onClick={() => { onDownload('pdf'); setShowDownloadMenu(false); }}
                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
              >
                PDF
              </button>
              <button
                onClick={() => { onDownload('excel'); setShowDownloadMenu(false); }}
                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
              >
                Excel
              </button>
              <button
                onClick={() => { onDownload('csv'); setShowDownloadMenu(false); }}
                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
              >
                CSV
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Template Card
const TemplateCard: React.FC<{
  template: ReportTemplate;
  onGenerate: () => void;
  onEdit?: () => void;
}> = ({ template, onGenerate, onEdit }) => (
  <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4">
    <div className="flex items-start justify-between mb-3">
      <div className="text-3xl">📋</div>
      {template.isSystem && (
        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">系统模板</span>
      )}
    </div>

    <h3 className="font-medium text-gray-900 mb-2">{template.name}</h3>

    <p className="text-sm text-gray-500 mb-3 line-clamp-2">{template.description}</p>

    <div className="flex flex-wrap gap-1 mb-3">
      <TypeBadge type={template.type} />
      <CategoryBadge category={template.category} />
    </div>

    <div className="text-xs text-gray-500 mb-3">
      包含: {template.sections.slice(0, 3).join(', ')}
      {template.sections.length > 3 && ` 等${template.sections.length}个章节`}
    </div>

    <div className="flex space-x-2">
      <button
        onClick={onGenerate}
        className="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        生成报表
      </button>
      {!template.isSystem && onEdit && (
        <button
          onClick={onEdit}
          className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          编辑
        </button>
      )}
    </div>
  </div>
);

// Subscription Row
const SubscriptionRow: React.FC<{
  subscription: Subscription;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}> = ({ subscription, onToggle, onEdit, onDelete }) => (
  <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
    <div className="flex-1">
      <div className="flex items-center space-x-3">
        <h3 className="font-medium text-gray-900">{subscription.templateName}</h3>
        <span className={`px-2 py-1 text-xs rounded ${
          subscription.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
        }`}>
          {subscription.isActive ? '启用' : '停用'}
        </span>
      </div>
      <div className="text-sm text-gray-500 mt-1">
        频率: {subscription.frequency === 'daily' ? '每日' : subscription.frequency === 'weekly' ? '每周' : '每月'}
        · 收件人: {subscription.recipients.length}人
      </div>
      <div className="text-xs text-gray-400 mt-1">
        {subscription.lastSent && `上次发送: ${new Date(subscription.lastSent).toLocaleString('zh-CN')}`}
        {subscription.nextSend && ` · 下次发送: ${new Date(subscription.nextSend).toLocaleString('zh-CN')}`}
      </div>
    </div>
    <div className="flex items-center space-x-2">
      <button
        onClick={onToggle}
        className={`px-3 py-1.5 text-sm rounded ${
          subscription.isActive
            ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
            : 'bg-green-100 text-green-700 hover:bg-green-200'
        }`}
      >
        {subscription.isActive ? '停用' : '启用'}
      </button>
      <button
        onClick={onEdit}
        className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
      >
        编辑
      </button>
      <button
        onClick={onDelete}
        className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
      >
        删除
      </button>
    </div>
  </div>
);

// Generate Report Modal
const GenerateReportModal: React.FC<{
  template: ReportTemplate | null;
  onClose: () => void;
  onGenerate: (config: { periodType: string; customRange?: [string, string] }) => void;
}> = ({ template, onClose, onGenerate }) => {
  const [periodType, setPeriodType] = useState('last_month');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  if (!template) return null;

  const handleGenerate = () => {
    onGenerate({
      periodType,
      customRange: periodType === 'custom' ? [customStart, customEnd] : undefined,
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">生成报表</h2>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">报表模板</label>
            <div className="p-3 bg-gray-50 rounded">
              <div className="font-medium">{template.name}</div>
              <div className="text-sm text-gray-500">{template.description}</div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">时间范围</label>
            <select
              value={periodType}
              onChange={e => setPeriodType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="last_day">昨天</option>
              <option value="last_week">上周</option>
              <option value="last_month">上月</option>
              <option value="last_quarter">上季度</option>
              <option value="custom">自定义</option>
            </select>
          </div>

          {periodType === 'custom' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
                <input
                  type="date"
                  value={customStart}
                  onChange={e => setCustomStart(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
                <input
                  type="date"
                  value={customEnd}
                  onChange={e => setCustomEnd(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-200 flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            取消
          </button>
          <button
            onClick={handleGenerate}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            生成报表
          </button>
        </div>
      </div>
    </div>
  );
};

// Report Preview Modal
const ReportPreviewModal: React.FC<{
  report: Report | null;
  onClose: () => void;
  onDownload: (format: ExportFormat) => void;
}> = ({ report, onClose, onDownload }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(100);

  if (!report) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[90vh] mx-4 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">{report.name}</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onDownload('pdf')}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              导出PDF
            </button>
            <button
              onClick={() => onDownload('excel')}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
            >
              导出Excel
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="p-2 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setZoom(Math.max(50, zoom - 10))}
              className="px-2 py-1 text-sm bg-white border border-gray-300 rounded"
            >
              -
            </button>
            <span className="text-sm">{zoom}%</span>
            <button
              onClick={() => setZoom(Math.min(200, zoom + 10))}
              className="px-2 py-1 text-sm bg-white border border-gray-300 rounded"
            >
              +
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              className="px-2 py-1 text-sm bg-white border border-gray-300 rounded disabled:opacity-50"
            >
              上一页
            </button>
            <span className="text-sm">{currentPage} / {report.pageCount || 1}</span>
            <button
              onClick={() => setCurrentPage(Math.min(report.pageCount || 1, currentPage + 1))}
              disabled={currentPage >= (report.pageCount || 1)}
              className="px-2 py-1 text-sm bg-white border border-gray-300 rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>

        {/* Preview Content */}
        <div className="flex-1 overflow-auto p-8 bg-gray-200">
          <div
            className="bg-white shadow-lg mx-auto p-8"
            style={{
              width: `${(210 * zoom) / 100}mm`,
              minHeight: `${(297 * zoom) / 100}mm`,
              transform: `scale(${zoom / 100})`,
              transformOrigin: 'top center',
            }}
          >
            {/* Mock Report Content */}
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-gray-900">LinkC 月度运营报告</h1>
              <p className="text-gray-500 mt-2">
                报告期间: {report.periodStart} ~ {report.periodEnd}
              </p>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">1. 执行摘要</h2>
              <p className="text-gray-700 leading-relaxed">
                本月清洁任务完成率达到98.5%，较上月提升2.3个百分点。
                机器人可用率保持在99.2%，成本节约达到HK$45,000。
                整体运营状况良好，各项指标均达到或超过预期目标。
              </p>
            </div>

            <div className="mt-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">2. 核心指标</h2>
              <div className="grid grid-cols-4 gap-4">
                {[
                  { label: '完成率', value: '98.5%' },
                  { label: '覆盖率', value: '95.2%' },
                  { label: '可用率', value: '99.2%' },
                  { label: '节约', value: '$45K' },
                ].map((item, index) => (
                  <div key={index} className="text-center p-4 bg-gray-50 rounded">
                    <div className="text-2xl font-bold text-blue-600">{item.value}</div>
                    <div className="text-sm text-gray-500">{item.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 text-center text-gray-400 text-sm">
              [报表预览 - 第 {currentPage} 页]
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-500">
          生成时间: {report.generatedAt ? new Date(report.generatedAt).toLocaleString('zh-CN') : '-'}
          {report.fileSize && ` | 大小: ${(report.fileSize / 1024 / 1024).toFixed(1)}MB`}
          {report.pageCount && ` | ${report.pageCount}页`}
        </div>
      </div>
    </div>
  );
};

// ============ Main Component ============

export const ReportCenter: React.FC<ReportCenterProps> = ({
  tenantId: _tenantId,
  onPreview,
  onDownload,
}) => {
  // State
  const [activeTab, setActiveTab] = useState<TabType>('my_reports');
  const [reports, setReports] = useState<Report[]>(mockReports);
  const [templates] = useState<ReportTemplate[]>(mockTemplates);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>(mockSubscriptions);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchKeyword, setSearchKeyword] = useState('');

  // Modals
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [previewReport, setPreviewReport] = useState<Report | null>(null);

  // Filter reports
  const filteredReports = reports.filter(r => {
    if (typeFilter && r.type !== typeFilter) return false;
    if (categoryFilter && r.category !== categoryFilter) return false;
    if (searchKeyword && !r.name.toLowerCase().includes(searchKeyword.toLowerCase())) return false;
    return true;
  });

  // Handlers
  const handleGenerateReport = useCallback((config: { periodType: string; customRange?: [string, string] }) => {
    console.log('Generate report:', selectedTemplate?.id, config);
    // In production, call API to generate report
    const newReport: Report = {
      id: `report-${Date.now()}`,
      templateId: selectedTemplate!.id,
      templateName: selectedTemplate!.name,
      name: `新报表 - ${new Date().toLocaleDateString('zh-CN')}`,
      type: selectedTemplate!.type,
      category: selectedTemplate!.category,
      periodStart: config.customRange?.[0] || '2026-01-01',
      periodEnd: config.customRange?.[1] || '2026-01-21',
      status: 'generating',
      generatedBy: 'user',
    };
    setReports(prev => [newReport, ...prev]);
    setSelectedTemplate(null);
    alert('报表生成任务已提交，请稍后查看');
  }, [selectedTemplate]);

  const handleDownload = useCallback((report: Report, format: ExportFormat) => {
    if (onDownload) {
      onDownload(report, format);
    } else {
      console.log('Download:', report.id, format);
      alert(`下载报表: ${report.name}.${format}`);
    }
  }, [onDownload]);

  const handlePreview = useCallback((report: Report) => {
    if (onPreview) {
      onPreview(report);
    } else {
      setPreviewReport(report);
    }
  }, [onPreview]);

  const handleToggleSubscription = useCallback((subId: string) => {
    setSubscriptions(prev =>
      prev.map(s => s.id === subId ? { ...s, isActive: !s.isActive } : s)
    );
  }, []);

  // Render content based on active tab
  const renderContent = () => {
    switch (activeTab) {
      case 'my_reports':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredReports.map(report => (
              <ReportCard
                key={report.id}
                report={report}
                onPreview={() => handlePreview(report)}
                onDownload={format => handleDownload(report, format)}
              />
            ))}
            {filteredReports.length === 0 && (
              <div className="col-span-full text-center py-12 text-gray-500">
                暂无报表
              </div>
            )}
          </div>
        );

      case 'templates':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {templates.map(template => (
              <TemplateCard
                key={template.id}
                template={template}
                onGenerate={() => setSelectedTemplate(template)}
              />
            ))}
          </div>
        );

      case 'subscriptions':
        return (
          <div className="space-y-4">
            {subscriptions.map(subscription => (
              <SubscriptionRow
                key={subscription.id}
                subscription={subscription}
                onToggle={() => handleToggleSubscription(subscription.id)}
                onEdit={() => console.log('Edit subscription:', subscription.id)}
                onDelete={() => setSubscriptions(prev => prev.filter(s => s.id !== subscription.id))}
              />
            ))}
            {subscriptions.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                暂无订阅
              </div>
            )}
          </div>
        );

      case 'history':
        return (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">报表名称</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">期间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">生成时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reports.map(report => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {report.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <TypeBadge type={report.type} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {report.periodStart} ~ {report.periodEnd}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {report.generatedAt ? new Date(report.generatedAt).toLocaleString('zh-CN') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={report.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handlePreview(report)}
                        disabled={report.status !== 'generated'}
                        className="text-blue-600 hover:text-blue-800 mr-3 disabled:opacity-50"
                      >
                        预览
                      </button>
                      <button
                        onClick={() => handleDownload(report, 'pdf')}
                        disabled={report.status !== 'generated'}
                        className="text-green-600 hover:text-green-800 disabled:opacity-50"
                      >
                        下载
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📊 报表中心</h1>
        <button
          onClick={() => setActiveTab('templates')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          + 新建报表
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b border-gray-200">
        <TabButton
          active={activeTab === 'my_reports'}
          onClick={() => setActiveTab('my_reports')}
        >
          我的报表
        </TabButton>
        <TabButton
          active={activeTab === 'templates'}
          onClick={() => setActiveTab('templates')}
        >
          报表模板
        </TabButton>
        <TabButton
          active={activeTab === 'subscriptions'}
          onClick={() => setActiveTab('subscriptions')}
          badge={subscriptions.filter(s => s.isActive).length}
        >
          订阅管理
        </TabButton>
        <TabButton
          active={activeTab === 'history'}
          onClick={() => setActiveTab('history')}
        >
          生成历史
        </TabButton>
      </div>

      {/* Filters (for reports tab) */}
      {activeTab === 'my_reports' && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
              <select
                value={typeFilter}
                onChange={e => setTypeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">全部</option>
                <option value="daily">日报</option>
                <option value="weekly">周报</option>
                <option value="monthly">月报</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
              <select
                value={categoryFilter}
                onChange={e => setCategoryFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">全部</option>
                <option value="operations">运营</option>
                <option value="customer">客户</option>
                <option value="equipment">设备</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">搜索</label>
              <input
                type="text"
                value={searchKeyword}
                onChange={e => setSearchKeyword(e.target.value)}
                placeholder="搜索报表名称..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {renderContent()}

      {/* Modals */}
      <GenerateReportModal
        template={selectedTemplate}
        onClose={() => setSelectedTemplate(null)}
        onGenerate={handleGenerateReport}
      />

      <ReportPreviewModal
        report={previewReport}
        onClose={() => setPreviewReport(null)}
        onDownload={format => {
          handleDownload(previewReport!, format);
          setPreviewReport(null);
        }}
      />
    </div>
  );
};

export default ReportCenter;
