#!/usr/bin/env bash
# Install the built wheel with each extra in a clean environment and check what it brings in.
set -euo pipefail

wheel=${1:?usage: check_wheel_extras.sh path/to/wheel.whl}
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

check() {
  local extra=$1 module=$2 adk=$3
  local venv="$workdir/$extra"
  uv venv --quiet "$venv"
  uv pip install --quiet --python "$venv/bin/python" "${wheel}[${extra}]"
  (cd "$workdir" && "$venv/bin/python" - "$module" "$adk" <<'PY'
import importlib
import importlib.util
import sys

from compliance_core.version import framework_version

module, adk = sys.argv[1], sys.argv[2] == "yes"
importlib.import_module(module)
try:
    has_adk = importlib.util.find_spec("google.adk") is not None
except ModuleNotFoundError:
    has_adk = False
assert has_adk == adk, f"{module}: unexpected Google ADK presence"
assert framework_version() != "0+unknown"
print(f"{module}: ok ({framework_version()})")
PY
  )
}

check mcp compliance_mcp.server no
check api compliance_api.app no
check server compliance_mcp.server no
check acp compliance_protocols.acp yes
check a2a compliance_protocols.a2a yes
