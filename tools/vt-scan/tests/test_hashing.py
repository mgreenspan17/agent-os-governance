# Program: vt-scan / tests/test_hashing.py
# Use case: Verify deterministic hashing, path-traversal refusal, symlink
#   refusal, and size-cap behavior.

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from vt_scan.hashing import (
    DEFAULT_MAX_FILE_BYTES,
    FileHashError,
    hash_set,
    sha256_file,
)


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.bin"
    p.write_bytes(b"hello vt-scan " * 1024)
    return p


def test_hash_set_is_deterministic(sample_file: Path) -> None:
    a = hash_set(str(sample_file))
    b = hash_set(str(sample_file))
    assert a == b
    assert a.size_bytes == sample_file.stat().st_size


def test_hash_set_matches_stdlib(sample_file: Path) -> None:
    data = sample_file.read_bytes()
    expected_sha256 = hashlib.sha256(data).hexdigest()
    expected_sha1 = hashlib.sha1(data).hexdigest()
    expected_md5 = hashlib.md5(data).hexdigest()
    h = hash_set(str(sample_file))
    assert h.sha256 == expected_sha256
    assert h.sha1 == expected_sha1
    assert h.md5 == expected_md5


def test_sha256_file_matches_hashlib(sample_file: Path) -> None:
    expected = hashlib.sha256(sample_file.read_bytes()).hexdigest()
    assert sha256_file(str(sample_file)) == expected


def test_hash_set_refuses_traversal(tmp_path: Path) -> None:
    bad = str(tmp_path / ".." / "escape.bin")
    with pytest.raises(FileHashError):
        hash_set(bad)


def test_hash_set_refuses_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.bin"
    target.write_bytes(b"x" * 16)
    link = tmp_path / "link.bin"
    os.symlink(str(target), str(link))
    with pytest.raises(FileHashError):
        hash_set(str(link))


def test_hash_set_refuses_oversize(tmp_path: Path) -> None:
    p = tmp_path / "big.bin"
    p.write_bytes(b"abcdef")  # 6 bytes
    with pytest.raises(FileHashError):
        # max_bytes is the *maximum allowed*, so 5 must reject a 6-byte file.
        hash_set(str(p), max_bytes=5)


def test_hash_set_empty_path() -> None:
    with pytest.raises(FileHashError):
        hash_set("")


def test_hash_set_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileHashError):
        hash_set(str(tmp_path / "does-not-exist"))


def test_default_size_cap_is_positive() -> None:
    assert DEFAULT_MAX_FILE_BYTES > 0
