import { Pause, Play } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { audioUrl } from '../../api/recordings'
import { formatDuration } from '../../utils/time'
import type { RecordingSearchResult } from '../../types'

interface Props {
  call: RecordingSearchResult
  onTimeUpdate: (t: number) => void
}

export default function AudioPlayer({ call, onTimeUpdate }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  // Auto-play when component mounts (new call selected)
  useEffect(() => {
    const el = audioRef.current
    if (!el) return
    el.load()
    el.play().catch(() => {})
  }, [call.call_id])

  const toggle = () => {
    const el = audioRef.current
    if (!el) return
    isPlaying ? el.pause() : el.play()
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const t = Number(e.target.value)
    if (audioRef.current) audioRef.current.currentTime = t
    setCurrentTime(t)
    onTimeUpdate(t)
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="bg-gray-900 border-t border-gray-800 px-6 py-4">
      <audio
        ref={audioRef}
        src={audioUrl(call.call_id)}
        onTimeUpdate={e => {
          const t = e.currentTarget.currentTime
          setCurrentTime(t)
          onTimeUpdate(t)
        }}
        onLoadedMetadata={e => setDuration(e.currentTarget.duration)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="flex items-center gap-4">
        {/* Play / Pause */}
        <button
          onClick={toggle}
          className="w-9 h-9 rounded-full bg-white text-gray-900 flex items-center justify-center flex-shrink-0 hover:scale-105 transition-transform"
        >
          {isPlaying ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
        </button>

        {/* Call info */}
        <div className="text-xs text-gray-400 w-36 flex-shrink-0 leading-tight">
          <div className="text-white font-medium truncate">{call.agent_name}</div>
          <div>{call.date} · {formatDuration(call.duration)}</div>
        </div>

        {/* Progress bar */}
        <div className="flex-1 flex items-center gap-2">
          <span className="text-xs text-gray-500 w-10 text-right tabular-nums">
            {formatDuration(currentTime)}
          </span>
          <div className="flex-1 relative">
            <div className="w-full h-1 bg-gray-700 rounded-full">
              <div
                className="h-1 bg-white rounded-full pointer-events-none"
                style={{ width: `${progress}%` }}
              />
            </div>
            <input
              type="range"
              min={0}
              max={duration || 0}
              step={0.5}
              value={currentTime}
              onChange={handleSeek}
              className="absolute inset-0 w-full opacity-0 cursor-pointer h-1"
            />
          </div>
          <span className="text-xs text-gray-500 w-10 tabular-nums">
            {formatDuration(duration)}
          </span>
        </div>
      </div>
    </div>
  )
}
