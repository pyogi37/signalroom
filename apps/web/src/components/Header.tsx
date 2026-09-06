import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Check, ChevronDown, ChevronRight, GitPullRequest, Moon, Plus, Sun, X } from 'lucide-react'
import type { Capabilities, Room, RoomSummary, StageRecord } from '../types'
import type { Theme } from '../theme'
import { ms, statusLabel } from '../format'
import { useGrammar } from '../motion'

const ORDER = ['Discover', 'Extract', 'Retrieve', 'Design', 'Critique', 'Gate']

type TopbarProps = {
  room: Room | null; rooms: RoomSummary[]; capabilities: Capabilities | null; theme: Theme
  onToggleTheme: () => void; onSelectRoom: (id: string) => void; onNewRoom: () => void; disabled: boolean
}

export function Topbar({ room, rooms, capabilities, theme, onToggleTheme, onSelectRoom, onNewRoom, disabled }: TopbarProps) {
  const [open, setOpen] = useState(false)
  const menu = useRef<HTMLDivElement>(null)
  const grammar = useGrammar()
  useEffect(() => {
    if (!open) return
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === 'Escape' : !menu.current?.contains(event.target as Node)) setOpen(false)
    }
    window.addEventListener('mousedown', close); window.addEventListener('keydown', close)
    return () => { window.removeEventListener('mousedown', close); window.removeEventListener('keydown', close) }
  }, [open])
  const modelLabel = !capabilities ? '' : capabilities.live ? `live · ${capabilities.model}` : capabilities.recordings ? `replay · ${capabilities.recordings} recordings` : 'no model'

  return <header className="topbar">
    <a className="brand" href="#" aria-label="SignalRoom"><span className="brand-mark" aria-hidden="true">S</span>SignalRoom</a>
    <div className="crumbs">
      <span>Rooms</span><ChevronRight size={14} aria-hidden="true"/>
      <div className="room-menu" ref={menu}>
        <button className="btn btn-quiet" onClick={() => setOpen(value => !value)} aria-haspopup="listbox" aria-expanded={open} disabled={disabled}>
          <strong>{room ? room.organization : 'No room open'}</strong><ChevronDown size={14} aria-hidden="true"/>
        </button>
        <AnimatePresence>{open && <motion.div className="room-menu-list" role="listbox" aria-label="Open a room" {...grammar.arrive}>
          {rooms.map(item => <button role="option" aria-selected={room?.id === item.id} aria-current={room?.id === item.id ? 'true' : undefined} className="room-menu-item" key={item.id} onClick={() => { onSelectRoom(item.id); setOpen(false) }}>
            <strong>{item.organization}</strong>
            <span>{item.requirements} claims · {item.open_items} open · {item.industry || 'industry not stated'}</span>
            <span className={`chip ${item.status === 'approved' ? 'ok' : item.verdict === 'needs_changes' ? 'warn' : 'accent'}`}>{item.status === 'approved' ? 'Approved' : item.verdict === 'needs_changes' ? 'Needs changes' : 'Open'}</span>
          </button>)}
          {rooms.length === 0 && <p className="empty">No rooms yet.</p>}
        </motion.div>}</AnimatePresence>
      </div>
      {modelLabel && <span className="mono" title={capabilities ? `${capabilities.mode} mode via ${capabilities.provider_host}` : ''}>{modelLabel}</span>}
    </div>
    <div className="topbar-actions">
      <button className="icon-btn" onClick={onToggleTheme} aria-label={theme === 'night' ? 'Switch to day rendition' : 'Switch to night rendition'} title={theme === 'night' ? 'Day' : 'Night'}>
        {theme === 'night' ? <Sun size={16}/> : <Moon size={16}/>}
      </button>
      <motion.button className="btn btn-primary" onClick={onNewRoom} disabled={disabled} whileTap={grammar.press}><Plus size={15}/> New room</motion.button>
    </div>
  </header>
}

type RequestHeaderProps = { room: Room | null; running: boolean; loading: boolean; evalLine: string | null }

export function RequestHeader({ room, running, loading, evalLine }: RequestHeaderProps) {
  const grammar = useGrammar()
  const status = running ? 'running' : room?.status ?? 'none'
  const badge = running ? 'Running' : room ? (room.status === 'approved' ? 'Approved' : room.status === 'failed' ? 'Failed' : 'Open') : loading ? 'Connecting' : 'No room'
  const claims = room ? room.requirements.length + room.use_cases.length : 0
  const open = room ? room.open_items.filter(item => item.status === 'open').length : 0
  return <section className="request" aria-live="polite">
    <div className="request-status">
      <AnimatePresence mode="wait" initial={false}>
        <motion.span key={status} className={`status-badge ${status}`} {...grammar.arrive} transition={grammar.focal}>
          <GitPullRequest size={14} aria-hidden="true"/>{badge}
        </motion.span>
      </AnimatePresence>
      {room && <span className="request-meta">
        <b>{claims} grounded claims</b><span aria-hidden="true">·</span><b>{open} open items</b><span aria-hidden="true">·</span>
        <span>brief r{room.brief?.revision ?? 0}</span><span aria-hidden="true">·</span><span>{room.utterances.length} lines, {room.speakers.length} speakers</span><span aria-hidden="true">·</span><span>synthetic</span>
      </span>}
    </div>
    <h1>{running ? 'Running the workflow against the transcript.' : room ? (room.status === 'approved' ? `Approved: the brief for ${room.organization}.` : `Review the brief for ${room.organization}.`) : loading ? 'Connecting to the API.' : 'Open a recorded room or start one from a synthetic transcript.'}</h1>
    <p className="request-lede">{room ? 'Every claim carries a quote that code verified against a numbered transcript line. Threads under each section are what the critic and the code checks could not accept. You decide.' : 'Everything here is invented and labelled synthetic.'}</p>
    {evalLine && <p className="eval-line mono" title="Latest evaluation run over the synthetic fixtures">{evalLine}</p>}
    <Checks stages={room?.stages ?? []} running={running}/>
  </section>
}

function Checks({ stages, running }: { stages: StageRecord[]; running: boolean }) {
  const byName = new Map(stages.map(stage => [stage.name, stage]))
  return <ol className="checks" aria-label="Workflow checks">
    {ORDER.map((name, index) => {
      const stage = byName.get(name)
      const status = running ? (index === 0 ? 'active' : 'pending') : stage?.status ?? 'pending'
      return <li className={`check ${status}`} key={name} aria-current={status === 'active' ? 'step' : undefined}>
        <span className="check-icon" aria-hidden="true">{status === 'complete' ? <Check size={11}/> : status === 'failed' ? <X size={11}/> : status === 'active' ? <span className="pulse"/> : null}</span>
        <span>
          <strong>{name}</strong>
          <small>{running ? (index === 0 ? 'Running' : 'Queued') : stage ? `${stage.detail}${stage.latency_ms > 0 ? ` · ${ms(stage.latency_ms)}` : ''}` : 'Not run'}</small>
          <span className="sr-only">{status === 'complete' ? 'Complete' : status === 'active' ? 'Waiting' : status === 'failed' ? 'Failed' : 'Pending'}</span>
        </span>
      </li>
    })}
  </ol>
}

export { statusLabel }
