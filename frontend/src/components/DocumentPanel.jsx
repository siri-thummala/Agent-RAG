// React state is used to remember the PDF selected in the file input.
import { useState } from 'react'


export default function DocumentPanel({
  documents,
  selectedDocumentId,
  isUploading,
  onSelectDocument,
  onUploadDocument,
  onDeleteDocument,
}) {
  // Store the PDF currently selected from the user's computer.
  const [selectedFile, setSelectedFile] = useState(null)


  async function handleUpload(event) {
    // Prevent the browser from refreshing when the form is submitted.
    event.preventDefault()

    if (!selectedFile) {
      return
    }

    // The parent App component performs the real API request.
    await onUploadDocument(selectedFile)

    // Clear the selected file after a successful upload.
    setSelectedFile(null)

    // Reset the visible file input.
    event.target.reset()
  }


  function handleDelete(document) {
    // Ask for confirmation because deletion also removes the PDF
    // and its Qdrant embeddings.
    const shouldDelete = window.confirm(
      `Delete "${document.filename}" permanently?`,
    )

    if (shouldDelete) {
      onDeleteDocument(document.id)
    }
  }


  return (
    <aside className="flex h-full flex-col border-r border-slate-200 bg-white">
      {/* Document-panel heading */}
      <div className="border-b border-slate-200 px-5 py-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Documents
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Upload PDFs and select where to search.
        </p>
      </div>


      {/* PDF upload form */}
      <form
        onSubmit={handleUpload}
        className="border-b border-slate-200 p-5"
      >
        <label
          htmlFor="pdf-upload"
          className="mb-2 block text-sm font-medium text-slate-700"
        >
          Choose a PDF
        </label>

        <input
          id="pdf-upload"
          type="file"
          accept="application/pdf,.pdf"
          disabled={isUploading}
          onChange={(event) => {
            setSelectedFile(event.target.files?.[0] || null)
          }}
          className="block w-full cursor-pointer rounded-lg border
                     border-slate-300 bg-slate-50 text-sm text-slate-600
                     file:mr-3 file:border-0 file:bg-slate-200
                     file:px-3 file:py-2 file:font-medium
                     file:text-slate-700 hover:file:bg-slate-300"
        />

        <button
          type="submit"
          disabled={!selectedFile || isUploading}
          className="mt-3 w-full rounded-lg bg-indigo-600 px-4 py-2.5
                     text-sm font-semibold text-white transition
                     hover:bg-indigo-700 disabled:cursor-not-allowed
                     disabled:bg-slate-300"
        >
          {isUploading ? 'Processing PDF...' : 'Upload PDF'}
        </button>
      </form>


      {/* Scrollable document list */}
      <div className="flex-1 overflow-y-auto p-3">
        {/* Search across every uploaded document */}
        <button
          type="button"
          onClick={() => onSelectDocument(null)}
          className={`mb-2 w-full rounded-lg px-3 py-3 text-left transition ${
            selectedDocumentId === null
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-slate-700 hover:bg-slate-100'
          }`}
        >
          <p className="text-sm font-semibold">
            All documents
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Search across every ready PDF
          </p>
        </button>


        {/* Show a helpful message before any PDF has been uploaded */}
        {documents.length === 0 && (
          <p className="px-3 py-8 text-center text-sm text-slate-500">
            No documents uploaded yet.
          </p>
        )}


        {/* Create one selectable item for every uploaded document */}
        {documents.map((document) => (
          <div
            key={document.id}
            className={`mb-2 rounded-lg border transition ${
              selectedDocumentId === document.id
                ? 'border-indigo-300 bg-indigo-50'
                : 'border-transparent hover:bg-slate-100'
            }`}
          >
            <button
              type="button"
              onClick={() => onSelectDocument(document.id)}
              className="w-full px-3 pb-2 pt-3 text-left"
            >
              <p className="truncate text-sm font-medium text-slate-800">
                {document.filename}
              </p>

              <div className="mt-2 flex items-center justify-between">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    document.status === 'ready'
                      ? 'bg-emerald-100 text-emerald-700'
                      : document.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {document.status}
                </span>

                <span className="text-xs text-slate-400">
                  {new Date(document.created_at).toLocaleDateString()}
                </span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleDelete(document)}
              className="mx-3 mb-3 text-xs font-medium text-red-600
                         hover:text-red-700"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </aside>
  )
}