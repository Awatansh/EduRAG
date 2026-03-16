/**
 * API client for KB Agent backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Get stored auth token.
 */
function getToken() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('kb_agent_token');
  }
  return null;
}

/**
 * Set auth token.
 */
function setToken(token) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('kb_agent_token', token);
  }
}

/**
 * Clear auth token.
 */
function clearToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('kb_agent_token');
  }
}

/**
 * Make an authenticated API request.
 */
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser will set multipart boundary)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }

  if (res.status === 204) return null;
  return res.json();
}

// ── Auth API ──────────────────────────────────────────────

export async function register(email, password, fullName) {
  const data = await apiFetch('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  return data;
}

export async function login(email, password) {
  const data = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function getMe() {
  return apiFetch('/api/auth/me');
}

export function logout() {
  clearToken();
}

export function isAuthenticated() {
  return !!getToken();
}

// ── Documents API ─────────────────────────────────────────

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch('/api/documents/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function listDocuments() {
  return apiFetch('/api/documents');
}

export async function getDocument(id) {
  return apiFetch(`/api/documents/${id}`);
}

export async function getDocumentStatus(id) {
  return apiFetch(`/api/documents/${id}/status`);
}

export async function deleteDocument(id) {
  return apiFetch(`/api/documents/${id}`, { method: 'DELETE' });
}

// ── Query API ─────────────────────────────────────────────

export async function askQuestion(question, documentIds = null, topK = 5) {
  return apiFetch('/api/query/ask', {
    method: 'POST',
    body: JSON.stringify({
      question,
      document_ids: documentIds,
      top_k: topK,
    }),
  });
}

export async function getChatHistory(limit = 50) {
  return apiFetch(`/api/query/history?limit=${limit}`);
}

// ── Quiz API ──────────────────────────────────────────────

export async function generateQuiz(documentIds, quizType = 'mcq', numQuestions = 5) {
  return apiFetch('/api/quiz/generate', {
    method: 'POST',
    body: JSON.stringify({
      document_ids: documentIds,
      quiz_type: quizType,
      num_questions: numQuestions,
    }),
  });
}

export async function listQuizzes() {
  return apiFetch('/api/quiz');
}

export async function getQuiz(id) {
  return apiFetch(`/api/quiz/${id}`);
}

export async function submitQuiz(id, answers) {
  return apiFetch(`/api/quiz/${id}/submit`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  });
}
