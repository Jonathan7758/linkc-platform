/**
 * LinkC Platform API 服务
 */

import axios from "axios"

const API_BASE = import.meta.env.VITE_API_URL || ""
const TENANT_ID = "tenant_001"

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json"
  }
})

// 空间管理 API
export const spacesApi = {
  listBuildings: () => 
    api.get(`/api/v1/spaces/buildings?tenant_id=${TENANT_ID}`),
  
  getBuilding: (buildingId) => 
    api.get(`/api/v1/spaces/buildings/${buildingId}`),
  
  listFloors: (buildingId) => 
    api.get(`/api/v1/spaces/buildings/${buildingId}/floors`),
  
  listZones: (params = {}) => 
    api.get("/api/v1/spaces/zones", { params }),
  
  getZone: (zoneId) => 
    api.get(`/api/v1/spaces/zones/${zoneId}`)
}

// 任务管理 API
export const tasksApi = {
  list: (params = {}) => 
    api.get("/api/v1/tasks", { params: { tenant_id: TENANT_ID, ...params } }),
  
  getPending: () => 
    api.get(`/api/v1/tasks/pending?tenant_id=${TENANT_ID}`),
  
  get: (taskId) => 
    api.get(`/api/v1/tasks/${taskId}`),
  
  create: (task) => 
    api.post(`/api/v1/tasks?tenant_id=${TENANT_ID}`, task),
  
  assign: (taskId, robotId) => 
    api.post(`/api/v1/tasks/${taskId}/assign`, { robot_id: robotId, assigned_by: "web_user" }),
  
  updateStatus: (taskId, status, completionRate = null) => 
    api.patch(`/api/v1/tasks/${taskId}/status`, { status, completion_rate: completionRate })
}

// 机器人管理 API
export const robotsApi = {
  list: (params = {}) => 
    api.get("/api/v1/robots", { params: { tenant_id: TENANT_ID, ...params } }),
  
  getAvailable: (minBattery = 20) => 
    api.get(`/api/v1/robots/available?tenant_id=${TENANT_ID}&min_battery=${minBattery}`),
  
  getStatus: (robotId) => 
    api.get(`/api/v1/robots/${robotId}`),
  
  startCleaning: (robotId, zoneId, mode = "standard") => 
    api.post(`/api/v1/robots/${robotId}/start-cleaning`, { zone_id: zoneId, cleaning_mode: mode }),
  
  stopCleaning: (robotId, reason = null) => 
    api.post(`/api/v1/robots/${robotId}/stop-cleaning`, { reason }),
  
  sendToCharger: (robotId) => 
    api.post(`/api/v1/robots/${robotId}/charge`)
}

// Agent API
export const agentsApi = {
  list: () => 
    api.get("/api/v1/agents"),
  
  get: (agentId) => 
    api.get(`/api/v1/agents/${agentId}`),
  
  run: (agentId) => 
    api.post(`/api/v1/agents/${agentId}/run?tenant_id=${TENANT_ID}`),
  
  getPendingApprovals: () => 
    api.get("/api/v1/agents/approvals/pending"),
  
  approve: (decisionId, approved, approver = "web_user") => 
    api.post(`/api/v1/agents/approvals/${decisionId}`, { approved, approver }),
  
  getStats: () => 
    api.get("/api/v1/agents/stats")
}

export default api
