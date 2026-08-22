// Use a deployment URL from the frontend environment when available.
// During local development, connect to FastAPI on port 8000.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000/api/v1'


// Send an HTTP request and handle successful and failed responses.
async function apiRequest(endpoint, options = {}) {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    options,
  )

  // A successful DELETE response contains no JSON body.
  if (response.status === 204) {
    return null
  }

  // Read the JSON returned by FastAPI.
  const data = await response.json()

  // Convert unsuccessful responses into JavaScript errors.
  if (!response.ok) {
    const errorMessage =
      typeof data.detail === 'string'
        ? data.detail
        : `Request failed with status ${response.status}`

    throw new Error(errorMessage)
  }

  return data
}


// Get all uploaded document records from PostgreSQL.
export function listDocuments() {
  return apiRequest('/documents')
}


// Upload a real PDF file.
//
// FormData is required because FastAPI expects a multipart file
// rather than a JSON request.
export function uploadDocument(file) {
  const formData = new FormData()

  // The field name must match the FastAPI parameter.
  formData.append(
    'uploaded_file',
    file,
  )

  return apiRequest('/documents', {
    method: 'POST',
    body: formData,

    // Do not manually add Content-Type.
    // The browser creates the multipart boundary automatically.
  })
}


// Ask a question and optionally continue an existing conversation.
//
// documentId selects one PDF or remains null for all documents.
//
// conversationId continues a saved LangGraph thread.
// A null value tells FastAPI to create a new conversation.
export function askQuestion(
  question,
  documentId = null,
  conversationId = null,
) {
  return apiRequest('/questions/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      document_id: documentId,
      conversation_id: conversationId,
    }),
  })
}


// Delete a document.
//
// FastAPI will remove:
// 1. its PostgreSQL document record;
// 2. its saved PDF file;
// 3. its Qdrant chunks and embeddings.
export function deleteDocument(documentId) {
  return apiRequest(
    `/documents/${encodeURIComponent(documentId)}`,
    {
      method: 'DELETE',
    },
  )
}

// Get document, question, route and performance statistics
// for the Recharts analytics dashboard.
export function getAnalyticsSummary() {
  return apiRequest('/analytics/summary')
}
// Send retrieval test cases to the backend evaluation endpoint.
//
// `cases` contains questions and the terms we expect Qdrant to retrieve.
// `topK` controls how many similar chunks are checked for each question.
export function runEvaluation(cases, topK = 5) {
  return apiRequest('/evaluation/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      cases,
      top_k: topK,
    }),
  })
}