import { useEffect, useRef } from 'react'

// Calls `callback` immediately and then every `interval` ms.
// `callback` is kept in a ref so the timer isn't reset on every render.
export default function useAutoRefresh(callback, interval = 30000, enabled = true) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) return undefined
    savedCallback.current()
    const id = setInterval(() => savedCallback.current(), interval)
    return () => clearInterval(id)
  }, [interval, enabled])
}
