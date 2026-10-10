import { useState } from "react";
import Papa from "papaparse";

import { predictBatch } from "../services/mockApi";

import "../styles/batch.css";

function BatchPredict() {
  const [file, setFile] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [results, setResults] = useState([]);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    setError("");
    setResults([]);
    setTickets([]);

    if (!selectedFile) {
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Please upload a valid CSV file.");
      setFile(null);
      return;
    }

    setFile(selectedFile);

    Papa.parse(selectedFile, {
      header: true,
      skipEmptyLines: true,

      complete: (result) => {
        if (result.errors.length > 0) {
          setError("There was a problem reading the CSV file.");
          return;
        }

        const parsedTickets = result.data;

        if (parsedTickets.length === 0) {
          setError("The uploaded CSV file does not contain any tickets.");
          return;
        }

        setTickets(parsedTickets);
      },

      error: () => {
        setError("Unable to read the selected CSV file.");
      },
    });
  };

  const handleBatchPrediction = async () => {
    setError("");
    setResults([]);

    if (tickets.length === 0) {
      setError("Please upload a CSV file first.");
      return;
    }

    try {
      setLoading(true);

      const predictions = await predictBatch(tickets);

      setResults(predictions);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to process the batch. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const downloadResults = () => {
    if (results.length === 0) {
      return;
    }

    const csv = Papa.unparse(results);

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.setAttribute(
      "download",
      "ticket_prediction_results.csv"
    );

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  return (
    <main className="batch-page">
      <div className="batch-container">

        <div className="batch-heading">
          <p className="page-tag">Batch Prediction</p>

          <h1>Process Multiple Support Tickets</h1>

          <p>
            Upload a CSV file containing customer support tickets,
            preview the data, and run batch classification.
          </p>
        </div>

        <section className="upload-card">
          <div className="upload-area">

            <div className="upload-icon">
              ↑
            </div>

            <h3>Upload Ticket Dataset</h3>

            <p>
              Select a CSV file containing customer support tickets.
            </p>

            <label className="file-button">
              Choose CSV File

              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
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
            <div className="batch-error">
              {error}
            </div>
          )}
        </section>

        {tickets.length > 0 && (
          <section className="preview-section">

            <div className="section-header">

              <div>
                <h2>Dataset Preview</h2>

                <p>
                  {tickets.length} ticket
                  {tickets.length !== 1 ? "s" : ""} loaded
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
                Showing the first 10 of {tickets.length} tickets.
              </p>
            )}

          </section>
        )}

        {results.length > 0 && (
          <section className="results-section">

            <div className="section-header">

              <div>
                <h2>Prediction Results</h2>

                <p>
                  Successfully processed {results.length} tickets.
                </p>
              </div>

              <button
                className="download-button"
                onClick={downloadResults}
              >
                Download Results
              </button>

            </div>

            <div className="table-wrapper">

              <table className="data-table">

                <thead>
                  <tr>
                    <th>#</th>
                    <th>Subject</th>
                    <th>Category</th>
                    <th>Assigned Team</th>
                    <th>Confidence</th>
                  </tr>
                </thead>

                <tbody>
                  {results.map((result) => (
                    <tr key={result.id}>

                      <td>{result.id}</td>

                      <td>
                        {result.subject || "—"}
                      </td>

                      <td>
                        <span className="category-badge">
                          {result.category}
                        </span>
                      </td>

                      <td>{result.team}</td>

                      <td>
                        {(result.confidence * 100).toFixed(1)}%
                      </td>

                    </tr>
                  ))}
                </tbody>

              </table>

            </div>

          </section>
        )}

      </div>
    </main>
  );
}

export default BatchPredict;