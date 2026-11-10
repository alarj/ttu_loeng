from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from lecture_notes.web.models import Course, Lecture, Operation, StoredUpload, User


def _oracle_kwargs() -> dict[str, str]:
    required = {
        "user": os.getenv("ORACLE_USER", "").strip(),
        "password": os.getenv("ORACLE_PASSWORD", ""),
        "dsn": os.getenv("ORACLE_DSN", "").strip(),
    }
    if not all(required.values()):
        raise RuntimeError("ORACLE_USER, ORACLE_PASSWORD and ORACLE_DSN are required")
    optional = {
        "config_dir": os.path.expanduser(os.getenv("ORACLE_CONFIG_DIR", "").strip()),
        "wallet_location": os.path.expanduser(os.getenv("ORACLE_WALLET_LOCATION", "").strip()),
        "wallet_password": os.getenv("ORACLE_WALLET_PASSWORD", ""),
    }
    return {**required, **{key: value for key, value in optional.items() if value}}


def _row(cursor: Any, value: Sequence[Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {column[0].lower(): item for column, item in zip(cursor.description, value)}


def _returning_number(variable: Any) -> int:
    value = variable.getvalue()
    if isinstance(value, list):
        value = value[0]
    return int(value)


class OracleTransaction:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def insert_submission(
        self,
        user_id: int,
        public_id: str,
        resolver: dict[str, Any],
        resolver_path: str,
    ) -> int:
        with self.connection.cursor() as cursor:
            output = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO submissions (
                    public_id, user_id, echo_public_url, echo_public_section_id,
                    echo_canonical_section_id, course_title, resolver_manifest_path
                ) VALUES (
                    :public_id, :user_id, :public_url, :public_section_id,
                    :canonical_section_id, :course_title, :resolver_path
                ) RETURNING submission_id INTO :output
                """,
                {
                    "public_id": public_id,
                    "user_id": user_id,
                    "public_url": resolver["input_public_url"],
                    "public_section_id": resolver["public_section_id"],
                    "canonical_section_id": resolver["canonical_section_id"],
                    "course_title": resolver.get("course_title"),
                    "resolver_path": resolver_path,
                    "output": output,
                },
            )
            return _returning_number(output)

    def insert_lecture(self, submission_id: int, lesson: dict[str, Any]) -> int:
        from datetime import datetime, timezone

        start = lesson.get("start_time_utc")
        start_at = None
        if start:
            parsed_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            start_at = parsed_start.astimezone(timezone.utc).replace(tzinfo=None)
        with self.connection.cursor() as cursor:
            output = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO lecture_processings (
                    submission_id, echo_lesson_id, lecture_title, lecture_start_at,
                    duration_seconds, recording_status
                ) VALUES (
                    :submission_id, :lesson_id, :title, :start_at,
                    :duration_seconds, :recording_status
                ) RETURNING lecture_processing_id INTO :output
                """,
                {
                    "submission_id": submission_id,
                    "lesson_id": lesson["lesson_id"],
                    "title": lesson.get("display_name") or lesson.get("name"),
                    "start_at": start_at,
                    "duration_seconds": None,
                    "recording_status": lesson["recording_status"],
                    "output": output,
                },
            )
            return _returning_number(output)

    def insert_upload(self, lecture_processing_id: int, upload: StoredUpload) -> int:
        with self.connection.cursor() as cursor:
            output = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO uploads (
                    public_id, lecture_processing_id, upload_type, original_filename,
                    stored_relative_path, media_type, size_bytes, sha256
                ) VALUES (
                    :public_id, :lecture_id, 'SLIDES', :filename,
                    :stored_path, :media_type, :size_bytes, :sha256
                ) RETURNING upload_id INTO :output
                """,
                {
                    "public_id": upload.public_id,
                    "lecture_id": lecture_processing_id,
                    "filename": upload.original_filename,
                    "stored_path": upload.relative_path,
                    "media_type": upload.media_type,
                    "size_bytes": upload.size_bytes,
                    "sha256": upload.sha256,
                    "output": output,
                },
            )
            return _returning_number(output)

    def insert_operation(
        self,
        lecture_processing_id: int,
        operation_type: str,
        previous_operation_id: int | None,
        slide_sensitivity_level: int | None = None,
    ) -> tuple[int, str]:
        with self.connection.cursor() as cursor:
            output = cursor.var(int)
            public_id = str(uuid.uuid4())
            idempotency_key = f"ttu_loeng:{operation_type}:{public_id}"
            cursor.execute(
                """
                SELECT NVL(MAX(attempt_number), 0) + 1
                  FROM background_operations
                 WHERE lecture_processing_id = :lecture_id
                   AND operation_type = :operation_type
                """,
                {"lecture_id": lecture_processing_id, "operation_type": operation_type},
            )
            attempt_number = int(cursor.fetchone()[0])
            cursor.execute(
                """
                INSERT INTO background_operations (
                    public_id, lecture_processing_id, previous_operation_id,
                    operation_type, attempt_number, slide_sensitivity_level, idempotency_key
                ) VALUES (
                    :public_id, :lecture_id, :previous_id, :operation_type,
                    :attempt_number, :slide_sensitivity_level, :idempotency_key
                ) RETURNING operation_id INTO :output
                """,
                {
                    "public_id": public_id,
                    "lecture_id": lecture_processing_id,
                    "previous_id": previous_operation_id,
                    "operation_type": operation_type,
                    "attempt_number": attempt_number,
                    "slide_sensitivity_level": slide_sensitivity_level,
                    "idempotency_key": idempotency_key,
                    "output": output,
                },
            )
            return _returning_number(output), idempotency_key


class OracleRepository:
    def __init__(self, pool: Any) -> None:
        self.pool = pool

    @classmethod
    def from_env(cls) -> "OracleRepository":
        import oracledb

        pool = oracledb.create_pool(min=1, max=5, increment=1, **_oracle_kwargs())
        return cls(pool)

    def close(self) -> None:
        self.pool.close()

    @contextmanager
    def transaction(self) -> Iterator[OracleTransaction]:
        with self.pool.acquire() as connection:
            try:
                yield OracleTransaction(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        with self.pool.acquire() as connection:
            yield connection

    def get_or_create_google_user(self, subject: str, email: str, display_name: str) -> User:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, public_id, email, display_name, role_code, enabled
                  FROM app_users
                 WHERE identity_provider = 'GOOGLE'
                   AND external_subject = :subject
                   AND end_date IS NULL
                """,
                {"subject": subject},
            )
            result = _row(cursor, cursor.fetchone())
            if result is None:
                output = cursor.var(int)
                cursor.execute(
                    """
                    INSERT INTO app_users (
                        public_id, identity_provider, external_subject, email,
                        display_name, role_code, enabled
                    ) VALUES (
                        :public_id, 'GOOGLE', :subject, :email, :display_name, 'USER', 1
                    ) RETURNING user_id INTO :output
                    """,
                    {
                        "public_id": str(uuid.uuid4()),
                        "subject": subject,
                        "email": email.lower(),
                        "display_name": display_name,
                        "output": output,
                    },
                )
                connection.commit()
                return self.get_user(_returning_number(output))
            cursor.execute(
                """
                UPDATE app_users
                   SET email = :email, display_name = :display_name, last_updated = SYSTIMESTAMP
                 WHERE user_id = :user_id
                """,
                {"email": email.lower(), "display_name": display_name, "user_id": result["user_id"]},
            )
            connection.commit()
            return self.get_user(int(result["user_id"]))

    def get_user(self, user_id: int) -> User:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, public_id, email, display_name, role_code, enabled
                  FROM app_users
                 WHERE user_id = :user_id AND end_date IS NULL
                """,
                {"user_id": user_id},
            )
            row = _row(cursor, cursor.fetchone())
        if row is None:
            raise KeyError(user_id)
        return User(
            user_id=int(row["user_id"]),
            public_id=row["public_id"],
            email=row["email"] or "",
            display_name=row["display_name"] or row["email"] or "",
            role_code=row["role_code"],
            enabled=bool(row["enabled"]),
        )

    def find_submission(self, user_id: int, public_id: str) -> int | None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT submission_id
                  FROM submissions
                 WHERE user_id = :user_id
                   AND public_id = :public_id
                   AND end_date IS NULL
                """,
                {"user_id": user_id, "public_id": public_id},
            )
            value = cursor.fetchone()
        return int(value[0]) if value is not None else None

    def list_courses(self) -> list[Course]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.echo_canonical_section_id,
                       MAX(s.course_title) KEEP (
                           DENSE_RANK LAST ORDER BY s.created, s.submission_id
                       ) AS course_title,
                       MAX(s.echo_public_url) KEEP (
                           DENSE_RANK LAST ORDER BY s.created, s.submission_id
                       ) AS echo_public_url,
                       COUNT(*) AS lecture_count
                  FROM submissions s
                  JOIN lecture_processings lp ON lp.submission_id = s.submission_id
                 WHERE s.end_date IS NULL AND lp.end_date IS NULL
                 GROUP BY s.echo_canonical_section_id
                 ORDER BY course_title
                """
            )
            rows = [_row(cursor, value) for value in cursor.fetchall()]
        return [
            Course(
                echo_canonical_section_id=row["echo_canonical_section_id"],
                course_title=row["course_title"] or "",
                lecture_count=int(row["lecture_count"]),
                echo_public_url=row["echo_public_url"],
            )
            for row in rows
            if row is not None
        ]

    def get_course(self, canonical_section_id: str) -> Course:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.echo_canonical_section_id,
                       MAX(s.course_title) KEEP (
                           DENSE_RANK LAST ORDER BY s.created, s.submission_id
                       ) AS course_title,
                       MAX(s.echo_public_url) KEEP (
                           DENSE_RANK LAST ORDER BY s.created, s.submission_id
                       ) AS echo_public_url,
                       COUNT(*) AS lecture_count
                  FROM submissions s
                  JOIN lecture_processings lp ON lp.submission_id = s.submission_id
                 WHERE s.echo_canonical_section_id = :section_id
                   AND s.end_date IS NULL AND lp.end_date IS NULL
                 GROUP BY s.echo_canonical_section_id
                """,
                {"section_id": canonical_section_id},
            )
            row = _row(cursor, cursor.fetchone())
        if row is None:
            raise KeyError(canonical_section_id)
        return Course(
            echo_canonical_section_id=row["echo_canonical_section_id"],
            course_title=row["course_title"] or "",
            lecture_count=int(row["lecture_count"]),
            echo_public_url=row["echo_public_url"],
        )

    def list_lectures(self, canonical_section_id: str | None = None) -> list[Lecture]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT lp.lecture_processing_id, lp.public_id, lp.submission_id,
                       s.echo_canonical_section_id, s.course_title,
                       lp.lecture_title, lp.echo_lesson_id,
                       lp.lecture_start_at, lp.duration_seconds, lp.recording_status,
                       lp.default_slides_operation_id,
                       lp.created
                  FROM lecture_processings lp
                  JOIN submissions s ON s.submission_id = lp.submission_id
                 WHERE lp.end_date IS NULL AND s.end_date IS NULL
                   AND (:section_id IS NULL OR s.echo_canonical_section_id = :section_id)
                 ORDER BY LOWER(lp.lecture_title) NULLS LAST,
                          lp.lecture_start_at NULLS LAST,
                          lp.lecture_processing_id
                """,
                {"section_id": canonical_section_id},
            )
            rows = [_row(cursor, value) for value in cursor.fetchall()]
        lectures = [self._lecture(value) for value in rows if value is not None]
        self._attach_operations(lectures)
        return lectures

    def active_echo_lesson_ids(self, canonical_section_id: str) -> set[str]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT lp.echo_lesson_id
                  FROM lecture_processings lp
                  JOIN submissions s ON s.submission_id = lp.submission_id
                 WHERE s.echo_canonical_section_id = :section_id
                   AND lp.end_date IS NULL
                   AND s.end_date IS NULL
                """,
                {"section_id": canonical_section_id},
            )
            return {str(row[0]) for row in cursor.fetchall() if row[0] is not None}

    def get_lecture(self, lecture_processing_id: int) -> Lecture:
        return self._get_lecture("lp.lecture_processing_id = :value", lecture_processing_id)

    def get_public_lecture(self, public_id: str) -> Lecture:
        return self._get_lecture("lp.public_id = :value", public_id)

    def _get_lecture(self, predicate: str, value: object) -> Lecture:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT lp.lecture_processing_id, lp.public_id, lp.submission_id,
                       s.echo_canonical_section_id, s.course_title,
                       lp.lecture_title, lp.echo_lesson_id,
                       lp.lecture_start_at, lp.duration_seconds, lp.recording_status,
                       lp.default_slides_operation_id,
                       lp.created
                  FROM lecture_processings lp
                  JOIN submissions s ON s.submission_id = lp.submission_id
                 WHERE {predicate} AND lp.end_date IS NULL AND s.end_date IS NULL
                """,
                {"value": value},
            )
            row = _row(cursor, cursor.fetchone())
        if row is None:
            raise KeyError(value)
        lecture = self._lecture(row)
        self._attach_operations([lecture])
        return lecture

    @staticmethod
    def _lecture(row: dict[str, Any]) -> Lecture:
        return Lecture(
            lecture_processing_id=int(row["lecture_processing_id"]),
            public_id=row["public_id"],
            submission_id=int(row["submission_id"]),
            echo_canonical_section_id=row["echo_canonical_section_id"],
            course_title=row["course_title"],
            lecture_title=row["lecture_title"],
            echo_lesson_id=row["echo_lesson_id"],
            lecture_start_at=row["lecture_start_at"],
            duration_seconds=float(row["duration_seconds"]) if row["duration_seconds"] is not None else None,
            recording_status=row["recording_status"],
            created=row["created"],
            default_slides_operation_id=(
                int(row["default_slides_operation_id"])
                if row["default_slides_operation_id"] is not None
                else None
            ),
            operations=[],
        )

    def _attach_operations(self, lectures: list[Lecture]) -> None:
        if not lectures:
            return
        by_id = {lecture.lecture_processing_id: lecture for lecture in lectures}
        binds = {f"id{index}": value for index, value in enumerate(by_id)}
        placeholders = ", ".join(f":{name}" for name in binds)
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT operation_id, lecture_processing_id, operation_type, attempt_number,
                       slide_sensitivity_level, ords_job_id,
                       local_outcome, registration_error_message,
                       local_started_at, local_completed_at
                  FROM background_operations
                 WHERE lecture_processing_id IN ({placeholders}) AND end_date IS NULL
                 ORDER BY operation_id
                """,
                binds,
            )
            rows = [_row(cursor, value) for value in cursor.fetchall()]
        for row in rows:
            if row is None:
                continue
            by_id[int(row["lecture_processing_id"])].operations.append(
                Operation(
                    operation_id=int(row["operation_id"]),
                    operation_type=row["operation_type"],
                    attempt_number=int(row["attempt_number"]),
                    ords_job_id=int(row["ords_job_id"]) if row["ords_job_id"] is not None else None,
                    slide_sensitivity_level=(
                        int(row["slide_sensitivity_level"])
                        if row["slide_sensitivity_level"] is not None
                        else None
                    ),
                    local_outcome=row["local_outcome"],
                    registration_error_message=row["registration_error_message"],
                    local_started_at=row["local_started_at"],
                    local_completed_at=row["local_completed_at"],
                )
            )

    def set_operation_registered(self, operation_id: int, ords_job_id: int) -> None:
        self._execute_update(
            """
            UPDATE background_operations
               SET ords_job_id = :job_id, ords_registered_at = SYSTIMESTAMP,
                   registration_error_code = NULL, registration_error_message = NULL,
                   last_updated = SYSTIMESTAMP
             WHERE operation_id = :operation_id AND end_date IS NULL
            """,
            {"job_id": ords_job_id, "operation_id": operation_id},
        )

    def set_registration_error(self, operation_id: int, code: str, message: str) -> None:
        self._execute_update(
            """
            UPDATE background_operations
               SET registration_error_code = :code, registration_error_message = :message,
                   last_updated = SYSTIMESTAMP
             WHERE operation_id = :operation_id AND end_date IS NULL
            """,
            {"code": code[:100], "message": message[:2000], "operation_id": operation_id},
        )

    def set_public_sharing(self, lecture_processing_id: int, enabled: bool) -> str | None:
        public_id = str(uuid.uuid4()) if enabled else None
        self._execute_update(
            """
            UPDATE lecture_processings
               SET public_id = :public_id, last_updated = SYSTIMESTAMP
             WHERE lecture_processing_id = :lecture_id AND end_date IS NULL
            """,
            {"public_id": public_id, "lecture_id": lecture_processing_id},
        )
        return public_id

    def create_slide_reprocessing(self, lecture_processing_id: int, sensitivity_level: int) -> tuple[int, str, int]:
        with self.transaction() as transaction:
            with transaction.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT lecture_processing_id
                      FROM lecture_processings
                     WHERE lecture_processing_id = :lecture_id
                       AND end_date IS NULL
                       FOR UPDATE
                    """,
                    {"lecture_id": lecture_processing_id},
                )
                if cursor.fetchone() is None:
                    raise KeyError(lecture_processing_id)
                cursor.execute(
                    """
                    SELECT operation_id, ords_job_id
                      FROM background_operations
                     WHERE lecture_processing_id = :lecture_id
                       AND operation_type = 'asr'
                       AND local_outcome = 'SUCCEEDED'
                       AND ords_job_id IS NOT NULL
                       AND end_date IS NULL
                    """,
                    {"lecture_id": lecture_processing_id},
                )
                row = cursor.fetchone()
            if row is None:
                raise KeyError(lecture_processing_id)
            previous_operation_id, previous_job_id = (int(row[0]), int(row[1]))
            operation_id, idempotency_key = transaction.insert_operation(
                lecture_processing_id,
                "slides",
                previous_operation_id,
                sensitivity_level,
            )
        return operation_id, idempotency_key, previous_job_id

    def set_default_slides_operation(self, lecture_processing_id: int, operation_id: int) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE lecture_processings
                   SET default_slides_operation_id = :operation_id,
                       last_updated = SYSTIMESTAMP
                 WHERE lecture_processing_id = :lecture_id
                   AND end_date IS NULL
                """,
                {"lecture_id": lecture_processing_id, "operation_id": operation_id},
            )
            if cursor.rowcount != 1:
                raise KeyError(lecture_processing_id)
            connection.commit()

    def soft_delete_lecture(self, lecture_processing_id: int) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE lecture_processings
                   SET end_date = SYSDATE, last_updated = SYSTIMESTAMP
                 WHERE lecture_processing_id = :lecture_id
                   AND end_date IS NULL
                """,
                {"lecture_id": lecture_processing_id},
            )
            if cursor.rowcount != 1:
                raise KeyError(lecture_processing_id)
            connection.commit()

    def operation_context(self, operation_id: int) -> dict[str, Any]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT bo.operation_id, bo.operation_type, bo.ords_job_id,
                       bo.local_outcome, bo.slide_sensitivity_level,
                       lp.lecture_processing_id, lp.echo_lesson_id,
                       s.echo_public_url,
                       u.stored_relative_path AS slides_relative_path
                  FROM background_operations bo
                  JOIN lecture_processings lp
                    ON lp.lecture_processing_id = bo.lecture_processing_id
                  JOIN submissions s ON s.submission_id = lp.submission_id
                  LEFT JOIN uploads u
                    ON u.lecture_processing_id = lp.lecture_processing_id
                   AND u.upload_type = 'SLIDES' AND u.end_date IS NULL
                 WHERE bo.operation_id = :operation_id
                   AND bo.end_date IS NULL AND lp.end_date IS NULL AND s.end_date IS NULL
                """,
                {"operation_id": operation_id},
            )
            row = _row(cursor, cursor.fetchone())
        if row is None:
            raise KeyError(operation_id)
        return row

    def mark_operation_started(self, operation_id: int) -> None:
        self._execute_update(
            """
            UPDATE background_operations
               SET local_started_at = SYSTIMESTAMP, local_completed_at = NULL,
                   local_outcome = NULL, local_error_code = NULL,
                   local_error_message = NULL, last_updated = SYSTIMESTAMP
             WHERE operation_id = :operation_id AND end_date IS NULL
            """,
            {"operation_id": operation_id},
        )

    def mark_operation_completed(
        self,
        operation_id: int,
        outcome: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self._execute_update(
            """
            UPDATE background_operations
               SET local_completed_at = SYSTIMESTAMP, local_outcome = :outcome,
                   local_error_code = :error_code, local_error_message = :error_message,
                   last_updated = SYSTIMESTAMP
             WHERE operation_id = :operation_id AND end_date IS NULL
            """,
            {
                "operation_id": operation_id,
                "outcome": outcome,
                "error_code": error_code[:100] if error_code else None,
                "error_message": error_message[:2000] if error_message else None,
            },
        )

    def _execute_update(self, statement: str, binds: dict[str, Any]) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(statement, binds)
            connection.commit()
