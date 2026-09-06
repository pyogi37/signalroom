import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { AlertCircle, MessageSquare, RotateCcw } from 'lucide-react'
import type { Finding, Room } from '../types'
import { baselineLabel, label, readinessLabel, sentence } from '../format'
import { useGrammar } from '../motion'

type Props = {
  room: Room; selected: string | null; answers: Record<string, string>
  onAnswer: (id: string, value: string) => void; onSendAnswers: () => void; busy: boolean
}

const SECTION_OF: [RegExp, string][] = [
  [/^snapshot/, 'snapshot'], [/^readiness|^UC-/i, 'usecases'], [/^constraints/, 'constraints'], [/^recommendation/, 'recommendation'],
  [/^success/, 'measures'], [/^risks?/, 'risks'], [/^extraction|^transcript|^REQ-/i, 'evidence'], [/^OI-/i, 'items'],
]
function sectionFor(finding: Finding): string {
  for (const [pattern, section] of SECTION_OF) if (pattern.test(finding.location)) return section
  return 'general'
}

function Line({ room, line }: { room: Room; line: number | null | undefined }) {
  if (line == null) return null
  const utterance = room.utterances.find(item => item.line === line)
  return <abbr className="lref" title={utterance ? `L${line} ${utterance.speaker}: ${utterance.text}` : `Line ${line}`}>L{line}</abbr>
}

function Row({ g, children, kind = '', head = false }: { g?: ReactNode; children: ReactNode; kind?: string; head?: boolean }) {
  return <div className={`row ${kind} ${head ? 'head' : ''}`}><span className="g" aria-hidden={g == null}>{g ?? ''}</span><div className="c">{children}</div></div>
}

function Threads({ findings, room }: { findings: Finding[]; room: Room }) {
  const grammar = useGrammar()
  if (!findings.length) return null
  return <div className="threads">
    <AnimatePresence initial={false}>
      {findings.map((finding, index) => <motion.article className={`thread ${finding.severity}`} key={`${finding.kind}-${finding.location}-${index}`} {...grammar.arrive} aria-label={`${sentence(finding.kind)} finding`}>
        <div className="thread-head">
          <span className={`chip ${finding.source === 'code' ? 'code' : 'critic'}`}>{finding.source === 'code' ? 'code check' : 'critic'}</span>
          <strong>{sentence(finding.kind)}</strong>
          <span className={`sev ${finding.severity}`}>{finding.severity}</span>
        </div>
        <div className="thread-body">
          {finding.text}
          <small>{finding.location}{finding.lines.length ? <> · {finding.lines.map((line, i) => <span key={line}>{i ? ' ' : ''}<Line room={room} line={line}/></span>)}</> : null}</small>
        </div>
      </motion.article>)}
    </AnimatePresence>
  </div>
}

function Hunk({ id, title, count, flash, children }: { id: string; title: string; count?: string; flash: boolean; children: ReactNode }) {
  return <section className="hunk" aria-labelledby={`hunk-${id}`}>
    <div className={`hunk-head ${flash ? 'flash' : ''}`}><h2 id={`hunk-${id}`}><span className="mono">@@ {id}</span>{title}</h2>{count && <span>{count}</span>}</div>
    {children}
  </section>
}

export function Document({ room, selected, answers, onAnswer, onSendAnswers, busy }: Props) {
  const grammar = useGrammar()
  const [showTranscript, setShowTranscript] = useState(false)
  const previousRevision = useRef<number | null>(null)
  const [flash, setFlash] = useState(false)
  useEffect(() => {
    const revision = room.brief?.revision ?? null
    if (previousRevision.current !== null && revision !== previousRevision.current) { setFlash(true); const timer = setTimeout(() => setFlash(false), 1300); return () => clearTimeout(timer) }
    previousRevision.current = revision
  }, [room.brief?.revision])

  const requirement = room.requirements.find(item => item.id === selected)
  const useCase = room.use_cases.find(item => item.id === selected)
  const claim = requirement ?? useCase
  const brief = room.brief
  const readiness = new Map(brief?.readiness.map(item => [item.use_case_id, item]) ?? [])
  const bySection = useMemo(() => {
    const groups: Record<string, Finding[]> = {}
    const order = { high: 0, medium: 1, low: 2 }
    for (const finding of [...(room.critique?.findings ?? [])].sort((a, b) => order[a.severity] - order[b.severity])) (groups[sectionFor(finding)] ??= []).push(finding)
    return groups
  }, [room.critique])
  const openItems = room.open_items.filter(item => item.status === 'open')
  const answered = room.open_items.filter(item => item.status === 'answered')
  const pending = openItems.filter(item => answers[item.id]?.trim()).length
  const canReply = room.status === 'awaiting_review'

  return <article className="doc" aria-label="Brief under review">
    <div className="doc-title"><span><span className="mono">brief.md</span> · {room.organization}</span><span>{room.critique ? `${room.critique.findings.length} threads · ${sentence(room.critique.verdict)}` : 'no critique yet'}</span></div>

    <Hunk id="evidence" title="Selected change" flash={false}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div key={claim?.id ?? 'none'} className="rows" {...grammar.arrive}>
          {claim ? <>
            <Row g={<span className="mono">{claim.id}</span>} head>{requirement ? requirement.title : useCase!.name}<span className={`chip ${requirement ? (requirement.confidence === 'high' ? 'ok' : requirement.confidence === 'low' ? 'bad' : 'warn') : 'accent'}`}>{requirement ? `${requirement.confidence} confidence` : 'use case'}</span></Row>
            {requirement ? <Row kind="dim">{requirement.detail}</Row> : <><Row kind="dim"><span className="lab">Trigger</span>{useCase!.trigger_condition}</Row><Row kind="dim"><span className="lab">Expected output</span>{useCase!.expected_output}</Row></>}
            <Row g={<Line room={room} line={claim.evidence.line}/>} kind="add">“{claim.evidence.quote}”<span className="who">{claim.evidence.speaker} · verified verbatim against line {claim.evidence.line}</span></Row>
            {requirement && <Row kind="dim"><span className="lab">Why this confidence</span>{requirement.confidence_reason}</Row>}
          </> : <Row kind="dim">Select a claim on the left to see its verified line.</Row>}
        </motion.div>
      </AnimatePresence>
      <Threads findings={[...(bySection.evidence ?? []), ...(bySection.general ?? [])]} room={room}/>
    </Hunk>

    {brief && <>
      <Hunk id="snapshot" title="Snapshot" count={`revision ${brief.revision}`} flash={flash}>
        <div className="rows">
          <Row><span className="lab">Goal</span>{brief.snapshot.one_line_goal}</Row>
          <Row><span className="lab">Scope</span>{brief.snapshot.scope_summary}</Row>
          <Row><span className="lab">Deployment shape</span>{brief.snapshot.deployment_shape}</Row>
          <Row><span className="lab">Stakeholder roles</span>{brief.snapshot.stakeholder_roles.join(', ') || 'TBC'}</Row>
        </div>
        <Threads findings={bySection.snapshot ?? []} room={room}/>
      </Hunk>

      <Hunk id="usecases" title="Use cases and readiness" count={`${room.use_cases.length} established`} flash={flash}>
        {room.use_cases.length ? <div className="rows"><div className="row"><span className="g" aria-hidden="true"/><div className="c tbl-scroll"><table className="tbl">
          <thead><tr><th>Id</th><th>Use case</th><th>Trigger condition</th><th>Expected output</th><th>Readiness</th></tr></thead>
          <tbody>{room.use_cases.map(item => { const a = readiness.get(item.id); return <tr key={item.id}>
            <td className="mono">{item.id}</td><td>{item.name}</td><td>{item.trigger_condition}</td><td>{item.expected_output}</td>
            <td><span className={`chip ${a?.readiness === 'proven_pattern' ? 'ok' : a?.readiness === 'needs_feasibility_check' ? 'warn' : ''}`}>{readinessLabel[a?.readiness ?? 'unknown']}</span>{a?.note && <small>{a.note}{a.cited_passage_ids.length ? ` (${a.cited_passage_ids.join(', ')})` : ''}</small>}</td>
          </tr> })}</tbody>
        </table></div></div></div> : <div className="rows"><Row kind="dim">The conversation did not establish a concrete trigger. That is recorded, not invented.</Row></div>}
        <Threads findings={bySection.usecases ?? []} room={room}/>
      </Hunk>

      <Hunk id="constraints" title="Environment and constraints" count={`${brief.constraints.length}`} flash={flash}>
        <div className="rows">{brief.constraints.map((item, index) => <Row key={index} g={item.line ? <Line room={room} line={item.line}/> : <span className="mono">{item.source === 'pattern_library' ? 'ref' : 'assume'}</span>} kind={item.line ? '' : 'dim'}>{item.constraint}{item.passage_id && <span className="who">{item.passage_id}</span>}</Row>)}</div>
        <Threads findings={bySection.constraints ?? []} room={room}/>
      </Hunk>

      <Hunk id="recommendation" title="Recommended approach" count={`${brief.recommendation.phases.length} phases`} flash={flash}>
        <div className="rows">
          <Row>{brief.recommendation.approach}</Row>
          {brief.recommendation.phases.map((phase, index) => <Row key={phase.name} g={<span className="mono">{index + 1}</span>} head>{phase.name}<span className="chip">{phase.duration}</span><span className="who">{phase.purpose}</span>{phase.exit_criteria.length > 0 && <ul>{phase.exit_criteria.map(item => <li key={item}>{item}</li>)}</ul>}</Row>)}
          {brief.recommendation.discussed_not_in_scope.length > 0 && <Row kind="del"><span className="lab">Discussed, not in scope</span>{brief.recommendation.discussed_not_in_scope.join('; ')}</Row>}
        </div>
        <Threads findings={bySection.recommendation ?? []} room={room}/>
      </Hunk>

      <Hunk id="measures" title="Success measures" count={`${brief.success_measures.length}`} flash={flash}>
        <div className="rows">{brief.success_measures.map((item, index) => <Row key={index} g={item.line ? <Line room={room} line={item.line}/> : null}>{item.measure}<span className={`chip ${item.baseline_status === 'confirmed' ? 'ok' : item.baseline_status === 'not_stated' ? 'bad' : 'warn'}`}>{baselineLabel[item.baseline_status]}</span><span className="who">owner role: {item.owner_role}</span></Row>)}</div>
        <Threads findings={bySection.measures ?? []} room={room}/>
      </Hunk>

      <Hunk id="risks" title="Risks" count={`${brief.risks.length}`} flash={flash}>
        <div className="rows">{brief.risks.map(risk => <Row key={risk.title} g={<AlertCircle size={13} aria-hidden="true"/>} head>{risk.title}<span className={`chip ${risk.severity === 'high' ? 'bad' : risk.severity === 'medium' ? 'warn' : ''}`}>{risk.severity}</span><span className="who">{risk.mitigation} · basis: {risk.basis}</span></Row>)}</div>
        <Threads findings={bySection.risks ?? []} room={room}/>
      </Hunk>
    </>}

    <Hunk id="items" title="Open items" count={`${openItems.length} open · ${answered.length} answered`} flash={flash}>
      {openItems.map(item => <div className="item" key={item.id}>
        <span className="g">{item.id}</span>
        <div className="c">
          <strong>{item.question}</strong>
          <small>{item.why_it_matters} · owner role: {item.suggested_owner_role}{item.related_line ? <> · raised at <Line room={room} line={item.related_line}/></> : null}</small>
          {item.rejected_answers.length > 0 && <small className="rejected">Not a confirmed fact, kept open: “{item.rejected_answers[item.rejected_answers.length - 1]}”</small>}
          <label className="reply"><span className="sr-only">Answer to {item.id}</span><input placeholder={canReply ? 'Reply with a confirmed answer from the customer' : 'This room is no longer open for answers'} value={answers[item.id] || ''} onChange={event => onAnswer(item.id, event.target.value)} disabled={busy || !canReply}/></label>
        </div>
      </div>)}
      {openItems.length === 0 && <p className="empty">Every open item has a confirmed answer.</p>}
      {openItems.length > 0 && canReply && <div className="reply-bar">
        <motion.button className="btn" disabled={busy || pending === 0} onClick={onSendAnswers} whileTap={grammar.press}><RotateCcw size={14}/>{busy ? 'Re-running from extract' : pending ? `Add ${pending} answer${pending > 1 ? 's' : ''} and re-run` : 'Add an answer to re-run'}</motion.button>
        <span className="hint">Answers become new attributed lines. A vague answer cannot close an item.</span>
      </div>}
      {answered.map(item => <div className="item answered" key={item.id}><span className="g">{item.id}</span><div className="c"><strong>{item.question}</strong><p><MessageSquare size={12} aria-hidden="true" style={{ verticalAlign: '-2px', marginRight: 6 }}/>Answered at <Line room={room} line={item.answered_line}/>: {item.answer}</p></div></div>)}
      <Threads findings={bySection.items ?? []} room={room}/>
    </Hunk>

    {room.contradictions.length > 0 && <Hunk id="disputed" title="Contradictions left unresolved" count={`${room.contradictions.length}`} flash={false}>
      <div className="rows">{room.contradictions.map((item, index) => <Row key={index} g={<><Line room={room} line={item.line_a}/> <Line room={room} line={item.line_b}/></>}>{item.topic}<span className="who">{item.note}</span></Row>)}</div>
    </Hunk>}

    {room.retrieved.length > 0 && <Hunk id="refs" title="Reference passages retrieved" count={`${room.retrieved.length} · synthetic pattern library`} flash={false}>
      <div className="rows">{room.retrieved.map(hit => <Row key={hit.passage_id} g={<span className="mono">ref</span>} kind="dim"><b>{hit.title}</b> <span className="mono">{hit.passage_id}</span><br/>{hit.passage}<span className="who">{hit.source} · supports {hit.supports.join(', ')}</span></Row>)}</div>
    </Hunk>}

    <Hunk id="transcript" title="Transcript" count={`${room.utterances.length} lines`} flash={false}>
      <div className="rows">
        <Row kind="dim"><button className="link" onClick={() => setShowTranscript(value => !value)} aria-expanded={showTranscript}>{showTranscript ? 'Hide the transcript' : 'Show the full transcript'}</button></Row>
        <AnimatePresence initial={false}>{showTranscript && <motion.div {...grammar.expand} style={{ overflow: 'hidden' }}>
          {room.utterances.map(item => <Row key={item.line} g={<span className="mono">L{item.line}</span>} kind={item.origin === 'follow_up' ? 'add' : ''}><b>{item.speaker}</b> {item.text}</Row>)}
        </motion.div>}</AnimatePresence>
      </div>
    </Hunk>
  </article>
}

export { label }
