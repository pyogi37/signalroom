import type { Session } from './types'

export const demo: Session = {
  id: 'northstar-discovery', organization: 'Northstar Cold Chain', status: 'review', stage: 'approval', progress: 86,
  requirements: [
    { id: 'REQ-01', title: 'Detect loading-bay temperature excursions', detail: 'Notify an operations lead when a monitored loading bay remains outside its configured range.', kind: 'functional', confidence: 'high', evidence: { speaker: 'Operations lead', quote: 'We usually discover an excursion when the shift report is already being written.', timestamp: '04:18' } },
    { id: 'REQ-02', title: 'Use existing sensor infrastructure', detail: 'The PoC must read from the existing telemetry gateway rather than replace installed sensors.', kind: 'constraint', confidence: 'high', evidence: { speaker: 'IT architect', quote: 'The gateway is staying. Anything new has to consume its API.', timestamp: '08:42' } },
    { id: 'REQ-03', title: 'Reduce investigation time', detail: 'Demonstrate a material reduction in time spent assembling the event timeline.', kind: 'success', confidence: 'medium', evidence: { speaker: 'Operations lead', quote: 'A supervisor can lose most of an hour piecing together one event.', timestamp: '12:06' } },
  ],
  open_questions: ['What API authentication method does the existing gateway support?', 'Who is authorized to acknowledge or close an excursion?', 'What baseline will be used for the PoC investigation-time metric?'],
  risks: [
    { title: 'Alert fatigue', severity: 'high', mitigation: 'Calibrate duration thresholds on historical telemetry before live notifications.' },
    { title: 'Gateway rate limits unknown', severity: 'medium', mitigation: 'Confirm API envelope before finalizing polling and backfill design.' },
  ],
  brief: {
    problem: 'Excursions are identified late and investigations require manual correlation across telemetry and shift records.',
    recommendation: 'Run a six-week, two-site PoC with read-only telemetry ingestion, event correlation, an evidence timeline, and supervisor review.',
    architecture: ['Telemetry adapter', 'Event normalizer', 'Evidence store', 'Investigation agent', 'Review workspace'],
    success: ['Detection latency measured', 'Investigation time compared with baseline', 'Every alert retains source evidence'],
  },
  stages: [
    { name: 'Discover', status: 'complete', detail: '14 evidence statements captured' }, { name: 'Structure', status: 'complete', detail: '3 requirements, 3 open questions' },
    { name: 'Retrieve', status: 'complete', detail: '4 synthetic reference passages' }, { name: 'Design', status: 'complete', detail: 'PoC architecture proposed' },
    { name: 'Critique', status: 'complete', detail: '2 risks, no unsupported numbers' }, { name: 'Approve', status: 'active', detail: 'Waiting for solution engineer' },
  ],
}

