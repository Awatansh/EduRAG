'use client';
import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { isAuthenticated, getDocument, getDocumentStatus } from '@/lib/api';

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pollRef = useRef(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }
    loadDocument();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [params.id, router]);

  async function loadDocument() {
    try {
      const data = await getDocument(params.id);
      setDoc(data);

      // Poll status if still processing
      if (data.status === 'pending' || data.status === 'processing') {
        pollRef.current = setInterval(async () => {
          const status = await getDocumentStatus(params.id);
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollRef.current);
            const updated = await getDocument(params.id);
            setDoc(updated);
          }
        }, 3000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function formatBytes(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  if (loading) return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-logo">KB Agent</div>
      </aside>
      <main className="main-content">
        <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }} /></div>
      </main>
    </div>
  );

  if (error) return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-logo">KB Agent</div>
      </aside>
      <main className="main-content">
        <div className="alert alert-error">{error}</div>
      </main>
    </div>
  );

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-logo">KB Agent</div>
        <nav className="sidebar-nav">
          <button className="nav-link" onClick={() => router.push('/dashboard')}>
            <span className="icon">📄</span> Documents
          </button>
          <button className="nav-link" onClick={() => router.push('/chat')}>
            <span className="icon">💬</span> Chat
          </button>
          <button className="nav-link" onClick={() => router.push('/quiz')}>
            <span className="icon">🧠</span> Quiz
          </button>
        </nav>
      </aside>

      <main className="main-content">
        <button className="btn btn-secondary btn-sm" onClick={() => router.back()} style={{ marginBottom: 24 }}>
          ← Back
        </button>

        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 className="page-title">{doc.filename}</h1>
              <div className="doc-meta" style={{ marginTop: 8 }}>
                <span>{doc.file_type.toUpperCase()}</span>
                <span>{formatBytes(doc.file_size_bytes)}</span>
                {doc.page_count && <span>{doc.page_count} pages</span>}
              </div>
            </div>
            <span className={`badge badge-${doc.status}`}>{doc.status}</span>
          </div>

          {doc.error_message && (
            <div className="alert alert-error" style={{ marginTop: 16 }}>{doc.error_message}</div>
          )}

          {(doc.status === 'pending' || doc.status === 'processing') && (
            <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}>
              <div className="spinner" /> Processing document...
            </div>
          )}
        </div>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: 16 }}>Document Info</h2>
        <div className="card">
          <table style={{ width: '100%', fontSize: '0.9rem' }}>
            <tbody>
              <tr>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)', width: 160 }}>Document ID</td>
                <td style={{ padding: '8px 0', fontFamily: 'monospace', fontSize: '0.8rem' }}>{doc.id}</td>
              </tr>
              <tr>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)' }}>Type</td>
                <td style={{ padding: '8px 0' }}>{doc.file_type}</td>
              </tr>
              <tr>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)' }}>Size</td>
                <td style={{ padding: '8px 0' }}>{formatBytes(doc.file_size_bytes)}</td>
              </tr>
              <tr>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)' }}>Status</td>
                <td style={{ padding: '8px 0' }}>{doc.status}</td>
              </tr>
              <tr>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)' }}>Uploaded</td>
                <td style={{ padding: '8px 0' }}>{new Date(doc.created_at).toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
