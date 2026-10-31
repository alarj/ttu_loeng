from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    runtime_root: Path

    @property
    def outputs_root(self) -> Path:
        return self.runtime_root / "outputs"

    @property
    def work_root(self) -> Path:
        return self.runtime_root / "work"


def settings() -> Settings:
    repo_root = Path(os.environ.get("TTU_LOENG_REPO_ROOT", Path.cwd())).resolve()
    runtime_root = Path(os.environ.get("TTU_LOENG_RUNTIME_ROOT", "/srv/ttu-loeng")).resolve()
    return Settings(repo_root=repo_root, runtime_root=runtime_root)


def ensure_runtime_output(path: Path, config: Settings) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(config.repo_root)
    except ValueError:
        pass
    else:
        raise ValueError("--output-dir must be outside the project checkout")

    try:
        resolved.relative_to(config.runtime_root)
    except ValueError as exc:
        raise ValueError("--output-dir must be inside TTU_LOENG_RUNTIME_ROOT") from exc
    return resolved
