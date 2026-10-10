
const API_BASE = "/api";
const MAX_BATCH_SIZE = 5000;

function createRequestId() {
  return globalThis.crypto?.randomUUID?.()
    ?? `request-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

// Handle successful responses and structured backend errors.
async function parseResponse(response) {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error?.message
      ?? data?.detail
      ?? `Request failed with HTTP ${response.status}.`
    );
  }

  return data;
}

function normalizeChannel(value) {
  const channel = String(value ?? "email").trim().toLowerCase();

  if (["email", "chat", "call_transcript"].includes(channel)) {
    return channel;
  }

  throw new Error(
    `Unsupported channel "${channel}". Use email, chat, or call_transcript.`
  );
}

// Single-ticket prediction.
export async function predictTicket(subject, description) {
  const response = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": createRequestId(),
    },
    body: JSON.stringify({
      channel: "email",
      subject: subject.trim(),
      text: description.trim(),
    }),
  });

  return parseResponse(response);
}

// Normalize CSV columns into the backend's expected schema.
function normalizeTickets(tickets) {
  if (tickets.length === 0) {
    throw new Error("The CSV file contains no tickets.");
  }

  if (tickets.length > MAX_BATCH_SIZE) {
    throw new Error(`A maximum of ${MAX_BATCH_SIZE} tickets is supported.`);
  }

  const seenIds = new Set();

  return tickets.map((ticket, index) => {
    const ticketId = String(
      ticket.ticket_id ?? ticket.id ?? `TICKET-${index + 1}`
    ).trim();

    const subject = String(ticket.subject ?? "").trim();
    const text = String(
      ticket.text ?? ticket.description ?? ticket.message ?? ""
    ).trim();

    if (!ticketId) {
      throw new Error(`Ticket ${index + 1} has an empty ticket ID.`);
    }

    if (seenIds.has(ticketId)) {
      throw new Error(`Duplicate ticket ID: ${ticketId}`);
    }

    if (!text) {
      throw new Error(
        `Ticket ${ticketId} needs a text, description, or message column.`
      );
    }

    seenIds.add(ticketId);

    return {
      ticket_id: ticketId,
      channel: normalizeChannel(ticket.channel),
      subject,
      text,
    };
  });
}

// Submit the batch, poll until completion, then retrieve its results.
export async function predictBatch(tickets) {
  const normalizedTickets = normalizeTickets(tickets);
  const requestId = createRequestId();

  const createResponse = await fetch(`${API_BASE}/batch/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
      "Idempotency-Key": requestId,
    },
    body: JSON.stringify({ tickets: normalizedTickets }),
  });

  const job = await parseResponse(createResponse);

  if (!job.job_id) {
    throw new Error("The backend did not return a batch job ID.");
  }

  const jobUrl = `${API_BASE}/batch/jobs/${encodeURIComponent(job.job_id)}`;

  // Poll every two seconds while the backend processes the batch.
  while (true) {
    const statusResponse = await fetch(jobUrl, {
      headers: { "X-Request-ID": createRequestId() },
    });

    const status = await parseResponse(statusResponse);

    if (status.status === "succeeded") {
      break;
    }

    if (["failed", "cancelled"].includes(status.status)) {
      throw new Error(
        status.error?.message
        ?? `Batch job ${status.status}.`
      );
    }

    const retryAfter = Number(statusResponse.headers.get("Retry-After"));
    const delay = Number.isFinite(retryAfter) && retryAfter > 0
      ? retryAfter * 1000
      : 2000;

    await sleep(delay);
  }

  // Retrieve all results in one page, matching the backend's 5,000 limit.
  const resultsResponse = await fetch(
    `${jobUrl}/results?offset=0&limit=${MAX_BATCH_SIZE}`,
    { headers: { "X-Request-ID": createRequestId() } }
  );

  const resultsData = await parseResponse(resultsResponse);

  // Keep the original subject available for the results table and CSV export.
  const subjectsById = new Map(
    normalizedTickets.map((ticket) => [ticket.ticket_id, ticket.subject])
  );

  return resultsData.predictions.map((prediction) => ({
    ...prediction,
    id: prediction.ticket_id,
    subject: subjectsById.get(prediction.ticket_id) ?? "",
  }));
}
