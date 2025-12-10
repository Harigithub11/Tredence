import axios from 'axios'
import type { WorkflowGraph, WorkflowRun, HealthResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiClient = {
  // Health check
  health: async (): Promise<HealthResponse> => {
    const { data } = await api.get<HealthResponse>('/health')
    return data
  },

  // Graph operations
  graphs: {
    list: async (): Promise<WorkflowGraph[]> => {
      // Note: This endpoint doesn't exist yet, will return empty array
      try {
        const { data } = await api.get<WorkflowGraph[]>('/graph/')
        return data
      } catch {
        return []
      }
    },

    get: async (id: number): Promise<WorkflowGraph> => {
      const { data } = await api.get<WorkflowGraph>(`/graph/${id}`)
      return data
    },

    getByName: async (name: string): Promise<WorkflowGraph> => {
      const { data } = await api.get<WorkflowGraph>(`/graph/name/${name}`)
      return data
    },

    create: async (graph: Omit<WorkflowGraph, 'id' | 'created_at' | 'updated_at' | 'version' | 'is_active'>): Promise<WorkflowGraph> => {
      const { data } = await api.post<WorkflowGraph>('/graph/create', graph)
      return data
    },

    delete: async (id: number): Promise<void> => {
      await api.delete(`/graph/${id}`)
    },
  },

  // Workflow run operations
  runs: {
    execute: async (graphName: string, initialState: Record<string, any>, useLLM: boolean = false): Promise<WorkflowRun> => {
      const { data } = await api.post<WorkflowRun>('/graph/run', {
        graph_name: graphName,
        initial_state: initialState,
        timeout: 300,
        use_llm: useLLM,
      })
      return data
    },

    getState: async (runId: string): Promise<WorkflowRun & { execution_logs: any[] }> => {
      const { data } = await api.get(`/graph/state/${runId}`)
      return data
    },
  },
}

export default apiClient
