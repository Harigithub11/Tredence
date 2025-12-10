import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp } from 'lucide-react'
import apiClient from '../services/api'

interface StatsData {
  avg_execution_time_ms: number
  success_rate: number
}

export default function WorkflowStats() {
  const [stats, setStats] = useState<StatsData>({
    avg_execution_time_ms: 0,
    success_rate: 0
  })

  useEffect(() => {
    loadStats()
    const interval = setInterval(loadStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadStats = async () => {
    try {
      const response = await apiClient.get('/graph/stats/summary')
      setStats({
        avg_execution_time_ms: response.data.avg_execution_time_ms,
        success_rate: response.data.success_rate
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const formatExecutionTime = (ms: number) => {
    if (ms === 0) return '0s'
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <div className="card">
      <h2 className="text-lg font-bold text-gray-900 mb-4">Workflow Stats</h2>

      <div className="space-y-4">
        <StatItem
          label="Avg Execution Time"
          value={formatExecutionTime(stats.avg_execution_time_ms)}
          trend=""
          positive={true}
        />
        <StatItem
          label="Success Rate"
          value={`${stats.success_rate.toFixed(0)}%`}
          trend=""
          positive={true}
        />
      </div>

    </div>
  )
}

interface StatItemProps {
  label: string
  value: string
  trend: string
  positive: boolean
}

function StatItem({ label, value, trend, positive }: StatItemProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{label}</p>
        <p className="text-lg font-bold text-gray-900">{value}</p>
      </div>
      <div
        className={`flex items-center space-x-1 text-sm ${
          positive ? 'text-green-600' : 'text-red-600'
        }`}
      >
        <TrendingUp className="w-4 h-4" />
        <span>{trend}</span>
      </div>
    </div>
  )
}
