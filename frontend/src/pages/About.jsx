import "../styles/about.css";

function About() {
  return (
    <main className="about-page">

      <div className="about-container">

        <section className="about-heading">
          <p className="page-tag">
            System Information
          </p>

          <h1>
            Customer Support Ticket Classification & Routing
          </h1>

          <p>
            An end-to-end machine learning system developed for
            TensorForge 2.0 Phase 2 to classify customer support
            tickets and route them to the appropriate support team.
          </p>
        </section>

        <section className="system-status">

          <div className="status-card">
            <span>Frontend</span>
            <strong>React</strong>
            <div className="status-indicator ready">
              Ready
            </div>
          </div>

          <div className="status-card">
            <span>Backend API</span>
            <strong>FastAPI</strong>
            <div className="status-indicator pending">
              In Development
            </div>
          </div>

          <div className="status-card">
            <span>ML Model</span>
            <strong>Pending</strong>
            <div className="status-indicator pending">
              In Development
            </div>
          </div>

        </section>

        <section className="about-grid">

          <div className="about-card">

            <h2>System Architecture</h2>

            <div className="architecture-flow">

              <div className="architecture-item">
                <span>1</span>

                <div>
                  <strong>React Frontend</strong>
                  <p>
                    Users submit individual tickets or batch files.
                  </p>
                </div>
              </div>

              <div className="architecture-arrow">
                ↓
              </div>

              <div className="architecture-item">
                <span>2</span>

                <div>
                  <strong>Backend API</strong>
                  <p>
                    Validates requests and handles prediction services.
                  </p>
                </div>
              </div>

              <div className="architecture-arrow">
                ↓
              </div>

              <div className="architecture-item">
                <span>3</span>

                <div>
                  <strong>ML Classification Model</strong>
                  <p>
                    Predicts the appropriate ticket category.
                  </p>
                </div>
              </div>

              <div className="architecture-arrow">
                ↓
              </div>

              <div className="architecture-item">
                <span>4</span>

                <div>
                  <strong>Ticket Routing</strong>
                  <p>
                    Maps the predicted category to the required
                    support team.
                  </p>
                </div>
              </div>

            </div>

          </div>

          <div className="about-card">

            <h2>Model Information</h2>

            <div className="info-list">

              <div className="info-row">
                <span>Model</span>
                <strong>Pending final selection</strong>
              </div>

              <div className="info-row">
                <span>Validation Score</span>
                <strong>Pending</strong>
              </div>

              <div className="info-row">
                <span>Categories</span>
                <strong>Pending</strong>
              </div>

              <div className="info-row">
                <span>Training Status</span>
                <strong>In Development</strong>
              </div>

            </div>

            <div className="information-note">
              Final model information will be updated after model
              training and validation are completed.
            </div>

          </div>

        </section>

        <section className="capabilities-card">

          <div className="capabilities-heading">
            <h2>System Capabilities</h2>

            <p>
              Main capabilities included in the Phase 2 MVP.
            </p>
          </div>

          <div className="capability-grid">

            <div className="capability-item">
              <strong>Single Prediction</strong>

              <p>
                Classify individual customer support tickets.
              </p>
            </div>

            <div className="capability-item">
              <strong>Automatic Routing</strong>

              <p>
                Route tickets based on their predicted category.
              </p>
            </div>

            <div className="capability-item">
              <strong>Batch Processing</strong>

              <p>
                Process multiple support tickets using batch
                prediction.
              </p>
            </div>

            <div className="capability-item">
              <strong>Analytics Dashboard</strong>

              <p>
                Visualize classification and routing activity.
              </p>
            </div>

          </div>

        </section>

      </div>

    </main>
  );
}

export default About;