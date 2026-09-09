"""Scanning, signing and comparison logic."""

from __future__ import annotations

import fnmatch
import hashlib
import hmac
import json
import os
import stat
from pathlib import Path

VERSION = 1
DEFAULT_EXCLUDES = (".git", ".git/**", "__pycache__", "**/__pycache__/**", "*.pyc", "**/*.pyc")


class IntegrityError(Exception):
    """Invalid key, baseline or scan input."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _excluded(relative: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns)


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def scan(root: Path, excludes=(), protected_paths=()) -> dict[str, dict]:
    """Return stable metadata for regular files and symbolic links below root."""
    try:
        root = root.resolve(strict=True)
    except OSError as error:
        raise IntegrityError(f"Pasta monitorada indisponível: {error}") from error
    if not root.is_dir():
        raise IntegrityError("O caminho monitorado deve ser uma pasta.")
    patterns = tuple(DEFAULT_EXCLUDES) + tuple(excludes)
    protected = {Path(path).resolve(strict=False) for path in protected_paths}
    entries: dict[str, dict] = {}

    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept = []
        for name in sorted(directories):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.resolve(strict=False) in protected or _excluded(relative, patterns):
                continue
            if path.is_symlink():
                entries[relative] = {"type": "symlink", "target": os.readlink(path)}
            else:
                kept.append(name)
        directories[:] = kept

        for name in sorted(files):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.resolve(strict=False) in protected or _excluded(relative, patterns):
                continue
            try:
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode):
                    entries[relative] = {"type": "symlink", "target": os.readlink(path)}
                elif stat.S_ISREG(info.st_mode):
                    entries[relative] = {
                        "type": "file",
                        "size": info.st_size,
                        "sha256": _hash_file(path),
                    }
            except (FileNotFoundError, PermissionError, OSError) as error:
                raise IntegrityError(f"Não foi possível ler {relative}: {error}") from error
    return dict(sorted(entries.items()))


def build_baseline(root: Path, key: bytes, excludes=(), protected_paths=()) -> dict:
    if len(key) < 32:
        raise IntegrityError("A chave deve ter pelo menos 32 bytes.")
    try:
        root = root.resolve(strict=True)
    except OSError as error:
        raise IntegrityError(f"Pasta monitorada indisponível: {error}") from error
    unsigned = {
        "version": VERSION,
        "algorithm": "HMAC-SHA256",
        "root": str(root),
        "excludes": list(excludes),
        "entries": scan(root, excludes, protected_paths),
    }
    return {**unsigned, "signature": hmac.new(key, _canonical(unsigned), hashlib.sha256).hexdigest()}


def verify_baseline(baseline: dict, key: bytes) -> None:
    if not isinstance(baseline, dict) or baseline.get("version") != VERSION:
        raise IntegrityError("Formato ou versão da base inválida.")
    signature = baseline.get("signature")
    if not isinstance(signature, str):
        raise IntegrityError("A base não possui assinatura.")
    if (baseline.get("algorithm") != "HMAC-SHA256"
            or not isinstance(baseline.get("root"), str)
            or not isinstance(baseline.get("excludes"), list)
            or not all(isinstance(pattern, str) for pattern in baseline["excludes"])
            or not isinstance(baseline.get("entries"), dict)):
        raise IntegrityError("A estrutura da base é inválida.")
    unsigned = {name: value for name, value in baseline.items() if name != "signature"}
    expected = hmac.new(key, _canonical(unsigned), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise IntegrityError("Assinatura inválida: a base, ou a chave, não confere.")


def compare(expected: dict[str, dict], current: dict[str, dict]) -> dict:
    expected_names, current_names = set(expected), set(current)
    created = sorted(current_names - expected_names)
    removed = sorted(expected_names - current_names)
    modified = sorted(name for name in expected_names & current_names if expected[name] != current[name])
    return {
        "status": "changed" if created or removed or modified else "clean",
        "summary": {"created": len(created), "modified": len(modified), "removed": len(removed)},
        "created": created,
        "modified": modified,
        "removed": removed,
    }
