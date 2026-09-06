import { useCallback, useEffect, useState } from 'react'
import { AnimatePresence, LayoutGroup } from 'motion/react'
import { Plus } from 'lucide-react'
import { API, ApiError, api } from './api'
import type { AuditEvent, Capabilities, EvaluationSummary, Room, RoomSummary, TraceStep } from './types'
import { Changes } from './components/Changes'
import { Composer } from './components/Composer'
import { Document } from './components/Document'
import { RequestHeader, Topbar } from './components/Header'
import { ReviewPanel } from './components/ReviewPanel'
import { percent } from './format'
import { useTheme } from './theme'

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
  const [theme, toggleTheme] = useTheme()
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null)
  const [rooms, setRooms] = useState<RoomSummary[]>([])
  const [room, setRoom] = useState<Room | null>(null)
  const [trace, setTrace] = useState<TraceStep[]>([])
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [evaluation, setEvaluation] = useState<EvaluationSummary | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [composer, setComposer] = useState(false)
  const [busy, setBusy] = useState<Busy>('loading')
  const [banner, setBanner] = useState<Notice>(null)
  const [notice, setNotice] = useState<Notice>(null)
  const [retryDraft, setRetryDraft] = useState<{ organization: string; industry: string; transcript: string } | null>(null)

  const loadRoom = useCallback(async (id: string) => {
    const loaded = await api.room(id)
    setRoom(loaded)
    setSelected(loaded.requirements[0]?.id ?? loaded.use_cases[0]?.id ?? null)
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
        else if (!caps.live && caps.recordings === 0) setBanner({ tone: 'warn', text: 'No rooms, no recordings and no model key. Set a key in apps/api/.env to run a transcript, or run the evaluation suite in record mode to create replayable rooms.' })
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
      setNotice({ tone: 'ok', text: `Paused at the gate. ${created.grounding.passed} of ${created.grounding.proposed} proposed quotes passed the verbatim check.` })
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

  const pendingAnswers = room ? room.open_items.filter(item => item.status === 'open' && answers[item.id]?.trim()).length : 0
  function sendAnswers() {
    if (!room) return
    const payload = room.open_items.filter(item => item.status === 'open' && answers[item.id]?.trim()).map(item => ({ open_item_id: item.id, answer: answers[item.id].trim() }))
    if (!payload.length) { setNotice({ tone: 'warn', text: 'Add at least one answer before re-running.' }); return }
    decide({ kind: 'follow_up', answers: payload, answered_by: 'Follow-up (solution engineer)' }, 'Answers added as new lines. Extraction, design and critique ran again.')
  }

  const running = busy === 'running'
  const evalLine = evaluation ? `eval: recall ${percent(evaluation.summary.requirement_recall)} · traps ${evaluation.summary.traps.passed}/${evaluation.summary.traps.total} · quotes ${percent(evaluation.summary.grounding.pass_rate)} · ${evaluation.mode}` : null

  return <LayoutGroup>
    <main className="shell">
      <Topbar room={room} rooms={rooms} capabilities={capabilities} theme={theme} onToggleTheme={toggleTheme} disabled={busy === 'loading'}
        onSelectRoom={id => { setNotice(null); loadRoom(id).catch(error => setBanner(describeError(error))) }} onNewRoom={() => setComposer(true)}/>

      {banner && <div className={`banner ${banner.tone}`} role="alert">
        <span>{banner.text}</span>
        {retryDraft && <button className="link" onClick={() => { setBanner(null); setComposer(true) }}>Edit and retry</button>}
        <button className="link" onClick={() => setBanner(null)} aria-label="Dismiss">Dismiss</button>
      </div>}

      <RequestHeader room={room} running={running} loading={busy === 'loading'} evalLine={evalLine}/>

      {room && !running ? <section className="workspace" aria-busy={busy !== null}>
        <Changes room={room} selected={selected} onSelect={setSelected}/>
        <Document room={room} selected={selected} answers={answers} onAnswer={(id, value) => setAnswers(current => ({ ...current, [id]: value }))} onSendAnswers={sendAnswers} busy={busy === 'deciding'}/>
        <ReviewPanel room={room} audit={audit} trace={trace} busy={busy === 'deciding'} notice={notice} pendingAnswers={pendingAnswers}
          onApprove={() => decide({ kind: 'approve' }, 'Approved. The workflow reached its end and the decision is in the timeline.')}
          onRequestChanges={note => decide({ kind: 'request_changes', note }, 'Changes requested. Design and critique ran again with your note.')}
          onSendAnswers={sendAnswers}/>
      </section> : <section className="workspace" style={{ gridTemplateColumns: '1fr' }}>
        <article className="doc">
          {running ? <div className="running-doc" aria-live="polite"><p className="hint">Three model calls, one gate. Twenty seconds to two minutes depending on the provider route.</p><span className="skeleton" style={{ width: '62%' }}/><span className="skeleton" style={{ width: '88%' }}/><span className="skeleton" style={{ width: '74%' }}/><span className="skeleton" style={{ width: '81%' }}/></div>
            : <div className="empty-doc">{busy === 'loading' ? <p>Loading</p> : <><h2>No room open</h2><p>Open the bundled synthetic rooms from recorded model runs, or start a new one from a transcript. Without a model key, only recorded rooms can be opened.</p><div className="empty-actions"><button className="btn btn-primary" onClick={loadRecordedRooms}>Load recorded rooms</button><button className="btn" onClick={() => setComposer(true)}><Plus size={15}/> New room</button></div><p className="hint">API: {API}</p></>}</div>}
        </article>
      </section>}

      <AnimatePresence>{composer && <Composer key="composer" busy={running} onClose={() => setComposer(false)} onSubmit={createRoom} initial={retryDraft}/>}</AnimatePresence>
    </main>
  </LayoutGroup>
}
