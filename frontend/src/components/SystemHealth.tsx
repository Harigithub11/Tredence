import { useEffect, useState } from 'react'
import { Database, Zap, CheckCircle, XCircle } from 'lucide-react'
import apiClient from '../services/api'
import type { HealthResponse } from '../types'

export default function SystemHealth() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 10000) // Check every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const checkHealth = async () => {
    try {
      const data = await apiClient.health()
      setHealth(data)
    } catch (error) {
      console.error('Health check failed:', error)
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="text-lg font-bold text-gray-900 mb-4">System Health</h2>

      <div className="space-y-3">
        <HealthItem
          icon={<Zap className="w-5 h-5" />}
          label="API"
          status={health?.status === 'healthy'}
          loading={loading}
        />
        <HealthItem
          icon={<Database className="w-5 h-5" />}
          label="Database"
          status={health?.database === true}
          loading={loading}
        />
      </div>

      {health && (
        <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
          Last checked: {new Date(health.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )
}

interface HealthItemProps {
  icon: React.ReactNode
  label: string
  status: boolean
  loading: boolean
}

function HealthItem({ icon, label, status, loading }: HealthItemProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <div className="text-gray-600">{icon}</div>
        <span className="text-sm font-medium text-gray-900">{label}</span>
      </div>
      {loading ? (
        <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
      ) : status ? (
        <CheckCircle className="w-5 h-5 text-green-600" />
      ) : (
        <XCircle className="w-5 h-5 text-red-600" />
      )}
    </div>
  )
}
