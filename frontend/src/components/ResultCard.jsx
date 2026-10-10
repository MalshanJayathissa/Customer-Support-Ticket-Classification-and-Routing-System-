
function ResultCard({ result }) {
  if (!result) {
    return null;
  }

  const confidence = Number(result.confidence);
  const confidenceText = Number.isFinite(confidence)
    ? `${(confidence * 100).toFixed(1)}%`
    : "Unavailable";

  const needsReview = result.needs_human_review === true;

  return (
    <div className="result-card">
      <div className="result-header">
        <div>
          <p className="result-label">Prediction Result</p>
          <h2>Ticket Classification</h2>
        </div>

        <span className="status-badge">
          {needsReview ? "Review Required" : "Classified"}
        </span>
      </div>

      <div className="result-grid">
        <div className="result-item">
          <span>Category</span>
          <strong>{result.category}</strong>
        </div>

        <div className="result-item">
          <span>Assigned Team</span>
          <strong>{result.team}</strong>
        </div>

        <div className="result-item">
          <span>Confidence</span>
          <strong>{confidenceText}</strong>
        </div>

        <div className="result-item">
          <span>Urgency</span>
          <strong>{result.is_urgent ? "Urgent" : "Normal"}</strong>
        </div>

        {result.secondary_category && (
          <div className="result-item">
            <span>Secondary Category</span>
            <strong>{result.secondary_category}</strong>
          </div>
        )}

        {result.ticket_id && (
          <div className="result-item">
            <span>Ticket ID</span>
            <strong>{result.ticket_id}</strong>
          </div>
        )}
      </div>

      {needsReview && (
        <p className="error-message">
          The model's confidence is below the configured threshold.
          Please review this classification before routing the ticket.
        </p>
      )}

      <p className="result-label">
        Model version: {result.model_version ?? "Unknown"}
      </p>
    </div>
  );
}

export default ResultCard;
