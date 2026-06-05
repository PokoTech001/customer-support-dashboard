import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { analyzeCall, transcribeCall } from '../api/analyze'
import { searchRecordings } from '../api/recordings'
import TranscriptCurtain from '../components/transcript/TranscriptCurtain'
import RecordingsPanel from '../components/transcript/RecordingsPanel'
import type {
  RecordingSearchParams,
  RecordingSearchResult,
  TranscriptAnalysisResult,
  TranscriptTurn,
} from '../types'

export default function TranscriptPage() {
  const [recordings, setRecordings] = useState<RecordingSearchResult[]>([])
  const [selectedCall, setSelectedCall] = useState<RecordingSearchResult | null>(null)
  const [curtainOpen, setCurtainOpen] = useState(false)
  const [transcript, setTranscript] = useState<TranscriptTurn[] | null>(null)
  const [analysis, setAnalysis] = useState<TranscriptAnalysisResult | null>(null)
  const [currentTime, setCurrentTime] = useState(0)

  /* ------------------------------------------------------------------ search */

  const searchMutation = useMutation({
    mutationFn: searchRecordings,
    onSuccess: data => setRecordings(data.results),
  })

  const handleSearch = (params: RecordingSearchParams) => {
    searchMutation.mutate(params)
  }

  /* ------------------------------------------------------------------ play */

  const transcribeMutation = useMutation({
    mutationFn: transcribeCall,
    onSuccess: data => {
      setTranscript(data.transcript)
    },
  })

  const handlePlay = (call: RecordingSearchResult) => {
    setSelectedCall(call)
    setTranscript(null)
    setAnalysis(null)
    setCurrentTime(0)
    setCurtainOpen(true)
    transcribeMutation.mutate({ call_id: call.call_id, agent_name: call.agent_name })
  }

  /* ------------------------------------------------------------------ analyze */

  const analyzeMutation = useMutation({
    mutationFn: analyzeCall,
    onSuccess: data => setAnalysis(data),
  })

  const handleAnalyze = () => {
    if (!selectedCall || analysis) return
    analyzeMutation.mutate({
      call_id: selectedCall.call_id,
      agent_name: selectedCall.agent_name,
    })
  }

  /* ------------------------------------------------------------------ back */

  const handleBack = () => {
    setCurtainOpen(false)
    // Small delay so curtain slides out before clearing state
    setTimeout(() => {
      setSelectedCall(null)
      setTranscript(null)
      setAnalysis(null)
      setCurrentTime(0)
      transcribeMutation.reset()
      analyzeMutation.reset()
    }, 500)
  }

  /* ------------------------------------------------------------------ render */

  const transcribeError =
    transcribeMutation.isError
      ? 'Transcription failed. Please try again.'
      : null

  const analyzeError =
    analyzeMutation.isError
      ? 'Analysis failed. Please try again.'
      : null

  return (
    <>
      <RecordingsPanel
        recordings={recordings}
        isLoading={searchMutation.isPending}
        onSearch={handleSearch}
        onPlay={handlePlay}
      />

      <TranscriptCurtain
        isOpen={curtainOpen}
        call={selectedCall}
        transcript={transcript}
        isTranscribing={transcribeMutation.isPending}
        transcribeError={transcribeError}
        analysis={analysis}
        isAnalyzing={analyzeMutation.isPending}
        analyzeError={analyzeError}
        currentTime={currentTime}
        onBack={handleBack}
        onAnalyze={handleAnalyze}
        onTimeUpdate={setCurrentTime}
      />
    </>
  )
}
