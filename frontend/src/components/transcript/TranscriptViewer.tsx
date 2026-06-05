import { useEffect, useRef } from 'react'
import { tsToSeconds } from '../../utils/time'
import type { TranscriptTurn } from '../../types'

interface Props {
  transcript: TranscriptTurn[]
  currentTime: number
  agentName: string
}

export default function TranscriptViewer({ transcript, currentTime, agentName }: Props) {
  const turnRefs = useRef<(HTMLDivElement | null)[]>([])

  // Find the last turn whose timestamp <= currentTime
  let activeIndex = -1
  for (let i = transcript.length - 1; i >= 0; i--) {
    if (tsToSeconds(transcript[i].timestamp) <= currentTime) {
      activeIndex = i
      break
    }
  }

  useEffect(() => {
    const el = turnRefs.current[activeIndex]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [activeIndex])

  return (
    <div className="transcript-scroll overflow-y-auto h-full px-8 py-10 space-y-7">
      {transcript.map((turn, i) => {
        const isActive = i === activeIndex
        const isAgent = turn.speaker.toLowerCase() !== 'customer'

        return (
          <div
            key={i}
            ref={el => { turnRefs.current[i] = el }}
            className={`transition-all duration-300 ${
              isActive ? 'opacity-100' : 'opacity-40'
            }`}
          >
            <span
              className={`text-sm font-semibold ${
                isAgent ? 'text-blue-400' : 'text-gray-400'
              }`}
            >
              {turn.speaker.toLowerCase()}
            </span>
            <span
              className={`ml-2 transition-all duration-300 ${
                isActive ? 'text-white text-lg' : 'text-gray-300 text-base'
              }`}
            >
              : {turn.text}
            </span>
            <span className="ml-2 text-gray-600 text-sm">({turn.timestamp})</span>
          </div>
        )
      })}
    </div>
  )
}
