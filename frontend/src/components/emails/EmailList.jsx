import EmailCard from './EmailCard'

export default function EmailList({ emails, onApprove, onReject }) {
  return (
    <div className="flex flex-col gap-4">
      {emails.map((email) => (
        <EmailCard
          key={email.id}
          email={email}
          onApprove={onApprove}
          onReject={onReject}
        />
      ))}
    </div>
  )
}
