"""Scope-gated HTTP tool. Exploitation mechanics route through here so every
request is checked against ScopeGuard before it leaves the machine."""
from __future__ import annotations
import time
from typing import Any
import httpx
from ..scope import ScopeGuard, OutOfScope


class HttpTool:
    name = "http_request"
    description = (
        "Send an HTTP request to an IN-SCOPE target and return status, headers, "
        "and body. Requests to out-of-scope hosts are rejected."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "method": {"type": "string", "default": "GET"},
            "url": {"type": "string"},
            "headers": {"type": "object"},
            "body": {"type": "string"},
        },
        "required": ["url"],
        "additionalProperties": False,
    }

    def __init__(self, guard: ScopeGuard):
        self.guard = guard
        self._last = 0.0
        self._min_interval = 1.0 / max(1, guard.scope.rate_limit_rps)

    def run(self, method: str = "GET", url: str = "", headers: dict | None = None,
            body: str | None = None) -> dict[str, Any]:
        try:
            self.guard.check_url(url)
        except OutOfScope as e:
            return {"error": "out_of_scope", "detail": str(e)}
        # crude client-side rate limit
        wait = self._min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        try:
            r = httpx.request(method.upper(), url, headers=headers or {},
                              content=body, timeout=30, follow_redirects=False)
        except httpx.HTTPError as e:
            return {"error": "request_failed", "detail": str(e)}
        return {
            "status": r.status_code,
            "headers": dict(r.headers),
            "body": r.text[:20000],
            "truncated": len(r.text) > 20000,
        }
