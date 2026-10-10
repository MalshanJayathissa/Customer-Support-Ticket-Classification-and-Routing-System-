import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Single ticket prediction
export const predictTicket = async (subject, description) => {
  const response = await api.post("/predict", {
    channel: "email",
    subject: subject.trim(),
    text: description.trim(),
  });

  return response.data;
};

// Batch prediction
export const predictBatch = async (tickets, onProgress) => {
  const prepared = tickets.map((ticket, index) => ({
    ticket_id: String(
      ticket.ticket_id || `WEB-${Date.now()}-${index}`
    ),
    channel: ["email", "chat", "call_transcript"].includes(
      ticket.channel
    )
      ? ticket.channel
      : "email",
    subject: String(ticket.subject || ""),
    text: String(ticket.text || ticket.description || "").trim(),
  }));

  if (prepared.length === 0 || prepared.length > 5000) {
    throw new Error("Upload between 1 and 5,000 tickets.");
  }

  if (prepared.some((ticket) => !ticket.text)) {
    throw new Error("Every ticket must contain text.");
  }

  const formatResults = (predictions, start = 0) =>
    predictions.map((prediction, index) => ({
      ...prediction,
      id: start + index + 1,
      subject: prepared[start + index].subject,
    }));

  // Small batch: 1–100
  if (prepared.length <= 100) {
    onProgress?.("Processing tickets...");

    const { data } = await api.post("/predict/batch", {
      tickets: prepared,
    });

    return formatResults(data.predictions);
  }

  // Medium batch: process in blocks of 100
  if (prepared.length <= 2000) {
    const results = [];

    for (let start = 0; start < prepared.length; start += 100) {
      const chunk = prepared.slice(start, start + 100);

      const { data } = await api.post("/predict/batch", {
        tickets: chunk,
      });

      results.push(...formatResults(data.predictions, start));

      onProgress?.(
        `Processed ${results.length} / ${prepared.length} tickets`
      );
    }

    return results;
  }

  // Large batch: 2,001–5,000
  onProgress?.("Submitting asynchronous batch job...");

  const { data: job } = await api.post("/batch/jobs", {
    tickets: prepared,
  });

  const jobId = job.job_id;

  // Poll the job status
  while (true) {
    const { data: status } = await api.get(
      `/batch/jobs/${jobId}`
    );

    onProgress?.(
      `Job ${status.status}: ${status.processed} / ${status.total}`
    );

    if (status.status === "failed" ||
        status.status === "cancelled") {
      throw new Error(status.error || `Job ${status.status}`);
    }

    if (status.status === "succeeded") {
      break;
    }

    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  // Download all results, 100 per page
  const allPredictions = [];
  let offset = 0;

  while (true) {
    const { data } = await api.get(
      `/batch/jobs/${jobId}/results`,
      {
        params: { offset, limit: 100 },
      }
    );

    allPredictions.push(...data.predictions);

    onProgress?.(
      `Downloading results: ${allPredictions.length} / ${prepared.length}`
    );

    if (data.next_offset == null) {
      break;
    }

    offset = data.next_offset;
  }

  if (allPredictions.length !== prepared.length) {
    throw new Error("Incomplete batch results received.");
  }

  onProgress?.("Batch processing completed.");

  return formatResults(allPredictions);
};