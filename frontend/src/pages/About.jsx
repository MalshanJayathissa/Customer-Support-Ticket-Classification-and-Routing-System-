
import { useEffect, useState } from "react";
import "../styles/about.css";

function About() {
  const [health, setHealth] = useState(null);
  const [checking, setChecking] = useState(true);

  // ============================================
  // Fetch Real Backend Health Status
  // ============================================

  useEffect(() => {
    const controller = new AbortController();

    const checkBackend = async () => {
      try {
        const response = await fetch("/api/health", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Backend health check failed: ${response.status}`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setHealth(data);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error("Backend health error:", error);
          setHealth(null);
        }
      } finally {
        if (!controller.signal.aborted) {
          setChecking(false);
        }
      }
    };

    checkBackend();

    return () => {
      controller.abort();
    };
  }, []);

  // ============================================
  // System Status
  // ============================================

  const backendReady = health?.status === "ok";

  const modelReady =
    backendReady && health?.model_loaded === true;

  const modelVersion =
    health?.model_version || "Unavailable";

  return (
    <main className="about-page">
      <div className="about-container">

        {/* Page Heading */}

        <section className="about-heading">
          <p className="page-tag">
            System Information
          </p>

          <h1>
            Customer Support Ticket Classification & Routing
          </h1>

          <p>
            An end-to-end machine learning system developed
            for TensorForge 2.0 Phase 2 to classify customer
            support tickets, predict urgency, and route
            requests to the appropriate support team.
          </p>
        </section>

        {/* ============================================
            System Status Cards
        ============================================ */}

        <section className="system-status">

          <div className="status-card">
            <span>Frontend</span>

            <strong>React + Vite</strong>

            <div className="status-indicator ready">
              Running
            </div>
          </div>

          <div className="status-card">
            <span>Backend API</span>

            <strong>FastAPI</strong>

            <div
              className={`status-indicator ${
                backendReady ? "ready" : "pending"
              }`}
            >
              {checking
                ? "Checking..."
                : backendReady
                ? "Connected"
                : "Unavailable"}
            </div>
          </div>

          <div className="status-card">
            <span>ML Model</span>

            <strong>XLM-RoBERTa</strong>

            <div
              className={`status-indicator ${
                modelReady ? "ready" : "pending"
              }`}
            >
              {checking
                ? "Checking..."
                : modelReady
                ? "Model Loaded"
                : "Not Verified"}
            </div>
          </div>

        </section>

        {/* ============================================
            Architecture and Model Information
        ============================================ */}

        <section className="about-grid">

          <div className="about-card">

            <h2>System Architecture</h2>

            <div className="architecture-flow">

              <div className="architecture-item">
                <span>1</span>

                <div>
                  <strong>React Frontend</strong>

                  <p>
                    Users submit individual customer support
                    tickets or upload CSV datasets.
                  </p>
                </div>
              </div>

              <div className="architecture-arrow">↓</div>

              <div className="architecture-item">
                <span>2</span>

                <div>
                  <strong>FastAPI Backend</strong>

                  <p>
                    Authenticates requests, validates ticket
                    data, and manages prediction jobs.
                  </p>
                </div>
              </div>

              <div className="architecture-arrow">↓</div>

              <div className="architecture-item">
                <span>3</span>

                <div>
                  <strong>ML Inference Pipeline</strong>

                  <p>
                    XLM-RoBERTa performs primary classification.
                    Additional classifiers handle secondary
                    categories and urgency.
                  </p>
                </div>
              </div>

              <div className="architecture-arrow">↓</div>

              <div className="architecture-item">
                <span>4</span>

                <div>
                  <strong>Automatic Ticket Routing</strong>

                  <p>
                    Assigns each ticket to the appropriate
                    support team based on its predicted category.
                  </p>
                </div>
              </div>

            </div>
          </div>

          {/* Model Information */}

          <div className="about-card">

            <h2>Model Information</h2>

            <div className="info-list">

              <div className="info-row">
                <span>Primary Model</span>
                <strong>XLM-RoBERTa</strong>
              </div>

              <div className="info-row">
                <span>Model Version</span>
                <strong>{modelVersion}</strong>
              </div>

              <div className="info-row">
                <span>Primary Categories</span>
                <strong>11</strong>
              </div>

              <div className="info-row">
                <span>Secondary Classifiers</span>
                <strong>Included</strong>
              </div>

              <div className="info-row">
                <span>Urgency Classifier</span>
                <strong>Included</strong>
              </div>

              <div className="info-row">
                <span>Validation Score</span>
                <strong>Not yet published</strong>
              </div>

              <div className="info-row">
                <span>Backend Health</span>

                <strong>
                  {checking
                    ? "Checking..."
                    : backendReady
                    ? "Healthy"
                    : "Not Connected"}
                </strong>
              </div>

            </div>

            <div className="information-note">
              Model status and version are retrieved from
              the live FastAPI health endpoint. Model
              validation metrics will be included once
              verified by the ML development team.
            </div>

          </div>

        </section>

        {/* ============================================
            System Capabilities
        ============================================ */}

        <section className="capabilities-card">

          <div className="capabilities-heading">
            <h2>System Capabilities</h2>

            <p>
              Main features implemented for TensorForge 2.0.
            </p>
          </div>

          <div className="capability-grid">

            <div className="capability-item">
              <strong>Single Prediction</strong>

              <p>
                Classify individual support tickets and
                return predicted categories and confidence.
              </p>
            </div>

            <div className="capability-item">
              <strong>Automatic Routing</strong>

              <p>
                Assign tickets to appropriate support teams
                using the predicted classification.
              </p>
            </div>

            <div className="capability-item">
              <strong>Batch Processing</strong>

              <p>
                Process synchronous batches and asynchronous
                jobs containing up to 5,000 tickets.
              </p>
            </div>

            <div className="capability-item">
              <strong>Analytics Dashboard</strong>

              <p>
                Visualize classification and routing statistics
                from completed predictions in the current
                browser session.
              </p>
            </div>

          </div>

        </section>

      </div>
    </main>
  );
}

export default About;
