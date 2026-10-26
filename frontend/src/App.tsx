import { useEffect, useState } from 'react'
import { FileText, FolderOpen, Plus, Search, Trash2, Sparkles, MessageSquare, RefreshCw, Activity, ChevronRight, PanelLeftClose } from 'lucide-react'
import { api, type DocumentDetail, type DocumentItem } from './api'

export default function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selected, setSelected] = useState<DocumentDetail | null>(null)
  const [query, setQuery] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [citations, setCitations] = useState<{source:string; excerpt:string}[]>([])
  const [summary, setSummary] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [backend, setBackend] = useState('checking')

  async function refresh() {
    try {
      const [list, health] = await Promise.all([api.list(), api.health()])
      setDocuments(list)
      setBackend(health.status)
    } catch (e) {
      setBackend('offline')
      setError(e instanceof Error ? e.message : 'Could not connect to backend')
    }
  }
  useEffect(() => { void refresh() }, [])

  async function openDocument(doc: DocumentItem) {
    setError(''); setNotice(''); setAnswer(''); setSummary(''); setCitations([])
    try { setSelected(await api.get(doc.id)) }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not open document') }
  }
  async function upload(file?: File) {
    if (!file) return
    setBusy(true); setError(''); setNotice('')
    try {
      const doc = await api.upload(file)
      await refresh()
      await openDocument(doc)
      setNotice(`Uploaded ${doc.filename}`)
    } catch (e) { setError(e instanceof Error ? e.message : 'Upload failed') }
    finally { setBusy(false) }
  }
  async function removeDocument(doc: DocumentItem) {
    if (!window.confirm(`Delete "${doc.filename}" and its stored content?`)) return
    setError('')
    try {
      await api.remove(doc.id)
      if (selected?.id === doc.id) setSelected(null)
      await refresh()
      setNotice('Document deleted.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Delete failed') }
  }
  async function ask() {
    if (!selected || !question.trim()) return
    setBusy(true); setError(''); setAnswer(''); setCitations([])
    try {
      const result = await api.ask(selected.id, question.trim())
      setAnswer(result.answer); setCitations(result.citations)
    } catch (e) { setError(e instanceof Error ? e.message : 'Question failed') }
    finally { setBusy(false) }
  }
  async function summarize() {
    if (!selected) return
    setBusy(true); setError(''); setSummary('')
    try { setSummary((await api.summarize(selected.id)).summary) }
    catch (e) { setError(e instanceof Error ? e.message : 'Summary failed') }
    finally { setBusy(false) }
  }
  const filtered = documents.filter(d => d.filename.toLowerCase().includes(query.toLowerCase()))
  const formatSize = (n: number) => n < 1024 * 1024 ? `${Math.max(1, Math.round(n/1024))} KB` : `${(n/1024/1024).toFixed(1)} MB`

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={19}/></div><div><strong>documind</strong><small>DOCUMENT INTELLIGENCE</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <button className="nav-item active"><FolderOpen size={17}/> Documents <span className="nav-count">{documents.length}</span></button>
      <button className="nav-item" onClick={() => selected && void summarize()}><Sparkles size={17}/> AI summary</button>
      <div className="sidebar-bottom">
        <div className="status-card"><span className={`status-dot ${backend === 'ok' ? 'online' : ''}`}/><div><strong>{backend === 'ok' ? 'Local backend connected' : backend === 'offline' ? 'Backend unavailable' : 'Connecting to backend'}</strong><small>{backend === 'ok' ? 'Your files stay on this machine' : 'Start the FastAPI server'}</small></div></div>
        <div className="user-chip"><div className="avatar">D</div><div><strong>Local workspace</strong><small>Private development mode</small></div><PanelLeftClose size={16} className="muted-icon"/></div>
      </div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="breadcrumbs">Workspace <ChevronRight size={14}/> <strong>Documents</strong></div><div className="top-actions"><span className="local-pill"><span className="status-dot online"/> LOCAL AI</span><button className="icon-button" title="Refresh documents" onClick={() => void refresh()}><RefreshCw size={17}/></button></div></header>
      <div className="content">
        <div className="page-heading"><div><div className="eyebrow">YOUR KNOWLEDGE, CONNECTED</div><h1>Document workspace</h1><p>Upload a document, explore its contents, and ask your local AI assistant.</p></div><label className="primary-button upload-button"><Plus size={17}/> Upload document<input type="file" accept=".pdf,.docx,.txt" onChange={e => { void upload(e.target.files?.[0]); e.currentTarget.value = '' }} disabled={busy}/></label></div>
        {error && <div className="alert error">{error}</div>}
        {notice && <div className="alert success">{notice}</div>}
        <div className="stats-row"><div className="stat-card"><div className="stat-icon lavender"><FolderOpen size={18}/></div><div><small>Documents</small><strong>{documents.length}</strong></div></div><div className="stat-card"><div className="stat-icon mint"><Activity size={18}/></div><div><small>Processing status</small><strong>{documents.length ? 'Ready to use' : 'Awaiting files'}</strong></div></div><div className="stat-card"><div className="stat-icon peach"><MessageSquare size={18}/></div><div><small>AI engine</small><strong>Local Ollama</strong></div></div></div>
        <div className="workspace-grid">
          <section className="panel library-panel">
            <div className="panel-heading"><div><h2>Document library</h2><p>Your uploaded files, stored locally</p></div><span className="count-pill">{documents.length} files</span></div>
            <div className="search-box"><Search size={16}/><input placeholder="Search your documents..." value={query} onChange={e => setQuery(e.target.value)}/></div>
            {filtered.length === 0 ? <div className="empty-state"><div className="empty-icon"><FileText size={24}/></div><strong>{query ? 'No matching documents' : 'Your library is empty'}</strong><p>{query ? 'Try a different filename.' : 'Upload a PDF, DOCX, or TXT file to get started.'}</p><label className="secondary-button">{query ? 'Clear search' : 'Choose a document'}<input type={query ? 'button' : 'file'} accept=".pdf,.docx,.txt" onClick={query ? () => setQuery('') : undefined} onChange={e => { void upload(e.target.files?.[0]); e.currentTarget.value = '' }} /></label></div> :
              <div className="document-list">{filtered.map(doc => <div key={doc.id} className={`document-row ${selected?.id === doc.id ? 'selected' : ''}`}><button className="document-main" onClick={() => void openDocument(doc)}><div className="file-icon"><FileText size={18}/></div><div className="document-meta"><strong title={doc.filename}>{doc.filename}</strong><small>{formatSize(doc.size_bytes)} · {doc.status === 'needs_ocr' ? 'Text unavailable — OCR needed' : 'Processed'}</small></div></button><button className="delete-button" title={`Delete ${doc.filename}`} onClick={() => void removeDocument(doc)}><Trash2 size={15}/></button></div>)}</div>}
            <div className="panel-footer"><span><span className="status-dot online"/> Local file storage</span><span>Max 25 MB / file</span></div>
          </section>
          <section className="panel detail-panel">
            {!selected ? <div className="detail-empty"><div className="hero-orb"><Sparkles size={26}/></div><h2>Your documents, understood.</h2><p>Select a document from your library to read its extracted text, generate a summary, or ask a question.</p><div className="feature-chips"><span><FileText size={14}/> PDF / DOCX / TXT</span><span><Sparkles size={14}/> Local AI</span></div></div> :
              <><div className="panel-heading detail-heading"><div className="selected-file"><div className="file-icon large"><FileText size={21}/></div><div><h2>{selected.filename}</h2><p>{formatSize(selected.size_bytes)} · {selected.status}</p></div></div><button className="secondary-button small" onClick={() => void summarize()} disabled={busy}><Sparkles size={15}/> Summarize</button></div>
              <div className="document-preview"><div className="preview-toolbar"><span>EXTRACTED TEXT</span><span>{selected.extracted_text.length.toLocaleString()} characters</span></div>{selected.extracted_text ? <pre>{selected.extracted_text}</pre> : <div className="empty-text">No text was extracted. Scanned document OCR is planned for the next phase.</div>}</div>
              {summary && <div className="result-card"><div className="result-title"><Sparkles size={16}/> AI summary</div><div className="result-text">{summary}</div></div>}
              <div className="chat-area"><div className="chat-title"><div><MessageSquare size={17}/><strong>Ask this document</strong></div><span>Answers generated locally</span></div><form className="ask-form" onSubmit={e => { e.preventDefault(); void ask() }}><input value={question} onChange={e => setQuestion(e.target.value)} placeholder="What is this document about?" disabled={busy}/><button className="primary-button" disabled={busy || !question.trim()}>{busy ? 'Working…' : 'Ask AI'}</button></form>
              {answer && <div className="result-card"><div className="result-title"><Sparkles size={16}/> AI answer</div><div className="result-text">{answer}</div>{citations.length > 0 && <div className="citations"><strong>Context sent to model</strong>{citations.map(c => <div key={c.source} className="citation"><small>{c.source}</small><p>{c.excerpt}</p></div>)}</div>}</div>}
              </div></>}
          </section>
        </div>
        <footer className="page-footer"><span>DocuMind AI · Phase 1</span><span>Local-first by design</span></footer>
      </div>
    </main>
  </div>
}
