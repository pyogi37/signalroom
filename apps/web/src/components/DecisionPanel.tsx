import { useState } from 'react'
import { Activity, ArrowRight, Download, FileCheck2, ShieldCheck } from 'lucide-react'
import { api } from '../api'
import type { AuditEvent, Room, TraceStep } from '../types'
import { label, ms, sentence, tokens, usd, when } from '../format'

type Props = {
  room: Room
  audit: AuditEvent[]
  trace: TraceStep[]
  busy: boolean
  notice: { tone: 'ok' | 'warn' | 'error'; text: string } | null
  onApprove: () => void
  onRequestChanges: (note: string) => void
}

export function DecisionPanel({ room, audit, trace, busy, notice, onApprove, onRequestChanges }: Props) {
  const [note, setNote] = useState('')
  const [showTrace, setShowTrace] = useState(false)
  const awaiting = room.status === 'awaiting_review'
  const verdict = room.critique?.verdict
  const high = room.critique?.findings.filter(item => item.severity === 'high').length ?? 0
  const metrics = room.metrics

  return <aside className="decision-panel" aria-label="Review decision">
    <div className={`decision-state ${room.status}`}><FileCheck2 size={19} aria-hidden="true"/>{room.status === 'approved' ? 'Approved' : room.status === 'failed' ? 'Failed' : 'Awaiting reviewer'}</div>
    <h2>{room.status === 'approved' ? 'Brief approved' : room.status === 'failed' ? 'The workflow stopped' : 'Make the call'}</h2>
    {room.status === 'failed' && <p className="error-text">{room.error}</p>}
    {awaiting && <p>{verdict === 'needs_changes' ? `The critic found ${high} high-severity issue${high === 1 ? '' : 's'}. Send it back with a note, or answer open items and re-run.` : 'The critic did not block this brief. Approve it, send it back with a note, or answer open items and re-run.'}</p>}
    {room.status === 'approved' && <p>Reviewer, timestamp and brief revision are recorded in the audit trail below.</p>}

    {awaiting && <div className="decision-actions">
      <button className="button button-primary" onClick={onApprove} disabled={busy}>Approve brief <ArrowRight size={16}/></button>
      <label className="note-field">Note for a change request
        <textarea value={note} onChange={event => setNote(event.target.value)} rows={3} placeholder="Say what should change. The design stage revises with this note." disabled={busy}/>
      </label>
      <button className="button button-secondary" onClick={() => { onRequestChanges(note.trim()); setNote('') }} disabled={busy || !note.trim()}>Request changes</button>
    </div>}
    <a className="button button-secondary export" href={api.exportUrl(room.id)}><Download size={15}/> Export brief (DOCX)</a>
    {notice && <div className={`notice ${notice.tone}`} role="status">{notice.text}</div>}

    <dl className="quality-checks">
      <div><dt>Model calls</dt><dd>{metrics.calls.length} · {metrics.modes.join(', ') || '–'}</dd></div>
      <div><dt>Latency, all calls</dt><dd>{ms(metrics.total_latency_ms)}</dd></div>
      <div><dt>Tokens in / out</dt><dd>{tokens(metrics.total_input_tokens)} / {tokens(metrics.total_output_tokens)}</dd></div>
      <div><dt>Estimated cost</dt><dd>{usd(metrics.total_cost_usd)}</dd></div>
      <div><dt>Model</dt><dd className="wrap">{metrics.calls[0]?.model ?? '–'}</dd></div>
    </dl>

    {room.decisions.length > 0 && <div className="audit-list">
      <h3><ShieldCheck size={14} aria-hidden="true"/> Decisions</h3>
      {room.decisions.map((decision, index) => <div key={index}><strong>{sentence(decision.kind)}</strong><span>{when(decision.decided_at)}{decision.note ? ` · ${decision.note}` : ''}</span></div>)}
    </div>}

    {audit.length > 0 && <div className="audit-list">
      <h3><Activity size={14} aria-hidden="true"/> Audit trail</h3>
      {audit.slice(-6).map(event => <div key={event.id}><strong>{label(event.event)}</strong><span>{event.actor} · {when(event.created_at)}</span></div>)}
    </div>}

    <div className="audit-list">
      <h3>Workflow trace <button className="link-button" onClick={() => setShowTrace(value => !value)} aria-expanded={showTrace}>{showTrace ? 'Hide' : `${trace.length} checkpoints`}</button></h3>
      {showTrace && trace.map((step, index) => <div key={index}>
        <strong>{step.ran.length ? step.ran.map(label).join(', ') : 'start'}{step.interrupted ? ' · paused at the gate' : ''}</strong>
        <span>next: {step.next.length ? step.next.join(', ') : 'end'} · req {step.counts.requirements} · open {step.counts.open_items} · findings {step.counts.findings}{step.counts.brief_revision ? ` · brief r${step.counts.brief_revision}` : ''}</span>
      </div>)}
    </div>
    <p className="audit-note"><ShieldCheck size={14} aria-hidden="true"/> Approval is a real interrupt in the workflow. Nothing here is a customer result; every room is synthetic.</p>
  </aside>
}
