"""Simple CLI to exercise a Grok-compatible chat endpoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Final

import httpx
from dotenv import load_dotenv

DEFAULT_ENDPOINT: Final[str] = "/v1/chat/completions"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a test chat completion request to a Grok API endpoint.",
    )
    parser.add_argument("prompt", help="User message to send to Grok.")
    parser.add_argument(
        "--model",
        default="grok-4-fast",
        help="Model identifier to request (default: %(default)s).",
    )
    parser.add_argument(
        "--system",
        default="You are a helpful assistant.",
        help="Optional system prompt.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"API path appended to GROK_BASE_URL (default: {DEFAULT_ENDPOINT}).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        help="Maximum number of tokens to generate.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP client timeout in seconds.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the full JSON response instead of a compact summary.",
    )
    return parser


@dataclass(slots=True, frozen=True)
class GrokRequest:
    """Parameters for the Grok chat call."""

    model: str
    prompt: str
    system_prompt: str
    endpoint: str
    max_tokens: int
    temperature: float


@dataclass(slots=True)
class GrokClient:
    """Tiny HTTP wrapper around the Grok REST API."""

    base_url: str
    token: str
    timeout: float

    def chat(self, request: GrokRequest) -> dict[str, Any]:
        """Send a chat completion request."""
        url = f"{self.base_url.rstrip('/')}{request.endpoint}"
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.prompt},
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()


def _load_env_credentials() -> tuple[str, str]:
    load_dotenv()
    base_url = os.getenv("GROK_BASE_URL")
    token = os.getenv("GROK_AUTH_TOKEN")
    if not base_url:
        raise RuntimeError("Missing GROK_BASE_URL in environment or .env file.")
    if not token:
        raise RuntimeError("Missing GROK_AUTH_TOKEN in environment or .env file.")
    return base_url, token


def _render_response(data: dict[str, Any]) -> str:
    """Return either the assistant content or a JSON dump fallback."""
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return json.dumps(data, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        base_url, token = _load_env_credentials()
    except RuntimeError as exc:
        parser.error(str(exc))

    request = GrokRequest(
        model=args.model,
        prompt=args.prompt,
        system_prompt=args.system,
        endpoint=args.endpoint,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )

    client = GrokClient(base_url=base_url, token=token, timeout=args.timeout)
    try:
        response_json = client.chat(request)
    except httpx.HTTPStatusError as exc:
        body = exc.response.text
        parser.error(f"Request failed ({exc.response.status_code}): {body}")
    except httpx.HTTPError as exc:
        parser.error(f"HTTP error: {exc}")  # pragma: no cover - network side effect

    if args.raw:
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
    else:
        print(_render_response(response_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
