import { formatDuration } from '../../utils/time'
import type { AgentMetrics } from '../../types'

interface Props {
  agents: AgentMetrics[]
}

const pct = (n: number) => `${n.toFixed(1)}%`

export default function AgentTable({ agents }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800">
        <h3 className="text-sm font-medium text-gray-300">Agent Analytics</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 text-xs uppercase tracking-wide border-b border-gray-800">
              <th className="text-left px-5 py-3">Agent</th>
              <th className="text-right px-4 py-3">Answered</th>
              <th className="text-right px-4 py-3">Missed</th>
              <th className="text-right px-4 py-3">Answer Rate</th>
              <th className="text-right px-4 py-3">Avg Talk Time</th>
              <th className="text-right px-4 py-3">FCR</th>
              <th className="text-right px-5 py-3">SLA</th>
            </tr>
          </thead>
          <tbody>
            {agents.map(a => (
              <tr
                key={a.agent_name}
                className="border-b border-gray-800/50 last:border-0 hover:bg-gray-800/30 transition-colors"
              >
                <td className="px-5 py-3 text-white font-medium">{a.agent_name}</td>
                <td className="px-4 py-3 text-right text-gray-300 tabular-nums">{a.answered}</td>
                <td className="px-4 py-3 text-right text-gray-300 tabular-nums">{a.missed}</td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className={a.answer_rate >= 80 ? 'text-green-400' : a.answer_rate >= 60 ? 'text-yellow-400' : 'text-red-400'}>
                    {pct(a.answer_rate)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-gray-300 tabular-nums">{formatDuration(a.avg_talk_time)}</td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className={a.first_call_resolution >= 70 ? 'text-green-400' : 'text-yellow-400'}>
                    {pct(a.first_call_resolution)}
                  </span>
                </td>
                <td className="px-5 py-3 text-right tabular-nums">
                  <span className={a.sla_compliance >= 80 ? 'text-green-400' : a.sla_compliance >= 60 ? 'text-yellow-400' : 'text-red-400'}>
                    {pct(a.sla_compliance)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
