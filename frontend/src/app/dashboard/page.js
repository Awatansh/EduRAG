'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, listDocuments, uploadDocument, deleteDocument, logout } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }
    loadDocuments();
  }, [router]);

  async function loadDocuments() {
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      await uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this document and all its chunks?')) return;
    try {
      await deleteDocument(id);
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    }
  }

  function handleLogout() {
    logout();
    router.push('/login');
  }

  function formatBytes(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
    });
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">Edu Rag</div>
        <nav className="sidebar-nav">
          <button className="nav-link active" onClick={() => router.push('/dashboard')}>
            <span className="icon">📄</span> Documents
          </button>
          <button className="nav-link" onClick={() => router.push('/chat')}>
            <span className="icon">💬</span> Chat
          </button>
          <button className="nav-link" onClick={() => router.push('/quiz')}>
            <span className="icon">🧠</span> Quiz
          </button>
        </nav>
        <button className="nav-link" onClick={handleLogout} style={{ marginTop: 'auto' }}>
          <span className="icon">🚪</span> Logout
        </button>
      </aside>

      {/* Main */}
      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">Your Documents</h1>
            <p className="page-subtitle">{total} document{total !== 1 ? 's' : ''} uploaded</p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.mp4,.mp3,.wav"
              onChange={handleUpload}
              style={{ display: 'none' }}
              id="file-upload"
            />
            <button
              className="btn btn-primary"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? <><span className="spinner" /> Uploading...</> : '+ Upload Document'}
            </button>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }} /></div>
        ) : documents.length === 0 ? (
          <div
            className="upload-area"
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-icon">📁</div>
            <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>
              Drop files here or click to upload
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Supports PDF, Images (PNG, JPEG, TIFF), Video (MP4), Audio (MP3, WAV)
            </p>
          </div>
        ) : (
          <div className="doc-grid">
            {documents.map((doc) => (
              <div key={doc.id} className="card doc-card fade-in">
                <div className="doc-card-header">
                  <span className="doc-filename">{doc.filename}</span>
                  <span className={`badge badge-${doc.status}`}>{doc.status}</span>
                </div>
                <div className="doc-meta">
                  <span>{doc.file_type.toUpperCase()}</span>
                  <span>{formatBytes(doc.file_size_bytes)}</span>
                  <span>{formatDate(doc.created_at)}</span>
                </div>
                <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => router.push(`/documents/${doc.id}`)}
                  >
                    View
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(doc.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
