export default function WebSources({ sources = [] }) {
  // Render nothing when LangGraph did not use live web search.
  if (sources.length === 0) {
    return null
  }

  return (
    <section>
      <h3 className="mb-3 text-sm font-semibold text-slate-700">
        Live web sources
      </h3>

      <div className="space-y-3">
        {sources.map((source, index) => (
          <article
            key={`${source.url}-${index}`}
            className="rounded-xl border border-blue-200 bg-blue-50 p-4"
          >
            {/* Number and title of the web result */}
            <p className="text-sm font-semibold text-slate-800">
              Web Source {index + 1}: {source.title}
            </p>

            {/* Short text returned by the search engine */}
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {source.snippet}
            </p>

            {/* Open the original source in a new browser tab */}
            {source.url && (
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-block text-sm font-medium
                           text-blue-700 hover:underline"
              >
                Visit source
              </a>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}