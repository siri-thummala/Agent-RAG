// React hooks load and store analytics data.
import { useEffect, useState } from 'react'

// Recharts components used by the dashboard.
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

// Frontend API function.
import { getAnalyticsSummary } from '../services/api'

// Interactive Qdrant retrieval-evaluation section.
import EvaluationPanel from './EvaluationPanel'


// Colors used for LangGraph routes.
const ROUTE_COLORS = {
  document: '#4f46e5',
  web: '#0284c7',
  both: '#7c3aed',
}


// Reusable card for displaying one analytics measurement.
function MetricCard({
  title,
  value,
  description,
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">
        {title}
      </p>

      <p className="mt-2 text-3xl font-bold text-slate-900">
        {value}
      </p>

      <p className="mt-2 text-xs text-slate-400">
        {description}
      </p>
    </article>
  )
}


export default function AnalyticsDashboard({
  onBack,
}) {
  // Dashboard response returned by FastAPI.
  const [analytics, setAnalytics] = useState(null)

  // Loading and error states.
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')


  // Request the latest analytics measurements from FastAPI.
  async function loadAnalytics() {
    try {
      setError('')
      setIsLoading(true)

      const analyticsData =
        await getAnalyticsSummary()

      setAnalytics(analyticsData)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }


  // Load dashboard data when this component first opens.
  useEffect(() => {
    loadAnalytics()
  }, [])


  // Show a loading screen while the request is running.
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">
        Loading analytics...
      </div>
    )
  }


  // Show an error and retry button if analytics could not load.
  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-slate-50">
        <p className="text-sm text-red-600">
          {error}
        </p>

        <button
          type="button"
          onClick={loadAnalytics}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Try again
        </button>
      </div>
    )
  }


  // Add readable names and colors to route data.
  const routeChartData =
    analytics.route_distribution.map(
      (item) => ({
        ...item,
        name:
          item.route.charAt(0).toUpperCase()
          + item.route.slice(1),
        fill: ROUTE_COLORS[item.route],
      }),
    )


  return (
    <div className="min-h-screen bg-slate-50">
      {/* Dashboard header */}
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-slate-950 px-6 py-4 text-white">
        <div>
          <h1 className="text-lg font-bold">
            RAG Analytics
          </h1>

          <p className="text-xs text-slate-400">
            Retrieval and workflow performance
          </p>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={loadAnalytics}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold hover:bg-slate-800"
          >
            Refresh
          </button>

          <button
            type="button"
            onClick={onBack}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold hover:bg-indigo-500"
          >
            Back to chat
          </button>
        </div>
      </header>


      <main className="mx-auto max-w-7xl p-6">
        {/* Main statistics */}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Total documents"
            value={analytics.total_documents}
            description={`${analytics.ready_documents} ready for retrieval`}
          />

          <MetricCard
            title="Questions"
            value={analytics.total_questions}
            description="Successfully processed RAG requests"
          />

          <MetricCard
            title="Conversations"
            value={analytics.total_conversations}
            description="Persistent LangGraph threads"
          />

          <MetricCard
            title="Average response"
            value={`${analytics.average_response_time_ms.toFixed(0)} ms`}
            description="End-to-end workflow processing time"
          />
        </section>


        {/* Retrieval-quality card */}
        <section className="mt-4">
          <MetricCard
            title="Average retrieval similarity"
            value={
              analytics.average_similarity_score === null
                ? 'No data'
                : analytics.average_similarity_score.toFixed(3)
            }
            description="Average strongest Qdrant document match"
          />
        </section>


        {/* Recharts visualizations */}
        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* LangGraph route distribution */}
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">
              LangGraph route usage
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Document, web and combined workflow decisions
            </p>

            <div className="mt-5 h-80">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <PieChart>
                  <Pie
                    data={routeChartData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {routeChartData.map((entry) => (
                      <Cell
                        key={entry.route}
                        fill={entry.fill}
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </article>


          {/* Daily question activity */}
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">
              Question activity
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Successful questions during the last 14 days
            </p>

            <div className="mt-5 h-80">
              {analytics.daily_questions.length === 0 ? (
                <div className="flex h-full items-center justify-center text-sm text-slate-400">
                  Ask a question to create activity data.
                </div>
              ) : (
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <BarChart
                    data={analytics.daily_questions}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#e2e8f0"
                    />

                    <XAxis
                      dataKey="date"
                      tick={{
                        fontSize: 12,
                      }}
                    />

                    <YAxis
                      allowDecimals={false}
                      tick={{
                        fontSize: 12,
                      }}
                    />

                    <Tooltip />

                    <Bar
                      dataKey="count"
                      name="Questions"
                      fill="#4f46e5"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </article>
        </section>


        {/* Run retrieval-quality test cases from the dashboard. */}
        <EvaluationPanel />
      </main>
    </div>
  )
}
