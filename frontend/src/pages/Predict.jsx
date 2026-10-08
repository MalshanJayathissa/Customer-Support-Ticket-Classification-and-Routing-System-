import { useState } from "react";

import PredictionForm from "../components/PredictionForm";
import ResultCard from "../components/ResultCard";
import { predictTicket } from "../services/mockApi";

import "../styles/predict.css";

function Predict() {
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setResult(null);

    if (!subject.trim() || !description.trim()) {
      setError("Please enter both the ticket subject and description.");
      return;
    }

    try {
      setLoading(true);

      const prediction = await predictTicket(
        subject,
        description
      );

      setResult(prediction);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to classify the ticket. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="predict-page">
      <div className="predict-container">

        <div className="predict-heading">
          <p className="page-tag">Single Prediction</p>

          <h1>Classify a Support Ticket</h1>

          <p>
            Enter the customer support request below to classify
            the ticket and determine the appropriate routing team.
          </p>
        </div>

        <div className="prediction-layout">

          <div className="form-card">
            <PredictionForm
              subject={subject}
              setSubject={setSubject}
              description={description}
              setDescription={setDescription}
              onSubmit={handleSubmit}
              loading={loading}
            />

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>

          <div className="prediction-result-area">
            {result ? (
              <ResultCard result={result} />
            ) : (
              <div className="empty-result">
                <div className="empty-icon">↗</div>

                <h3>Prediction Result</h3>

                <p>
                  Submit a support ticket to view its predicted
                  category and routing information.
                </p>
              </div>
            )}
          </div>

        </div>

      </div>
    </main>
  );
}

export default Predict;