import type { TranscriptAnalysisResult } from '../../types'

interface Props {
  analysis: TranscriptAnalysisResult
}

const sentimentColor = {
  Positive: 'text-green-400',
  Neutral: 'text-yellow-400',
  Negative: 'text-red-400',
}

const sentimentBg = {
  Positive: 'bg-green-400/10 border-green-400/30',
  Neutral: 'bg-yellow-400/10 border-yellow-400/30',
  Negative: 'bg-red-400/10 border-red-400/30',
}

export default function AnalysisPanel({ analysis }: Props) {
  const sColor = sentimentColor[analysis.sentiment] ?? 'text-gray-400'
  const sBg = sentimentBg[analysis.sentiment] ?? 'bg-gray-800 border-gray-700'
  const scoreColor =
    analysis.agent_performance_score >= 7
      ? 'text-green-400'
      : analysis.agent_performance_score >= 4
        ? 'text-yellow-400'
        : 'text-red-400'

  return (
    <div className="overflow-y-auto h-full px-6 py-8 space-y-6 border-t border-gray-800">
      {/* Language */}
      <div className="flex flex-wrap gap-2">
        {analysis.language_detected.map(lang => (
          <span key={lang} className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs rounded-full">
            {lang}
          </span>
        ))}
      </div>

      {/* Sentiment + Tone */}
      <div className="flex gap-4">
        <div className={`flex-1 rounded-lg border px-4 py-3 ${sBg}`}>
          <div className="text-xs text-gray-500 mb-1">Sentiment</div>
          <div className={`font-semibold ${sColor}`}>{analysis.sentiment}</div>
        </div>
        <div className="flex-1 rounded-lg border border-gray-700 bg-gray-800/50 px-4 py-3">
          <div className="text-xs text-gray-500 mb-1">Agent Tone</div>
          <div className="font-semibold text-white">{analysis.agent_tone}</div>
        </div>
      </div>

      {/* Score */}
      <div className="rounded-lg border border-gray-700 bg-gray-800/50 px-4 py-3">
        <div className="text-xs text-gray-500 mb-2">Performance Score</div>
        <div className="flex items-end gap-2">
          <span className={`text-3xl font-bold tabular-nums ${scoreColor}`}>
            {analysis.agent_performance_score.toFixed(1)}
          </span>
          <span className="text-gray-500 text-sm mb-1">/ 10</span>
        </div>
        <p className="text-xs text-gray-400 mt-2 leading-relaxed">{analysis.performance_reasoning}</p>
      </div>

      {/* Query buckets */}
      <div>
        <div className="text-xs text-gray-500 mb-2">Issue Categories</div>
        <div className="flex flex-wrap gap-2">
          {analysis.query_buckets.map(b => (
            <span key={b} className="px-2 py-1 bg-gray-800 border border-gray-700 text-gray-300 text-xs rounded">
              {b}
            </span>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div>
        <div className="text-xs text-gray-500 mb-2">Coaching Recommendations</div>
        <ol className="space-y-2">
          {analysis.recommendations.map((r, i) => (
            <li key={i} className="flex gap-3 text-sm text-gray-300">
              <span className="text-blue-400 font-semibold flex-shrink-0">{i + 1}.</span>
              <span>{r}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Summary */}
      <div className="rounded-lg bg-gray-800/50 border border-gray-700 px-4 py-3">
        <div className="text-xs text-gray-500 mb-2">Call Summary</div>
        <p className="text-sm text-gray-300 leading-relaxed">{analysis.call_summary}</p>
      </div>
    </div>
  )
}
