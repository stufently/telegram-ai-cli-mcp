#!/usr/bin/env bash
# Build dist-mcpb/telegram-ai-cli-mcp-<pyproject version>.mcpb.
# The only build entry point, locally and in CI. npm, the mcpb CLI, and uv
# run in Docker as the current user; nothing is installed on the host.
# `version` is read from pyproject.toml and is not stored in mcpb/manifest.json.
# Tool names and descriptions are copied from the staged server, the same
# objects `tools/list` publishes, so the manifest cannot drift from the code.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

NODE_IMAGE="node:24.21.0-slim"
UV_IMAGE="ghcr.io/astral-sh/uv:0.12.23-python3.14-trixie-slim"
MCPB_CLI="@anthropic-ai/mcpb@2.1.2"
OUT="dist-mcpb"
NPM_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/promo-mcpb-npm"
UV_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/telegram-ai-cli-mcp-uv"
mkdir -p "$NPM_CACHE" "$UV_CACHE"
rm -rf "$OUT"
mkdir -p "$OUT"

VERSION="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
if [ -z "$VERSION" ]; then
  echo "pyproject.toml version is empty" >&2
  exit 1
fi
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cat >"$WORK/list_tools.py" <<'PY'
import json
import sys

import telegram_ai_cli_mcp.ops  # noqa: F401  (registers every operation)
from telegram_ai_cli_mcp.mcp_server import _tool_for
from telegram_ai_cli_mcp.opspec import REGISTRY

tools = [_tool_for(op, plan=False) for op in REGISTRY.read_tools()]
tools += [_tool_for(op, plan=True) for op in REGISTRY.plan_tools()]
payload = [{"name": tool.name, "description": tool.description or ""} for tool in tools]
names = [item["name"] for item in payload]
if not names or len(names) != len(set(names)):
    sys.exit("tool list is empty or has duplicate names")
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print("listed %d tools" % len(payload))
PY

cat >"$WORK/finish_manifest.py" <<'PY'
import json
import sys
import tomllib

stage, pyproject, source_manifest = sys.argv[1:]
version = tomllib.load(open(pyproject, "rb"))["project"]["version"]
manifest = json.load(open(source_manifest, encoding="utf-8"))
if "version" in manifest:
    sys.exit(f"{source_manifest}: version is substituted from pyproject.toml, do not store it")
live = json.load(open(f"{stage}/tools-list.json", encoding="utf-8"))
declared = [item.get("name") for item in manifest.get("tools") or []]
live_names = [item["name"] for item in live]
if set(declared) != set(live_names) or len(declared) != len(set(live_names)):
    missing = sorted(set(live_names) - set(declared))
    extra = sorted(set(declared) - set(live_names))
    sys.exit(f"tool names differ; missing {missing}; extra {extra}")
for item in live:
    text = str(item.get("description") or "")
    words = text.split()
    if "Use when" not in text or len(words) < 25:
        sys.exit(f"tool {item.get('name')!r} description is not ready ({len(words)} words)")
manifest["version"] = version
manifest["tools"] = [
    {"name": item["name"], "description": item["description"]} for item in live
]
with open(f"{stage}/manifest.json", "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2, ensure_ascii=False)
    handle.write("\n")
print("manifest %s %s, %d tools" % (manifest["name"], version, len(live)))
PY

cat >"$WORK/mcpbignore" <<'EOF'
**/.git/**
**/__pycache__/**
**/*.pyc
**/.env
**/.env.*
**/.venv/**
**/tests/**
**/*.ts
**/*.tsx
**/*.mts
**/*.cts
tools-list.json
uv.lock
EOF

STAGE="$WORK/stage"
mkdir -p "$STAGE"
cp pyproject.toml README.md LICENSE "$STAGE/"
cp -a telegram_ai_cli_mcp "$STAGE/telegram_ai_cli_mcp"
cp mcpb/launch.py "$STAGE/launch.py"
cp "$WORK/mcpbignore" "$STAGE/.mcpbignore"
find "$STAGE" -type d -name __pycache__ -print0 | xargs -0r rm -rf
find "$STAGE" -type f -name '*.pyc' -delete

uid="$(id -u)"
gid="$(id -g)"

docker run --rm -u "$uid:$gid" -e HOME=/tmp \
  -e UV_CACHE_DIR=/cache \
  -e UV_PROJECT_ENVIRONMENT=/tmp/tgai-venv \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$UV_CACHE":/cache \
  -v "$STAGE":/ext \
  -v "$WORK/list_tools.py":/list_tools.py:ro \
  -w /ext \
  "$UV_IMAGE" \
  uv run --directory /ext python /list_tools.py /ext/tools-list.json

python3 "$WORK/finish_manifest.py" "$STAGE" pyproject.toml mcpb/manifest.json
rm -f "$STAGE/tools-list.json" "$STAGE/uv.lock"
rm -rf "$STAGE/.venv"
find "$STAGE" -type d -name __pycache__ -print0 | xargs -0r rm -rf

docker run --rm -u "$uid:$gid" -e HOME=/tmp -e npm_config_cache=/npm \
  -v "$NPM_CACHE":/npm \
  -v "$STAGE":/app \
  -v "$PWD/$OUT":/out \
  -w /app \
  "$NODE_IMAGE" \
  npx -y "$MCPB_CLI" pack /app "/out/telegram-ai-cli-mcp-${VERSION}.mcpb"

test -f "$OUT/telegram-ai-cli-mcp-${VERSION}.mcpb"
echo "built $OUT/telegram-ai-cli-mcp-${VERSION}.mcpb"
