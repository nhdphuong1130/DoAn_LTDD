#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/backend"

if [ -f "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
else
  UV="uv"
fi

echo "Building full knowledge graph in Neo4j..."
$UV run python scripts/build_full_knowledge_graph.py
