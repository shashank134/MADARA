"""Config loading for model routing and program scope."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f) or {}


@dataclass
class ModelConfig:
    backends: dict[str, Any]
    roles: dict[str, Any]
    fallback_order: list[str]

    @classmethod
    def load(cls, path: Path | None = None) -> "ModelConfig":
        data = _load_yaml(path or ROOT / "config" / "model.yaml")
        return cls(
            backends=data["backends"],
            roles=data["roles"],
            fallback_order=data.get("fallback_order", list(data["roles"].keys())),
        )

    def resolve(self, role: str) -> tuple[dict[str, Any], str]:
        """Return (backend_cfg, model_id) for a role name."""
        r = self.roles[role]
        return self.backends[r["backend"]], r["model"]


@dataclass
class Scope:
    program: str
    platform: str
    policy_url: str
    authorization: str
    in_scope: dict[str, Any]
    out_of_scope: dict[str, Any] = field(default_factory=dict)
    rate_limit_rps: int = 5

    @classmethod
    def load(cls, path: Path) -> "Scope":
        d = _load_yaml(Path(path))
        return cls(
            program=d["program"],
            platform=d.get("platform", "self-hosted"),
            policy_url=d.get("policy_url", ""),
            authorization=d.get("authorization", ""),
            in_scope=d.get("in_scope", {}),
            out_of_scope=d.get("out_of_scope", {}),
            rate_limit_rps=int(d.get("rate_limit_rps", 5)),
        )


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v
