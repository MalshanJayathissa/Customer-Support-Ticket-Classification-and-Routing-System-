
import { useState } from "react";
import Papa from "papaparse";

import { predictBatch } from "../services/api";
import { recordPredictions } from "../services/analyticsStore";

import "../styles/batch.css";

function BatchPredict() {
  const [file, setFile] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [results, setResults] = useState([]);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobStatus, setJobStatus] = useState("");

  // =====================================================
  // CSV Upload
  // =====================================================

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    setError("");
    setResults([]);
    setTickets([]);
    setFile(null);
    setJobStatus("");

    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Please upload a valid CSV file.");
      return;
    }

    Papa.parse(selectedFile, {
      header: true,
      skipEmptyLines: "greedy",
      transformHeader: (header) => header.trim(),

      complete: (parsed) => {
        if (parsed.errors.length > 0) {
          setError("Unable to parse the CSV file correctly.");
          return;
        }

        const rows = parsed.data;
        const columns = parsed.meta.fields || [];

        if (rows.length === 0) {
          setError("CSV file contains no tickets.");
          return;
        }

        if (rows.length > 5000) {
          setError(
            "Maximum batch size is 5,000 tickets."
          );
          return;
        }

        if (
          !columns.includes("text") &&
          !columns.includes("description")
        ) {
          setError(
            "CSV must contain a 'text' or 'description' column."
          );
          return;
        }

        const invalidIndex = rows.findIndex((ticket) => {
          const text = String(
            ticket.text ?? ticket.description ?? ""
          ).trim();

          return text.length === 0;
        });

        if (invalidIndex !== -1) {
          setError(
            `Ticket ${invalidIndex + 1} has empty text.`
          );
          return;
        }

        setFile(selectedFile);
        setTickets(rows);

        setJobStatus(
          `${rows.length.toLocaleString()} tickets loaded.`
        );
      },

      error: () => {
        setError("Unable to read the selected CSV file.");
      },
    });
  };

  // =====================================================
  // Batch Prediction
  // =====================================================

  const handleBatchPrediction = async () => {
    if (loading) return;

    setError("");
    setResults([]);
    setJobStatus("");

    if (tickets.length === 0) {
      setError("Please upload a CSV file first.");
      return;
    }

    try {
      setLoading(true);

      setJobStatus("Preparing batch prediction...");

      // Existing API service handles:
      // 1-100: synchronous prediction
      // 101-2000: chunked requests
      // 2001-5000: asynchronous jobs

      const predictions = await predictBatch(
        tickets,
        setJobStatus
      );

      if (
        !Array.isArray(predictions) ||
        predictions.length !== tickets.length
      ) {
        throw new Error(
          "The API returned an incomplete set of predictions."
        );
      }

      setResults(predictions);

      // Record real results in session analytics.
      recordPredictions(predictions, tickets);

      setJobStatus(
        `Batch processing completed successfully. ` +
        `${predictions.length.toLocaleString()} tickets processed.`
      );
    } catch (err) {
      console.error("Batch prediction error:", err);

      setError(
        err.response?.data?.error?.message ||
        err.message ||
        "Unable to process the batch."
      );

      setJobStatus("");
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // Download All Results
  // =====================================================

  const downloadResults = () => {
    if (results.length === 0) return;

    const csv = Papa.unparse(results);

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = "ticket_prediction_results.csv";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const processingMethod =
    tickets.length <= 100
      ? "Synchronous Batch Prediction"
      : tickets.length <= 2000
      ? "Chunked Batch Prediction"
      : "Asynchronous Batch Job";

  // =====================================================
  // Page
  // =====================================================

  return (
    <main className="batch-page">
      <div className="batch-container">
        <div className="batch-heading">
          <p className="page-tag">
            Batch Prediction
          </p>

          <h1>Process Multiple Support Tickets</h1>

          <p>
            Upload a CSV file and classify up to 5,000 customer
            support tickets with the trained ML model.
          </p>
        </div>

        {/* Upload area */}

        <section className="upload-card">
          <div className="upload-area">
            <div className="upload-icon">
              ↑
            </div>

            <h3>Upload Ticket Dataset</h3>

            <p>
              Select a CSV file containing customer support tickets.
            </p>

            <p style={{ marginTop: "8px", fontSize: "13px" }}>
              Supports up to 5,000 tickets per upload.
            </p>

            <label className="file-button">
              Choose CSV File

              <input
                type="file"
                accept=".csv,text/csv"
                onChange={handleFileChange}
                disabled={loading}
                hidden
              />
            </label>

            {file && (
              <p className="selected-file">
                Selected: {file.name}
              </p>
            )}
          </div>

          {error && (
            <div className="batch-error" role="alert">
              {error}
            </div>
          )}

          {jobStatus && (
            <div
              role="status"
              aria-live="polite"
              style={{
                marginTop: "15px",
                padding: "15px",
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                borderRadius: "8px",
                color: "#1d4ed8",
                fontSize: "14px",
              }}
            >
              {loading ? "⏳ " : ""}
              {jobStatus}
            </div>
          )}
        </section>

        {/* Dataset Preview */}

        {tickets.length > 0 && (
          <section className="preview-section">
            <div className="section-header">
              <div>
                <h2>Dataset Preview</h2>

                <p>
                  {tickets.length.toLocaleString()} tickets loaded
                </p>
              </div>

              <button
                className="run-batch-button"
                onClick={handleBatchPrediction}
                disabled={loading}
              >
                {loading
                  ? "Processing..."
                  : "Run Batch Prediction"}
              </button>
            </div>

            <div
              style={{
                marginBottom: "20px",
                padding: "12px 15px",
                background: "#f8fafc",
                borderRadius: "8px",
                color: "#475569",
                fontSize: "13px",
              }}
            >
              <strong>Processing Method: </strong>
              {processingMethod}
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    {Object.keys(tickets[0]).map((column) => (
                      <th key={column}>
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {tickets.slice(0, 10).map((ticket, index) => (
                    <tr key={index}>
                      {Object.keys(tickets[0]).map((column) => (
                        <td key={column}>
                          {ticket[column]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {tickets.length > 10 && (
              <p className="preview-note">
                Showing first 10 of{" "}
                {tickets.length.toLocaleString()} tickets.
              </p>
            )}
          </section>
        )}

        {/* Prediction Results */}

        {results.length > 0 && (
          <section className="results-section">
            <div className="section-header">
              <div>
                <h2>Prediction Results</h2>

                <p>
                  {results.length.toLocaleString()} tickets processed
                  successfully.
                </p>
              </div>

              <button
                className="download-button"
                onClick={downloadResults}
              >
                Download All Results
              </button>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Ticket ID</th>
                    <th>Subject</th>
                    <th>Category</th>
                    <th>Assigned Team</th>
                    <th>Confidence</th>
                    <th>Urgent</th>
                  </tr>
                </thead>

                <tbody>
                  {results.slice(0, 100).map((result, index) => (
                    <tr key={`${result.ticket_id || index}-${index}`}>
                      <td>{index + 1}</td>

                      <td>{result.ticket_id || "—"}</td>

                      <td>{result.subject || "—"}</td>

                      <td>
                        <span className="category-badge">
                          {result.category}
                        </span>
                      </td>

                      <td>{result.team || "—"}</td>

                      <td>
                        {typeof result.confidence === "number"
                          ? `${(result.confidence * 100).toFixed(1)}%`
                          : "—"}
                      </td>

                      <td>
                        {result.is_urgent ? "Yes" : "No"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {results.length > 100 && (
              <p className="preview-note">
                Showing first 100 of{" "}
                {results.length.toLocaleString()} results.
                Download the CSV to view every prediction.
              </p>
            )}
          </section>
        )}
      </div>
    </main>
  );
}

export default BatchPredict;
