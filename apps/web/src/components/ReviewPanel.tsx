import { useState } from 'react'
import { motion } from 'motion/react'
import { AlertTriangle, CheckCircle2, Download, ShieldCheck, XCircle } from 'lucide-react'
import { api } from '../api'
import type { AuditEvent, Room, TraceStep } from '../types'
import { label, ms, sentence, tokens, usd, when } from '../format'
import { useGrammar } from '../motion'

type Choice = 'approve' | 'request_changes' | 'comment'
type Props = {
  room: Room; audit: AuditEvent[]; trace: TraceStep[]; busy: boolean
  notice: { tone: 'ok' | 'warn' | 'error'; text: string } | null
  pendingAnswers: number
  onApprove: () => void; onRequestChanges: (note: string) => void; onSendAnswers: () => void
}

export function ReviewPanel({ room, audit, trace, busy, notice, pendingAnswers, onApprove, onRequestChanges, onSendAnswers }: Props) {
  const grammar = useGrammar()
  const high = room.critique?.findings.filter(item => item.severity === 'high').length ?? 0
  const needsChanges = room.critique?.verdict === 'needs_changes'
  const [choice, setChoice] = useState<Choice>(needsChanges ? 'request_changes' : 'approve')
  const [note, setNote] = useState('')
  const [showTrace, setShowTrace] = useState(false)
  const awaiting = room.status === 'awaiting_review'
  const metrics = room.metrics

  function submit() {
    if (choice === 'approve') onApprove()
    else if (choice === 'request_changes') { onRequestChanges(note.trim()); setNote('') }
    else onSendAnswers()
  }
  const submitLabel = choice === 'approve' ? 'Approve brief' : choice === 'request_changes' ? 'Request changes' : pendingAnswers ? `Add ${pendingAnswers} answer${pendingAnswers > 1 ? 's' : ''} and re-run` : 'Add an answer first'
  const submitDisabled = busy || (choice === 'request_changes' && !note.trim()) || (choice === 'comment' && pendingAnswers === 0)

  return <aside className="review" aria-label="Review">
    <section className="panel">
      <div className="panel-head">Submit review<span>{awaiting ? 'waiting on you' : room.status === 'approved' ? 'closed' : 'stopped'}</span></div>
      <div className="panel-body">
        {room.status === 'approved' && <div className="verdict approved"><CheckCircle2 size={18}/><span>Approved. Reviewer, timestamp and brief revision are in the timeline.</span></div>}
        {room.status === 'failed' && <div className="verdict bad"><XCircle size={18}/><span>The workflow stopped: {room.error}</span></div>}
        {awaiting && <div className={`verdict ${needsChanges ? 'warn' : 'ok'}`}>
          {needsChanges ? <AlertTriangle size={18}/> : <CheckCircle2 size={18}/>}
          <span>{needsChanges ? `The critic found ${high} high-severity issue${high === 1 ? '' : 's'}. ${room.critique?.summary ?? ''}` : `The critic did not block this brief. ${room.critique?.summary ?? ''}`}</span>
        </div>}
        {awaiting && <>
          <div className="choices" role="radiogroup" aria-label="Decision">
            {([['approve', 'Approve', 'Ends the workflow. The decision is recorded.'], ['request_changes', 'Request changes', 'Design and critique run again with your note.'], ['comment', 'Answer open items', 'Answers become new transcript lines; extraction runs again.']] as const).map(([value, title, text]) => <label className="choice" key={value} data-on={choice === value}>
              <input type="radio" name="decision" value={value} checked={choice === value} onChange={() => setChoice(value)} disabled={busy}/>
              <strong>{title}</strong><small>{text}</small>
              {value === 'request_changes' && choice === value && <textarea rows={3} value={note} onChange={event => setNote(event.target.value)} placeholder="Say what should change." disabled={busy} aria-label="Change request note"/>}
            </label>)}
          </div>
          <motion.button className="btn btn-primary btn-block submit" onClick={submit} disabled={submitDisabled} whileTap={grammar.press}>{busy ? 'Working' : submitLabel}</motion.button>
        </>}
        <a className="btn btn-block" style={{ marginTop: 8 }} href={api.exportUrl(room.id)}><Download size={14}/> Export brief as DOCX</a>
        {notice && <div className={`notice ${notice.tone}`} role="status">{notice.text}</div>}
      </div>
    </section>

    <section className="panel">
      <div className="panel-head">Checks<span>{metrics.modes.join(', ') || 'no calls'}</span></div>
      <div className="panel-body">
        <dl className="kv">
          <div><dt>Model calls</dt><dd>{metrics.calls.length}</dd></div>
          <div><dt>Latency, all calls</dt><dd>{ms(metrics.total_latency_ms)}</dd></div>
          <div><dt>Tokens in / out</dt><dd>{tokens(metrics.total_input_tokens)} / {tokens(metrics.total_output_tokens)}</dd></div>
          <div><dt>Estimated cost</dt><dd>{usd(metrics.total_cost_usd)}</dd></div>
          <div><dt>Model</dt><dd className="wrap">{metrics.calls[0]?.model ?? 'none'}</dd></div>
        </dl>
      </div>
    </section>

    <section className="panel">
      <div className="panel-head">Timeline<span>{audit.length} events</span></div>
      <div className="panel-body timeline">
        {audit.slice(-8).map(event => <div className={`tl ${event.actor !== 'system' ? 'human' : ''} ${event.event === 'brief_approved' ? 'approve' : ''}`} key={event.id}><i aria-hidden="true"/><div><strong>{sentence(event.event)}</strong><span>{event.actor} · {when(event.created_at)}</span></div></div>)}
        {audit.length === 0 && <span className="hint">No events yet.</span>}
        <button className="link" style={{ marginTop: 8 }} onClick={() => setShowTrace(value => !value)} aria-expanded={showTrace}>{showTrace ? 'Hide the graph trace' : `Show the graph trace (${trace.length} checkpoints)`}</button>
        {showTrace && trace.map((step, index) => <div className="trace-step" key={index}><strong>{step.ran.length ? step.ran.map(label).join(', ') : 'start'}{step.interrupted ? ' · paused at gate' : ''}</strong><span>next {step.next.length ? step.next.join(', ') : 'end'} · req {step.counts.requirements} · open {step.counts.open_items} · findings {step.counts.findings}{step.counts.brief_revision ? ` · r${step.counts.brief_revision}` : ''}</span></div>)}
      </div>
    </section>

    <p className="footnote"><ShieldCheck size={14}/>Approval is an interrupt in the workflow, not a status flag. Every room is synthetic.</p>
  </aside>
}
