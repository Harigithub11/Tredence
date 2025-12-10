import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Play, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import type { WorkflowRun } from '../types'
import { useWebSocket } from '../hooks/useWebSocket'

interface ActiveRunsProps {
  runs: WorkflowRun[]
}

export default function ActiveRuns({ runs }: ActiveRunsProps) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Active Runs</h2>
        <span className="badge badge-info">{runs.length} active</span>
      </div>

      {runs.length === 0 ? (
        <div className="text-center py-12">
          <Play className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No active workflow runs</p>
          <p className="text-sm text-gray-500 mt-1">
            Start a new workflow to see real-time progress here
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {runs.map((run) => (
            <RunCard key={run.run_id} run={run} />
          ))}
        </div>
      )}
    </div>
  )
}

interface RunCardProps {
  run: WorkflowRun
}

function RunCard({ run }: RunCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { messages } = useWebSocket(run.run_id)

  // Calculate progress from messages
  const progress = calculateProgress(run, messages)
  const currentNode = getCurrentNode(messages)

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors">
      {/* Run Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <StatusIcon status={run.status} />
          <div>
            <h3 className="font-medium text-gray-900">{run.run_id}</h3>
            {run.started_at && (
              <p className="text-xs text-gray-500">
                Started {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1 hover:bg-gray-100 rounded"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600" />
          )}
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-600">
            {run.status === 'running' ? `Status: Running (${currentNode || 'initializing'})` : `Status: ${run.status}`}
          </span>
          <span className="font-medium text-gray-900">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              run.status === 'running'
                ? 'bg-primary-600'
                : run.status === 'completed'
                ? 'bg-green-600'
                : 'bg-red-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Quality Score (if completed) */}
      {run.final_state?.quality_score !== undefined && (
        <div className="mb-3">
          <QualityBadge score={run.final_state.quality_score} />
        </div>
      )}

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
          {run.total_iterations !== undefined && (
            <DetailRow label="Iterations" value={run.total_iterations.toString()} />
          )}
          {run.total_execution_time_ms !== undefined && (
            <DetailRow
              label="Execution Time"
              value={`${(run.total_execution_time_ms / 1000).toFixed(2)}s`}
            />
          )}
          {run.error_message && (
            <div className="bg-red-50 text-red-700 p-3 rounded text-xs">
              <strong>Error:</strong> {run.error_message}
            </div>
          )}
          {messages.length > 0 && (
            <div className="mt-2">
              <p className="text-gray-600 font-medium mb-2">Recent Events:</p>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {messages.slice(-5).map((msg, idx) => (
                  <div key={idx} className="text-xs text-gray-600">
                    • {msg.type} at {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'running':
      return <Clock className="w-5 h-5 text-yellow-600 animate-pulse" />
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-600" />
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-600" />
    default:
      return <Clock className="w-5 h-5 text-gray-600" />
  }
}

function QualityBadge({ score }: { score: number }) {
  const getColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800'
    if (score >= 60) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getColor(score)}`}>
      Quality: {score}/100
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}:</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  )
}

function calculateProgress(run: WorkflowRun, messages: any[]): number {
  if (run.status === 'completed') return 100
  if (run.status === 'failed') return 100
  if (run.status === 'pending') return 0

  // Calculate based on messages
  const progressMsg = messages.find((m: any) => m.type === 'progress_update')
  if (progressMsg?.progress_percentage) {
    return progressMsg.progress_percentage
  }

  // Default for running
  return 50
}

function getCurrentNode(messages: any[]): string | null {
  const statusMsg = messages.findLast((m: any) => m.type === 'status_update' && m.current_node)
  return statusMsg?.current_node || null
}
