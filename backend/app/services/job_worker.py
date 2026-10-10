
import threading

from app.services.job_manager import job_manager


class JobWorker:
    def __init__(self, inference_service):
        # Share the model instance created in main.py.
        self.inference_service = inference_service

        # Protect worker state and prevent simultaneous jobs.
        self.lock = threading.Lock()
        self.running = False

    def process_job(self, job_id):
        # Claim the worker before processing.
        with self.lock:
            if self.running:
                return

            self.running = True

        try:
            job = job_manager.get_job(job_id)

            if job is None or job["status"] != "queued":
                return

            # Record the start time and model version.
            job_manager.update_job(
                job_id,
                status="running",
                started_at=job_manager._now(),
                model_version=self.inference_service.model_version,
            )

            results = self.inference_service.predict_batch(
                job["tickets"]
            )

            predictions = []

            for result in results:
                current_job = job_manager.get_job(job_id)

                if current_job is None:
                    return

                if current_job["status"] == "cancelled":
                    return

                predictions.append(result)

                # Persist predictions and update progress.
                job_manager.update_job(
                    job_id,
                    processed=len(predictions),
                    predictions=predictions,
                )

            # Do not overwrite cancellation with success.
            current_job = job_manager.get_job(job_id)

            if current_job is None:
                return

            if current_job["status"] == "cancelled":
                return

            job_manager.update_job(
                job_id,
                status="succeeded",
                processed=len(predictions),
                predictions=predictions,
                model_version=self.inference_service.model_version,
                completed_at=job_manager._now(),
                error=None,
            )

        except Exception as exc:
            current_job = job_manager.get_job(job_id)

            if (
                current_job is not None
                and current_job["status"] != "cancelled"
            ):
                job_manager.update_job(
                    job_id,
                    status="failed",
                    completed_at=job_manager._now(),
                    error=str(exc),
                )

        finally:
            # Release the worker and start the next queued job.
            with self.lock:
                self.running = False

            self._start_next_queued_job()

    def submit(self, job_id):
        thread = threading.Thread(
            target=self.process_job,
            args=(job_id,),
            daemon=True,
        )
        thread.start()

    def _start_next_queued_job(self):
        with self.lock:
            if self.running:
                return

        next_job = self._find_next_queued_job()

        if next_job is not None:
            self.submit(next_job["job_id"])

    def _find_next_queued_job(self):
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
