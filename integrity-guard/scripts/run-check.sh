#!/usr/bin/env sh
set -u

if [ "$#" -lt 1 ]; then
  echo "Uso: $0 PASTA [BASE] [CHAVE] [RELATORIO]" >&2
  exit 3
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(dirname -- "$script_dir")
cd "$project_dir" || exit 3
python3 -m integrity_guard check "$1" \
  --baseline "${2:-baseline.json}" \
  --key-file "${3:-.integrity-key}" \
  --report "${4:-reports/latest.json}"
