/**
 * LinkC Platform - API Service
 */

import {
  AgentActivity,
  ActivitiesResponse,
  PendingItemsResponse,
  FeedbackRequest,
  FeedbackResponse,
  RobotListResponse,
  AgentStatus,
  AgentType,
  ActivityLevel,
  PendingItemPriority
} from '../types/index';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// ============================================================
// HTTP Client
// ============================================================

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// ============================================================
// Agent Activities API
// ============================================================

export interface GetActivitiesParams {
  tenantId: string;
  agentType?: AgentType;
  level?: ActivityLevel;
  limit?: number;
  cursor?: string;
}

export async function getActivities(
  params: GetActivitiesParams
): Promise<ActivitiesResponse> {
  const searchParams = new URLSearchParams();
  if (params.agentType) searchParams.set('agent_type', params.agentType);
  if (params.level) searchParams.set('level', params.level);
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.cursor) searchParams.set('cursor', params.cursor);

  return fetchApi<ActivitiesResponse>(
    `/agents/activities?${searchParams.toString()}`
  );
}

// ============================================================
// Pending Items API
// ============================================================

export interface GetPendingItemsParams {
  tenantId: string;
  priority?: PendingItemPriority;
  status?: string;
  limit?: number;
}

export async function getPendingItems(
  params: GetPendingItemsParams
): Promise<PendingItemsResponse> {
  const searchParams = new URLSearchParams();
  if (params.priority) searchParams.set('priority', params.priority);
  if (params.status) searchParams.set('status', params.status);
  if (params.limit) searchParams.set('limit', params.limit.toString());

  return fetchApi<PendingItemsResponse>(
    `/agents/pending-items?${searchParams.toString()}`
  );
}

export interface ResolveItemRequest {
  action: string;
  comment?: string;
  params?: Record<string, unknown>;
}

export async function resolvePendingItem(
  itemId: string,
  request: ResolveItemRequest
): Promise<unknown> {
  return fetchApi(`/agents/pending-items/${itemId}/resolve`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ============================================================
// Feedback API
// ============================================================

export async function submitFeedback(
  request: FeedbackRequest
): Promise<FeedbackResponse> {
  return fetchApi<FeedbackResponse>('/agents/feedback', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ============================================================
// Robot API
// ============================================================

export interface GetRobotsParams {
  buildingId?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}

export async function getRobots(
  params: GetRobotsParams = {}
): Promise<RobotListResponse> {
  const searchParams = new URLSearchParams();
  if (params.buildingId) searchParams.set('building_id', params.buildingId);
  if (params.status) searchParams.set('status', params.status);
  if (params.page) searchParams.set('page', params.page.toString());
  if (params.pageSize) searchParams.set('page_size', params.pageSize.toString());

  return fetchApi<RobotListResponse>(`/robots?${searchParams.toString()}`);
}

export async function getRobotStatus(robotId: string): Promise<unknown> {
  return fetchApi(`/robots/${robotId}/status`);
}

// ============================================================
// Agent Status API
// ============================================================

export async function getAgentStatus(): Promise<{ agents: AgentStatus[] }> {
  return fetchApi<{ agents: AgentStatus[] }>('/agents/status');
}

export async function controlAgent(
  agentId: string,
  action: string,
  reason?: string
): Promise<unknown> {
  return fetchApi(`/agents/${agentId}/control`, {
    method: 'POST',
    body: JSON.stringify({ action, reason }),
  });
}

// ============================================================
// WebSocket
// ============================================================

export function createActivityWebSocket(
  tenantId: string,
  onMessage: (activity: AgentActivity) => void,
  filters?: { agentTypes?: AgentType[]; levels?: ActivityLevel[] }
): WebSocket {
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/agents/ws/activities?tenant_id=${tenantId}`;

  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    if (filters) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        filters: {
          agent_types: filters.agentTypes,
          levels: filters.levels,
        },
      }));
    }
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'activity') {
      onMessage(message.data);
    }
  };

  return ws;
}
