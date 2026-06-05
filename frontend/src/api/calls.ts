import client from './client'
import type { OverallAnalyticsResponse, AgentAnalyticsResponse, AnalyticsParams } from '../types'

export const getOverallAnalytics = (params: AnalyticsParams) =>
  client.get<OverallAnalyticsResponse>('/api/calls/overall', { params }).then(r => r.data)

export const getAgentAnalytics = (params: AnalyticsParams) =>
  client.get<AgentAnalyticsResponse>('/api/calls/agent', { params }).then(r => r.data)
