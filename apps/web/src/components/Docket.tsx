import { useState } from 'react'
import { BookOpen, CircleAlert, Quote, RotateCcw } from 'lucide-react'
import type { Finding, Room } from '../types'
import { baselineLabel, label, readinessLabel, sentence } from '../format'

type Props = {
  room: Room
  selectedClaim: string | null
  answers: Record<string, string>
  onAnswer: (id: string, value: string) => void
  onSendAnswers: () => void
  busy: boolean
}

function Line({ room, line }: { room: Room; line: number | null }) {
  if (line == null) return null
  const utterance = room.utterances.find(item => item.line === line)
  return <abbr className="line-ref" title={utterance ? `${utterance.speaker}: ${utterance.text}` : `Line ${line}`}>L{line}</abbr>
}

function FindingRow({ finding, room }: { finding: Finding; room: Room }) {
  return <div className="finding">
    <CircleAlert size={16} aria-hidden="true"/>
    <div>
      <strong>{sentence(finding.kind)}<span className={`source-badge ${finding.source}`}>{finding.source === 'code' ? 'code check' : 'critic'}</span></strong>
      <p>{finding.text}</p>
      <small>{finding.location}{finding.lines.length ? <> · {finding.lines.map(line => <Line key={line} room={room} line={line}/>).reduce<React.ReactNode[]>((acc, node, index) => index ? [...acc, ' ', node] : [node], [])}</> : null}</small>
    </div>
    <span className={`severity ${finding.severity}`}>{finding.severity}</span>
  </div>
}

export function Docket({ room, selectedClaim, answers, onAnswer, onSendAnswers, busy }: Props) {
  const [showTranscript, setShowTranscript] = useState(false)
  const requirement = room.requirements.find(item => item.id === selectedClaim)
  const useCase = room.use_cases.find(item => item.id === selectedClaim)
  const claim = requirement ?? useCase
  const evidence = claim?.evidence
  const brief = room.brief
  const critique = room.critique
  const openItems = room.open_items.filter(item => item.status === 'open')
  const answered = room.open_items.filter(item => item.status === 'answered')
  const readiness = new Map(brief?.readiness.map(item => [item.use_case_id, item]) ?? [])
  const severityOrder = { high: 0, medium: 1, low: 2 }
  const findings = [...(critique?.findings ?? [])].sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])
  const pendingAnswers = openItems.filter(item => answers[item.id]?.trim()).length

  return <article className="evidence-docket">
    {claim ? <>
      <header className="docket-header">
        <div className="document-id">
          <span>{claim.id}</span>
          <span>{requirement ? label(requirement.kind) : 'use case'}</span>
          {requirement && <span>{requirement.confidence} confidence</span>}
        </div>
        <h2>{requirement ? requirement.title : useCase!.name}</h2>
        {requirement ? <p>{requirement.detail}</p> : <p><b>Trigger:</b> {useCase!.trigger_condition}<br/><b>Output:</b> {useCase!.expected_output}</p>}
        {requirement && <p className="confidence-reason">Why this confidence: {requirement.confidence_reason}</p>}
      </header>
      {evidence && <section className="source-evidence" aria-labelledby="source-evidence-title">
        <div className="section-title"><h3 id="source-evidence-title">Source evidence</h3><span><Quote size={14}/> Verified quote · <Line room={room} line={evidence.line}/></span></div>
        <blockquote>“{evidence.quote}”</blockquote>
        <p>{evidence.speaker}</p>
      </section>}
    </> : <header className="docket-header">
      <div className="document-id"><span>{room.id}</span><span>{room.industry || 'industry not stated'}</span></div>
      <h2>{room.organization}</h2>
      <p>{room.utterances.length} lines from {room.speakers.length} speakers. Select a claim on the left to see its evidence.</p>
    </header>}

    {brief && <>
      <section className="brief-section" aria-labelledby="snapshot-title">
        <div className="section-title"><h3 id="snapshot-title">Snapshot</h3><span>Brief revision {brief.revision}</span></div>
        <dl className="snapshot">
          <div><dt>Goal</dt><dd>{brief.snapshot.one_line_goal}</dd></div>
          <div><dt>Scope</dt><dd>{brief.snapshot.scope_summary}</dd></div>
          <div><dt>Deployment shape</dt><dd>{brief.snapshot.deployment_shape}</dd></div>
          <div><dt>Stakeholder roles</dt><dd>{brief.snapshot.stakeholder_roles.join(', ') || 'TBC'}</dd></div>
        </dl>
      </section>

      <section className="brief-section" aria-labelledby="use-cases-title">
        <div className="section-title"><h3 id="use-cases-title">Use cases and readiness</h3><span>{room.use_cases.length} established</span></div>
        {room.use_cases.length ? <div className="table-scroll"><table className="brief-table">
          <thead><tr><th>Id</th><th>Use case</th><th>Trigger condition</th><th>Expected output</th><th>Readiness</th></tr></thead>
          <tbody>{room.use_cases.map(item => {
            const assessment = readiness.get(item.id)
            return <tr key={item.id}>
              <td className="mono">{item.id}</td><td>{item.name}</td><td>{item.trigger_condition}</td><td>{item.expected_output}</td>
              <td><span className={`readiness ${assessment?.readiness ?? 'unknown'}`}>{readinessLabel[assessment?.readiness ?? 'unknown']}</span>{assessment?.note && <small>{assessment.note}{assessment.cited_passage_ids.length ? ` (${assessment.cited_passage_ids.join(', ')})` : ''}</small>}</td>
            </tr>
          })}</tbody>
        </table></div> : <p className="empty-state">The conversation did not establish a concrete trigger. That is recorded, not invented.</p>}
      </section>

      <div className="analysis-grid">
        <section className="recommendation" aria-labelledby="recommendation-title">
          <div className="section-title"><h3 id="recommendation-title">Recommended approach</h3><span>Model draft, reviewed by the critic</span></div>
          <p>{brief.recommendation.approach}</p>
          <ol className="phases">
            {brief.recommendation.phases.map((phase, index) => <li key={phase.name}>
              <span className="mono">{String(index + 1).padStart(2, '0')}</span>
              <div><strong>{phase.name}</strong><small>{phase.duration}</small><p>{phase.purpose}</p>{phase.exit_criteria.length > 0 && <ul>{phase.exit_criteria.map(item => <li key={item}>{item}</li>)}</ul>}</div>
            </li>)}
          </ol>
          {brief.recommendation.discussed_not_in_scope.length > 0 && <p className="not-in-scope"><b>Discussed, not in scope:</b> {brief.recommendation.discussed_not_in_scope.join('; ')}</p>}
        </section>
        <section className="constraints" aria-labelledby="constraints-title">
          <div className="section-title"><h3 id="constraints-title">Environment and constraints</h3><span>{brief.constraints.length}</span></div>
          <ul className="constraint-list">{brief.constraints.map((item, index) => <li key={index}>{item.constraint}<small>{label(item.source)}{item.line ? <> · <Line room={room} line={item.line}/></> : item.passage_id ? ` · ${item.passage_id}` : ''}</small></li>)}</ul>
          <div className="section-title"><h3>Success measures</h3><span>{brief.success_measures.length}</span></div>
          <ul className="constraint-list">{brief.success_measures.map((item, index) => <li key={index}>{item.measure}<small><span className={`baseline ${item.baseline_status}`}>{baselineLabel[item.baseline_status]}</span> · owner: {item.owner_role}{item.line ? <> · <Line room={room} line={item.line}/></> : null}</small></li>)}</ul>
        </section>
      </div>

      <div className="analysis-grid">
        <section className="critique" aria-labelledby="critique-title">
          <div className="section-title"><h3 id="critique-title">Critic pass</h3><span>{findings.length} findings · {critique ? sentence(critique.verdict) : ''}</span></div>
          {critique?.summary && <p className="critique-summary">{critique.summary}</p>}
          {findings.map((finding, index) => <FindingRow key={index} finding={finding} room={room}/>)}
          {findings.length === 0 && <p className="empty-state">No findings.</p>}
        </section>
        <section className="risks" aria-labelledby="risks-title">
          <div className="section-title"><h3 id="risks-title">Risks</h3><span>{brief.risks.length}</span></div>
          {brief.risks.map(risk => <div className="risk" key={risk.title}><CircleAlert size={16} aria-hidden="true"/><div><strong>{risk.title}</strong><p>{risk.mitigation}</p><small>Basis: {risk.basis}</small></div><span className={`severity ${risk.severity}`}>{risk.severity}</span></div>)}
        </section>
      </div>
    </>}

    <section className="questions" aria-labelledby="questions-title">
      <div className="section-title"><h3 id="questions-title">Open items</h3><span>{openItems.length} open · {answered.length} answered</span></div>
      {openItems.map(item => <label className="question" key={item.id}>
        <span className="mono">{item.id}</span>
        <span>
          <strong>{item.question}</strong>
          <small>{item.why_it_matters} · owner role: {item.suggested_owner_role}{item.related_line ? <> · raised at <Line room={room} line={item.related_line}/></> : null}</small>
          {item.rejected_answers.length > 0 && <small className="rejected">Not a confirmed fact, kept open: “{item.rejected_answers[item.rejected_answers.length - 1]}”</small>}
          <input aria-label={`Answer to ${item.id}: ${item.question}`} placeholder="Add a confirmed answer from the customer" value={answers[item.id] || ''} onChange={event => onAnswer(item.id, event.target.value)} disabled={busy || room.status !== 'awaiting_review'}/>
        </span>
      </label>)}
      {openItems.length === 0 && <p className="empty-state">Every open item has a confirmed answer.</p>}
      {openItems.length > 0 && room.status === 'awaiting_review' && <button className="button button-secondary rerun" disabled={busy || pendingAnswers === 0} onClick={onSendAnswers}><RotateCcw size={15}/>{busy ? 'Re-running from extract…' : pendingAnswers ? `Add ${pendingAnswers} answer${pendingAnswers > 1 ? 's' : ''} and re-run` : 'Add an answer to re-run'}</button>}
      {answered.length > 0 && <div className="answered-list">{answered.map(item => <p key={item.id}><span className="mono">{item.id}</span> <b>{item.question}</b> Answered at <Line room={room} line={item.answered_line}/>: {item.answer}</p>)}</div>}
    </section>

    {room.contradictions.length > 0 && <section className="brief-section" aria-labelledby="contradictions-title">
      <div className="section-title"><h3 id="contradictions-title">Contradictions left unresolved</h3><span>{room.contradictions.length}</span></div>
      <ul className="constraint-list">{room.contradictions.map((item, index) => <li key={index}>{item.topic}: {item.note}<small><Line room={room} line={item.line_a}/> vs <Line room={room} line={item.line_b}/></small></li>)}</ul>
    </section>}

    {room.retrieved.length > 0 && <section className="sources" aria-labelledby="sources-title">
      <div className="section-title"><h3 id="sources-title">Reference passages retrieved</h3><span>{room.retrieved.length} · synthetic pattern library</span></div>
      <div className="source-list">{room.retrieved.map(hit => <article key={hit.passage_id}><BookOpen size={16} aria-hidden="true"/><div><strong>{hit.title}</strong><span>{hit.passage_id} · {hit.source} · supports {hit.supports.join(', ')}</span><p>{hit.passage}</p></div></article>)}</div>
    </section>}

    <section className="transcript" aria-labelledby="transcript-title">
      <div className="section-title"><h3 id="transcript-title">Transcript</h3><button className="link-button" onClick={() => setShowTranscript(value => !value)} aria-expanded={showTranscript}>{showTranscript ? 'Hide' : `Show ${room.utterances.length} lines`}</button></div>
      {showTranscript && <ol className="transcript-lines">{room.utterances.map(item => <li key={item.line} className={item.origin}><span className="mono">L{item.line}</span><b>{item.speaker}</b><span>{item.text}</span></li>)}</ol>}
    </section>
  </article>
}
