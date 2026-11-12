from __future__ import annotations

import io
import json
import unittest

from lecture_notes.web.ords import OrdsClient
from lecture_notes.web.settings import OrdsSettings


class Response:
    def __init__(self, payload, status=200):
        self.payload = json.dumps(payload).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return self.payload


class FakeOpener:
    def __init__(self):
        self.requests = []
        self.token_count = 0

    def __call__(self, request, timeout):
        self.requests.append(request)
        if request.full_url.endswith("/oauth/token"):
            self.token_count += 1
            return Response({"access_token": f"token-{self.token_count}", "expires_in": 3600})
        return Response({"job_id": 123, "status": "QUEUED"}, status=201)


class RetryingOpener(FakeOpener):
    def __init__(self):
        super().__init__()
        self.api_attempts = 0

    def __call__(self, request, timeout):
        if request.full_url.endswith("/oauth/token"):
            return super().__call__(request, timeout)
        self.requests.append(request)
        self.api_attempts += 1
        if self.api_attempts == 1:
            raise TimeoutError("do-not-log-this-error-detail")
        return Response({"job_id": 123, "status": "QUEUED"}, status=201)


class Timer:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


class OrdsClientTests(unittest.TestCase):
    def test_token_is_reused_and_registration_payload_uses_operation_id(self):
        opener = FakeOpener()
        now = [100.0]
        client = OrdsClient(
            OrdsSettings("https://ords.example/jobs", "client", "secret", 60, 300, 300),
            opener=opener,
            clock=lambda: now[0],
            sleeper=lambda value: None,
        )

        first = client.register_job(
            operation_id=45,
            operation_type="asr",
            idempotency_key="key",
            lecture_processing_id=12,
            previous_job_id=None,
        )
        client.job_status(123)

        self.assertEqual(first["job_id"], 123)
        self.assertEqual(opener.token_count, 1)
        request_body = json.loads(opener.requests[1].data.decode("utf-8"))
        self.assertEqual(request_body["application_job_id"], "45")
        self.assertEqual(request_body["parameters"], {"lecture_processing_id": 12})
        self.assertEqual(opener.requests[2].get_header("Authorization"), "Bearer token-1")

    def test_registration_keeps_technical_id_when_display_metadata_is_added(self):
        opener = FakeOpener()
        client = OrdsClient(
            OrdsSettings("https://ords.example/jobs", "client", "secret", 60, 300, 300),
            opener=opener,
            clock=lambda: 100.0,
            sleeper=lambda value: None,
        )

        client.register_job(
            operation_id=45,
            operation_type="asr",
            idempotency_key="key",
            lecture_processing_id=12,
            previous_job_id=None,
            parameters={
                "lecture_processing_id": 999,
                "lecture_title": "Loeng 1",
                "lecture_start_at": "2026-11-01T10:00:00Z",
            },
        )

        request_body = json.loads(opener.requests[1].data.decode("utf-8"))
        self.assertEqual(
            request_body["parameters"],
            {
                "lecture_processing_id": 12,
                "lecture_title": "Loeng 1",
                "lecture_start_at": "2026-11-01T10:00:00Z",
            },
        )

    def test_logs_request_stage_status_and_duration_without_sensitive_values(self):
        opener = FakeOpener()
        client = OrdsClient(
            OrdsSettings(
                "https://ords.example/jobs",
                "sensitive-client-id",
                "sensitive-client-secret",
                60,
                300,
                300,
            ),
            opener=opener,
            clock=lambda: 100.0,
            timer=Timer(10.0, 10.125, 20.0, 20.75),
            sleeper=lambda value: None,
        )

        with self.assertLogs("lecture_notes.web.ords", level="INFO") as captured:
            client.register_job(
                operation_id=987654,
                operation_type="asr-sensitive-body",
                idempotency_key="sensitive-idempotency-key",
                lecture_processing_id=765432,
                previous_job_id=None,
            )

        logs = "\n".join(captured.output)
        self.assertIn("endpoint=oauth/token method=POST attempt=1/2", logs)
        self.assertIn("status=200 elapsed_seconds=0.125", logs)
        self.assertIn("endpoint=application/jobs method=POST attempt=1/2", logs)
        self.assertIn("status=201 elapsed_seconds=0.750", logs)
        for sensitive_value in (
            "sensitive-client-id",
            "sensitive-client-secret",
            "token-1",
            "987654",
            "asr-sensitive-body",
            "sensitive-idempotency-key",
            "765432",
        ):
            self.assertNotIn(sensitive_value, logs)

    def test_timeout_has_one_short_retry_and_does_not_log_exception_detail(self):
        delays = []
        opener = RetryingOpener()
        client = OrdsClient(
            OrdsSettings("https://ords.example/jobs", "client", "secret", 60, 300, 300),
            opener=opener,
            clock=lambda: 100.0,
            timer=Timer(1.0, 1.1, 2.0, 2.4, 3.0, 3.2),
            sleeper=delays.append,
        )

        with self.assertLogs("lecture_notes.web.ords", level="INFO") as captured:
            client.register_job(
                operation_id=45,
                operation_type="asr",
                idempotency_key="key",
                lecture_processing_id=12,
                previous_job_id=None,
            )

        logs = "\n".join(captured.output)
        self.assertIn(
            "endpoint=application/jobs method=POST attempt=1/2 status=none "
            "error_type=TimeoutError elapsed_seconds=0.400 retry=true retry_delay_seconds=0.25",
            logs,
        )
        self.assertIn("endpoint=application/jobs method=POST attempt=2/2 status=201", logs)
        self.assertNotIn("do-not-log-this-error-detail", logs)
        self.assertEqual(delays, [0.25])


if __name__ == "__main__":
    unittest.main()
