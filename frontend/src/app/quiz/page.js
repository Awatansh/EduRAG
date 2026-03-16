'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  isAuthenticated, listDocuments, generateQuiz, listQuizzes,
  getQuiz, submitQuiz, logout
} from '@/lib/api';

export default function QuizPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState([]);
  const [quizzes, setQuizzes] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [quizType, setQuizType] = useState('mcq');
  const [numQuestions, setNumQuestions] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }
    loadData();
  }, [router]);

  async function loadData() {
    try {
      const [docsData, quizzesData] = await Promise.all([
        listDocuments(),
        listQuizzes(),
      ]);
      setDocuments(docsData.documents.filter(d => d.status === 'completed'));
      setQuizzes(quizzesData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleDoc(id) {
    setSelectedDocs(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    );
  }

  async function handleGenerate() {
    if (selectedDocs.length === 0) {
      setError('Select at least one document');
      return;
    }
    setGenerating(true);
    setError('');
    try {
      const quiz = await generateQuiz(selectedDocs, quizType, numQuestions);
      setActiveQuiz(quiz);
      setAnswers({});
      setSubmitted(false);
      await loadData(); // refresh quiz list
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSubmit() {
    if (!activeQuiz) return;
    try {
      const updated = await submitQuiz(activeQuiz.id, answers);
      setActiveQuiz(updated);
      setSubmitted(true);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleViewQuiz(id) {
    try {
      const quiz = await getQuiz(id);
      setActiveQuiz(quiz);
      setSubmitted(!!quiz.submitted_at);
      setAnswers({});
    } catch (err) {
      setError(err.message);
    }
  }

  // ── Render Active Quiz ──────────────────────────────────
  if (activeQuiz) {
    const questions = Array.isArray(activeQuiz.questions) ? activeQuiz.questions : [];

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
            <button className="nav-link active" onClick={() => router.push('/quiz')}>
              <span className="icon">🧠</span> Quiz
            </button>
          </nav>
        </aside>

        <main className="main-content">
          <button className="btn btn-secondary btn-sm" onClick={() => setActiveQuiz(null)} style={{ marginBottom: 24 }}>
            ← Back to Quizzes
          </button>

          <h1 className="page-title">{activeQuiz.title || 'Quiz'}</h1>

          {submitted && activeQuiz.score != null && (
            <div className="quiz-score card" style={{ margin: '24px 0' }}>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>Your Score</p>
              <div className="quiz-score-value">{activeQuiz.score}%</div>
            </div>
          )}

          {questions.map((q, i) => (
            <div key={i} className="quiz-question card fade-in" style={{ marginBottom: 16 }}>
              <div className="quiz-question-text">
                {i + 1}. {q.question}
              </div>
              {q.options && (
                <div className="quiz-options">
                  {q.options.map((opt, j) => {
                    let className = 'quiz-option';
                    if (answers[String(i)] === opt) className += ' selected';
                    if (submitted && opt === q.correct_answer) className += ' correct';
                    if (submitted && answers[String(i)] === opt && opt !== q.correct_answer) className += ' incorrect';
                    return (
                      <div
                        key={j}
                        className={className}
                        onClick={() => !submitted && setAnswers(prev => ({ ...prev, [String(i)]: opt }))}
                      >
                        <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>
                          {String.fromCharCode(65 + j)}.
                        </span>
                        {opt}
                      </div>
                    );
                  })}
                </div>
              )}
              {submitted && q.explanation && (
                <p style={{ marginTop: 12, fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                  💡 {q.explanation}
                </p>
              )}
            </div>
          ))}

          {!submitted && questions.length > 0 && (
            <button className="btn btn-primary btn-lg" onClick={handleSubmit} style={{ marginTop: 16 }}>
              Submit Quiz
            </button>
          )}
        </main>
      </div>
    );
  }

  // ── Render Quiz Generator ───────────────────────────────
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
          <button className="nav-link active" onClick={() => router.push('/quiz')}>
            <span className="icon">🧠</span> Quiz
          </button>
        </nav>
        <button className="nav-link" onClick={() => { logout(); router.push('/login'); }} style={{ marginTop: 'auto' }}>
          <span className="icon">🚪</span> Logout
        </button>
      </aside>

      <main className="main-content">
        <h1 className="page-title" style={{ marginBottom: 24 }}>Quiz Generator</h1>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }} /></div>
        ) : (
          <>
            {/* Generate new quiz */}
            <div className="card" style={{ marginBottom: 32 }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 16 }}>Generate New Quiz</h2>

              <div className="form-group">
                <label className="form-label">Select Documents</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {documents.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      No processed documents available. Upload and process documents first.
                    </p>
                  ) : (
                    documents.map((doc) => (
                      <label
                        key={doc.id}
                        className={`quiz-option ${selectedDocs.includes(doc.id) ? 'selected' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedDocs.includes(doc.id)}
                          onChange={() => toggleDoc(doc.id)}
                          style={{ accentColor: 'var(--accent-primary)' }}
                        />
                        {doc.filename}
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 16 }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label className="form-label">Quiz Type</label>
                  <select className="form-select" value={quizType} onChange={(e) => setQuizType(e.target.value)}>
                    <option value="mcq">Multiple Choice</option>
                    <option value="true_false">True / False</option>
                    <option value="short_answer">Short Answer</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label className="form-label">Number of Questions</label>
                  <input
                    type="number"
                    className="form-input"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
                    min={1} max={20}
                  />
                </div>
              </div>

              <button
                className="btn btn-primary"
                onClick={handleGenerate}
                disabled={generating || selectedDocs.length === 0}
              >
                {generating ? <><span className="spinner" /> Generating...</> : '🧠 Generate Quiz'}
              </button>
            </div>

            {/* Past quizzes */}
            {quizzes.length > 0 && (
              <>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 16 }}>Past Quizzes</h2>
                <div className="doc-grid">
                  {quizzes.map((quiz) => (
                    <div
                      key={quiz.id}
                      className="card doc-card"
                      onClick={() => handleViewQuiz(quiz.id)}
                    >
                      <div className="doc-filename">{quiz.title || 'Quiz'}</div>
                      <div className="doc-meta">
                        <span>{quiz.quiz_type.toUpperCase()}</span>
                        <span>{quiz.num_questions} questions</span>
                        {quiz.score != null && <span>Score: {quiz.score}%</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
