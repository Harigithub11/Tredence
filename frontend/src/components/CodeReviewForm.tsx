import { useState } from 'react'
import { Play, Loader2 } from 'lucide-react'
import apiClient from '../services/api'

const EXAMPLE_CODE = `def find_duplicates(nums):
    duplicates = []
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] == nums[j]:
                if nums[i] not in duplicates:
                    duplicates.append(nums[i])
    return duplicates
`

// Get improved code from backend or fallback to original
function getImprovedCode(data: any, originalCode: string): string {
  // If LLM generated improved code, use it
  if (data?.improved_code) {
    return data.improved_code
  }

  // Fallback to original code if no improvement available
  return originalCode
}

// Get algorithm name from backend data
function getAlgorithmName(data: any): string | null {
  return data?.algorithm_name || null
}

// Alternative Solution Card Component
function AlternativeSolutionCard({ solution, idx }: { solution: any; idx: number }) {
  const [copied, setCopied] = useState(false)
  const icons = ['⚡', '🎯', '🚀']

  return (
    <div className="bg-white rounded-lg p-4 border-2 border-purple-300">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="font-semibold text-purple-900 flex items-center">
            <span className="text-lg mr-2">{icons[idx] || '💡'}</span>
            Solution {idx + 1}: {solution.name}
          </h4>
          {solution.description && (
            <p className="text-xs text-gray-500 ml-7">{solution.description}</p>
          )}
        </div>
        <button
          onClick={() => {
            navigator.clipboard.writeText(solution.code)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
          }}
          className={`text-xs text-white px-3 py-1.5 rounded transition-all duration-200 flex items-center ${
            copied
              ? 'bg-purple-700 scale-95'
              : 'bg-purple-600 hover:bg-purple-700 hover:scale-105 active:scale-95'
          }`}
        >
          {copied ? (
            <>
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </>
          )}
        </button>
      </div>
      <div className="bg-gray-900 rounded p-3 overflow-x-auto">
        <pre className="text-xs text-purple-400 font-mono">
          <code>{solution.code}</code>
        </pre>
      </div>
      {solution.pros && (
        <div className="mt-3 flex items-start space-x-2">
          <span className="text-green-500 text-sm">✓</span>
          <div className="text-sm text-gray-700">
            <strong>Pros:</strong> {solution.pros}
          </div>
        </div>
      )}
    </div>
  )
}

export default function CodeReviewForm() {
  const [code, setCode] = useState(EXAMPLE_CODE)
  const [useLLM, setUseLLM] = useState(true)
  const [threshold, setThreshold] = useState(70)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [showAlternatives, setShowAlternatives] = useState(false)
  const [copiedMain, setCopiedMain] = useState(false)
  const [copiedAlt, setCopiedAlt] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const run = await apiClient.runs.execute(
        'code_review',
        { code, quality_threshold: threshold },
        useLLM
      )

      // Poll for results
      const pollInterval = setInterval(async () => {
        try {
          const state = await apiClient.runs.getState(run.run_id)
          if (state.status === 'completed') {
            clearInterval(pollInterval)
            setResult(state.final_state)
            setLoading(false)
          } else if (state.status === 'failed') {
            clearInterval(pollInterval)
            setError('Workflow execution failed. Please try again.')
            setLoading(false)
          }
        } catch (pollError) {
          console.error('Polling error:', pollError)
        }
      }, 1000)

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval)
        if (loading) {
          setError('Workflow timed out after 5 minutes')
          setLoading(false)
        }
      }, 300000)
    } catch (error: any) {
      console.error('Code review failed:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred'
      setError(`Error: ${errorMessage}`)
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Code Review</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Code Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Python Code
            </label>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input font-mono text-sm"
              rows={15}
              placeholder="Paste your Python code here..."
              required
            />
          </div>

          {/* Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quality Threshold
              </label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                min="0"
                max="100"
                className="input"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={useLLM}
                  onChange={(e) => setUseLLM(e.target.checked)}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">
                  Enable AI-powered suggestions (Gemini)
                </span>
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Run Code Review</span>
              </>
            )}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && result.data && (
          <div className="mt-8 pt-8 border-t border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Analysis Results</h2>

            {/* Quality Score */}
            <div className="mb-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">Quality Score</h3>
                  <p className="text-sm text-gray-600">
                    {result.data.quality_pass ? (
                      <span className="text-green-600 font-medium">✓ Passed (threshold: {result.data.quality_threshold})</span>
                    ) : (
                      <span className="text-red-600 font-medium">✗ Failed (threshold: {result.data.quality_threshold})</span>
                    )}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold text-indigo-600">{result.data.quality_score}</div>
                  <div className="text-sm text-gray-500">out of 100</div>
                </div>
              </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-gray-900">{result.data.function_count || 0}</div>
                <div className="text-sm text-gray-600">Functions</div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-orange-600">{result.data.issue_count || 0}</div>
                <div className="text-sm text-gray-600">Issues</div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-purple-600">{result.data.avg_complexity || 0}</div>
                <div className="text-sm text-gray-600">Avg Complexity</div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-blue-600">{result.iteration || 0}</div>
                <div className="text-sm text-gray-600">Iterations</div>
              </div>
            </div>

            {/* Complexity Analysis */}
            {result.data.complexity_analysis && Object.keys(result.data.complexity_analysis).length > 0 && (
              <div className="mb-6 bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Complexity Analysis</h3>
                <div className="space-y-4">
                  {Object.entries(result.data.complexity_analysis).map(([funcName, analysis]: [string, any]) => (
                    <div key={funcName} className="border-l-4 border-purple-500 pl-4">
                      <h4 className="font-mono font-semibold text-gray-900 mb-2">{funcName}()</h4>
                      <div className="grid grid-cols-2 gap-4 mb-2">
                        <div>
                          <span className="text-sm font-medium text-gray-700">Time: </span>
                          <span className="text-sm font-mono bg-purple-100 text-purple-800 px-2 py-1 rounded">
                            {analysis.time_complexity}
                          </span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-700">Space: </span>
                          <span className="text-sm font-mono bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {analysis.space_complexity}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{analysis.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Issues */}
            {result.data.issues && result.data.issues.length > 0 && (
              <div className="mb-6 bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Issues Found</h3>
                <div className="space-y-3">
                  {result.data.issues.map((issue: any, idx: number) => (
                    <div
                      key={idx}
                      className={`flex items-start p-4 rounded-lg border ${
                        issue.severity === 'error' ? 'bg-red-50 border-red-200' :
                        issue.severity === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                        'bg-blue-50 border-blue-200'
                      }`}
                    >
                      <div className="flex-shrink-0 mr-3">
                        <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                          issue.severity === 'error' ? 'bg-red-500 text-white' :
                          issue.severity === 'warning' ? 'bg-yellow-500 text-white' :
                          'bg-blue-500 text-white'
                        }`}>
                          {issue.severity === 'error' ? '!' : issue.severity === 'warning' ? '⚠' : 'i'}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900">{issue.function || 'General'}</span>
                          <span className="text-xs text-gray-500">Line {issue.line}</span>
                        </div>
                        <p className="text-sm text-gray-700">{issue.message}</p>
                        <span className="text-xs text-gray-500 mt-1 inline-block">
                          Type: {issue.type.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Test Results */}
            {result.data.test_results && (
              <div className={`mb-6 p-6 rounded-lg border-2 ${
                result.data.test_results.failed > 0
                  ? 'bg-red-50 border-red-300'
                  : 'bg-green-50 border-green-300'
              }`}>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  {result.data.test_results.failed > 0 ? (
                    <>
                      <span className="text-2xl mr-2">❌</span>
                      Test Validation Failed
                    </>
                  ) : (
                    <>
                      <span className="text-2xl mr-2">✅</span>
                      All Tests Passed
                    </>
                  )}
                </h3>

                <div className="mb-4 flex items-center space-x-4">
                  <div className="px-4 py-2 bg-white rounded-lg border border-gray-200">
                    <span className="text-sm text-gray-600">Total Tests: </span>
                    <span className="font-bold text-gray-900">{result.data.test_results.total}</span>
                  </div>
                  <div className="px-4 py-2 bg-green-100 rounded-lg border border-green-300">
                    <span className="text-sm text-green-700">Passed: </span>
                    <span className="font-bold text-green-900">{result.data.test_results.passed}</span>
                  </div>
                  <div className="px-4 py-2 bg-red-100 rounded-lg border border-red-300">
                    <span className="text-sm text-red-700">Failed: </span>
                    <span className="font-bold text-red-900">{result.data.test_results.failed}</span>
                  </div>
                </div>

                {/* Test Failures */}
                {result.data.test_results.failures && result.data.test_results.failures.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-red-900">Failed Tests:</h4>
                    {result.data.test_results.failures.map((failure: any, idx: number) => (
                      <div key={idx} className="p-4 bg-white rounded-lg border border-red-200">
                        <div className="text-sm font-medium text-gray-900 mb-2">
                          Test {failure.test_num}: {failure.description}
                        </div>
                        <div className="space-y-1 text-sm font-mono">
                          <div className="text-gray-700">
                            <span className="text-gray-500">Input:</span> {JSON.stringify(failure.input)}
                          </div>
                          <div className="text-red-700">
                            <span className="text-gray-500">Got:</span> {JSON.stringify(failure.got)}
                          </div>
                          <div className="text-green-700">
                            <span className="text-gray-500">Expected:</span> {JSON.stringify(failure.expected)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Execution Errors */}
                {result.data.test_results.errors && result.data.test_results.errors.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <h4 className="text-sm font-semibold text-red-900">Execution Errors:</h4>
                    {result.data.test_results.errors.map((error: any, idx: number) => (
                      <div key={idx} className="p-4 bg-white rounded-lg border border-red-200">
                        <div className="text-sm font-medium text-gray-900 mb-2">
                          Test {error.test_num}: {error.description}
                        </div>
                        <div className="text-sm text-red-700 font-mono">
                          {error.error}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Logic Errors (from LLM Analysis) */}
            {result.data.logic_errors && result.data.logic_errors.length > 0 && (
              <div className="mb-6 p-6 rounded-lg border-2 bg-orange-50 border-orange-300">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="text-2xl mr-2">⚠️</span>
                  Logic Errors Detected (AI Analysis)
                </h3>
                <ul className="space-y-2">
                  {result.data.logic_errors.map((error: string, idx: number) => (
                    <li key={idx} className="flex items-start p-3 bg-white rounded border border-orange-200">
                      <span className="text-orange-500 mr-2 font-bold">•</span>
                      <span className="text-sm text-gray-700">{error}</span>
                    </li>
                  ))}
                </ul>

                {/* Edge Case Failures */}
                {result.data.edge_case_failures && result.data.edge_case_failures.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Edge Cases That May Fail:</h4>
                    <ul className="space-y-2">
                      {result.data.edge_case_failures.map((edge_case: string, idx: number) => (
                        <li key={idx} className="flex items-start p-3 bg-white rounded border border-orange-200">
                          <span className="text-orange-400 mr-2">⚡</span>
                          <span className="text-sm text-gray-700">{edge_case}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Suggestions */}
            {((result.data.rule_suggestions && result.data.rule_suggestions.length > 0) ||
              (result.data.llm_suggestions && result.data.llm_suggestions.length > 0)) && (
              <div className="mb-6 bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Suggestions</h3>

                {/* Rule-based Suggestions */}
                {result.data.rule_suggestions && result.data.rule_suggestions.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Rule-Based</h4>
                    <ul className="space-y-2">
                      {result.data.rule_suggestions.map((suggestion: string, idx: number) => (
                        <li key={idx} className="flex items-start">
                          <span className="text-green-500 mr-2">→</span>
                          <span className="text-sm text-gray-700">{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* AI-powered Suggestions */}
                {result.data.llm_suggestions && result.data.llm_suggestions.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                      <span className="mr-2">AI-Powered</span>
                      <span className="text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white px-2 py-1 rounded">Gemini</span>
                    </h4>
                    <ul className="space-y-2">
                      {result.data.llm_suggestions.map((suggestion: string, idx: number) => (
                        <li key={idx} className="flex items-start">
                          <span className="text-purple-500 mr-2">✨</span>
                          <span className="text-sm text-gray-700">{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Improved Code */}
            <div className="mb-6 bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-lg border-2 border-green-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="text-2xl mr-2">✨</span>
                  Improved Code
                  {getAlgorithmName(result.data) && (
                    <span className="ml-3 text-sm font-normal text-purple-600 bg-purple-100 px-3 py-1 rounded-full">
                      {getAlgorithmName(result.data)}
                    </span>
                  )}
                </h3>
                <button
                  onClick={() => {
                    const improvedCode = getImprovedCode(result.data, code)
                    navigator.clipboard.writeText(improvedCode)
                    setCopiedMain(true)
                    setTimeout(() => setCopiedMain(false), 2000)
                  }}
                  className={`text-sm text-white px-4 py-2 rounded-lg transition-all duration-200 flex items-center ${
                    copiedMain
                      ? 'bg-green-700 scale-95'
                      : 'bg-green-600 hover:bg-green-700 hover:scale-105 active:scale-95'
                  }`}
                >
                  {copiedMain ? (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Copied!
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy Code
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Here's your code with improvements based on the analysis:
              </p>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm text-green-400 font-mono">
                  <code>{getImprovedCode(result.data, code)}</code>
                </pre>
              </div>
              <div className="mt-4 p-3 bg-white rounded border border-green-200">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Applied Improvements:</h4>
                <ul className="text-sm text-gray-700 space-y-1">
                  {result.data.improvements_applied && result.data.improvements_applied.length > 0 ? (
                    result.data.improvements_applied.map((improvement: string, idx: number) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-green-600 mr-2">✓</span>
                        <span>{improvement}</span>
                      </li>
                    ))
                  ) : (
                    <>
                      <li className="flex items-start">
                        <span className="text-green-600 mr-2">✓</span>
                        <span>Code analyzed and reviewed for quality</span>
                      </li>
                      {result.data.issues?.some((i: any) => i.type === 'missing_docstring') && (
                        <li className="flex items-start">
                          <span className="text-green-600 mr-2">✓</span>
                          <span>Added comprehensive docstrings</span>
                        </li>
                      )}
                    </>
                  )}
                </ul>
              </div>
            </div>

            {/* Alternative Solutions */}
            {result.data.alternative_solutions && result.data.alternative_solutions.length > 0 && (
              <div className="mb-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200 overflow-hidden">
                <button
                  onClick={() => setShowAlternatives(!showAlternatives)}
                  className="w-full p-6 flex items-center justify-between hover:bg-purple-100/50 transition-colors"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">🔄</span>
                    <div className="text-left">
                      <h3 className="text-lg font-semibold text-gray-900">Alternative Solutions</h3>
                      <p className="text-sm text-gray-600">Explore different approaches to solve this problem</p>
                    </div>
                  </div>
                  <svg
                    className={`w-6 h-6 text-gray-600 transition-transform duration-300 ${
                      showAlternatives ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                <div
                  className={`transition-all duration-300 ease-in-out ${
                    showAlternatives ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
                  } overflow-hidden`}
                >
                  <div className="px-6 pb-6 space-y-4">
                    {result.data.alternative_solutions.map((solution: any, idx: number) => (
                      <AlternativeSolutionCard key={idx} solution={solution} idx={idx} />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Functions Analyzed */}
            {result.data.functions && result.data.functions.length > 0 && (
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Functions Analyzed</h3>
                <div className="space-y-3">
                  {result.data.functions.map((func: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div>
                        <span className="font-mono font-medium text-gray-900">{func.name}(</span>
                        <span className="font-mono text-gray-600">{func.args.join(', ')}</span>
                        <span className="font-mono font-medium text-gray-900">)</span>
                        {func.decorators && func.decorators.length > 0 && (
                          <span className="ml-2 text-xs text-purple-600">@{func.decorators.join(', @')}</span>
                        )}
                      </div>
                      <div className="text-right text-sm text-gray-500">
                        <div>Complexity: {result.data.complexity?.[func.name] || 'N/A'}</div>
                        <div>{func.body_lines} lines</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
