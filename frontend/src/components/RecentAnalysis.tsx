import { TrendingUp, Code, AlertCircle } from 'lucide-react'
import type { WorkflowRun } from '../types'

interface RecentAnalysisProps {
  runs: WorkflowRun[]
}

export default function RecentAnalysis({ runs }: RecentAnalysisProps) {
  return (
    <div className="card">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Recent Analysis</h2>

      {runs.length === 0 ? (
        <div className="text-center py-8">
          <Code className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No recent code reviews</p>
        </div>
      ) : (
        <div className="space-y-4">
          {runs.slice(0, 5).map((run) => (
            <AnalysisCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  )
}

function AnalysisCard({ run }: { run: WorkflowRun }) {
  const result = run.final_state as any

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">Code Review #{run.id}</h3>
          <p className="text-xs text-gray-500">
            {run.completed_at
              ? new Date(run.completed_at).toLocaleString()
              : 'In progress'}
          </p>
        </div>
        {result?.quality_score !== undefined && (
          <div
            className={`px-3 py-1 rounded text-sm font-medium ${
              result.quality_score >= 80
                ? 'bg-green-100 text-green-800'
                : result.quality_score >= 60
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {result.quality_score}/100
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-primary-600" />
          <div>
            <p className="text-gray-500">Time</p>
            <p className="font-medium">
              {result?.complexity_analysis?.time_complexity || 'N/A'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-primary-600" />
          <div>
            <p className="text-gray-500">Space</p>
            <p className="font-medium">
              {result?.complexity_analysis?.space_complexity || 'N/A'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600" />
          <div>
            <p className="text-gray-500">Issues</p>
            <p className="font-medium">{result?.issue_count || 0}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
