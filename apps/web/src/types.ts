export type Utterance = { line: number; speaker: string; text: string; origin: 'transcript' | 'follow_up' }
export type Evidence = { line: number; speaker: string; quote: string }
export type Confidence = 'high' | 'medium' | 'low'
export type Severity = 'high' | 'medium' | 'low'

export type Requirement = {
  id: string; title: string; detail: string
  kind: 'functional' | 'constraint' | 'success_measure'
  confidence: Confidence; confidence_reason: string; evidence: Evidence
}
export type UseCase = { id: string; name: string; trigger_condition: string; expected_output: string; evidence: Evidence }
export type OpenItem = {
  id: string; question: string; why_it_matters: string; suggested_owner_role: string; related_line: number | null
  status: 'open' | 'answered'; answer: string | null; answered_line: number | null; rejected_answers: string[]
}
export type Contradiction = { topic: string; line_a: number; line_b: number; note: string }
export type GroundingDrop = { kind: 'requirement' | 'use_case'; title: string; reason: string; proposed_line: number; proposed_quote: string }
export type GroundingRepair = { kind: 'requirement' | 'use_case'; title: string; proposed_line: number; actual_line: number }
export type GroundingReport = { proposed: number; passed: number; repaired: number; dropped: number; drops: GroundingDrop[]; repairs: GroundingRepair[] }
export type SearchHit = { passage_id: string; title: string; passage: string; score: number; source: string; shared_terms: number; supports: string[] }

export type Readiness = 'proven_pattern' | 'needs_feasibility_check' | 'unknown'
export type Brief = {
  snapshot: { one_line_goal: string; scope_summary: string; deployment_shape: string; stakeholder_roles: string[] }
  readiness: { use_case_id: string; readiness: Readiness; note: string; cited_passage_ids: string[] }[]
  constraints: { constraint: string; source: 'transcript' | 'pattern_library' | 'assumption'; line: number | null; passage_id: string | null }[]
  recommendation: { approach: string; phases: { name: string; purpose: string; duration: string; exit_criteria: string[] }[]; discussed_not_in_scope: string[] }
  success_measures: { measure: string; baseline_status: 'confirmed' | 'not_stated' | 'to_be_confirmed'; owner_role: string; line: number | null }[]
  risks: { title: string; severity: Severity; mitigation: string; basis: string }[]
  revision: number
}
export type FindingKind = 'unsupported_claim' | 'contradiction' | 'missing_owner' | 'scope_creep' | 'overclaim' | 'unverified_number' | 'dropped_evidence' | 'invalid_citation'
export type Finding = { kind: FindingKind; severity: Severity; text: string; location: string; lines: number[]; source: 'model' | 'code' }
export type Critique = { findings: Finding[]; verdict: 'ready_for_review' | 'needs_changes'; summary: string }

export type StageRecord = { name: string; status: 'complete' | 'active' | 'failed' | 'pending'; detail: string; latency_ms: number }
export type StageMetric = { stage: string; mode: string; model: string; latency_ms: number; input_tokens: number; output_tokens: number; estimated_cost_usd: number | null }
export type Metrics = { calls: StageMetric[]; total_latency_ms: number; total_input_tokens: number; total_output_tokens: number; total_cost_usd: number | null; modes: string[] }
export type Decision = { kind: 'approve' | 'request_changes' | 'follow_up'; note: string; decided_at: string }

export type RoomStatus = 'awaiting_review' | 'approved' | 'failed'
export type Room = {
  id: string; organization: string; industry: string; status: RoomStatus; created_at: string; updated_at: string
  transcript: string; utterances: Utterance[]; speakers: { speaker: string; lines: number }[]
  requirements: Requirement[]; use_cases: UseCase[]; open_items: OpenItem[]; contradictions: Contradiction[]
  grounding: GroundingReport; retrieved: SearchHit[]; brief: Brief | null; critique: Critique | null
  stages: StageRecord[]; metrics: Metrics; review_note: string | null; decisions: Decision[]
  error: string | null; synthetic: boolean; fixture: string | null
}
export type RoomSummary = {
  id: string; organization: string; industry: string; status: RoomStatus; fixture: string | null
  created_at: string; updated_at: string; requirements: number; open_items: number; findings: number
  verdict: 'ready_for_review' | 'needs_changes' | null; modes: string[]
}
export type Capabilities = { mode: string; live: boolean; model: string; provider_host: string; recordings: number; synthetic_only: boolean }
export type TraceStep = {
  step: number | null; ran: string[]; next: string[]; interrupted: boolean; created_at: string | null; status: string | null
  counts: { utterances: number; requirements: number; open_items: number; retrieved: number; findings: number; brief_revision: number | null }
}
export type AuditEvent = { id: number; event: string; actor: string; detail: unknown; created_at: string }
export type FixtureSummary = { id: string; organization: string; industry: string; transcript: string; lines: number; seeded: boolean }
export type EvaluationSummary = {
  run_at: string; mode: string; model: string; provider_host: string; floor_breaches: string[]
  summary: {
    fixtures: number; completed: number; requirement_recall: number | null; requirement_precision: number | null; open_item_recall: number | null
    traps: { passed: number; total: number; by_type: Record<string, { passed: number; total: number }> }
    grounding: { proposed: number; passed: number; repaired: number; dropped: number; pass_rate: number | null }
    latency_ms: { mean: number | null; max: number | null }; tokens: { input: number; output: number }; cost_usd: number | null
  }
}
export type DecisionBody = { kind: 'approve' } | { kind: 'request_changes'; note: string } | { kind: 'follow_up'; answers: { open_item_id: string; answer: string }[]; answered_by?: string }
