from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be positive")
    return value


def _positive_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class WebSettings:
    base_url: str
    google_client_id: str
    session_secret: str
    runtime_root: Path
    ui_status_poll_interval_seconds: int

    @classmethod
    def from_env(cls) -> "WebSettings":
        return cls(
            base_url=os.getenv("APP_BASE_URL", "https://ttu-loeng.fun-o.eu").strip().rstrip("/"),
            google_client_id=_required("GOOGLE_CLIENT_ID"),
            session_secret=_required("SESSION_SECRET"),
            runtime_root=Path(os.getenv("TTU_LOENG_RUNTIME_ROOT", "/srv/ttu-loeng")).resolve(),
            ui_status_poll_interval_seconds=_positive_int("UI_STATUS_POLL_INTERVAL_SECONDS", 30),
        )


@dataclass(frozen=True)
class OrdsSettings:
    base_url: str
    client_id: str
    client_secret: str
    token_refresh_margin_seconds: int
    claim_interval_seconds: int
    heartbeat_interval_seconds: int
    request_timeout_seconds: float = 1.5

    @classmethod
    def from_env(cls) -> "OrdsSettings":
        return cls(
            base_url=_required("ORDS_BASE_URL").rstrip("/"),
            client_id=_required("ORDS_OAUTH_CLIENT_ID"),
            client_secret=_required("ORDS_OAUTH_CLIENT_SECRET"),
            token_refresh_margin_seconds=_positive_int("ORDS_TOKEN_REFRESH_MARGIN_SECONDS", 60),
            claim_interval_seconds=_positive_int("ORDS_CLAIM_INTERVAL_SECONDS", 300),
            heartbeat_interval_seconds=_positive_int("ORDS_HEARTBEAT_INTERVAL_SECONDS", 300),
            request_timeout_seconds=_positive_float("ORDS_REQUEST_TIMEOUT_SECONDS", 1.5),
        )


@dataclass(frozen=True)
class WorkerSettings:
    runtime_root: Path
    host_id: str
    cpu_threads: int
    asr_model: str
    asr_revision: str
    asr_model_subfolder: str
    asr_configuration_id: str
    slide_coarse_seconds: float
    slide_refine_seconds: float

    @classmethod
    def from_env(cls) -> "WorkerSettings":
        return cls(
            runtime_root=Path(os.getenv("TTU_LOENG_RUNTIME_ROOT", "/srv/ttu-loeng")).resolve(),
            host_id=os.getenv("WORKER_HOST_ID", "ttu-loeng-server").strip() or "ttu-loeng-server",
            cpu_threads=_positive_int("ASR_CPU_THREADS", 3),
            asr_model="TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604",
            asr_revision="310c550922fc1d1bebf3fad41f9b33ede6652bdc",
            asr_model_subfolder="ct2",
            asr_configuration_id="taltechnlp-turbo-et-verbatim-2604-int8",
            slide_coarse_seconds=float(os.getenv("SLIDE_COARSE_INTERVAL_SECONDS", "20")),
            slide_refine_seconds=float(os.getenv("SLIDE_REFINE_INTERVAL_SECONDS", "2")),
        )

