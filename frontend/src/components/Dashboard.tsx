import { useState, useEffect } from 'react'
import { Activity, PlayCircle, Clock, CheckCircle2, AlertCircle } from 'lucide-react'
import ActiveRuns from './ActiveRuns'
import RecentAnalysis from './RecentAnalysis'
import SystemHealth from './SystemHealth'
import WorkflowStats from './WorkflowStats'
import apiClient from '../services/api'
import type { WorkflowRun } from '../types'

export default function Dashboard() {
  const [activeRuns, setActiveRuns] = useState<WorkflowRun[]>([])
  const [recentRuns, setRecentRuns] = useState<WorkflowRun[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    running: 0,
    completed: 0,
    failed: 0,
  })

  useEffect(() => {
    loadDashboardData()
    const interval = setInterval(loadDashboardData, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const loadDashboardData = async () => {
    try {
      // In a real implementation, these would be actual API calls
      // For now, we'll use mock data as the list endpoint doesn't exist yet
      setIsLoading(false)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Workflow Orchestration Dashboard
          </h1>
          <p className="mt-1 text-gray-600">
            Real-time monitoring and execution of workflow graphs
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-primary-600 animate-pulse" />
          <span className="text-sm text-gray-600">Live Updates</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total Runs"
          value={stats.total}
          icon={<PlayCircle className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Running"
          value={stats.running}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={<CheckCircle2 className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Failed"
          value={stats.failed}
          icon={<AlertCircle className="w-6 h-6" />}
          color="red"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Active Runs (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <ActiveRuns runs={activeRuns} />
          <RecentAnalysis runs={recentRuns} />
        </div>

        {/* Right Column - System Info (1/3 width) */}
        <div className="space-y-6">
          <SystemHealth />
          <WorkflowStats />
        </div>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  color: 'blue' | 'yellow' | 'green' | 'red'
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}
