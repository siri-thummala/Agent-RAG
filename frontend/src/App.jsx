// React hooks store application data and run startup logic.
import { useEffect, useMemo, useState } from 'react'

// Frontend components.
import AnalyticsDashboard from './components/AnalyticsDashboard'
import ChatPanel from './components/ChatPanel'
import DocumentPanel from './components/DocumentPanel'

// Functions that communicate with FastAPI.
import {
  askQuestion,
  deleteDocument,
  listDocuments,
  uploadDocument,
} from './services/api'


export default function App() {
  // Documents returned by PostgreSQL.
  const [documents, setDocuments] = useState([])

  // null means search across every uploaded document.
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)

  // LangGraph thread ID used to continue the same conversation.
  const [conversationId, setConversationId] = useState(null)

  // Latest question, answer, route and sources.
  const [result, setResult] = useState(null)

  // Readable API error.
  const [error, setError] = useState('')

  // Loading states prevent repeated requests.
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isAsking, setIsAsking] = useState(false)

  // Controls whether the chat or analytics dashboard is visible.
  const [showAnalytics, setShowAnalytics] = useState(false)


  // Load documents when the application first opens.
  useEffect(() => {
    let ignoreResult = false

    async function loadInitialDocuments() {
      try {
        const documentData = await listDocuments()

        if (!ignoreResult) {
          setDocuments(documentData)
        }
      } catch (requestError) {
        if (!ignoreResult) {
          setError(requestError.message)
        }
      } finally {
        if (!ignoreResult) {
          setIsLoadingDocuments(false)
        }
      }
    }

    loadInitialDocuments()

    // Ignore a late API result if the component has been removed.
    return () => {
      ignoreResult = true
    }
  }, [])


  // Refresh the document list after uploading or deleting.
  async function refreshDocuments() {
    const documentData = await listDocuments()
    setDocuments(documentData)
  }


  // Find the filename of the currently selected document.
  const selectedDocumentName = useMemo(() => {
    if (selectedDocumentId === null) {
      return null
    }

    const selectedDocument = documents.find(
      (document) => document.id === selectedDocumentId,
    )

    return selectedDocument?.filename || null
  }, [documents, selectedDocumentId])


  async function handleUploadDocument(file) {
    try {
      setError('')
      setIsUploading(true)

      // FastAPI processes and indexes the uploaded PDF.
      const uploadedDocument = await uploadDocument(file)

      await refreshDocuments()

      // Select the newly uploaded PDF automatically.
      setSelectedDocumentId(uploadedDocument.id)

      // A new document begins a separate conversation.
      setConversationId(null)
      setResult(null)
    } catch (requestError) {
      setError(requestError.message)

      // Keep the selected file visible if uploading fails.
      throw requestError
    } finally {
      setIsUploading(false)
    }
  }


  async function handleDeleteDocument(documentId) {
    try {
      setError('')

      await deleteDocument(documentId)

      // Reset the chat if its selected document was deleted.
      if (selectedDocumentId === documentId) {
        setSelectedDocumentId(null)
        setConversationId(null)
        setResult(null)
      }

      await refreshDocuments()
    } catch (requestError) {
      setError(requestError.message)
    }
  }


  async function handleAskQuestion(question) {
    try {
      setError('')
      setIsAsking(true)

      // Send the existing conversation ID.
      // It is null only for the first question in a new chat.
      const response = await askQuestion(
        question,
        selectedDocumentId,
        conversationId,
      )

      // Remember the ID returned by FastAPI.
      // Follow-up questions reuse the same ID.
      setConversationId(
        response.conversation_id,
      )

      setResult({
        question,
        answer: response.answer,
        route: response.route,
        sources: response.sources,
        webSources: response.web_sources,
      })
    } catch (requestError) {
      setResult(null)
      setError(requestError.message)
    } finally {
      setIsAsking(false)
    }
  }


  function handleSelectDocument(documentId) {
    setSelectedDocumentId(documentId)

    // Changing the search scope begins a new conversation.
    setConversationId(null)
    setResult(null)
    setError('')
  }


  function handleNewConversation() {
    // Keep the selected document but begin a new LangGraph thread.
    setConversationId(null)
    setResult(null)
    setError('')
  }


  // Replace the chat interface with the dashboard when selected.
  if (showAnalytics) {
    return (
      <AnalyticsDashboard
        onBack={() => setShowAnalytics(false)}
      />
    )
  }


  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-50">
      {/* Application header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-slate-950 px-6 py-4 text-white">
        <div>
          <h1 className="text-lg font-bold tracking-tight">
            Agentic RAG
          </h1>

          <p className="text-xs text-slate-400">
            Document intelligence platform
          </p>
        </div>


        <div className="flex items-center gap-4">
          {/* Shows whether the current chat has persistent memory */}
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <span
              className={`h-2 w-2 rounded-full ${
                conversationId
                  ? 'bg-indigo-400'
                  : 'bg-slate-500'
              }`}
            />

            {conversationId
              ? 'Memory active'
              : 'New conversation'}
          </div>


          {/* Open the Recharts dashboard */}
          <button
            type="button"
            onClick={() => setShowAnalytics(true)}
            className="rounded-lg border border-slate-700 px-3 py-2
                       text-xs font-semibold text-slate-200 transition
                       hover:border-slate-500 hover:bg-slate-800"
          >
            Analytics
          </button>


          {/* Begin a separate LangGraph conversation */}
          <button
            type="button"
            onClick={handleNewConversation}
            className="rounded-lg border border-slate-700 px-3 py-2
                       text-xs font-semibold text-slate-200 transition
                       hover:border-slate-500 hover:bg-slate-800"
          >
            New chat
          </button>
        </div>
      </header>


      {/* Main application layout */}
      <div className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[320px_minmax(0,1fr)] md:grid-rows-[minmax(0,1fr)]">
        <DocumentPanel
          documents={documents}
          selectedDocumentId={selectedDocumentId}
          isUploading={isUploading}
          onSelectDocument={handleSelectDocument}
          onUploadDocument={handleUploadDocument}
          onDeleteDocument={handleDeleteDocument}
        />

        {isLoadingDocuments ? (
          <div className="flex items-center justify-center text-sm text-slate-500">
            Loading documents...
          </div>
        ) : (
          <ChatPanel
            selectedDocumentName={selectedDocumentName}
            result={result}
            error={error}
            isAsking={isAsking}
            onAskQuestion={handleAskQuestion}
          />
        )}
      </div>
    </div>
  )
}