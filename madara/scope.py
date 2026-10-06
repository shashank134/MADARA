"""Scope enforcement — the guard that keeps you authorized and paid.

Every outbound request the agent makes is checked against the loaded program
scope. Deny-by-default: if a host is not explicitly in_scope, it is blocked.
This also contains prompt-injection blast radius — a tested page cannot steer
the agent into hitting a third party.
"""
from __future__ import annotations
import fnmatch
from urllib.parse import urlparse
from .config import Scope


class OutOfScope(Exception):
    pass


class ScopeGuard:
    def __init__(self, scope: Scope):
        self.scope = scope
        self._in = [d.lower() for d in scope.in_scope.get("domains", [])]
        self._out = [d.lower() for d in scope.out_of_scope.get("domains", [])]

    def _host_matches(self, host: str, patterns: list[str]) -> bool:
        host = host.lower().rstrip(".")
        return any(fnmatch.fnmatch(host, p) for p in patterns)

    def check_url(self, url: str) -> str:
        host = urlparse(url if "://" in url else f"//{url}", scheme="https").hostname
        if not host:
            raise OutOfScope(f"Cannot parse host from: {url!r}")
        # Explicit out-of-scope always wins.
        if self._host_matches(host, self._out):
            raise OutOfScope(f"{host} is explicitly OUT of scope for {self.scope.program}")
        if not self._host_matches(host, self._in):
            raise OutOfScope(
                f"{host} is not in the in_scope list for {self.scope.program} — denied by default"
            )
        return host

    def is_in_scope(self, url: str) -> bool:
        try:
            self.check_url(url)
            return True
        except OutOfScope:
            return False
