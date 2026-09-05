import { useState } from 'react'
import { ChevronRight, Plus } from 'lucide-react'
import type { Room, RoomSummary } from '../types'
import { statusLabel } from '../format'

type Props = {
  rooms: RoomSummary[]
  room: Room | null
  selectedClaim: string | null
  onSelectRoom: (id: string) => void
  onSelectClaim: (id: string) => void
  onNewRoom: () => void
}

export function Sidebar({ rooms, room, selectedClaim, onSelectRoom, onSelectClaim, onNewRoom }: Props) {
  const [showRooms, setShowRooms] = useState(false)
  const [showGrounding, setShowGrounding] = useState(false)
  const claims = room ? [
    ...room.requirements.map(item => ({ id: item.id, title: item.title, kind: item.kind, confidence: item.confidence as string })),
    ...room.use_cases.map(item => ({ id: item.id, title: item.name, kind: 'use case', confidence: 'grounded' })),
  ] : []
  const grounding = room?.grounding

  return <aside className="requirements-panel" aria-label="Rooms and grounded claims">
    <div className="panel-heading">
      <h2>Rooms</h2>
      <button className="link-button" onClick={() => setShowRooms(value => !value)} aria-expanded={showRooms}>{showRooms ? 'Hide' : `${rooms.length} rooms`}</button>
    </div>
    {showRooms && <div className="room-list" role="list">
      {rooms.map(item => <button role="listitem" key={item.id} className={`room-row ${room?.id === item.id ? 'selected' : ''}`} onClick={() => { onSelectRoom(item.id); setShowRooms(false) }} aria-current={room?.id === item.id ? 'true' : undefined}>
        <strong>{item.organization}</strong>
        <span>{statusLabel[item.status]} · {item.requirements} req · {item.open_items} open{item.verdict === 'needs_changes' ? ' · needs changes' : ''}</span>
      </button>)}
      {rooms.length === 0 && <p className="empty-state">No rooms yet.</p>}
    </div>}

    <div className="panel-heading">
      <h2>Grounded claims</h2>
      <span>{claims.length}</span>
    </div>
    <div className="requirement-list">
      {claims.map(item => <button key={item.id} onClick={() => onSelectClaim(item.id)} className={`requirement-row ${item.id === selectedClaim ? 'selected' : ''}`} aria-current={item.id === selectedClaim ? 'true' : undefined}>
        <span className="requirement-meta"><b>{item.id}</b><span>{item.kind.replaceAll('_', ' ')}</span></span>
        <strong>{item.title}</strong>
        <span className="requirement-state"><i className={`confidence-dot ${item.confidence}`} aria-hidden="true"/>{item.confidence}<ChevronRight size={15}/></span>
      </button>)}
      {room && claims.length === 0 && <p className="empty-state">Nothing survived the quote check. See the grounding report below.</p>}
    </div>

    {grounding && <div className="grounding-summary">
      <div className="panel-heading compact"><h3>Quote check</h3><button className="link-button" onClick={() => setShowGrounding(value => !value)} aria-expanded={showGrounding}>{showGrounding ? 'Hide' : 'Details'}</button></div>
      <dl className="quality-checks">
        <div><dt>Proposed by the model</dt><dd>{grounding.proposed}</dd></div>
        <div><dt>Passed</dt><dd>{grounding.passed}</dd></div>
        <div><dt>Repaired to the right line</dt><dd>{grounding.repaired}</dd></div>
        <div><dt>Dropped</dt><dd>{grounding.dropped}</dd></div>
      </dl>
      {showGrounding && <div className="grounding-detail">
        {grounding.drops.map((drop, index) => <p key={`d${index}`}><b>Dropped</b> {drop.kind.replace('_', ' ')} “{drop.title}”: cited L{drop.proposed_line}, {drop.reason.replaceAll('_', ' ')}. Proposed quote: “{drop.proposed_quote}”</p>)}
        {grounding.repairs.map((repair, index) => <p key={`r${index}`}><b>Repaired</b> {repair.kind.replace('_', ' ')} “{repair.title}”: cited L{repair.proposed_line}, found on L{repair.actual_line}.</p>)}
        {grounding.drops.length + grounding.repairs.length === 0 && <p>Every proposed quote was found on the line it cited.</p>}
      </div>}
    </div>}

    <button className="continue-discovery" onClick={onNewRoom}><Plus size={17}/><span><strong>New room</strong><small>Paste a synthetic transcript</small></span></button>
  </aside>
}
