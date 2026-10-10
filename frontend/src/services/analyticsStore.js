
import { useSyncExternalStore } from "react";

// In-memory analytics.
// Data resets when the browser page is fully reloaded.

function emptyAnalytics() {
  return {
    totalPredictions: 0,
    confidenceSum: 0,
    confidenceCount: 0,
    assignedCount: 0,
    categories: {},
    teams: {},
    recentPredictions: [],
  };
}

let analytics = emptyAnalytics();

const listeners = new Set();

function subscribe(listener) {
  listeners.add(listener);

  return () => listeners.delete(listener);
}

function getSnapshot() {
  return analytics;
}

function notify() {
  listeners.forEach((listener) => listener());
}

// React hook used by the Dashboard.
export function useAnalytics() {
  return useSyncExternalStore(
    subscribe,
    getSnapshot,
    getSnapshot
  );
}

// Record predictions returned by the REAL API.
export function recordPredictions(predictions, tickets = []) {
  if (!Array.isArray(predictions) || predictions.length === 0) {
    return;
  }

  const next = {
    ...analytics,
    categories: { ...analytics.categories },
    teams: { ...analytics.teams },
    recentPredictions: [...analytics.recentPredictions],
  };

  const newRecent = [];

  predictions.forEach((prediction, index) => {
    if (!prediction || typeof prediction !== "object") {
      return;
    }

    next.totalPredictions += 1;

    const category = prediction.category || "Unknown";
    const team = prediction.team || null;

    next.categories[category] =
      (next.categories[category] || 0) + 1;

    if (team) {
      next.teams[team] = (next.teams[team] || 0) + 1;
      next.assignedCount += 1;
    }

    const confidence = Number(prediction.confidence);

    if (
      prediction.confidence !== null &&
      prediction.confidence !== undefined &&
      Number.isFinite(confidence) &&
      confidence >= 0 &&
      confidence <= 1
    ) {
      next.confidenceSum += confidence;
      next.confidenceCount += 1;
    }

    const ticket = tickets[index] || {};

    newRecent.push({
      id:
        prediction.ticket_id ||
        ticket.ticket_id ||
        `PRED-${next.totalPredictions}`,
      subject:
        prediction.subject ||
        ticket.subject ||
        "Support ticket",
      category,
      team: team || "Not assigned",
      confidence:
        prediction.confidence !== null &&
        prediction.confidence !== undefined &&
        Number.isFinite(confidence)
          ? confidence
          : null,
    });
  });

  // Keep only the 10 latest predictions in memory.
  next.recentPredictions = [
    ...newRecent.reverse(),
    ...next.recentPredictions,
  ].slice(0, 10);

  analytics = next;

  notify();
}

// Clear session statistics.
export function resetAnalytics() {
  analytics = emptyAnalytics();
  notify();
}
