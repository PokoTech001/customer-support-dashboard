import { Search } from 'lucide-react'
import { useState } from 'react'
import { formatDuration, toDateTime } from '../../utils/time'
import type { RecordingSearchResult, RecordingSearchParams } from '../../types'

interface Props {
  recordings: RecordingSearchResult[]
  isLoading: boolean
  onSearch: (params: RecordingSearchParams) => void
  onPlay: (call: RecordingSearchResult) => void
}

export default function RecordingsPanel({ recordings, isLoading, onSearch, onPlay }: Props) {
  const [fromDate, setFromDate] = useState('')
  const [fromTime, setFromTime] = useState('00:00')
  const [toDate, setToDate] = useState('')
  const [toTime, setToTime] = useState('23:59')
  const [agentName, setAgentName] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!fromDate || !toDate) return
    onSearch({
      from_date: toDateTime(fromDate, fromTime),
      to_date: toDateTime(toDate, toTime),
      agent_name: agentName || undefined,
    })
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-semibold mb-6">Transcript Analytics</h1>

      {/* Search form */}
      <form onSubmit={handleSearch} className="bg-gray-900 rounded-xl border border-gray-800 p-5 mb-6">
        <div className="grid grid-cols-2 gap-3 mb-3">
          {/* From */}
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">From</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={fromDate}
                onChange={e => setFromDate(e.target.value)}
                required
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
              <input
                type="time"
                value={fromTime}
                onChange={e => setFromTime(e.target.value)}
                className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* To */}
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">To</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={toDate}
                onChange={e => setToDate(e.target.value)}
                required
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
              <input
                type="time"
                value={toTime}
                onChange={e => setToTime(e.target.value)}
                className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs text-gray-400 mb-1.5">Agent Name</label>
            <input
              type="text"
              value={agentName}
              onChange={e => setAgentName(e.target.value)}
              placeholder="All agents"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Search size={14} />
            {isLoading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </form>

      {/* Results table */}
      {recordings.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wide">
                <th className="text-left px-5 py-3">Date</th>
                <th className="text-left px-5 py-3">Time</th>
                <th className="text-left px-5 py-3">Agent</th>
                <th className="text-left px-5 py-3">Duration</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {recordings.map(call => (
                <tr
                  key={call.call_id}
                  className="border-b border-gray-800/50 last:border-0 hover:bg-gray-800/40 transition-colors"
                >
                  <td className="px-5 py-3 text-gray-300">{call.date}</td>
                  <td className="px-5 py-3 text-gray-300">{call.time}</td>
                  <td className="px-5 py-3 text-white font-medium">{call.agent_name}</td>
                  <td className="px-5 py-3 text-gray-400 tabular-nums">{formatDuration(call.duration)}</td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => onPlay(call)}
                      className="flex items-center gap-1.5 ml-auto bg-white text-gray-900 hover:bg-gray-100 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors"
                    >
                      ▶ Play
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!isLoading && recordings.length === 0 && (
        <p className="text-center text-gray-600 py-12">Search for recordings to get started.</p>
      )}
    </div>
  )
}
