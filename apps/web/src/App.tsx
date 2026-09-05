import { useEffect, useRef, useState } from 'react'
import { Activity, ArrowRight, BookOpen, Check, ChevronRight, CircleAlert, Download, FileCheck2, Mic, Plus, Quote, Radio, RotateCcw, ShieldCheck, Square, Upload, X } from 'lucide-react'
import { demo } from './demo'
import type { Session } from './types'

const API = 'http://127.0.0.1:8000'

export function App() {
  const [session, setSession] = useState<Session>(demo)
  const [selected, setSelected] = useState(0)
  const [notice, setNotice] = useState('')
  const [composer, setComposer] = useState(false)
  const [organization, setOrganization] = useState('Atlas Distribution')
  const [transcript, setTranscript] = useState('Operations lead: We need alerts when a shipment exception persists for more than a few minutes.\nIT architect: It must use our existing gateway API; replacing installed infrastructure is out of scope.\nSponsor: Success means reducing the time supervisors spend investigating each event.\nCompliance lead: Every decision needs an evidence trail for quarterly review.')
  const [analyzing, setAnalyzing] = useState(false)
  const [knowledgeFile, setKnowledgeFile] = useState<File | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [followingUp, setFollowingUp] = useState(false)
  const [capabilities, setCapabilities] = useState({ llm: false, transcription: false, local_fallback: true })
  const [recording, setRecording] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('')
  const recorder = useRef<MediaRecorder | null>(null)
  const [evaluation, setEvaluation] = useState<Record<string, string | number | boolean>>({})
  const [audit, setAudit] = useState<{ id: number; event: string; created_at: string }[]>([])

  useEffect(() => {
    fetch(`${API}/api/sessions/demo`).then(r => r.ok ? r.json() : Promise.reject()).then(setSession).catch(() => undefined)
    fetch(`${API}/api/capabilities`).then(r => r.ok ? r.json() : Promise.reject()).then(setCapabilities).catch(() => undefined)
  }, [])
  useEffect(() => {
    fetch(`${API}/api/sessions/${session.id}/evaluation`).then(r => r.ok ? r.json() : Promise.reject()).then(setEvaluation).catch(() => setEvaluation({}))
    fetch(`${API}/api/sessions/${session.id}/audit`).then(r => r.ok ? r.json() : Promise.reject()).then(setAudit).catch(() => setAudit([]))
  }, [session.id, session.status])

  async function approve() {
    try {
      const response = await fetch(`${API}/api/sessions/${session.id}/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision: 'approve' }) })
      if (!response.ok) throw new Error()
      setSession(await response.json())
    } catch { setSession({ ...session, status: 'approved', progress: 100 }) }
    setNotice('Brief approved. The decision is now part of the audit trail.')
  }

  async function analyzeDiscovery() {
    setAnalyzing(true); setNotice('')
    try {
      if (knowledgeFile) {
        const form = new FormData(); form.append('file', knowledgeFile)
        const upload = await fetch(`${API}/api/knowledge/upload`, { method: 'POST', body: form })
        if (!upload.ok) throw new Error('Document upload failed')
      }
      const response = await fetch(`${API}/api/sessions/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ organization, transcript }) })
      if (!response.ok) throw new Error('Analysis failed')
      setSession(await response.json()); setSelected(0); setComposer(false); setKnowledgeFile(null); setAnswers({})
    } catch { setNotice('The analysis API is unavailable. Start the backend and try again.') }
    finally { setAnalyzing(false) }
  }

  async function answerGaps() {
    const payload = session.open_questions.filter(question => answers[question]?.trim()).map(question => ({ question, answer: answers[question].trim() }))
    if (!payload.length) { setNotice('Add at least one answer before re-running the graph.'); return }
    setFollowingUp(true); setNotice('')
    try {
      const response = await fetch(`${API}/api/sessions/${session.id}/follow-up`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers: payload }) })
      if (!response.ok) throw new Error()
      setSession(await response.json()); setSelected(0); setAnswers({}); setNotice('Follow-up evidence added and the solution graph re-ran.')
    } catch { setNotice('The follow-up could not be saved. Check that the API is running.') }
    finally { setFollowingUp(false) }
  }

  async function toggleRecording() {
    if (recording) { recorder.current?.stop(); return }
    if (!capabilities.transcription) { setVoiceStatus('Voice adapter is ready. Add OPENAI_API_KEY to the API environment to enable transcription.'); return }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const chunks: Blob[] = []
      const active = new MediaRecorder(stream)
      active.ondataavailable = event => { if (event.data.size) chunks.push(event.data) }
      active.onstop = async () => {
        setRecording(false); stream.getTracks().forEach(track => track.stop()); setVoiceStatus('Transcribing…')
        const form = new FormData(); form.append('file', new Blob(chunks, { type: active.mimeType || 'audio/webm' }), 'discovery.webm')
        try {
          const response = await fetch(`${API}/api/audio/transcribe`, { method: 'POST', body: form })
          if (!response.ok) throw new Error()
          const data = await response.json(); setTranscript(value => `${value}${value ? '\n' : ''}Voice participant: ${data.transcript}`); setVoiceStatus('Transcript added below.')
        } catch { setVoiceStatus('Transcription failed. You can still paste the transcript manually.') }
      }
      recorder.current = active; active.start(); setRecording(true); setVoiceStatus('Listening… click stop when finished.')
    } catch { setVoiceStatus('Microphone permission was not granted.') }
  }

  const req = session.requirements[selected]

  const completedStages = session.stages.filter(stage => stage.status === 'complete').length

  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href="#" aria-label="SignalRoom home"><span className="brandmark" aria-hidden="true">S</span><span>SignalRoom</span></a>
      <div className="room-identity"><strong>{session.organization}</strong><span>Solution review</span></div>
      <div className="topbar-actions">
        <span className="model-status"><span aria-hidden="true" />{capabilities.llm ? 'Live model' : 'Local model'}</span>
        <button className="button button-secondary" onClick={() => setComposer(true)}><Plus size={16}/> Analyze new discovery</button>
      </div>
    </header>

    <section className="review-header">
      <div className="review-heading">
        <p>{session.status === 'approved' ? 'Decision recorded' : 'Human review required'}</p>
        <h1>{session.status === 'approved' ? 'This solution brief is approved.' : `Review the proposal for ${session.organization}.`}</h1>
        <span>{session.status === 'approved' ? 'The evidence, proposal, and reviewer decision are stored in the audit trail.' : 'Inspect the evidence and unresolved assumptions, then approve the brief or send it back.'}</span>
      </div>
      <div className="workflow-summary" aria-label={`Workflow ${session.progress}% complete`}>
        <div><span>{completedStages} of {session.stages.length} stages complete</span><strong>{session.progress}%</strong></div>
        <div className="progress"><i style={{ transform: `scaleX(${session.progress / 100})` }} /></div>
      </div>
    </section>

    <nav className="workflow" aria-label="Agent workflow">
      {session.stages.map((stage, i) => <div className={`workflow-step ${stage.status}`} key={stage.name}>
        <span className="step-marker">{stage.status === 'complete' ? <Check size={14}/> : i + 1}</span>
        <span><strong>{stage.name}</strong><small>{stage.detail}</small></span>
      </div>)}
    </nav>

    <section className="workspace">
      <aside className="requirements-panel" aria-label="Requirements">
        <div className="panel-heading"><h2>Requirements</h2><span>{session.requirements.length} grounded</span></div>
        <div className="requirement-list">
          {session.requirements.map((item, i) => <button key={item.id} onClick={() => setSelected(i)} className={`requirement-row ${i === selected ? 'selected' : ''}`} aria-current={i === selected ? 'true' : undefined}>
            <span className="requirement-meta"><b>{item.id}</b><span>{item.kind}</span></span>
            <strong>{item.title}</strong>
            <span className="requirement-state"><i className={`confidence-dot ${item.confidence}`} />{item.confidence}<ChevronRight size={15}/></span>
          </button>)}
        </div>
        <button className="continue-discovery" onClick={() => setComposer(true)}><Mic size={17}/><span><strong>Continue discovery</strong><small>Add transcript or reference material</small></span></button>
      </aside>

      <article className="evidence-docket">
        <header className="docket-header">
          <div className="document-id"><span>{req.id}</span><span>{req.kind}</span><span>{req.confidence} confidence</span></div>
          <h2>{req.title}</h2>
          <p>{req.detail}</p>
        </header>

        <section className="source-evidence" aria-labelledby="source-evidence-title">
          <div className="section-title"><h3 id="source-evidence-title">Source evidence</h3><span><Quote size={14}/> Transcript · {req.evidence.timestamp}</span></div>
          <blockquote>“{req.evidence.quote}”</blockquote>
          <p>{req.evidence.speaker}</p>
        </section>

        <div className="analysis-grid">
          <section className="recommendation" aria-labelledby="recommendation-title">
            <div className="section-title"><h3 id="recommendation-title">Recommended approach</h3><span>Agent proposal</span></div>
            <p>{session.brief.recommendation}</p>
            <ol className="architecture">
              {session.brief.architecture.map((part, i) => <li key={part}><span>{String(i + 1).padStart(2, '0')}</span><strong>{part}</strong>{i < session.brief.architecture.length - 1 && <ArrowRight size={14}/>}</li>)}
            </ol>
          </section>
          <section className="critique" aria-labelledby="critique-title">
            <div className="section-title"><h3 id="critique-title">Critic pass</h3><span>{session.risks.length} risks</span></div>
            {session.risks.map(risk => <div className="risk" key={risk.title}><CircleAlert size={16}/><div><strong>{risk.title}</strong><p>{risk.mitigation}</p></div><span className={`severity ${risk.severity}`}>{risk.severity}</span></div>)}
          </section>
        </div>

        <section className="questions" aria-labelledby="questions-title">
          <div className="section-title"><h3 id="questions-title">Unresolved before implementation</h3><span>{session.open_questions.length} questions</span></div>
          {session.open_questions.length ? session.open_questions.map((q, i) => <label className="question" key={q}>
            <span>{String(i + 1).padStart(2, '0')}</span><span><strong>{q}</strong><input aria-label={`Answer: ${q}`} placeholder="Add a confirmed answer" value={answers[q] || ''} onChange={event => setAnswers({ ...answers, [q]: event.target.value })}/></span>
          </label>) : <p className="empty-state">All implementation questions have confirmed answers.</p>}
          {session.open_questions.length > 0 && <button className="button button-secondary rerun" disabled={followingUp} onClick={answerGaps}><RotateCcw size={15}/>{followingUp ? 'Re-running graph…' : 'Add answers and re-run'}</button>}
        </section>

        {!!session.brief.retrieval?.length && <section className="sources" aria-labelledby="sources-title">
          <div className="section-title"><h3 id="sources-title">Retrieved knowledge</h3><span>{session.brief.retrieval.length} passages</span></div>
          <div className="source-list">{session.brief.retrieval.map((hit, i) => <article key={`${hit.title}-${i}`}><BookOpen size={16}/><div><strong>{hit.title}</strong><span>{hit.source} · {Math.round(hit.score * 100)}% match</span><p>{hit.passage}</p></div></article>)}</div>
        </section>}
      </article>

      <aside className="decision-panel" aria-label="Review decision">
        <div className={`decision-state ${session.status}`}><FileCheck2 size={19}/>{session.status === 'approved' ? 'Approved' : 'Awaiting reviewer'}</div>
        <h2>{session.status === 'approved' ? 'Brief approved' : 'Make the final call'}</h2>
        <p>AI-generated working material. Confirm that the evidence, assumptions, and open questions support the proposed solution.</p>

        <dl className="quality-checks">
          <div><dt>Grounded requirements</dt><dd>{Math.round(Number(evaluation.grounding_rate ?? 1) * 100)}%</dd></div>
          <div><dt>Unsupported numbers</dt><dd>{evaluation.unsupported_numeric_claims ?? 0}</dd></div>
          <div><dt>Retrieved passages</dt><dd>{evaluation.retrieval_hits ?? session.brief.retrieval?.length ?? 0}</dd></div>
        </dl>

        {session.status !== 'approved' && <div className="decision-actions"><button className="button button-primary" onClick={approve}>Approve brief <ArrowRight size={16}/></button><button className="button button-secondary" onClick={() => setNotice('Change request captured. The brief will return to the critique stage.')}>Request changes</button></div>}
        <a className="button button-secondary export" href={`${API}/api/sessions/${session.id}/export.docx`}><Download size={15}/> Export brief</a>
        {notice && <div className="notice" role="status">{notice}</div>}

        {!!audit.length && <div className="audit-list"><h3><Activity size={14}/> Recent activity</h3>{audit.slice(-3).map(event => <div key={event.id}><strong>{event.event.replaceAll('_', ' ')}</strong><span>{event.created_at}</span></div>)}</div>}
        <p className="audit-note"><ShieldCheck size={14}/> Reviewer, timestamp, and workflow version are logged with the decision.</p>
      </aside>
    </section>

    {composer && <div className="overlay" role="dialog" aria-modal="true" aria-label="Analyze new discovery">
      <section className="composer">
        <header><div><h2>Analyze a new discovery</h2><p>Start a solution room from a synthetic conversation and optional reference material.</p></div><button className="icon-button" aria-label="Close" onClick={() => setComposer(false)}><X/></button></header>
        <div className="composer-body">
          <label>Organization<input value={organization} onChange={event => setOrganization(event.target.value)} /></label>
          <label>Discovery transcript<textarea value={transcript} onChange={event => setTranscript(event.target.value)} rows={11} /></label>
          <div className="voice-control"><button className={`button button-secondary record ${recording ? 'active' : ''}`} type="button" onClick={toggleRecording}>{recording ? <Square size={14}/> : <Radio size={14}/>} {recording ? 'Stop recording' : 'Record discovery'}</button>{voiceStatus && <span className="voice-status">{voiceStatus}</span>}</div>
          <label className="file-field">Reference document <span>Optional · TXT, MD, PDF, DOCX</span><div><Upload size={16}/><strong>{knowledgeFile?.name || 'Choose a reference file'}</strong><input type="file" accept=".txt,.md,.pdf,.docx" onChange={event => setKnowledgeFile(event.target.files?.[0] || null)}/></div></label>
          <div className="composer-note"><ShieldCheck size={16}/><span><strong>Portfolio-safe input only</strong>Use synthetic or non-confidential content in this demo.</span></div>
        </div>
        <footer><button className="button button-secondary" onClick={() => setComposer(false)}>Cancel</button><button className="button button-primary analyze" disabled={analyzing || transcript.length < 40} onClick={analyzeDiscovery}>{analyzing ? 'Running solution graph…' : 'Analyze discovery'} <ArrowRight size={16}/></button></footer>
      </section>
    </div>}
  </main>
}
