/* Motion grammar: "the review".
   One focal moment (a submitted decision resolving the checks), continuity for
   selection and re-review, feedback on controls. Spatial movement collapses to
   opacity under prefers-reduced-motion; state colour changes always remain. */

import { useReducedMotion, type Transition } from 'motion/react'

export const ease = [0.16, 1, 0.3, 1] as const

export const durations = { feedback: 0.12, state: 0.2, layout: 0.32, focal: 0.6 }

export function useGrammar() {
  const reduced = useReducedMotion() ?? false
  const t = (seconds: number): Transition => ({ duration: reduced ? Math.min(seconds, 0.2) : seconds, ease })
  return {
    reduced,
    state: t(durations.state),
    layout: t(durations.layout),
    focal: t(durations.focal),
    /* An element arriving in place: rises 6px unless motion is reduced. */
    arrive: {
      initial: { opacity: 0, y: reduced ? 0 : 6 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: reduced ? 0 : -4, transition: t(durations.feedback) },
      transition: t(durations.state),
    },
    /* A thread or panel opening: height follows content. */
    expand: {
      initial: { opacity: 0, height: 0 },
      animate: { opacity: 1, height: 'auto' },
      exit: { opacity: 0, height: 0, transition: t(durations.feedback) },
      transition: t(durations.layout),
    },
    press: reduced ? undefined : { scale: 0.985 },
  }
}
