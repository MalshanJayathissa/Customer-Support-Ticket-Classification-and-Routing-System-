"""Threaded TensorForge batch worker with incremental progress reporting."""

import threading

from app.services.inference import InferenceService
from app.services.job_manager import job_manager


class JobWorker:
    def __init__(self):
        self.inference_service = InferenceService()
        self.lock = threading.Lock()
        self.running = False

    def process_job(self, job_id):
        with self.lock:
            if self.running:
                return
            self.running = True

        try:
            job = job_manager.get_job(job_id)
            if job is None or job["status"] != "queued":
                return

            tickets = job["tickets"]
            total = len(tickets)
            predictions = []
            job_manager.update_job(
                job_id,
                status="running",
                started_at=job_manager._now(),
                model_version=self.inference_service.model_version,
            )

            # Incremental ML inference allows status polling during large jobs.
            for start in range(0, total, 50):
                current = job_manager.get_job(job_id)
                if current is None or current["status"] == "cancelled":
                    return

                chunk = tickets[start:start + 50]
                chunk_predictions = self.inference_service.predict_batch(chunk)

                current = job_manager.get_job(job_id)
                if current is None or current["status"] == "cancelled":
                    return

                predictions.extend(chunk_predictions)
                job_manager.update_job(
                    job_id,
                    processed=len(predictions),
                    predictions=predictions,
                )
                print(
                    f"Job {job_id}: {len(predictions)}/{total} processed",
                    flush=True,
                )

            current = job_manager.get_job(job_id)
            if current is None or current["status"] == "cancelled":
                return

            job_manager.update_job(
                job_id,
                status="succeeded",
                processed=total,
                predictions=predictions,
                completed_at=job_manager._now(),
            )
            print(f"Job {job_id} succeeded ({total} tickets)", flush=True)

        except Exception as exc:
            print(f"Job {job_id} failed: {exc}", flush=True)
            try:
                current = job_manager.get_job(job_id)
                if current is not None and current["status"] != "cancelled":
                    job_manager.update_job(
                        job_id,
                        status="failed",
                        completed_at=job_manager._now(),
                        error=str(exc),
                    )
            except Exception:
                # Log original failure if SQLite itself is not operational.
                import traceback
                traceback.print_exc()
        finally:
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
                SELECT job_id FROM jobs
                WHERE status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
        return {"job_id": row[0]} if row is not None else None


job_worker = JobWorker()
