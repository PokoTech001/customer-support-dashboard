import { ChevronDown, Loader2 } from 'lucide-react'
import { formatDuration } from '../../utils/time'
import type { RecordingSearchResult, TranscriptTurn, TranscriptAnalysisResult } from '../../types'
import AudioPlayer from './AudioPlayer'
import TranscriptViewer from './TranscriptViewer'
import AnalysisPanel from './AnalysisPanel'

interface Props {
  isOpen: boolean
  call: RecordingSearchResult | null
  transcript: TranscriptTurn[] | null
  isTranscribing: boolean
  transcribeError: string | null
  analysis: TranscriptAnalysisResult | null
  isAnalyzing: boolean
  analyzeError: string | null
  currentTime: number
  onBack: () => void
  onAnalyze: () => void
  onTimeUpdate: (t: number) => void
}

export default function TranscriptCurtain({
  isOpen,
  call,
  transcript,
  isTranscribing,
  transcribeError,
  analysis,
  isAnalyzing,
  analyzeError,
  currentTime,
  onBack,
  onAnalyze,
  onTimeUpdate,
}: Props) {
  return (
    <div
      className={`fixed inset-0 z-50 bg-gray-950 flex flex-col transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${
        isOpen ? 'translate-y-0' : 'translate-y-full'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 flex-shrink-0">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-gray-400 hover:text-white text-sm transition-colors"
        >
          <ChevronDown size={18} />
          Back to recordings
        </button>

        {call && (
          <div className="text-sm text-gray-400 text-center">
            <span className="text-white font-medium">{call.agent_name}</span>
            <span className="mx-2">·</span>
            {call.date}
            <span className="mx-2">·</span>
            {formatDuration(call.duration)}
          </div>
        )}

        <button
          onClick={onAnalyze}
          disabled={isAnalyzing || analysis !== null}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
        >
          {isAnalyzing && <Loader2 size={13} className="animate-spin" />}
          {analysis ? 'Analyzed' : isAnalyzing ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>

      {/* Body — transcript left, analysis right (when available) */}
      <div className="flex-1 flex min-h-0">
        {/* Transcript pane */}
        <div className={`flex flex-col min-h-0 transition-all duration-300 ${analysis ? 'w-3/5' : 'w-full'}`}>
          {isTranscribing && (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-gray-500">
              <Loader2 size={28} className="animate-spin" />
              <span className="text-sm">Transcribing call…</span>
            </div>
          )}

          {transcribeError && !isTranscribing && (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-red-400 text-sm">{transcribeError}</p>
            </div>
          )}

          {transcript && !isTranscribing && (
            <TranscriptViewer
              transcript={transcript}
              currentTime={currentTime}
              agentName={call?.agent_name ?? 'Agent'}
            />
          )}
        </div>

        {/* Analysis pane (slides in) */}
        {analysis && (
          <div className="w-2/5 border-l border-gray-800 min-h-0">
            {analyzeError && (
              <div className="flex items-center justify-center h-full">
                <p className="text-red-400 text-sm">{analyzeError}</p>
              </div>
            )}
            {!analyzeError && <AnalysisPanel analysis={analysis} />}
          </div>
        )}
      </div>

      {/* Sticky audio player */}
      {call && isOpen && (
        <AudioPlayer call={call} onTimeUpdate={onTimeUpdate} />
      )}
    </div>
  )
}
