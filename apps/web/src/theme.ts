import { useEffect, useState } from 'react'

export type Theme = 'day' | 'night'
const KEY = 'signalroom.theme'

function preferred(): Theme {
  try {
    const stored = localStorage.getItem(KEY)
    if (stored === 'day' || stored === 'night') return stored
  } catch { /* storage unavailable */ }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'night' : 'day'
}

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => (typeof window === 'undefined' ? 'day' : preferred()))
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.querySelector('meta[name="color-scheme"]')?.setAttribute('content', theme === 'night' ? 'dark' : 'light')
    try { localStorage.setItem(KEY, theme) } catch { /* ignore */ }
  }, [theme])
  return [theme, () => setTheme(current => (current === 'day' ? 'night' : 'day'))]
}
