import { BarChart3, TrendingUp } from 'lucide-react'

export default function WorkflowStats() {
  return (
    <div className="card">
      <h2 className="text-lg font-bold text-gray-900 mb-4">Workflow Stats</h2>

      <div className="space-y-4">
        <StatItem
          label="Avg Execution Time"
          value="2.3s"
          trend="-12%"
          positive={true}
        />
        <StatItem
          label="Success Rate"
          value="94%"
          trend="+5%"
          positive={true}
        />
        <StatItem
          label="Avg Quality Score"
          value="87/100"
          trend="+3"
          positive={true}
        />
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <button className="w-full flex items-center justify-center space-x-2 text-sm text-primary-600 hover:text-primary-700">
          <BarChart3 className="w-4 h-4" />
          <span>View Detailed Analytics</span>
        </button>
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
