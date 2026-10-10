function PredictionForm({
  subject,
  setSubject,
  description,
  setDescription,
  onSubmit,
  loading,
}) {
  return (
    <form className="prediction-form" onSubmit={onSubmit}>
      <div className="form-group">
        <label htmlFor="subject">Ticket Subject</label>

        <input
          id="subject"
          type="text"
          placeholder="Example: Unable to access my account"
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="description">Ticket Description</label>

        <textarea
          id="description"
          rows="7"
          placeholder="Describe the customer's issue..."
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          disabled={loading}
        />
      </div>

      <button
        type="submit"
        className="predict-button"
        disabled={loading}
      >
        {loading ? "Classifying..." : "Classify Ticket"}
      </button>
    </form>
  );
}

export default PredictionForm;