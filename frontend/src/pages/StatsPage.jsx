import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { getStats } from '../api/stats'
import { useToast } from '../hooks/useToast'
import { errorMessage } from '../api/client'

const PIE_COLORS = ['#c8f064', '#6eb5ff', '#f5a623', '#5ce8a4', '#f07070', '#b39ddb']

function toData(obj) {
  return Object.entries(obj || {}).map(([name, value]) => ({ name, value }))
}

const tooltipStyle = {
  backgroundColor: '#1c1f24',
  border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: 8,
  color: '#f0f0ee',
  fontSize: 12,
}

function ChartCard({ title, children, hasData }) {
  return (
    <div className="rounded-xl border border-border bg-bg-card p-5">
      <h2 className="mb-4 font-heading text-base font-bold text-text">{title}</h2>
      {hasData ? (
        <div className="h-72 w-full">{children}</div>
      ) : (
        <p className="py-16 text-center text-sm text-muted">No data available.</p>
      )}
    </div>
  )
}

export default function StatsPage() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const { error } = useToast()

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((e) => error(errorMessage(e, 'Failed to load stats')))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size={32} />
      </div>
    )
  }

  if (!stats) {
    return <EmptyState title="No statistics" subtitle="Stats could not be loaded." icon="📊" />
  }

  const categoryData = toData(stats.by_category)
  const languageData = toData(stats.by_language)
  const urgencyData = toData(stats.by_urgency)

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        Aggregate metrics across <span className="num text-text">{stats.total}</span> processed email(s).
      </p>

      <ChartCard title="Emails by category" hasData={categoryData.length > 0}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={categoryData} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="name" tick={{ fill: '#8a8d94', fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={50} />
            <YAxis allowDecimals={false} tick={{ fill: '#8a8d94', fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
            <Bar dataKey="value" fill="#c8f064" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Emails by language" hasData={languageData.length > 0}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={languageData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ name, value }) => `${name}: ${value}`}
                labelLine={false}
              >
                {languageData.map((entry, i) => (
                  <Cell key={entry.name} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#8a8d94' }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Emails by urgency" hasData={urgencyData.length > 0}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={urgencyData} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" tick={{ fill: '#8a8d94', fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fill: '#8a8d94', fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
              <Bar dataKey="value" fill="#6eb5ff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  )
}
