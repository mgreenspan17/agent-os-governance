# Program: vt-scan / hashing.py
# Use case: Stream-hash local files (sha256/sha1/md5) so we can look them up on
#   VirusTotal by hash without uploading the bytes prematurely. Reuses the
#   path-safety guard style from universal-ingestion-suite's canonicalization.
# Version history:
#   0.1.0  2026-11-24  Phase A: initial implementation. sha256_file,
#                        hash_set, _canonicalize_path, FileHashError.

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


CHUNK_SIZE = 4 * 1024 * 1024  # 4 MiB streaming chunks
DEFAULT_MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MiB — matches VT public API upload cap


class FileHashError(ValueError):
    """Raised when the local file cannot be hashed safely (path, symlink, size)."""


@dataclass
class HashSet:
    """Computed hashes plus the file size, in a single struct that is easy to log
    and serialize. Fields are named to match VT's API conventions."""

    sha256: str
    sha1: str
    md5: str
    size_bytes: int

    def to_dict(self) -> Dict[str, str]:
        return {
            "sha256": self.sha256,
            "sha1": self.sha1,
            "md5": self.md5,
            "size_bytes": str(self.size_bytes),
        }


def _canonicalize_path(path: str) -> str:
    """Normalize to forward slashes and reject paths containing a `..` token.
    Pattern taken from universal-ingestion-suite/backend/app/services/canonicalization.py
    so the two scanners agree on what a safe path looks like."""
    if not isinstance(path, str) or not path:
        raise FileHashError(f"empty or non-string path: {path!r}")
    normalized = os.path.normpath(path).replace("\\", "/")
    if normalized.startswith("/"):
        normalized = normalized.lstrip("/")
    parts = normalized.split("/")
    if ".." in parts:
        raise FileHashError(f"path traversal detected: {path!r}")
    return normalized


def _validate_file(path: str, max_bytes: int) -> Path:
    canonical = _canonicalize_path(path)
    file_path = Path(canonical)
    if file_path.is_symlink():
        raise FileHashError(f"refusing to hash symlink: {path!r}")
    if not file_path.is_file():
        raise FileHashError(f"not a regular file: {path!r}")
    size = file_path.stat().st_size
    if max_bytes > 0 and size > max_bytes:
        raise FileHashError(
            f"refusing to hash file exceeding {max_bytes} bytes: "
            f"{size} bytes at {path!r}"
        )
    return file_path


def sha256_file(path: str, max_bytes: int = DEFAULT_MAX_FILE_BYTES) -> str:
    """Stream-hash a single file with SHA-256. Refuses symlinks, traversal, oversize."""
    file_path = _validate_file(path, max_bytes)
    sha256 = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_set(path: str, max_bytes: int = DEFAULT_MAX_FILE_BYTES) -> HashSet:
    """Stream-compute SHA-256 + SHA-1 + MD5 in a single pass. Same guards as sha256_file."""
    file_path = _validate_file(path, max_bytes)
    sha256 = hashlib.sha256()
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    size = 0
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            sha256.update(chunk)
            sha1.update(chunk)
            md5.update(chunk)
            size += len(chunk)
    return HashSet(
        sha256=sha256.hexdigest(),
        sha1=sha1.hexdigest(),
        md5=md5.hexdigest(),
        size_bytes=size,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m vt_scan.hashing <path>", file=sys.stderr)
        sys.exit(2)
    result = hash_set(sys.argv[1])
    print(f"sha256: {result.sha256}")
    print(f"sha1:   {result.sha1}")
    print(f"md5:    {result.md5}")
    print(f"size:   {result.size_bytes}")
