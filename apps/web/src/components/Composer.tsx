import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { ArrowRight, ShieldCheck, Upload, X } from 'lucide-react'
import { api } from '../api'
import type { FixtureSummary } from '../types'
import { useGrammar } from '../motion'

type Props = {
  busy: boolean
  onClose: () => void
  onSubmit: (body: { organization: string; industry: string; transcript: string }, referenceFile: File | null) => void
  initial?: { organization: string; industry: string; transcript: string } | null
}

export function Composer({ busy, onClose, onSubmit, initial }: Props) {
  const grammar = useGrammar()
  const [organization, setOrganization] = useState(initial?.organization ?? '')
  const [industry, setIndustry] = useState(initial?.industry ?? '')
  const [transcript, setTranscript] = useState(initial?.transcript ?? '')
  const [referenceFile, setReferenceFile] = useState<File | null>(null)
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([])
  const first = useRef<HTMLInputElement>(null)

  useEffect(() => { api.fixtures().then(setFixtures).catch(() => setFixtures([])); first.current?.focus() }, [])
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
  const attributed = transcript.split('\n').filter(line => /^[^:]{1,60}:\s*\S/.test(line.trim())).length
  const canSubmit = !busy && organization.trim().length >= 2 && transcript.trim().length >= 40

  return <motion.div className="overlay" role="presentation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={grammar.state} onMouseDown={event => { if (event.target === event.currentTarget && !busy) onClose() }}>
    <motion.section className="sheet" role="dialog" aria-modal="true" aria-labelledby="composer-title"
      initial={{ x: grammar.reduced ? 0 : 32, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: grammar.reduced ? 0 : 24, opacity: 0 }} transition={grammar.layout}>
      <header>
        <div>
          <h2 id="composer-title">Open a new room</h2>
          <p>Paste a discovery transcript, one line per speaker turn. The workflow segments it, extracts grounded claims, drafts the brief, critiques it and stops at the gate for you.</p>
        </div>
        <button className="icon-btn" aria-label="Close" onClick={onClose} disabled={busy}><X size={16}/></button>
      </header>
      <div className="sheet-body">
        <div className="sheet-row">
          <label className="field">Organization<input ref={first} value={organization} onChange={event => setOrganization(event.target.value)} placeholder="Invented organization" /></label>
          <label className="field">Industry<input value={industry} onChange={event => setIndustry(event.target.value)} placeholder="As the customer describes it" /></label>
        </div>
        {fixtures.length > 0 && <label className="field">Load a synthetic example
          <select defaultValue="" onChange={event => loadFixture(event.target.value)}>
            <option value="" disabled>Choose a fixture</option>
            {fixtures.map(item => <option key={item.id} value={item.id}>{item.organization} · {item.industry} · {item.lines} lines</option>)}
          </select>
        </label>}
        <label className="field">Discovery transcript
          <textarea value={transcript} onChange={event => setTranscript(event.target.value)} rows={13} placeholder={'Operations lead: We usually find out too late.\nIT architect: Anything new has to use the existing API.'} />
          <span className="hint" aria-live="polite">{lines} lines, {attributed} with a speaker label{lines > 0 && attributed < lines ? `; ${lines - attributed} will be marked unattributed` : ''}.</span>
        </label>
        <label className="field file-field">Reference document<span className="hint">Optional. TXT, MD, PDF or DOCX, indexed into the pattern library.</span>
          <div><Upload size={15}/>{referenceFile?.name || 'Choose a synthetic reference file'}<input type="file" accept=".txt,.md,.pdf,.docx" onChange={event => setReferenceFile(event.target.files?.[0] || null)} aria-label="Reference document"/></div>
        </label>
        <div className="synthetic-note"><ShieldCheck size={15}/><span><b>Synthetic input only</b>Everything in this demo is invented. Do not paste real customer material.</span></div>
      </div>
      <footer>
        <button className="btn" onClick={onClose} disabled={busy}>Cancel</button>
        <motion.button className="btn btn-primary" disabled={!canSubmit} onClick={() => onSubmit({ organization: organization.trim(), industry: industry.trim(), transcript }, referenceFile)} whileTap={grammar.press}>
          {busy ? 'Running the workflow' : 'Run the workflow'} <ArrowRight size={15}/>
        </motion.button>
      </footer>
    </motion.section>
  </motion.div>
}
