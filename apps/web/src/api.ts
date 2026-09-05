import type { AuditEvent, Capabilities, DecisionBody, EvaluationSummary, FixtureSummary, Room, RoomSummary, TraceStep } from './types'

export const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  detail: string
  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
  get unreachable() { return this.status === 0 }
  get noModel() { return this.status === 503 }
  get providerFailed() { return this.status === 502 }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API}${path}`, init)
  } catch {
    throw new ApiError(0, `The SignalRoom API is not reachable at ${API}.`)
  }
  if (!response.ok) {
    let detail = response.statusText || `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
      else if (Array.isArray(body?.detail)) detail = body.detail.map((item: { msg?: string }) => item.msg ?? JSON.stringify(item)).join('; ')
    } catch { /* keep status text */ }
    throw new ApiError(response.status, detail)
  }
  return response.json() as Promise<T>
}

const json = (body: unknown): RequestInit => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const api = {
  capabilities: () => request<Capabilities>('/api/capabilities'),
  rooms: () => request<RoomSummary[]>('/api/rooms'),
  room: (id: string) => request<Room>(`/api/rooms/${id}`),
  createRoom: (body: { organization: string; industry: string; transcript: string }) => request<Room>('/api/rooms', json(body)),
  decide: (id: string, body: DecisionBody) => request<Room>(`/api/rooms/${id}/decision`, json(body)),
  trace: (id: string) => request<TraceStep[]>(`/api/rooms/${id}/trace`),
  audit: (id: string) => request<AuditEvent[]>(`/api/rooms/${id}/audit`),
  fixtures: () => request<FixtureSummary[]>('/api/fixtures'),
  evaluation: () => request<EvaluationSummary>('/api/evaluation/latest'),
  uploadKnowledge: (file: File, title = '') => {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    return request<{ status: string; title: string; passages: number }>('/api/knowledge/upload', { method: 'POST', body: form })
  },
  exportUrl: (id: string) => `${API}/api/rooms/${id}/export.docx`,
}
