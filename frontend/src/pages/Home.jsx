import { Link } from "react-router-dom";
import "../styles/home.css";

function Home() {
  return (
    <main className="home">
      <section className="hero">
        <p className="hero-tag">TensorForge 2.0 — Phase 2</p>

        <h1>
          Customer Support Ticket
          <span> Classification & Routing</span>
        </h1>

        <p className="hero-description">
          Automatically classify customer support tickets and route them
          to the appropriate support team using machine learning.
        </p>

        <div className="hero-buttons">
          <Link to="/predict" className="primary-button">
            Classify a Ticket
          </Link>

          <Link to="/dashboard" className="secondary-button">
            View Dashboard
          </Link>
        </div>
      </section>

      <section className="features">
        <div className="feature-card">
          <h3>Ticket Classification</h3>
          <p>
            Automatically identify the appropriate category for incoming
            customer support requests.
          </p>
        </div>

        <div className="feature-card">
          <h3>Smart Routing</h3>
          <p>
            Route classified tickets to the appropriate support team.
          </p>
        </div>

        <div className="feature-card">
          <h3>Batch Processing</h3>
          <p>
            Process multiple customer support tickets efficiently using
            batch prediction.
          </p>
        </div>
      </section>
    </main>
  );
}

export default Home;