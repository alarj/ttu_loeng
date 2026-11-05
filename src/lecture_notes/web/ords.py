from __future__ import annotations

import base64
import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from lecture_notes.web.settings import OrdsSettings


LOGGER = logging.getLogger(__name__)
REQUEST_ATTEMPTS = 2


class OrdsError(RuntimeError):
    def __init__(self, code: str, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class OrdsClient:
    def __init__(
        self,
        settings: OrdsSettings,
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
        clock: Callable[[], float] = time.monotonic,
        timer: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self._opener = opener
        self._clock = clock
        self._timer = timer
        self._sleeper = sleeper
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = threading.Lock()

    def register_job(
        self,
        *,
        operation_id: int,
        operation_type: str,
        idempotency_key: str,
        lecture_processing_id: int,
        previous_job_id: int | None,
    ) -> dict[str, Any]:
        return self._json_request(
            "POST",
            "application/jobs",
            {
                "application_code": "ttu_loeng",
                "job_type_code": operation_type,
                "application_job_id": str(operation_id),
                "idempotency_key": idempotency_key,
                "previous_job_id": previous_job_id,
                "parameters": {"lecture_processing_id": lecture_processing_id},
            },
        )

    def job_status(self, job_id: int) -> dict[str, Any]:
        query = urllib.parse.urlencode({"application_code": "ttu_loeng"})
        return self._json_request("GET", f"application/jobs/{job_id}?{query}")

    def worker_startup(self, worker: dict[str, str]) -> dict[str, Any]:
        return self._json_request("POST", "worker/startup", {"application_code": "ttu_loeng", **worker})

    def claim(self, worker: dict[str, str], request_id: str) -> dict[str, Any] | None:
        return self._json_request(
            "POST",
            "worker/claim",
            {"application_code": "ttu_loeng", "claim_request_id": request_id, **worker},
            allow_empty=True,
        )

    def start(self, job: dict[str, Any], worker: dict[str, str]) -> dict[str, Any]:
        return self._worker_job_request("start", job, worker)

    def heartbeat(self, job: dict[str, Any], worker: dict[str, str]) -> dict[str, Any]:
        return self._worker_job_request("heartbeat", job, worker)

    def complete(
        self,
        job: dict[str, Any],
        worker: dict[str, str],
        *,
        outcome: str,
        exit_code: int,
        end_reason: str,
    ) -> dict[str, Any]:
        body = self._execution_body(job, worker)
        body.update({"outcome": outcome, "exit_code": exit_code, "end_reason": end_reason})
        return self._json_request("POST", f"worker/jobs/{int(job['job_id'])}/complete", body)

    def _worker_job_request(self, action: str, job: dict[str, Any], worker: dict[str, str]) -> dict[str, Any]:
        return self._json_request(
            "POST",
            f"worker/jobs/{int(job['job_id'])}/{action}",
            self._execution_body(job, worker),
        )

    @staticmethod
    def _execution_body(job: dict[str, Any], worker: dict[str, str]) -> dict[str, Any]:
        return {
            "application_code": "ttu_loeng",
            "execution_token": job["execution_token"],
            **worker,
        }

    def _authorization(self, force: bool = False) -> str:
        with self._token_lock:
            if not force and self._token and self._clock() < self._token_expires_at:
                return self._token
            credentials = base64.b64encode(
                f"{self.settings.client_id}:{self.settings.client_secret}".encode("utf-8")
            ).decode("ascii")
            request = urllib.request.Request(
                f"{self.settings.base_url}/oauth/token",
                data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("ascii"),
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                method="POST",
            )
            payload = self._open_json(request, endpoint="oauth/token", authenticated=False)
            token = payload.get("access_token")
            expires_in = payload.get("expires_in")
            if not isinstance(token, str) or not isinstance(expires_in, (int, float)):
                raise OrdsError("INVALID_TOKEN_RESPONSE", "ORDS OAuth response is missing access_token or expires_in")
            usable_seconds = max(1.0, float(expires_in) - self.settings.token_refresh_margin_seconds)
            self._token = token
            self._token_expires_at = self._clock() + usable_seconds
            return token

    def _json_request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        allow_empty: bool = False,
    ) -> dict[str, Any] | None:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        for authentication_attempt in range(2):
            token = self._authorization(force=authentication_attempt == 1)
            request = urllib.request.Request(
                f"{self.settings.base_url}/{path}",
                data=data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method=method,
            )
            try:
                return self._open_json(
                    request,
                    endpoint=path.partition("?")[0],
                    authenticated=True,
                    allow_empty=allow_empty,
                )
            except OrdsError as exc:
                if exc.status == 401 and authentication_attempt == 0:
                    continue
                raise
        raise OrdsError("AUTHENTICATION_FAILED", "ORDS authentication failed", 401)

    def _open_json(
        self,
        request: urllib.request.Request,
        *,
        endpoint: str,
        authenticated: bool,
        allow_empty: bool = False,
    ) -> dict[str, Any] | None:
        method = request.get_method()
        for retry in range(REQUEST_ATTEMPTS):
            attempt = retry + 1
            started_at = self._timer()
            LOGGER.info(
                "ORDS request started endpoint=%s method=%s attempt=%d/%d timeout_seconds=%g",
                endpoint,
                method,
                attempt,
                REQUEST_ATTEMPTS,
                self.settings.request_timeout_seconds,
            )
            try:
                with self._opener(request, timeout=self.settings.request_timeout_seconds) as response:
                    if response.status == 204 and allow_empty:
                        self._log_success(endpoint, method, attempt, response.status, started_at)
                        return None
                    raw = response.read()
                    if not raw and allow_empty:
                        self._log_success(endpoint, method, attempt, response.status, started_at)
                        return None
                    payload = json.loads(raw.decode("utf-8"))
                    if not isinstance(payload, dict):
                        self._log_failure(
                            endpoint, method, attempt, started_at, error_type="invalid_response"
                        )
                        raise OrdsError("INVALID_RESPONSE", "ORDS response must be a JSON object")
                    self._log_success(endpoint, method, attempt, response.status, started_at)
                    return payload
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {}
                if exc.code == 401 and authenticated:
                    self._log_failure(
                        endpoint, method, attempt, started_at, status=exc.code, error_type="http"
                    )
                    raise OrdsError("UNAUTHORIZED", "ORDS authentication failed", 401) from exc
                retrying = (exc.code == 429 or exc.code >= 500) and retry < REQUEST_ATTEMPTS - 1
                retry_delay = self._retry_delay(exc, retry) if retrying else None
                if retry_delay is not None and retry_delay > self.settings.request_timeout_seconds:
                    retrying = False
                    retry_delay = None
                self._log_failure(
                    endpoint,
                    method,
                    attempt,
                    started_at,
                    status=exc.code,
                    error_type="http",
                    retry_delay=retry_delay,
                )
                if retrying:
                    self._sleeper(retry_delay)
                    continue
                code = str(payload.get("error_code") or f"HTTP_{exc.code}")
                message = str(payload.get("message") or "ORDS request failed")
                raise OrdsError(code, message, exc.code) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                retrying = retry < REQUEST_ATTEMPTS - 1
                retry_delay = 0.25 * float(2**retry) if retrying else None
                self._log_failure(
                    endpoint,
                    method,
                    attempt,
                    started_at,
                    error_type=type(exc).__name__,
                    retry_delay=retry_delay,
                )
                if retrying:
                    self._sleeper(retry_delay)
                    continue
                raise OrdsError("NETWORK_ERROR", f"ORDS request failed: {type(exc).__name__}") from exc
            except json.JSONDecodeError as exc:
                self._log_failure(
                    endpoint, method, attempt, started_at, error_type="invalid_json"
                )
                raise OrdsError("INVALID_RESPONSE", "ORDS response is not valid JSON") from exc
        raise OrdsError("REQUEST_FAILED", "ORDS request failed")

    @staticmethod
    def _retry_delay(exc: urllib.error.HTTPError, retry: int) -> float:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        return float(retry_after) if retry_after and retry_after.isdigit() else 0.25 * float(2**retry)

    def _log_success(
        self,
        endpoint: str,
        method: str,
        attempt: int,
        status: int,
        started_at: float,
    ) -> None:
        LOGGER.info(
            "ORDS request completed endpoint=%s method=%s attempt=%d/%d status=%d elapsed_seconds=%.3f",
            endpoint,
            method,
            attempt,
            REQUEST_ATTEMPTS,
            status,
            max(0.0, self._timer() - started_at),
        )

    def _log_failure(
        self,
        endpoint: str,
        method: str,
        attempt: int,
        started_at: float,
        *,
        error_type: str,
        status: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        LOGGER.warning(
            "ORDS request failed endpoint=%s method=%s attempt=%d/%d status=%s "
            "error_type=%s elapsed_seconds=%.3f retry=%s retry_delay_seconds=%s",
            endpoint,
            method,
            attempt,
            REQUEST_ATTEMPTS,
            status if status is not None else "none",
            error_type,
            max(0.0, self._timer() - started_at),
            "true" if retry_delay is not None else "false",
            f"{retry_delay:g}" if retry_delay is not None else "none",
        )
