'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, askQuestion, getChatHistory, clearChatHistory, logout } from '@/lib/api';

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }
    loadHistory();
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadHistory() {
    try {
      const history = await getChatHistory(50);
      setMessages(history);
    } catch {
      // Ignore history load failure
    } finally {
      setInitialLoading(false);
    }
  }

  async function handleClearHistory() {
    if (!confirm('Clear all chat messages? This cannot be undone.')) return;
    try {
      await clearChatHistory();
      setMessages([]);
    } catch {
      // Ignore clear failure silently
    }
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');

    // Optimistic UI — show user message immediately
    const userMsg = { id: Date.now(), role: 'user', content: question, source_chunks: [] };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await askQuestion(question);
      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        source_chunks: response.sources,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${err.message}`,
        source_chunks: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-logo">Edu Rag</div>
        <nav className="sidebar-nav">
          <button className="nav-link" onClick={() => router.push('/dashboard')}>
            <span className="icon">📄</span> Documents
          </button>
          <button className="nav-link active" onClick={() => router.push('/chat')}>
            <span className="icon">💬</span> Chat
          </button>
          <button className="nav-link" onClick={() => router.push('/quiz')}>
            <span className="icon">🧠</span> Quiz
          </button>
        </nav>
        <button className="nav-link" onClick={() => { logout(); router.push('/login'); }} style={{ marginTop: 'auto' }}>
          <span className="icon">🚪</span> Logout
        </button>
      </aside>

      <main className="main-content">
        <div className="chat-container">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h1 className="page-title" style={{ margin: 0 }}>Chat with your Knowledge Base</h1>
              {messages.length > 0 && (
                <button className="btn btn-danger btn-sm" onClick={handleClearHistory}>
                  🗑 Clear Chat
                </button>
              )}
            </div>
            <p className="page-subtitle" style={{ marginBottom: 20 }}>
              Ask questions about your uploaded documents
            </p>

          <div className="chat-messages">
            {initialLoading ? (
              <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }} /></div>
            ) : messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">💬</div>
                <p className="empty-state-title">No messages yet</p>
                <p>Ask a question about your documents to get started</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`chat-message ${msg.role}`}>
                  <div className={`chat-avatar ${msg.role === 'user' ? 'user-avatar' : 'ai-avatar'}`}>
                    {msg.role === 'user' ? 'U' : 'AI'}
                  </div>
                  <div className="chat-bubble">
                    {msg.content}
                    {msg.source_chunks && msg.source_chunks.length > 0 && (
                      <div style={{ marginTop: 12, paddingTop: 8, borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        📎 {msg.source_chunks.length} source{msg.source_chunks.length > 1 ? 's' : ''} referenced
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="chat-message assistant">
                <div className="chat-avatar ai-avatar">AI</div>
                <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div className="spinner" /> Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-input-area" onSubmit={handleSend}>
            <input
              type="text"
              className="form-input"
              placeholder="Ask a question about your documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
