export type Evidence = { speaker: string; quote: string; timestamp: string }
export type Requirement = { id: string; title: string; detail: string; kind: 'functional' | 'constraint' | 'success'; confidence: 'high' | 'medium' | 'low'; evidence: Evidence }
export type SearchHit = { title: string; passage: string; score: number; source: string }
export type Session = {
  id: string; organization: string; status: 'processing' | 'review' | 'approved'; stage: string; progress: number
  requirements: Requirement[]; open_questions: string[]
  risks: { title: string; severity: 'high' | 'medium' | 'low'; mitigation: string }[]
  brief: { problem: string; recommendation: string; architecture: string[]; success: string[]; retrieval?: SearchHit[]; transcript?: string }
  stages: { name: string; status: string; detail: string }[]
}
