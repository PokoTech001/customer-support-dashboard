import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useState } from 'react'
import { getAgentAnalytics, getOverallAnalytics } from '../api/calls'
import AgentTable from '../components/dashboard/AgentTable'
import DailyChart from '../components/dashboard/DailyChart'
import HourlyChart from '../components/dashboard/HourlyChart'
import KPICard from '../components/dashboard/KPICard'
import { daysAgo, formatDuration, today, toDateTime } from '../utils/time'

export default function DashboardPage() {
  const [fromDate, setFromDate] = useState(daysAgo(7))
  const [fromTime, setFromTime] = useState('00:00')
  const [toDate, setToDate] = useState(today())
  const [toTime, setToTime] = useState('23:59')

  // params that actually drive the queries — only updated on Search click
  const [params, setParams] = useState({
    from_date: toDateTime(daysAgo(7), '00:00'),
    to_date: toDateTime(today(), '23:59'),
  })

  const { data: overall, isLoading: loadingOverall, error: errOverall } = useQuery({
    queryKey: ['overall', params],
    queryFn: () => getOverallAnalytics(params),
  })

  const { data: agentData, isLoading: loadingAgents } = useQuery({
    queryKey: ['agents', params],
    queryFn: () => getAgentAnalytics(params),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setParams({
      from_date: toDateTime(fromDate, fromTime),
      to_date: toDateTime(toDate, toTime),
    })
  }

  const isLoading = loadingOverall || loadingAgents

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {/* Date filter */}
      <form onSubmit={handleSearch} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">From</label>
            <div className="flex gap-2">
              <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
              <input type="time" value={fromTime} onChange={e => setFromTime(e.target.value)}
                className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">To</label>
            <div className="flex gap-2">
              <input type="date" value={toDate} onChange={e => setToDate(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
              <input type="time" value={toTime} onChange={e => setToTime(e.target.value)}
                className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
            </div>
          </div>
          <button type="submit" disabled={isLoading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors">
            <Search size={14} />
            {isLoading ? 'Loading…' : 'Search'}
          </button>
        </div>
      </form>

      {errOverall && (
        <p className="text-red-400 text-sm">Failed to load analytics. Is the backend running?</p>
      )}

      {/* KPI cards */}
      {overall && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <KPICard label="Total Inbound" value={overall.total_inbound.toLocaleString()} />
            <KPICard label="Answered" value={overall.answered.toLocaleString()} sub={`${overall.answer_rate.toFixed(1)}% answer rate`} />
            <KPICard label="Missed" value={overall.missed.toLocaleString()} sub={`${(100 - overall.answer_rate).toFixed(1)}% miss rate`} />
            <KPICard label="Avg Handle Time" value={formatDuration(overall.avg_handle_time)} />
            <KPICard label="Avg Talk Time" value={formatDuration(overall.avg_talk_time)} />
            <KPICard label="SLA Compliance" value={`${overall.sla_compliance.toFixed(1)}%`} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <HourlyChart data={overall.hourly_distribution} />
            <DailyChart data={overall.daily_distribution} />
          </div>
        </>
      )}

      {/* Agent table */}
      {agentData && agentData.agents.length > 0 && (
        <AgentTable agents={agentData.agents} />
      )}

      {!isLoading && !overall && !errOverall && (
        <p className="text-center text-gray-600 py-12">
          Showing last 7 days. Adjust the date range and click Search.
        </p>
      )}
    </div>
  )
}
