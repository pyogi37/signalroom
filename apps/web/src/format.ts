export const label = (value: string) => value.replaceAll('_', ' ')
export const sentence = (value: string) => { const text = label(value); return text.charAt(0).toUpperCase() + text.slice(1) }
export const ms = (value: number | null | undefined) => value == null ? '–' : value >= 1000 ? `${(value / 1000).toFixed(1)} s` : `${Math.round(value)} ms`
export const tokens = (value: number | null | undefined) => value == null ? '–' : value.toLocaleString()
export const usd = (value: number | null | undefined) => value == null ? 'not priced' : value < 0.01 ? `$${value.toFixed(4)}` : `$${value.toFixed(3)}`
export const when = (iso: string | null | undefined) => {
  if (!iso) return ''
  const date = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}
export const percent = (value: number | null | undefined) => value == null ? '–' : `${Math.round(value * 100)}%`
export const statusLabel: Record<string, string> = { awaiting_review: 'Awaiting review', approved: 'Approved', failed: 'Failed' }
export const readinessLabel: Record<string, string> = { proven_pattern: 'Proven pattern', needs_feasibility_check: 'Needs feasibility check', unknown: 'Unknown' }
export const baselineLabel: Record<string, string> = { confirmed: 'Baseline confirmed', not_stated: 'No baseline stated', to_be_confirmed: 'Baseline to be confirmed' }
