"""Atomic JSON and key file handling."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from pathlib import Path

from .core import IntegrityError


def atomic_json(path: Path, value: dict) -> None:
    path = path.resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Não foi possível ler {path}: {error}") from error
    if not isinstance(value, dict):
        raise IntegrityError(f"O arquivo {path} deve conter um objeto JSON.")
    return value


def create_key(path: Path, force=False) -> None:
    path = path.resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as error:
        raise IntegrityError(f"A chave já existe: {path}. Use --force para substituir.") from error
    with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as stream:
        stream.write(secrets.token_hex(32) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def read_key(path: Path) -> bytes:
    try:
        raw = path.read_text(encoding="ascii").strip()
        key = bytes.fromhex(raw)
    except (OSError, UnicodeError, ValueError) as error:
        raise IntegrityError(f"Não foi possível ler a chave: {error}") from error
    if len(key) < 32:
        raise IntegrityError("A chave deve conter pelo menos 32 bytes em hexadecimal.")
    return key
