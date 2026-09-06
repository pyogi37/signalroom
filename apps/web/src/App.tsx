import { useCallback, useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { API, ApiError, api } from './api'
import type { Capabilities, AuditEvent, EvaluationSummary, Room, RoomSummary, TraceStep } from './types'
import { Composer } from './components/Composer'
import { DecisionPanel } from './components/DecisionPanel'
import { Docket } from './components/Docket'
import { Sidebar } from './components/Sidebar'
import { StageStrip } from './components/StageStrip'
import { percent, statusLabel } from './format'

type Notice = { tone: 'ok' | 'warn' | 'error'; text: string } | null
type Busy = 'loading' | 'running' | 'deciding' | null

function describeError(error: unknown): { tone: 'warn' | 'error'; text: string } {
  if (error instanceof ApiError) {
    if (error.unreachable) return { tone: 'error', text: `${error.detail} Start it with: cd apps/api && .venv\\Scripts\\uvicorn signalroom.main:app --port 8000` }
    if (error.noModel) return { tone: 'warn', text: `No model available. ${error.detail}` }
    if (error.providerFailed) return { tone: 'error', text: `The model provider failed. ${error.detail}` }
    return { tone: 'warn', text: error.detail }
  }
  return { tone: 'error', text: 'Something went wrong in the browser. Check the console.' }
}

function roomFromHash(): string | null {
  const match = window.location.hash.match(/room=([\w-]+)/)
  return match ? match[1] : null
}

export function App() {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null)
  const [rooms, setRooms] = useState<RoomSummary[]>([])
  const [room, setRoom] = useState<Room | null>(null)
  const [trace, setTrace] = useState<TraceStep[]>([])
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [evaluation, setEvaluation] = useState<EvaluationSummary | null>(null)
  const [selectedClaim, setSelectedClaim] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [composer, setComposer] = useState(false)
  const [busy, setBusy] = useState<Busy>('loading')
  const [banner, setBanner] = useState<Notice>(null)
  const [notice, setNotice] = useState<Notice>(null)
  const [retryDraft, setRetryDraft] = useState<{ organization: string; industry: string; transcript: string } | null>(null)

  const loadRoom = useCallback(async (id: string) => {
    const loaded = await api.room(id)
    setRoom(loaded)
    setSelectedClaim(loaded.requirements[0]?.id ?? loaded.use_cases[0]?.id ?? null)
    setAnswers({})
    window.location.hash = `room=${id}`
    api.trace(id).then(setTrace).catch(() => setTrace([]))
    api.audit(id).then(setAudit).catch(() => setAudit([]))
  }, [])

  const refreshRooms = useCallback(async () => {
    const list = await api.rooms()
    setRooms(list)
    return list
  }, [])

  useEffect(() => {
    (async () => {
      try {
        const [caps, list] = await Promise.all([api.capabilities(), refreshRooms()])
        setCapabilities(caps)
        api.evaluation().then(setEvaluation).catch(() => setEvaluation(null))
        const wanted = roomFromHash()
        const first = list.find(item => item.id === wanted) ?? list[0]
        if (first) await loadRoom(first.id)
        else if (!caps.live && caps.recordings === 0) setBanner({ tone: 'warn', text: 'No rooms, no recordings and no model key. Set GROQ_API_KEY in apps/api/.env to run a transcript, or run the evaluation suite in record mode to create replayable rooms.' })
        setBanner(current => current ?? null)
      } catch (error) {
        setBanner(describeError(error))
      } finally {
        setBusy(null)
      }
    })()
  }, [loadRoom, refreshRooms])

  async function createRoom(body: { organization: string; industry: string; transcript: string }, referenceFile: File | null) {
    setBusy('running'); setNotice(null); setBanner(null)
    try {
      if (referenceFile) {
        const indexed = await api.uploadKnowledge(referenceFile)
        setNotice({ tone: 'ok', text: `Indexed ${indexed.passages} passages from ${indexed.title} into the pattern library.` })
      }
      const created = await api.createRoom(body)
      await refreshRooms()
      await loadRoom(created.id)
      setComposer(false); setRetryDraft(null)
      setNotice({ tone: 'ok', text: `Workflow paused at the gate. ${created.grounding.passed} of ${created.grounding.proposed} proposed quotes passed the check.` })
    } catch (error) {
      const described = describeError(error)
      setRetryDraft(body)
      if (error instanceof ApiError && (error.noModel || error.providerFailed || error.unreachable)) { setComposer(false); setBanner(described) }
      else setNotice(described)
    } finally {
      setBusy(null)
    }
  }

  async function decide(body: Parameters<typeof api.decide>[1], success: string) {
    if (!room) return
    setBusy('deciding'); setNotice(null)
    try {
      const updated = await api.decide(room.id, body)
      setRoom(updated)
      setAnswers({})
      api.trace(room.id).then(setTrace).catch(() => undefined)
      api.audit(room.id).then(setAudit).catch(() => undefined)
      refreshRooms().catch(() => undefined)
      setNotice(updated.status === 'failed' ? { tone: 'error', text: `The re-run failed: ${updated.error}` } : { tone: 'ok', text: success })
    } catch (error) {
      setNotice(describeError(error))
    } finally {
      setBusy(null)
    }
  }

  async function loadRecordedRooms() {
    setBusy('loading'); setNotice(null); setBanner(null)
    try {
      const outcome = await api.seed()
      const list = await refreshRooms()
      if (list[0]) await loadRoom(list[0].id)
      if (!outcome.seeded.length) setBanner({ tone: 'warn', text: outcome.skipped.length ? `No recordings for ${outcome.skipped.join(', ')} yet. Run the evaluation suite in record mode to create them.` : 'Every bundled room is already open.' })
    } catch (error) {
      setBanner(describeError(error))
    } finally {
      setBusy(null)
    }
  }

  function sendAnswers() {
    if (!room) return
    const payload = room.open_items.filter(item => item.status === 'open' && answers[item.id]?.trim()).map(item => ({ open_item_id: item.id, answer: answers[item.id].trim() }))
    if (!payload.length) { setNotice({ tone: 'warn', text: 'Add at least one answer before re-running.' }); return }
    decide({ kind: 'follow_up', answers: payload, answered_by: 'Follow-up (solution engineer)' }, 'Answers added as new lines. Extraction, design and critique ran again.')
  }

  const running = busy === 'running'
  const completed = room?.stages.filter(stage => stage.status === 'complete').length ?? 0
  const modelLabel = !capabilities ? '…' : capabilities.live ? `Live · ${capabilities.model}` : capabilities.recordings ? `Replay · ${capabilities.recordings} recordings` : 'No model'

  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href="#" aria-label="SignalRoom home"><span className="brandmark" aria-hidden="true">S</span><span>SignalRoom</span></a>
      <div className="room-identity">{room ? <><strong>{room.organization}</strong><span>{statusLabel[room.status]} · synthetic</span></> : <span>Synthetic solutioning workbench</span>}</div>
      <div className="topbar-actions">
        <span className={`model-status ${capabilities?.live ? 'live' : 'replay'}`} title={capabilities ? `${capabilities.mode} mode via ${capabilities.provider_host}` : ''}><span aria-hidden="true"/>{modelLabel}</span>
        <button className="button button-secondary" onClick={() => setComposer(true)} disabled={busy === 'loading'}><Plus size={16}/> New room</button>
      </div>
    </header>

    {banner && <div className={`banner ${banner.tone}`} role="alert">
      <span>{banner.text}</span>
      {retryDraft && <button className="link-button" onClick={() => { setBanner(null); setComposer(true) }}>Edit and retry</button>}
      <button className="link-button" onClick={() => setBanner(null)} aria-label="Dismiss">Dismiss</button>
    </div>}

    <section className="review-header">
      <div className="review-heading">
        <p>{running ? 'Workflow running' : room?.status === 'approved' ? 'Decision recorded' : room ? 'Human review required' : busy === 'loading' ? 'Loading' : 'No room selected'}</p>
        <h1>{running ? 'Extracting, retrieving, drafting and critiquing…' : room ? (room.status === 'approved' ? `The brief for ${room.organization} is approved.` : `Review the brief for ${room.organization}.`) : busy === 'loading' ? 'Connecting to the API.' : 'Start a room from a synthetic transcript.'}</h1>
        <span>{room ? 'Every claim carries a quote that code verified against a numbered transcript line. The critic lists what it could not support. You decide.' : `API: ${API}`}</span>
      </div>
      <div className="workflow-summary" aria-label={room ? `${completed} of 6 stages complete` : undefined}>
        {room && <><div><span>{completed} of 6 stages complete</span><strong>{room.brief ? `brief r${room.brief.revision}` : ''}</strong></div>
        <div className="progress" aria-hidden="true"><i style={{ transform: `scaleX(${completed / 6})` }}/></div></>}
        {evaluation && <p className="eval-line">Latest eval: recall {percent(evaluation.summary.requirement_recall)} · traps {evaluation.summary.traps.passed}/{evaluation.summary.traps.total} · grounding {percent(evaluation.summary.grounding.pass_rate)} · {evaluation.mode}</p>}
      </div>
    </section>

    <StageStrip stages={room?.stages ?? []} running={running}/>

    <section className="workspace" aria-busy={busy !== null}>
      <Sidebar rooms={rooms} room={room} selectedClaim={selectedClaim} onSelectRoom={id => { setNotice(null); loadRoom(id).catch(error => setBanner(describeError(error))) }} onSelectClaim={setSelectedClaim} onNewRoom={() => setComposer(true)}/>
      {room ? <Docket room={room} selectedClaim={selectedClaim} answers={answers} onAnswer={(id, value) => setAnswers(current => ({ ...current, [id]: value }))} onSendAnswers={sendAnswers} busy={busy === 'deciding'}/>
        : <article className="evidence-docket empty-docket">{busy === 'loading' ? <p>Loading…</p> : <><h2>No room yet</h2><p>Open the bundled synthetic rooms from recorded model runs, or start a new one from a transcript. Without a model key, only recorded rooms can be opened.</p><div className="empty-actions"><button className="button button-primary" onClick={loadRecordedRooms}>Load recorded rooms</button><button className="button button-secondary" onClick={() => setComposer(true)}><Plus size={16}/> New room</button></div></>}</article>}
      {room ? <DecisionPanel room={room} audit={audit} trace={trace} busy={busy === 'deciding'} notice={notice}
        onApprove={() => decide({ kind: 'approve' }, 'Brief approved. The workflow reached its end and the decision is in the audit trail.')}
        onRequestChanges={note => decide({ kind: 'request_changes', note }, 'Changes requested. Design and critique ran again with your note.')}/>
        : <aside className="decision-panel"><p className="audit-note">Decisions appear here once a room is open.</p></aside>}
    </section>

    {composer && <Composer busy={running} onClose={() => setComposer(false)} onSubmit={createRoom} initial={retryDraft}/>}
  </main>
}
