const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export type DocumentItem = {
  id: number
  filename: string
  content_type: string
  size_bytes: number
  status: string
  created_at: string
}
export type DocumentDetail = DocumentItem & { extracted_text: string }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || message
    } catch { /* non-JSON error body */ }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
export const api = {
  health: () => request<{status: string}>('/api/health'),
  list: () => request<DocumentItem[]>('/api/documents'),
  get: (id: number) => request<DocumentDetail>(`/api/documents/${id}`),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<DocumentItem>('/api/documents', { method: 'POST', body: form })
  },
  remove: (id: number) => request<void>(`/api/documents/${id}`, { method: 'DELETE' }),
  ask: (id: number, question: string) =>
    request<{answer: string; citations: {source: string; excerpt: string}[]}>(`/api/documents/${id}/ask`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question}),
    }),
  summarize: (id: number) =>
    request<{summary: string}>(`/api/documents/${id}/summarize`, { method: 'POST' }),
}
