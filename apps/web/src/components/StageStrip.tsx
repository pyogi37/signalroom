import { Check, X } from 'lucide-react'
import type { StageRecord } from '../types'
import { ms } from '../format'

const ORDER = ['Discover', 'Extract', 'Retrieve', 'Design', 'Critique', 'Gate']

export function StageStrip({ stages, running }: { stages: StageRecord[]; running: boolean }) {
  const byName = new Map(stages.map(stage => [stage.name, stage]))
  return <nav className="workflow" aria-label="Workflow stages">
    {ORDER.map((name, index) => {
      const stage = byName.get(name)
      const status = running ? (index === 0 ? 'active' : 'pending') : stage?.status ?? 'pending'
      return <div className={`workflow-step ${status}`} key={name} aria-current={status === 'active' ? 'step' : undefined}>
        <span className="step-marker" aria-hidden="true">{status === 'complete' ? <Check size={14}/> : status === 'failed' ? <X size={14}/> : index + 1}</span>
        <span>
          <strong>{name}</strong>
          <small>{running ? (index === 0 ? 'Running…' : 'Queued') : stage?.detail ?? 'Not run'}{stage && stage.latency_ms > 0 && !running ? ` · ${ms(stage.latency_ms)}` : ''}</small>
        </span>
      </div>
    })}
  </nav>
}
