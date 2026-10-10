import threading

from app.services.inference import InferenceService
from app.services.job_manager import job_manager


class JobWorker:
    def __init__(self):
        self.inference_service = InferenceService()

        # Only one async batch job runs at a time.
        self.lock = threading.Lock()
        self.running = False

    # ========================================================
    # Process one job
    # ========================================================

    def process_job(self, job_id):
        # ----------------------------------------------------
        # Make sure only one worker job runs at a time
        # ----------------------------------------------------
        with self.lock:
            if self.running:
                return

            self.running = True

        try:
            job = job_manager.get_job(job_id)

            if job is None:
                return

            # Job may have been cancelled while queued.
            if job["status"] != "queued":
                return

            # ------------------------------------------------
            # Mark running
            # ------------------------------------------------
            job_manager.update_job(
                job_id,
                status="running",
                started_at=job_manager._now(),
            )

            # ------------------------------------------------
            # Run inference
            # ------------------------------------------------
            results = self.inference_service.predict_batch(
                job["tickets"]
            )

            predictions = []

            for result in results:
                # --------------------------------------------
                # Check cancellation during processing
                # --------------------------------------------
                current_job = job_manager.get_job(job_id)

                if current_job is None:
                    return

                if current_job["status"] == "cancelled":
                    return

                predictions.append(result)

                job_manager.update_job(
                    job_id,
                    processed=len(predictions),
                    predictions=predictions,
                )

            # ------------------------------------------------
            # Final cancellation check
            # ------------------------------------------------
            current_job = job_manager.get_job(job_id)

            if current_job is None:
                return

            if current_job["status"] == "cancelled":
                return

            # ------------------------------------------------
            # Mark succeeded
            # ------------------------------------------------
            job_manager.update_job(
                job_id,
                status="succeeded",
                processed=len(predictions),
                predictions=predictions,
                completed_at=job_manager._now(),
            )

        except Exception as exc:
            # -----------------------------------------------
            # Do not overwrite a cancelled job with failed.
            # -----------------------------------------------
            current_job = job_manager.get_job(job_id)

            if current_job is not None:
                if current_job["status"] != "cancelled":
                    job_manager.update_job(
                        job_id,
                        status="failed",
                        completed_at=job_manager._now(),
                        error=str(exc),
                    )

        finally:
            # ------------------------------------------------
            # Release worker
            # ------------------------------------------------
            with self.lock:
                self.running = False

            # ------------------------------------------------
            # Start next queued job
            # ------------------------------------------------
            self._start_next_queued_job()

    # ========================================================
    # Submit job
    # ========================================================

    def submit(self, job_id):
        thread = threading.Thread(
            target=self.process_job,
            args=(job_id,),
            daemon=True,
        )

        thread.start()

    # ========================================================
    # Start next queued job
    # ========================================================

    def _start_next_queued_job(self):
        with self.lock:
            if self.running:
                return

        next_job = self._find_next_queued_job()

        if next_job is not None:
            self.submit(next_job["job_id"])

    # ========================================================
    # Find oldest queued job
    # ========================================================

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

        return {
            "job_id": row[0],
        }


job_worker = JobWorker()