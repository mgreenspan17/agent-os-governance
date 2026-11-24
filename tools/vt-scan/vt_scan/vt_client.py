# Program: vt-scan / vt_client.py
# Use case: Thin wrapper over the VirusTotal public API. Phase A supports
#   hash-only lookups (`GET /files/{sha256}`); uploads are intentionally
#   stubbed for Phase B. Mask the x-apikey header on any error path so the
#   secret never leaks through structured logs.
# Version history:
#   0.1.0  2026-11-24  Phase A: lookup_file(key resolution, error mapping,
#                        header redaction, normalized VTVerdict).

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


VT_API_BASE = "https://www.virustotal.com/api/v3"
PUBLIC_KEY_ENV = "VT_API_KEY"


class VTClientError(Exception):
    """Base class for VT-client failures."""


class VTMissingKeyError(VTClientError):
    """Raised when VT_API_KEY is not configured."""


class VTAuthError(VTClientError):
    """Raised when VT rejects the key (401/403)."""


class VTRateLimitError(VTClientError):
    """Raised when VT returns 429. Exposes Retry-After."""

    def __init__(self, retry_after_seconds: float) -> None:
        super().__init__("rate limited by VirusTotal")
        self.retry_after_seconds = retry_after_seconds


@dataclass
class VTVerdict:
    """Normalized verdict from a VirusTotal file report.

    `found=False` means VT returned 404 (no prior report). `engines_total` is
    the sum of `last_analysis_stats` so we can report coverage even when zero
    detections occur."""

    malicious: int
    suspicious: int
    undetected: int
    harmless: int
    engines_total: int
    vt_link: str
    raw: dict
    found: bool

    def to_dict(self) -> dict:
        return {
            "malicious": self.malicious,
            "suspicious": self.suspicious,
            "undetected": self.undetected,
            "harmless": self.harmless,
            "engines_total": self.engines_total,
            "vt_link": self.vt_link,
            "found": self.found,
        }


def mask_api_key(value: str) -> str:
    """Render an API key as the secret-placeholder used in logs.

    Format: `{{VT_API_KEY}}` plus the trailing four chars so operators can
    correlate against their secret manager without exposing the rest."""
    if not value:
        return ""
    tail = value[-4:] if len(value) >= 4 else value
    return "{{VT_API_KEY}}:" + tail


def masked_headers(headers: dict) -> dict:
    """Return a copy of `headers` with `x-apikey` values redacted."""
    redacted: dict = {}
    for k, v in headers.items():
        if k.lower() == "x-apikey":
            redacted[k] = mask_api_key(v) if isinstance(v, str) else "{{VT_API_KEY}}"
        else:
            redacted[k] = v
    return redacted


def resolve_api_key() -> str:
    """Read VT_API_KEY from the environment. Never log the returned value."""
    value = os.environ.get(PUBLIC_KEY_ENV, "").strip()
    if not value:
        raise VTMissingKeyError(
            f"environment variable {PUBLIC_KEY_ENV} is not set; refusing to call VirusTotal"
        )
    return value


class VTClient:
    """Wrapper around requests for the VT v3 file endpoints.

    `requests` is imported lazily so the rest of the package remains usable
    on machines without the dependency (CLI cache/stats still work)."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 20) -> None:
        if api_key is not None:
            self.api_key = api_key
        else:
            try:
                self.api_key = resolve_api_key()
            except VTMissingKeyError:
                self.api_key = ""
        self.timeout_seconds = timeout_seconds
        self._last_status: Optional[int] = None
        # Lazy import so a missing `requests` is reported close to use.
        try:
            import requests  # noqa: F401  # type: ignore

            self._requests_import_ok = True
        except ImportError:
            self._requests_import_ok = False

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    @property
    def key_id(self) -> str:
        """Masked identifier safe to log."""
        if not self.api_key:
            return ""
        return "VT-****" + self.api_key[-4:]

    def _headers(self) -> dict:
        return {"x-apikey": self.api_key} if self.api_key else {}

    def lookup_file(self, sha256: str) -> VTVerdict:
        if not self._requests_import_ok:
            raise VTClientError(
                "the 'requests' library is not installed; "
                "install it via pip to call VirusTotal"
            )
        if not self.api_key:
            raise VTMissingKeyError("no VT_API_KEY configured; refusing network call")
        if not sha256:
            raise ValueError("sha256 is required")
        import requests  # local import to keep package import-time clean

        url = f"{VT_API_BASE}/files/{sha256}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise VTClientError(f"network error contacting VirusTotal: {exc}") from exc
        self._last_status = resp.status_code
        if resp.status_code == 404:
            # 404 means VT has no prior evaluation for this hash. This is the
            # expected path for unknown binaries and the cue to upload.
            return VTVerdict(0, 0, 0, 0, 0, "", {}, found=False)
        if resp.status_code in (401, 403):
            raise VTAuthError(f"VirusTotal rejected API key (status {resp.status_code})")
        if resp.status_code == 429:
            raise VTRateLimitError(_retry_after(resp))
        if resp.status_code >= 400:
            redacted = masked_headers(self._headers())
            raise VTClientError(
                f"VT lookup failed status={resp.status_code} "
                f"headers={redacted} body={resp.text[:200]!r}"
            )
        return _parse_file_report(resp.json())

    def upload_file(self, path: str) -> str:
        """Stub for Phase B: returns an analysis id or raises NotImplementedError."""
        raise NotImplementedError(
            "uploads are not implemented in Phase A; use lookup only"
        )


def _parse_file_report(payload: dict) -> VTVerdict:
    attrs = (payload.get("data") or {}).get("attributes") or {}
    stats = attrs.get("last_analysis_stats") or {}
    link = (payload.get("data") or {}).get("links", {}).get("self", "")
    engines_total = int(sum(int(v) for v in stats.values()))
    return VTVerdict(
        malicious=int(stats.get("malicious", 0)),
        suspicious=int(stats.get("suspicious", 0)),
        undetected=int(stats.get("undetected", 0)),
        harmless=int(stats.get("harmless", 0)),
        engines_total=engines_total,
        vt_link=link,
        raw=payload,
        found=True,
    )


def _retry_after(resp) -> float:
    try:
        return float(resp.headers.get("Retry-After", "60"))
    except ValueError:
        return 60.0


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m vt_scan.vt_client <sha256>", file=sys.stderr)
        sys.exit(2)
    client = VTClient()
    if not client.has_key:
        print("VT_API_KEY not set; refusing live lookup. Set the env var to run.", file=sys.stderr)
        sys.exit(5)
    verdict = client.lookup_file(sys.argv[1])
    print(json.dumps(verdict.to_dict(), indent=2))
