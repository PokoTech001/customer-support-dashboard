/** "MM:SS" → total seconds */
export const tsToSeconds = (ts: string): number => {
  const parts = ts.split(':').map(Number)
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return 0
}

/** seconds → "M:SS" display string */
export const formatDuration = (seconds: number): string => {
  const s = Math.floor(seconds)
  const mm = Math.floor(s / 60)
  const ss = (s % 60).toString().padStart(2, '0')
  return `${mm}:${ss}`
}

/** "YYYY-MM-DD" + "HH:MM" → "YYYY-MM-DD HH:MM:00" */
export const toDateTime = (date: string, time: string) => `${date} ${time}:00`

/** "YYYY-MM-DD" → "YYYY-MM-DD 00:00:00" */
export const toFromDate = (date: string) => `${date} 00:00:00`

/** "YYYY-MM-DD" → "YYYY-MM-DD 23:59:59" */
export const toToDate = (date: string) => `${date} 23:59:59`

/** Return today's date as "YYYY-MM-DD" */
export const today = () => new Date().toISOString().slice(0, 10)

/** Return date N days ago as "YYYY-MM-DD" */
export const daysAgo = (n: number) => {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

/** Return the 1st of the current month as "YYYY-MM-DD" */
export const firstOfMonth = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}
