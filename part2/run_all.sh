#!/usr/bin/env bash
# Starts the mock server, runs every Part 2 exercise, then stops the server.
cd "$(dirname "$0")"
python mock_arcgis.py 2>/dev/null &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT
sleep 1
export ARCGIS_TOKEN=secret123
for f in [0-9][0-9]_*.py; do
  echo; echo "================ $f"
  python "$f" || echo "!! $f FAILED"
done
