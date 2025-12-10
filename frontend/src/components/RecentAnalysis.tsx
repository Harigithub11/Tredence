import { useState } from 'react'
import { TrendingUp, Code, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
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
  const [expanded, setExpanded] = useState(false)
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
              {getComplexity(result, 'time_complexity')}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-primary-600" />
          <div>
            <p className="text-gray-500">Space</p>
            <p className="font-medium">
              {getComplexity(result, 'space_complexity')}
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

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-3 flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-700"
      >
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        <span>{expanded ? 'Hide' : 'Show'} Execution Flow</span>
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3 text-sm">
          <div>
            <span className="font-medium text-gray-700">Nodes:</span>
            <span className="ml-2 text-gray-600">extract_functions → analyze_complexity → detect_issues → improve_code → validate_tests</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">State:</span>
            <span className="ml-2 text-gray-600">Shared dict with code, functions, issues, complexity, improved_code</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Edges:</span>
            <span className="ml-2 text-gray-600">Linear flow: extract→analyze→detect→improve→validate</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Branching:</span>
            <span className="ml-2 text-gray-600">After validate_tests: quality_score ≥ threshold → end, else → improve_code</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Looping:</span>
            <span className="ml-2 text-gray-600">Improve→Validate loop until quality_score ≥ {run.initial_state?.quality_threshold || 70} (max 3 iterations)</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Tools:</span>
            <span className="ml-2 text-gray-600">AST parser, Radon complexity analyzer, {run.initial_state?.use_llm ? 'Gemini LLM for tests' : 'Pattern-based test generator'}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">API:</span>
            <span className="ml-2 text-gray-600">POST /graph/run triggered, GET /graph/state/{run.run_id} polled for updates</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Functions:</span>
            <span className="ml-2 text-gray-600">{result?.extracted_functions?.length || 0} function(s) extracted from code</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Complexity:</span>
            <span className="ml-2 text-gray-600">Time: {getComplexity(result, 'time_complexity')}, Space: {getComplexity(result, 'space_complexity')}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Issues:</span>
            <span className="ml-2 text-gray-600">{result?.issue_count || 0} issue(s) detected (style, complexity, best practices)</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Improvements:</span>
            <span className="ml-2 text-gray-600">{result?.improvements_applied?.length || 0} improvement(s) applied: {result?.improvements_applied?.join(', ') || 'none'}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Iterations:</span>
            <span className="ml-2 text-gray-600">{result?.iteration || 1} iteration(s) to reach quality score {result?.quality_score}/100</span>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to extract complexity from nested structure
function getComplexity(result: any, field: 'time_complexity' | 'space_complexity'): string {
  if (!result?.complexity_analysis) return 'N/A'

  // complexity_analysis is an object with function names as keys
  // Get the first function's complexity
  const firstFunc = Object.keys(result.complexity_analysis)[0]
  if (firstFunc && result.complexity_analysis[firstFunc]) {
    return result.complexity_analysis[firstFunc][field] || 'N/A'
  }

  return 'N/A'
}
