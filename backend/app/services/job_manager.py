import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone


class JobManager:
    RETENTION_HOURS = 6
    MAX_ACTIVE_JOBS = 4

    def __init__(self, db_path="jobs.db"):
        self.db_path = db_path
        self.lock = threading.Lock()

        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row

        self._create_tables()
        self.mark_running_jobs_interrupted()
        self._cleanup_expired()

    def _create_tables(self):
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    model_version TEXT,
                    error TEXT,
                    tickets TEXT NOT NULL,
                    predictions TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE
                )
                """
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS expired_jobs (
                    job_id TEXT PRIMARY KEY,
                    expired_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _cleanup_expired(self):
        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(hours=self.RETENTION_HOURS)
        ).isoformat()

        rows = self.connection.execute(
            """
            SELECT job_id
            FROM jobs
            WHERE status IN ('succeeded', 'failed', 'cancelled')
              AND completed_at IS NOT NULL
              AND completed_at < ?
            """,
            (cutoff,),
        ).fetchall()

        if not rows:
            return

        now = self._now()

        with self.connection:
            for row in rows:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO expired_jobs (
                        job_id,
                        expired_at
                    )
                    VALUES (?, ?)
                    """,
                    (
                        row["job_id"],
                        now,
                    ),
                )

                self.connection.execute(
                    """
                    DELETE FROM jobs
                    WHERE job_id = ?
                    """,
                    (row["job_id"],),
                )

    def is_expired(self, job_id):
        with self.lock:
            row = self.connection.execute(
                """
                SELECT job_id
                FROM expired_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

        return row is not None

    def count_active_jobs(self) -> int:
        with self.lock:
            row = self.connection.execute(
                """
                SELECT COUNT(*)
                FROM jobs
                WHERE status IN ('queued', 'running')
                """
            ).fetchone()

        return int(row[0] or 0)

    def create_job(self, tickets, idempotency_key=None):
        with self.lock:
            self._cleanup_expired()

            # Idempotency check
            if idempotency_key:
                existing = self.connection.execute(
                    """
                    SELECT *
                    FROM jobs
                    WHERE idempotency_key = ?
                    """,
                    (idempotency_key,),
                ).fetchone()

                if existing is not None:
                    return self._row_to_job(existing)

            job_id = str(uuid.uuid4())
            now = self._now()

            ticket_data = [
                ticket.model_dump()
                if hasattr(ticket, "model_dump")
                else ticket
                for ticket in tickets
            ]

            tickets_json = json.dumps(
                ticket_data,
                ensure_ascii=False,
            )

            # IMPORTANT:
            # predictions cannot be NULL because the DB column is NOT NULL.
            # New jobs start with an empty prediction list.
            predictions_json = json.dumps([])

            try:
                self.connection.execute(
                    """
                    INSERT INTO jobs (
                        job_id,
                        status,
                        total,
                        processed,
                        created_at,
                        started_at,
                        completed_at,
                        model_version,
                        error,
                        tickets,
                        predictions,
                        idempotency_key
                    )
                    VALUES (
                        ?,
                        'queued',
                        ?,
                        0,
                        ?,
                        NULL,
                        NULL,
                        NULL,
                        NULL,
                        ?,
                        ?,
                        ?
                    )
                    """,
                    (
                        job_id,
                        len(tickets),
                        now,
                        tickets_json,
                        predictions_json,
                        idempotency_key,
                    ),
                )

                self.connection.commit()

            except sqlite3.IntegrityError:
                # Handles a possible race where the same idempotency key
                # is inserted by another request at the same time.
                if idempotency_key:
                    existing = self.connection.execute(
                        """
                        SELECT *
                        FROM jobs
                        WHERE idempotency_key = ?
                        """,
                        (idempotency_key,),
                    ).fetchone()

                    if existing is not None:
                        return self._row_to_job(existing)

                raise

            row = self.connection.execute(
                """
                SELECT *
                FROM jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

            return self._row_to_job(row)

    def get_job(self, job_id):
        self._cleanup_expired()

        with self.lock:
            row = self.connection.execute(
                """
                SELECT *
                FROM jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def get_job_by_idempotency_key(self, idempotency_key):
        if not idempotency_key:
            return None

        self._cleanup_expired()

        with self.lock:
            row = self.connection.execute(
                """
                SELECT *
                FROM jobs
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def update_job(self, job_id, **fields):
        if not fields:
            return

        allowed_fields = {
            "status",
            "processed",
            "started_at",
            "completed_at",
            "model_version",
            "error",
            "predictions",
        }

        updates = []
        values = []

        for key, value in fields.items():
            if key not in allowed_fields:
                continue

            if key == "predictions":
                value = json.dumps(
                    value,
                    ensure_ascii=False,
                )

            updates.append(f"{key} = ?")
            values.append(value)

        if not updates:
            return

        values.append(job_id)

        with self.lock:
            self.connection.execute(
                f"""
                UPDATE jobs
                SET {", ".join(updates)}
                WHERE job_id = ?
                """,
                values,
            )

            self.connection.commit()

    def delete_job(self, job_id):
        with self.lock:
            self.connection.execute(
                """
                DELETE FROM jobs
                WHERE job_id = ?
                """,
                (job_id,),
            )

            self.connection.commit()

    def mark_running_jobs_interrupted(self):
        now = self._now()

        with self.connection:
            self.connection.execute(
                """
                UPDATE jobs
                SET
                    status = 'failed',
                    completed_at = ?,
                    error = ?
                WHERE status = 'running'
                """,
                (
                    now,
                    "Job interrupted by server restart.",
                ),
            )

    def _row_to_job(self, row):
        tickets = (
            json.loads(row["tickets"])
            if row["tickets"]
            else []
        )

        predictions = (
            json.loads(row["predictions"])
            if row["predictions"]
            else []
        )

        return {
            "job_id": row["job_id"],
            "status": row["status"],
            "total": row["total"],
            "processed": row["processed"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "model_version": row["model_version"],
            "error": row["error"],
            "tickets": tickets,
            "predictions": predictions,
            "idempotency_key": row["idempotency_key"],
        }


job_manager = JobManager()