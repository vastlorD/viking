"""Command line interface for Integrity Guard."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .core import IntegrityError, build_baseline, compare, scan, verify_baseline
from .storage import atomic_json, create_key, read_json, read_key


def _paths(args):
    root = Path(args.path).resolve(strict=False)
    baseline = Path(args.baseline).resolve(strict=False)
    key_file = Path(args.key_file).resolve(strict=False)
    protected = [baseline, key_file]
    if getattr(args, "report", None):
        protected.append(Path(args.report).resolve(strict=False))
    return root, baseline, key_file, protected


def _check(args):
    root, baseline_path, key_path, protected = _paths(args)
    baseline = read_json(baseline_path)
    key = read_key(key_path)
    verify_baseline(baseline, key)
    if Path(baseline["root"]).resolve(strict=False) != root:
        raise IntegrityError("A pasta informada não é a pasta registrada na base.")
    current = scan(root, baseline.get("excludes", []), protected)
    result = compare(baseline.get("entries", {}), current)
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    result["root"] = str(root)
    if args.report:
        atomic_json(Path(args.report), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "changed" else 0


def build_parser():
    parser = argparse.ArgumentParser(prog="integrity-guard", description="Monitora alterações em arquivos locais.")
    sub = parser.add_subparsers(dest="command", required=True)
    keygen = sub.add_parser("keygen", help="Cria uma chave local de assinatura")
    keygen.add_argument("--key-file", default=".integrity-key")
    keygen.add_argument("--force", action="store_true")
    init = sub.add_parser("init", help="Cria a base assinada")
    init.add_argument("path")
    init.add_argument("--baseline", default="baseline.json")
    init.add_argument("--key-file", default=".integrity-key")
    init.add_argument("--exclude", action="append", default=[])
    init.add_argument("--force", action="store_true")
    check = sub.add_parser("check", help="Compara a pasta com a base")
    check.add_argument("path")
    check.add_argument("--baseline", default="baseline.json")
    check.add_argument("--key-file", default=".integrity-key")
    check.add_argument("--report")
    watch = sub.add_parser("watch", help="Repete a verificação em intervalo fixo")
    watch.add_argument("path")
    watch.add_argument("--baseline", default="baseline.json")
    watch.add_argument("--key-file", default=".integrity-key")
    watch.add_argument("--report")
    watch.add_argument("--interval", type=float, default=60)
    watch.add_argument("--once", action="store_true", help=argparse.SUPPRESS)
    return parser


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "keygen":
            create_key(Path(args.key_file), args.force)
            print(f"Chave criada em {Path(args.key_file).resolve()}.")
            return 0
        if args.command == "init":
            root, baseline, key_file, protected = _paths(args)
            if baseline.exists() and not args.force:
                raise IntegrityError("A base já existe. Use --force para recriá-la após revisar as alterações.")
            value = build_baseline(root, read_key(key_file), args.exclude, protected)
            atomic_json(baseline, value)
            print(f"Base criada com {len(value['entries'])} entradas em {baseline}.")
            return 0
        if args.command == "check":
            return _check(args)
        if args.interval <= 0:
            raise IntegrityError("O intervalo deve ser positivo.")
        while True:
            status = _check(args)
            if args.once:
                return status
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 130
    except IntegrityError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 3


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
