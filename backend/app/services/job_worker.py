import json
import threading

from app.services.job_manager import job_manager


class JobWorker:
    def __init__(self, inference_service):
        # Reuse the model instance loaded by main.py.
        self.inference_service = inference_service

        # Only one background job should run at a time.
        self.lock = threading.Lock()
        self.running = False

    def process_job(self, job_id):
        """Process one queued job and persist its progress and outcome."""

        # Claim the worker so two jobs cannot run simultaneously.
        with self.lock:
            if self.running:
                return

            self.running = True

        try:
            job = job_manager.get_job(job_id)

            if job is None or job["status"] != "queued":
                return

            # Mark the job as running before starting inference.
            job_manager.update_job(
                job_id,
                status="running",
                started_at=job_manager._now(),
                model_version=self.inference_service.model_version,
            )

            # Predict the entire batch using the existing inference service.
            results = self.inference_service.predict_batch(
                job["tickets"]
            )

            predictions = []

            for result in results:
                # Check whether the job was deleted or cancelled.
                current_job = job_manager.get_job(job_id)

                if current_job is None:
                    return

                if current_job["status"] == "cancelled":
                    return

                # Preserve the original prediction order.
                if hasattr(result, "model_dump"):
                    prediction = result.model_dump(exclude_none=False)
                elif isinstance(result, dict):
                    prediction = result
                else:
                    # Support other Pydantic-compatible result objects.
                    prediction = dict(result)

                predictions.append(prediction)

                # Save partial progress so the job status stays current.
                job_manager.update_job(
                    job_id,
                    processed=len(predictions),
                    predictions=predictions,
                )

            # Check once more before marking the job successful.
            current_job = job_manager.get_job(job_id)

            if current_job is None:
                return

            if current_job["status"] == "cancelled":
                return

            # Store the final successful outcome.
            job_manager.update_job(
                job_id,
                status="succeeded",
                processed=len(predictions),
                predictions=predictions,
                model_version=self.inference_service.model_version,
                completed_at=job_manager._now(),
                error=None,
            )

        except Exception:
            # Avoid exposing internal exception details or stack traces
            # through the public API.
            current_job = job_manager.get_job(job_id)

            if (
                current_job is not None
                and current_job["status"] not in {"cancelled", "succeeded"}
            ):
                error_json = json.dumps({
                    "code": "inference_failed",
                    "message": "The batch job failed during inference.",
                })

                job_manager.update_job(
                    job_id,
                    status="failed",
                    completed_at=job_manager._now(),
                    error=error_json,
                )

        finally:
            # Release the worker even when processing fails or returns early.
            with self.lock:
                self.running = False

            # Start the next queued job, if one exists.
            self._start_next_queued_job()

    def submit(self, job_id):
        """Run a job in a background thread."""
        thread = threading.Thread(
            target=self.process_job,
            args=(job_id,),
            daemon=True,
        )
        thread.start()

    def _start_next_queued_job(self):
        """Submit the oldest queued job when the worker is available."""
        with self.lock:
            if self.running:
                return

        next_job = self._find_next_queued_job()

        if next_job is not None:
            self.submit(next_job["job_id"])

    def _find_next_queued_job(self):
        """Find the oldest job waiting in the SQLite queue."""
        with job_manager.lock:
            row = job_manager.connection.execute(
                """
                SELECT job_id
                FROM jobs
                WHERE status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return {"job_id": row["job_id"]}
