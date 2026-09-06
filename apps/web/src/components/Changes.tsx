import { useState } from 'react'
import { motion } from 'motion/react'
import type { Room } from '../types'
import { useGrammar } from '../motion'

type Props = { room: Room | null; selected: string | null; onSelect: (id: string) => void }

export function Changes({ room, selected, onSelect }: Props) {
  const [detail, setDetail] = useState(false)
  const grammar = useGrammar()
  if (!room) return <aside className="changes" aria-label="Changed claims"><div className="changes-head"><h2>Changed</h2><span>0</span></div><p className="empty">Claims appear here once a room is open.</p></aside>
  const g = room.grounding
  const groups = [
    { title: 'Requirements', items: room.requirements.map(item => ({ id: item.id, title: item.title, meta: `${item.kind.replaceAll('_', ' ')} · ${item.confidence}`, dot: item.confidence as string, line: item.evidence.line })) },
    { title: 'Use cases', items: room.use_cases.map(item => ({ id: item.id, title: item.name, meta: 'use case · grounded', dot: 'grounded', line: item.evidence.line })) },
  ]
  return <aside className="changes" aria-label="Changed claims">
    <div className="changes-head"><h2>Changed</h2><span>{room.requirements.length + room.use_cases.length} claims</span></div>
    {groups.map(group => group.items.length > 0 && <div className="changes-group" key={group.title}>
      <h3>{group.title}</h3>
      {group.items.map(item => <button className="change" key={item.id} onClick={() => onSelect(item.id)} aria-current={item.id === selected ? 'true' : undefined}>
        {item.id === selected && <motion.span className="change-marker" layoutId="change-marker" transition={grammar.layout} aria-hidden="true"/>}
        <span className="mono">{item.id}</span>
        <strong>{item.title}</strong>
        <small><i className={`dot ${item.dot}`} aria-hidden="true"/>{item.meta} · L{item.line}</small>
      </button>)}
    </div>)}
    {room.requirements.length + room.use_cases.length === 0 && <p className="empty">Nothing survived the quote check.</p>}
    <div className="quote-check">
      <h3>Quote check</h3>
      <dl className="kv">
        <dt>Proposed by the model</dt><dd>{g.proposed}</dd>
        <dt>Passed verbatim</dt><dd>{g.passed}</dd>
        <dt>Repaired to the right line</dt><dd>{g.repaired}</dd>
        <dt>Dropped</dt><dd>{g.dropped}</dd>
      </dl>
      {(g.drops.length > 0 || g.repairs.length > 0) && <button className="link" onClick={() => setDetail(value => !value)} aria-expanded={detail}>{detail ? 'Hide detail' : 'Show what changed'}</button>}
      {detail && <>
        {g.drops.map((drop, index) => <p key={`d${index}`}><b>Dropped</b> {drop.kind.replace('_', ' ')} “{drop.title}”: cited L{drop.proposed_line}, {drop.reason.replaceAll('_', ' ')}. Proposed quote: “{drop.proposed_quote}”</p>)}
        {g.repairs.map((repair, index) => <p key={`r${index}`}><b>Repaired</b> {repair.kind.replace('_', ' ')} “{repair.title}”: cited L{repair.proposed_line}, found on L{repair.actual_line}.</p>)}
      </>}
      {g.drops.length + g.repairs.length === 0 && <p>Every proposed quote was found on the line it cited.</p>}
    </div>
  </aside>
}
