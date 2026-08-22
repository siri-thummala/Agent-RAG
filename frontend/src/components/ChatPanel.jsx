// React state remembers what the user types into the question box.
import { useState } from 'react'

// Displays citations returned by live web search.
import WebSources from './WebSources'


export default function ChatPanel({
  selectedDocumentName,
  result,
  error,
  isAsking,
  onAskQuestion,
}) {
  // Store the current question typed by the user.
  const [question, setQuestion] = useState('')


  async function handleSubmit(event) {
    // Prevent the browser from refreshing the page.
    event.preventDefault()

    const cleanedQuestion = question.trim()

    // The backend requires at least three characters.
    if (cleanedQuestion.length < 3 || isAsking) {
      return
    }

    // The parent App component performs the API request.
    await onAskQuestion(cleanedQuestion)
  }


  // Convert backend route names into readable labels.
  const routeLabels = {
    document: 'PDF documents',
    web: 'Live web',
    both: 'PDF + live web',
  }


  return (
    <main className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-slate-50">
      {/* Top bar showing the current search scope */}
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Searching within
        </p>

        <h2 className="mt-1 truncate text-base font-semibold text-slate-900">
          {selectedDocumentName || 'All documents'}
        </h2>
      </header>


      {/* Scrollable answer area */}
      <section className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-4xl">
          {/* Initial message shown before the first question */}
          {!result && !error && (
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100 text-xl">
                ✦
              </div>

              <h1 className="mt-4 text-2xl font-bold text-slate-900">
                Ask your documents
              </h1>

              <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
                Ask about your uploaded PDFs or request current information
                from the live web.
              </p>
            </div>
          )}


          {/* Display API errors without crashing the interface */}
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}


          {/* Display the latest question and generated answer */}
          {result && (
            <div className="space-y-5">
              {/* User question */}
              <div className="ml-auto max-w-2xl rounded-2xl rounded-br-sm bg-indigo-600 px-5 py-4 text-white shadow-sm">
                <p className="text-sm leading-6">
                  {result.question}
                </p>
              </div>


              {/* Gemini answer */}
              <article className="rounded-2xl rounded-bl-sm border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                    Grounded answer
                  </p>

                  {/* Show the branch selected by LangGraph */}
                  {result.route && (
                    <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
                      {routeLabels[result.route] || result.route}
                    </span>
                  )}
                </div>

                <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                  {result.answer}
                </p>
              </article>


              {/* Retrieved Qdrant document chunks */}
              {(result.sources?.length || 0) > 0 && (
                <section>
                  <h3 className="mb-3 text-sm font-semibold text-slate-700">
                    Retrieved document sources
                  </h3>

                  <div className="space-y-3">
                    {result.sources.map((source, index) => (
                      <details
                        key={`${source.document_id}-${source.chunk_index}-${index}`}
                        className="rounded-xl border border-slate-200 bg-white shadow-sm"
                      >
                        <summary className="cursor-pointer list-none px-4 py-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div>
                              <span className="text-sm font-semibold text-slate-800">
                                Document Source {index + 1}
                              </span>

                              <span className="ml-2 text-sm text-slate-500">
                                {source.filename}, page {source.page_number}
                              </span>
                            </div>

                            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                              Score: {Number(source.score).toFixed(3)}
                            </span>
                          </div>
                        </summary>

                        <div className="border-t border-slate-100 px-4 py-4">
                          <p className="whitespace-pre-wrap text-sm leading-6 text-slate-600">
                            {source.text}
                          </p>
                        </div>
                      </details>
                    ))}
                  </div>
                </section>
              )}


              {/* Live web-search results */}
              <WebSources
                sources={result.webSources || []}
              />
            </div>
          )}
        </div>
      </section>


      {/* Question input stays at the bottom of the page */}
      <footer className="border-t border-slate-200 bg-white p-4">
        <form
          onSubmit={handleSubmit}
          className="mx-auto flex max-w-4xl gap-3"
        >
          <textarea
            value={question}
            disabled={isAsking}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about your PDFs or current web information..."
            rows="2"
            className="min-h-14 flex-1 resize-none rounded-xl border
                       border-slate-300 bg-white px-4 py-3 text-sm
                       text-slate-800 outline-none transition
                       placeholder:text-slate-400 focus:border-indigo-500
                       focus:ring-2 focus:ring-indigo-100
                       disabled:bg-slate-100"
          />

          <button
            type="submit"
            disabled={question.trim().length < 3 || isAsking}
            className="self-stretch rounded-xl bg-indigo-600 px-6
                       text-sm font-semibold text-white transition
                       hover:bg-indigo-700 disabled:cursor-not-allowed
                       disabled:bg-slate-300"
          >
            {isAsking ? 'Thinking...' : 'Ask'}
          </button>
        </form>
      </footer>
    </main>
  )
}