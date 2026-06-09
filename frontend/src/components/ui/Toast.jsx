import useToastStore from '../../hooks/useToast'

const STYLES = {
  success: { border: 'border-success/40', bar: 'bg-success', text: 'text-success' },
  error: { border: 'border-danger/40', bar: 'bg-danger', text: 'text-danger' },
  warning: { border: 'border-warning/40', bar: 'bg-warning', text: 'text-warning' },
  info: { border: 'border-info/40', bar: 'bg-info', text: 'text-info' },
}

export default function Toast() {
  const toasts = useToastStore((s) => s.toasts)
  const dismiss = useToastStore((s) => s.dismiss)

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-50 flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => {
        const style = STYLES[t.type] || STYLES.info
        return (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 overflow-hidden rounded-lg border ${style.border} bg-bg-card shadow-lg`}
          >
            <span className={`w-1 self-stretch ${style.bar}`} />
            <div className="flex flex-1 items-start justify-between gap-3 py-3 pr-3">
              <p className="text-sm leading-snug text-text">{t.message}</p>
              <button
                onClick={() => dismiss(t.id)}
                className="text-muted transition-colors hover:text-text"
                aria-label="Dismiss"
              >
                ✕
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
