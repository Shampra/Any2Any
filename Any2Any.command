#!/bin/bash
# Double-click launcher for macOS: starts the local Any2Any interface.
# Anytype must be open for an Anytype import; Anytwo must be open as the destination.
cd "$(dirname "$0")" || exit 1
export PYTHONIOENCODING=utf-8
if [ -x "./Any2Any" ]; then
  exec ./Any2Any --profile unified "$@"
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 or newer is required: https://www.python.org/downloads/macos/"
  echo "Appuyez sur Entrée pour fermer…"; read -r _
  exit 1
fi
exec python3 app/server.py --profile unified "$@"
