/**
 * LinkC Platform - Frontend Type Definitions
 */

// ============================================================
// Agent Types
// ============================================================

export type AgentType = 'cleaning_scheduler' | 'conversation' | 'data_collector';
export type ActivityLevel = 'info' | 'warning' | 'error' | 'critical';
export type ActivityType = 'decision' | 'tool_call' | 'escalation' | 'state_change';
export type PendingItemPriority = 'low' | 'medium' | 'high' | 'critical';
export type PendingItemStatus = 'pending' | 'in_progress' | 'resolved' | 'expired';
export type FeedbackType = 'approval' | 'correction' | 'rejection';

// ============================================================
// Agent Activity
// ============================================================

export interface AgentActivity {
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

export interface ActivitiesResponse {
  activities: AgentActivity[];
  nextCursor?: string;
  hasMore: boolean;
}

// ============================================================
// Pending Items
// ============================================================

export interface SuggestedAction {
  action: string;
  label: string;
  params?: Record<string, any>;
}

export interface PendingItem {
  itemId: string;
  type: string;
  priority: PendingItemPriority;
  status: PendingItemStatus;
  title: string;
  description: string;
  agentType: AgentType;
  relatedEntities: Record<string, string>;
  suggestedActions: SuggestedAction[];
  createdAt: string;
  expiresAt?: string;
}

export interface PendingItemsResponse {
  items: PendingItem[];
  total: number;
  byPriority: Record<string, number>;
}

// ============================================================
// Feedback
// ============================================================

export interface FeedbackRequest {
  activityId: string;
  feedbackType: FeedbackType;
  rating: number;
  comment?: string;
  correctionData?: Record<string, any>;
}

export interface FeedbackResponse {
  feedbackId: string;
  activityId: string;
  status: string;
  willAffectFuture: boolean;
}

// ============================================================
// Robot
// ============================================================

export interface Position {
  x: number;
  y: number;
  orientation: number;
  floorId?: string;
}

export interface Robot {
  robotId: string;
  name: string;
  brand: string;
  model: string;
  status: string;
  batteryLevel: number;
  position?: Position;
  currentTaskId?: string;
  lastActiveAt?: string;
}

export interface RobotListResponse {
  items: Robot[];
  total: number;
  page: number;
  pageSize: number;
}

// ============================================================
// Agent Status
// ============================================================

export interface AgentHealth {
  status: string;
  cpuUsage?: number;
  memoryUsage?: number;
}

export interface AgentStatistics {
  decisionsToday: number;
  escalationsToday: number;
  feedbackScore?: number;
  conversationsToday?: number;
  avgResponseTime?: number;
}

export interface AgentStatus {
  agentId: string;
  agentType: AgentType;
  status: string;
  lastActivityAt?: string;
  statistics: AgentStatistics;
  health: AgentHealth;
}

// ============================================================
// API Response
// ============================================================

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}
