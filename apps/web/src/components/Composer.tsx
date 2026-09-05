import { useEffect, useState } from 'react'
import { ArrowRight, ShieldCheck, Upload, X } from 'lucide-react'
import { api } from '../api'
import type { FixtureSummary } from '../types'

type Props = {
  busy: boolean
  onClose: () => void
  onSubmit: (body: { organization: string; industry: string; transcript: string }, referenceFile: File | null) => void
  initial?: { organization: string; industry: string; transcript: string } | null
}

export function Composer({ busy, onClose, onSubmit, initial }: Props) {
  const [organization, setOrganization] = useState(initial?.organization ?? '')
  const [industry, setIndustry] = useState(initial?.industry ?? '')
  const [transcript, setTranscript] = useState(initial?.transcript ?? '')
  const [referenceFile, setReferenceFile] = useState<File | null>(null)
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([])

  useEffect(() => { api.fixtures().then(setFixtures).catch(() => setFixtures([])) }, [])
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape' && !busy) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [busy, onClose])

  function loadFixture(id: string) {
    const fixture = fixtures.find(item => item.id === id)
    if (!fixture) return
    setOrganization(fixture.organization); setIndustry(fixture.industry); setTranscript(fixture.transcript)
  }

  const lines = transcript.split('\n').filter(line => line.trim()).length
  const attributed = transcript.split('\n').filter(line => /^[^:]{2,60}:\s*\S/.test(line.trim())).length
  const canSubmit = !busy && organization.trim().length >= 2 && transcript.trim().length >= 40

  return <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="composer-title">
    <section className="composer">
      <header>
        <div>
          <h2 id="composer-title">Start a solution room</h2>
          <p>Paste a discovery transcript, one line per speaker turn. The workflow segments it, extracts grounded requirements, drafts a brief and stops at the gate.</p>
        </div>
        <button className="icon-button" aria-label="Close" onClick={onClose} disabled={busy}><X/></button>
      </header>
      <div className="composer-body">
        <div className="composer-row">
          <label>Organization<input value={organization} onChange={event => setOrganization(event.target.value)} placeholder="Invented organization name" /></label>
          <label>Industry<input value={industry} onChange={event => setIndustry(event.target.value)} placeholder="As the customer describes it" /></label>
        </div>
        {fixtures.length > 0 && <label>Load a synthetic example
          <select defaultValue="" onChange={event => loadFixture(event.target.value)}>
            <option value="" disabled>Choose a fixture…</option>
            {fixtures.map(item => <option key={item.id} value={item.id}>{item.organization} · {item.industry} · {item.lines} lines</option>)}
          </select>
        </label>}
        <label>Discovery transcript
          <textarea value={transcript} onChange={event => setTranscript(event.target.value)} rows={14} placeholder={'Operations lead: We usually find out too late.\nIT architect: Anything new has to use the existing API.'} />
        </label>
        <p className="field-hint" aria-live="polite">{lines} lines, {attributed} with a speaker label{lines > 0 && attributed < lines ? `; ${lines - attributed} will be marked unattributed` : ''}.</p>
        <label className="file-field">Reference document <span>Optional · TXT, MD, PDF, DOCX · indexed into the pattern library</span>
          <div><Upload size={16}/><strong>{referenceFile?.name || 'Choose a synthetic reference file'}</strong>
            <input type="file" accept=".txt,.md,.pdf,.docx" onChange={event => setReferenceFile(event.target.files?.[0] || null)} aria-label="Reference document"/>
          </div>
        </label>
        <div className="composer-note"><ShieldCheck size={16}/><span><strong>Synthetic input only</strong>Everything in this demo is invented. Do not paste real customer material.</span></div>
      </div>
      <footer>
        <button className="button button-secondary" onClick={onClose} disabled={busy}>Cancel</button>
        <button className="button button-primary" disabled={!canSubmit} onClick={() => onSubmit({ organization: organization.trim(), industry: industry.trim(), transcript }, referenceFile)}>
          {busy ? 'Running the workflow…' : 'Run the workflow'} <ArrowRight size={16}/>
        </button>
      </footer>
    </section>
  </div>
}
