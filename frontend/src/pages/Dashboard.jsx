
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import {
  useAnalytics,
  resetAnalytics,
} from "../services/analyticsStore";

import "../styles/dashboard.css";

const PIE_COLORS = [
  "#2563eb",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#dc2626",
  "#64748b",
  "#0891b2",
  "#db2777",
  "#65a30d",
  "#9333ea",
  "#0f766e",
];

function Dashboard() {
  const analytics = useAnalytics();

  const total = analytics.totalPredictions;

  const categoryData = Object.entries(
    analytics.categories
  )
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const teamData = Object.entries(analytics.teams)
    .map(([name, tickets]) => ({ name, tickets }))
    .sort((a, b) => b.tickets - a.tickets);

  const averageConfidence =
    analytics.confidenceCount > 0
      ? (
          (analytics.confidenceSum /
            analytics.confidenceCount) *
          100
        ).toFixed(1)
      : null;

  const recentPredictions = analytics.recentPredictions;

  return (
    <main className="dashboard-page">
      <div className="dashboard-container">

        {/* Heading */}

        <div className="dashboard-heading">
          <div>
            <p className="page-tag">
              Analytics
            </p>

            <h1>System Dashboard</h1>

            <p>
              Classification and routing statistics calculated
              from real model predictions in this browser session.
            </p>
          </div>

          <span className="demo-badge">
            Session Analytics
          </span>
        </div>

        <p
          style={{
            marginBottom: "25px",
            color: "#64748b",
            fontSize: "13px",
            lineHeight: "1.6",
          }}
        >
          These statistics include predictions made since this
          page was loaded. They reset on a full browser refresh.
          They are not model validation scores or server-wide metrics.
        </p>

        {/* Summary Cards */}

        <section className="stats-grid">
          <div className="stat-card">
            <span>Total Predictions</span>

            <strong>
              {total.toLocaleString()}
            </strong>

            <p>Predictions completed in this session</p>
          </div>

          <div className="stat-card">
            <span>Categories Observed</span>

            <strong>
              {categoryData.length}
            </strong>

            <p>Distinct predicted categories</p>
          </div>

          <div className="stat-card">
            <span>Average Confidence</span>

            <strong>
              {averageConfidence === null
                ? "—"
                : `${averageConfidence}%`}
            </strong>

            <p>Mean prediction confidence</p>
          </div>

          <div className="stat-card">
            <span>Tickets Assigned</span>

            <strong>
              {analytics.assignedCount.toLocaleString()}
            </strong>

            <p>Predictions with an assigned team</p>
          </div>
        </section>

        {total === 0 ? (
          <section className="recent-card">
            <div
              style={{
                textAlign: "center",
                padding: "55px 20px",
              }}
            >
              <h2 style={{ marginBottom: "12px" }}>
                No Predictions Yet
              </h2>

              <p
                style={{
                  color: "#64748b",
                  lineHeight: "1.7",
                }}
              >
                Run a single prediction or batch prediction,
                then return to this dashboard to view actual
                classification and routing statistics.
              </p>
            </div>
          </section>
        ) : (
          <>
            {/* Category Charts */}

            <section className="dashboard-charts">
              <div className="chart-card">
                <div className="chart-header">
                  <h2>Tickets by Category</h2>

                  <p>
                    Actual predicted category counts.
                  </p>
                </div>

                <div
                  className="chart-area"
                  style={{
                    height: Math.max(
                      340,
                      categoryData.length * 35
                    ),
                  }}
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={categoryData}
                      layout="vertical"
                      margin={{
                        left: 5,
                        right: 25,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        horizontal={false}
                      />

                      <XAxis
                        type="number"
                        allowDecimals={false}
                      />

                      <YAxis
                        type="category"
                        dataKey="name"
                        width={155}
                        tick={{ fontSize: 11 }}
                      />

                      <Tooltip />

                      <Bar
                        dataKey="value"
                        name="Tickets"
                        fill="#2563eb"
                        radius={[0, 6, 6, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-card">
                <div className="chart-header">
                  <h2>Category Distribution</h2>

                  <p>
                    Relative distribution of predicted categories.
                  </p>
                </div>

                <div
                  className="chart-area"
                  style={{ height: 420 }}
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="43%"
                        outerRadius={95}
                      >
                        {categoryData.map((entry, index) => (
                          <Cell
                            key={entry.name}
                            fill={
                              PIE_COLORS[
                                index % PIE_COLORS.length
                              ]
                            }
                          />
                        ))}
                      </Pie>

                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>

            {/* Team Routing Chart */}

            <section className="team-chart-card">
              <div className="chart-header">
                <h2>Routing by Support Team</h2>

                <p>
                  Tickets assigned to each support team.
                </p>
              </div>

              <div
                className="team-chart-area"
                style={{
                  height: Math.max(
                    340,
                    teamData.length * 36
                  ),
                }}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={teamData}
                    layout="vertical"
                    margin={{
                      left: 15,
                      right: 30,
                    }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                    />

                    <XAxis
                      type="number"
                      allowDecimals={false}
                    />

                    <YAxis
                      type="category"
                      dataKey="name"
                      width={180}
                      tick={{ fontSize: 11 }}
                    />

                    <Tooltip />

                    <Bar
                      dataKey="tickets"
                      fill="#111827"
                      radius={[0, 6, 6, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Recent Predictions */}

            <section className="recent-card">
              <div className="recent-header">
                <h2>Recent Predictions</h2>

                <p>
                  Latest real model predictions in this session.
                </p>
              </div>

              <div className="dashboard-table-wrapper">
                <table className="dashboard-table">
                  <thead>
                    <tr>
                      <th>Ticket ID</th>
                      <th>Subject</th>
                      <th>Category</th>
                      <th>Assigned Team</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>

                  <tbody>
                    {recentPredictions.map((prediction, index) => (
                      <tr key={`${prediction.id}-${index}`}>
                        <td className="ticket-id">
                          {prediction.id}
                        </td>

                        <td>
                          {prediction.subject}
                        </td>

                        <td>
                          <span className="dashboard-category">
                            {prediction.category}
                          </span>
                        </td>

                        <td>
                          {prediction.team}
                        </td>

                        <td>
                          <span className="confidence-value">
                            {prediction.confidence === null
                              ? "—"
                              : `${(
                                  prediction.confidence * 100
                                ).toFixed(1)}%`}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {/* Reset Session */}

        {total > 0 && (
          <div style={{ textAlign: "right", marginTop: "20px" }}>
            <button
              type="button"
              onClick={() => {
                if (
                  window.confirm(
                    "Clear analytics recorded in this browser session?"
                  )
                ) {
                  resetAnalytics();
                }
              }}
              style={{
                padding: "11px 18px",
                border: "1px solid #cbd5e1",
                borderRadius: "8px",
                background: "white",
                color: "#334155",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              Clear Session Analytics
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

export default Dashboard;
