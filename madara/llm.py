"""Model-agnostic LLM layer.

The agent talks to ONE interface (`Backend.complete`). Claude and a local
open-weights model are both implementations behind it. Swapping models — because
one is deprecated, or because you got CVP access on a stronger one — is a config
change in config/model.yaml, never a code change here.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol


class Refusal(Exception):
    """Raised when a backend declines a request (e.g. Claude cyber safeguard).

    On the Anthropic API, flagged cyber requests return HTTP 200 with
    stop_reason == "refusal". We surface that as this exception so the agent
    can cascade to the next role in fallback_order (e.g. a CVP'd model, or the
    local floor).
    """
    def __init__(self, category: str | None, explanation: str | None):
        self.category = category
        self.explanation = explanation
        super().__init__(f"refused (category={category}): {explanation}")


@dataclass
class LLMResponse:
    content: list[dict[str, Any]]   # normalized Anthropic-style content blocks
    stop_reason: str
    raw: Any = None


class Backend(Protocol):
    def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse: ...


class AnthropicBackend:
    """Official Anthropic SDK. Model id (e.g. claude-opus-4-6) is passed in."""

    def __init__(self, cfg: dict[str, Any]):
        import anthropic  # imported lazily so `local` users need not install it
        self._anthropic = anthropic
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY / ant profile
        self.thinking = cfg.get("thinking", "adaptive")
        self.max_tokens = int(cfg.get("max_tokens", 16000))

    def complete(self, *, model, system, messages, tools=None) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": messages,
        }
        # opus-4-6 / 5 / 5.5 all take adaptive thinking (not budget_tokens).
        if self.thinking:
            kwargs["thinking"] = {"type": self.thinking}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.messages.create(**kwargs)
        # Guard the refusal stop_reason BEFORE reading content.
        if resp.stop_reason == "refusal":
            det = getattr(resp, "stop_details", None)
            raise Refusal(
                getattr(det, "category", None),
                getattr(det, "explanation", None),
            )
        content = [blk.model_dump() for blk in resp.content]
        return LLMResponse(content=content, stop_reason=resp.stop_reason, raw=resp)


class OllamaBackend:
    """Local open-weights floor via Ollama's OpenAI-compatible /v1 endpoint.

    No provider guardrails, fully local. Capability is lower than Claude, and
    tool-use translation here is minimal — good enough for recon planning,
    payload drafting and code analysis; extend for full agentic tool loops.
    """

    def __init__(self, cfg: dict[str, Any]):
        from openai import OpenAI
        self.client = OpenAI(
            base_url=cfg.get("base_url", "http://localhost:11434/v1"),
            api_key="ollama",  # Ollama ignores the key
        )

    def complete(self, *, model, system, messages, tools=None) -> LLMResponse:
        # Flatten Anthropic-style messages to OpenAI chat format (text only).
        oai_msgs = [{"role": "system", "content": system}]
        for m in messages:
            text = m["content"] if isinstance(m["content"], str) else _blocks_to_text(m["content"])
            oai_msgs.append({"role": m["role"], "content": text})
        resp = self.client.chat.completions.create(model=model, messages=oai_msgs)
        text = resp.choices[0].message.content or ""
        return LLMResponse(
            content=[{"type": "text", "text": text}],
            stop_reason="end_turn",
            raw=resp,
        )


def _blocks_to_text(blocks: list[dict[str, Any]]) -> str:
    out = []
    for b in blocks:
        if b.get("type") == "text":
            out.append(b["text"])
        elif b.get("type") == "tool_result":
            out.append(str(b.get("content", "")))
    return "\n".join(out)


def make_backend(cfg: dict[str, Any]) -> Backend:
    kind = cfg["kind"]
    if kind == "anthropic":
        return AnthropicBackend(cfg)
    if kind == "ollama":
        return OllamaBackend(cfg)
    raise ValueError(f"Unknown backend kind: {kind}")
