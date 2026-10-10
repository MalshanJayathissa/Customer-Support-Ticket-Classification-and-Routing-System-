function ResultCard({ result }) {
  if (!result) {
    return null;
  }

  return (
    <div className="result-card">
      <div className="result-header">
        <div>
          <p className="result-label">Prediction Result</p>
          <h2>Ticket Classified Successfully</h2>
        </div>

        <span className="status-badge">Classified</span>
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
          <strong>
            {(result.confidence * 100).toFixed(1)}%
          </strong>
        </div>
      </div>
    </div>
  );
}

export default ResultCard;