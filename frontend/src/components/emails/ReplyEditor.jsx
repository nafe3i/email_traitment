export default function ReplyEditor({ value, onChange, editable, placeholder }) {
  return (
    <textarea
      value={value || ''}
      onChange={(e) => onChange?.(e.target.value)}
      readOnly={!editable}
      placeholder={placeholder || 'No suggested reply generated.'}
      rows={10}
      className={`w-full resize-y rounded-lg border bg-bg-secondary p-3 text-sm leading-relaxed text-text outline-none transition-colors ${
        editable
          ? 'border-accent/50 focus:border-accent'
          : 'cursor-default border-border text-muted'
      }`}
    />
  )
}
