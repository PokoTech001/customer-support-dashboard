import client from './client'
import type {
  CallAnalysisRequest,
  TranscribeResponse,
  TranscriptAnalysisResult,
} from '../types'

export const transcribeCall = (body: CallAnalysisRequest) =>
  client
    .post<TranscribeResponse>('/api/analyze/transcribe', body)
    .then(r => r.data)

export const analyzeCall = (body: CallAnalysisRequest) =>
  client
    .post<TranscriptAnalysisResult>('/api/analyze/from-recording', body)
    .then(r => r.data)
