// React stores the evaluation form and returned results.
import { useState } from 'react'

// Calls the FastAPI retrieval-evaluation endpoint.
import { runEvaluation } from '../services/api'


export default function EvaluationPanel() {
  // Each case contains:
  // 1. a question;
  // 2. terms that should appear in the retrieved PDF chunks.
  const [cases, setCases] = useState([
    {
      question: '',
      expectedTerms: '',
    },
  ])

  // Number of Qdrant chunks checked for every question.
  const [topK, setTopK] = useState(5)

  // Stores the evaluation response returned by FastAPI.
  const [result, setResult] = useState(null)

  // Used to show loading and error messages.
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState('')


  // Update one field belonging to one evaluation case.
  function updateCase(index, field, value) {
    setCases((currentCases) =>
      currentCases.map((testCase, caseIndex) =>
        caseIndex === index
          ? {
              ...testCase,
              [field]: value,
            }
          : testCase,
      ),
    )
  }


  // Add another question to the evaluation.
  function addCase() {
    setCases((currentCases) => [
      ...currentCases,
      {
        question: '',
        expectedTerms: '',
      },
    ])
  }


  // Remove one test case.
  function removeCase(index) {
    setCases((currentCases) =>
      currentCases.filter(
        (_, caseIndex) => caseIndex !== index,
      ),
    )
  }


  // Run all entered test cases through the backend evaluator.
  async function handleRunEvaluation(event) {
    event.preventDefault()

    // Convert comma-separated text such as:
    // "XGBoost, 70%"
    // into:
    // ["XGBoost", "70%"]
    const preparedCases = cases.map((testCase) => ({
      question: testCase.question.trim(),
      expected_terms: testCase.expectedTerms
        .split(',')
        .map((term) => term.trim())
        .filter(Boolean),

      // Null means search across all uploaded PDFs.
      document_id: null,
    }))


    // Every case requires a question and at least one expected term.
    const hasInvalidCase = preparedCases.some(
      (testCase) =>
        !testCase.question
        || testCase.expected_terms.length === 0,
    )

    if (hasInvalidCase) {
      setError(
        'Every test case needs a question and at least one expected term.',
      )
      return
    }


    try {
      setError('')
      setIsRunning(true)
      setResult(null)

      const evaluationResult = await runEvaluation(
        preparedCases,
        Number(topK),
      )

      setResult(evaluationResult)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsRunning(false)
    }
  }


  return (
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h2 className="text-base font-semibold text-slate-900">
          Retrieval evaluation
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Test whether Qdrant retrieves PDF chunks containing
          the expected information.
        </p>
      </div>


      <form
        onSubmit={handleRunEvaluation}
        className="mt-5 space-y-4"
      >
        {cases.map((testCase, index) => (
          <div
            key={index}
            className="rounded-xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-700">
                Test case {index + 1}
              </p>

              {cases.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeCase(index)}
                  className="text-sm font-medium text-red-600 hover:text-red-700"
                >
                  Remove
                </button>
              )}
            </div>


            <label className="mt-4 block">
              <span className="text-sm font-medium text-slate-700">
                Question
              </span>

              <input
                type="text"
                value={testCase.question}
                onChange={(event) =>
                  updateCase(
                    index,
                    'question',
                    event.target.value,
                  )
                }
                placeholder="Which model achieved the best accuracy?"
                className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
            </label>


            <label className="mt-4 block">
              <span className="text-sm font-medium text-slate-700">
                Expected terms
              </span>

              <input
                type="text"
                value={testCase.expectedTerms}
                onChange={(event) =>
                  updateCase(
                    index,
                    'expectedTerms',
                    event.target.value,
                  )
                }
                placeholder="XGBoost, 70%"
                className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />

              <span className="mt-1 block text-xs text-slate-400">
                Separate multiple expected terms with commas.
              </span>
            </label>
          </div>
        ))}


        <div className="flex flex-wrap items-end justify-between gap-4">
          <button
            type="button"
            onClick={addCase}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Add test case
          </button>


          <div className="flex items-end gap-3">
            <label>
              <span className="block text-xs font-medium text-slate-500">
                Chunks per question
              </span>

              <select
                value={topK}
                onChange={(event) =>
                  setTopK(Number(event.target.value))
                }
                className="mt-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
              </select>
            </label>

            <button
              type="submit"
              disabled={isRunning}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {isRunning
                ? 'Running...'
                : 'Run evaluation'}
            </button>
          </div>
        </div>
      </form>


      {error && (
        <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
          {error}
        </p>
      )}


      {result && (
        <div className="mt-6">
          {/* Overall evaluation measurements */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <ResultCard
              title="Passed cases"
              value={`${result.passed_cases}/${result.total_cases}`}
            />

            <ResultCard
              title="Hit rate"
              value={`${result.hit_rate.toFixed(1)}%`}
            />

            <ResultCard
              title="Mean reciprocal rank"
              value={result.mean_reciprocal_rank.toFixed(3)}
            />

            <ResultCard
              title="Average similarity"
              value={
                result.average_top_similarity === null
                  ? 'No result'
                  : result.average_top_similarity.toFixed(3)
              }
            />
          </div>


          {/* Result for each individual question */}
          <div className="mt-5 space-y-3">
            {result.results.map((caseResult, index) => (
              <article
                key={`${caseResult.question}-${index}`}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <p className="font-medium text-slate-800">
                    {caseResult.question}
                  </p>

                  <span
                    className={
                      caseResult.passed
                        ? 'rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700'
                        : 'rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700'
                    }
                  >
                    {caseResult.passed
                      ? 'Passed'
                      : 'Failed'}
                  </span>
                </div>

                <p className="mt-3 text-sm text-slate-500">
                  Found:{' '}
                  {caseResult.found_terms.length > 0
                    ? caseResult.found_terms.join(', ')
                    : 'None'}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  Missing:{' '}
                  {caseResult.missing_terms.length > 0
                    ? caseResult.missing_terms.join(', ')
                    : 'None'}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  Top similarity:{' '}
                  {caseResult.top_similarity_score === null
                    ? 'No result'
                    : caseResult.top_similarity_score.toFixed(3)}
                  {' · '}
                  Reciprocal rank:{' '}
                  {caseResult.reciprocal_rank.toFixed(3)}
                </p>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}


// Small reusable card for one evaluation measurement.
function ResultCard({
  title,
  value,
}) {
  return (
    <article className="rounded-xl bg-slate-50 p-4">
      <p className="text-xs font-medium text-slate-500">
        {title}
      </p>

      <p className="mt-2 text-2xl font-bold text-slate-900">
        {value}
      </p>
    </article>
  )
}