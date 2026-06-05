import client from './client'
import type { RecordingSearchParams, RecordingSearchResponse } from '../types'

export const searchRecordings = (params: RecordingSearchParams) =>
  client
    .get<RecordingSearchResponse>('/api/recordings/search', { params })
    .then(r => r.data)

export const audioUrl = (callId: string) =>
  `${client.defaults.baseURL}/api/recordings/${callId}/audio`
