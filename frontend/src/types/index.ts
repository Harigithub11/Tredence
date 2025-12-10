export interface WorkflowGraph {
  id: number
  name: string
  description: string
  definition: {
    nodes: GraphNode[]
    edges: GraphEdge[]
    entry_point: string
  }
  created_at: string
  updated_at: string
  version: number
  is_active: boolean
}

export interface GraphNode {
  name: string
  tool: string
}

export interface GraphEdge {
  from: string
  to: string
  condition?: string
}

export interface WorkflowRun {
  id: number
  run_id: string
  graph_id: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  initial_state: Record<string, any>
  final_state?: Record<string, any>
  started_at?: string
  completed_at?: string
  total_iterations?: number
  total_execution_time_ms?: number
  error_message?: string
}

export interface ExecutionLog {
  id: number
  run_id: number
  node_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  iteration: number
  execution_time_ms?: number
  timestamp: string
  error_message?: string
}

export interface WebSocketMessage {
  type: string
  timestamp: string
}

export interface StatusUpdateMessage extends WebSocketMessage {
  type: 'status_update'
  run_id: string
  status: string
  current_node?: string
  progress?: number
  started_at?: string
}

export interface NodeCompletedMessage extends WebSocketMessage {
  type: 'node_completed'
  run_id: string
  node_name: string
  duration_ms: number
  output_preview?: Record<string, any>
  iteration: number
  node_status: string
}

export interface WorkflowCompletedMessage extends WebSocketMessage {
  type: 'workflow_completed'
  run_id: string
  status: string
  final_state: Record<string, any>
  total_duration_ms: number
  total_iterations: number
  error_message?: string
}

export interface ProgressUpdateMessage extends WebSocketMessage {
  type: 'progress_update'
  run_id: string
  current_node: string
  completed_nodes: number
  total_nodes: number
  progress_percentage: number
  estimated_time_remaining_ms?: number
}

export interface CodeReviewResult {
  quality_score: number
  issue_count: number
  issues: Array<{
    type: string
    severity: string
    message: string
    line?: number
  }>
  complexity_analysis: Record<string, {
    time_complexity: string
    space_complexity: string
    explanation: string
  }>
  rule_suggestions: string[]
  llm_suggestions?: string[]
  llm_analysis?: string
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  database: boolean
  timestamp: string
}
