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
} from "recharts";

import {
  dashboardStats,
  categoryData,
  teamData,
  recentPredictions,
} from "../data/mockDashboardData";

import "../styles/dashboard.css";

const PIE_COLORS = [
  "#2563eb",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#dc2626",
  "#64748b",
];

function Dashboard() {
  return (
    <main className="dashboard-page">
      <div className="dashboard-container">

        <div className="dashboard-heading">
          <div>
            <p className="page-tag">Analytics</p>

            <h1>System Dashboard</h1>

            <p>
              Overview of ticket classification, routing, and prediction
              activity.
            </p>
          </div>

          <span className="demo-badge">
            Demo Data
          </span>
        </div>

        <section className="stats-grid">

          <div className="stat-card">
            <span>Total Predictions</span>
            <strong>
              {dashboardStats.totalPredictions.toLocaleString()}
            </strong>
            <p>Tickets processed</p>
          </div>

          <div className="stat-card">
            <span>Categories</span>
            <strong>{dashboardStats.totalCategories}</strong>
            <p>Ticket categories</p>
          </div>

          <div className="stat-card">
            <span>Average Confidence</span>
            <strong>
              {dashboardStats.averageConfidence}%
            </strong>
            <p>Across predictions</p>
          </div>

          <div className="stat-card">
            <span>Successful Routes</span>
            <strong>
              {dashboardStats.successfulRoutes.toLocaleString()}
            </strong>
            <p>Tickets routed</p>
          </div>

        </section>

        <section className="dashboard-charts">

          <div className="chart-card">
            <div className="chart-header">
              <h2>Tickets by Category</h2>

              <p>
                Distribution of predicted ticket categories.
              </p>
            </div>

            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 12 }}
                  />

                  <YAxis
                    tick={{ fontSize: 12 }}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="value"
                    fill="#2563eb"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <h2>Category Distribution</h2>

              <p>
                Relative distribution of predicted classes.
              </p>
            </div>

            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={105}
                    label={({ name }) => name}
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
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

        </section>

        <section className="team-chart-card">

          <div className="chart-header">
            <h2>Routing by Support Team</h2>

            <p>
              Number of tickets routed to each support team.
            </p>
          </div>

          <div className="team-chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={teamData}
                layout="vertical"
                margin={{
                  left: 30,
                  right: 30,
                }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  horizontal={false}
                />

                <XAxis
                  type="number"
                  tick={{ fontSize: 12 }}
                />

                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={{ fontSize: 12 }}
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

        <section className="recent-card">

          <div className="recent-header">
            <div>
              <h2>Recent Predictions</h2>

              <p>
                Latest customer support ticket classifications.
              </p>
            </div>
          </div>

          <div className="dashboard-table-wrapper">
            <table className="dashboard-table">

              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Subject</th>
                  <th>Category</th>
                  <th>Assigned Team</th>
                  <th>Confidence</th>
                </tr>
              </thead>

              <tbody>
                {recentPredictions.map((prediction) => (
                  <tr key={prediction.id}>

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
                        {prediction.confidence}%
                      </span>
                    </td>

                  </tr>
                ))}
              </tbody>

            </table>
          </div>

        </section>

      </div>
    </main>
  );
}

export default Dashboard;