export interface RecordingSearchResult {
  call_id: string
  agent_name: string
  date: string
  time: string
  duration: number  // seconds
}

export interface RecordingSearchResponse {
  results: RecordingSearchResult[]
}

export interface TranscriptTurn {
  speaker: string   // real agent name | "Customer"
  timestamp: string // "MM:SS"
  text: string
}

export interface TranscribeResponse {
  language_detected: string[]
  transcript: TranscriptTurn[]
}

export interface TranscriptAnalysisResult {
  call_id?: string
  language_detected: string[]
  transcript: TranscriptTurn[]
  query_buckets: string[]
  sentiment: 'Positive' | 'Neutral' | 'Negative'
  sentiment_score: number
  agent_tone: string
  agent_performance_score: number
  performance_reasoning: string
  recommendations: string[]
  call_summary: string
}

export interface CallAnalysisRequest {
  call_id: string
  agent_name: string
}

export interface RecordingSearchParams {
  from_date: string
  to_date: string
  agent_name?: string
}

// ---------------------------------------------------------------------------
// Dashboard — analytics
// ---------------------------------------------------------------------------

export interface HourlyBucket {
  hour: number
  answered: number
  missed: number
}

export interface DailyBucket {
  date: string
  answered: number
  missed: number
}

export interface OverallAnalyticsResponse {
  total_inbound: number
  answered: number
  missed: number
  answer_rate: number
  avg_handle_time: number
  avg_talk_time: number
  sla_compliance: number
  hourly_distribution: HourlyBucket[]
  daily_distribution: DailyBucket[]
}

export interface AgentMetrics {
  agent_name: string
  answered: number
  missed: number
  answer_rate: number
  avg_talk_time: number
  first_call_resolution: number
  sla_compliance: number
}

export interface AgentAnalyticsResponse {
  agents: AgentMetrics[]
}

export interface AnalyticsParams {
  from_date: string
  to_date: string
}
