#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$BIN_DIR/../lib/smiles2docking" && pwd)"
INTERNAL_DIR="$APP_ROOT/_internal"
OPENBABEL_DIR="$INTERNAL_DIR/openbabel"

export PATH="$OPENBABEL_DIR/bin:$OPENBABEL_DIR:${PATH:-}"
export LD_LIBRARY_PATH="$OPENBABEL_DIR/lib:$OPENBABEL_DIR:$INTERNAL_DIR:${LD_LIBRARY_PATH:-}"

exec "$APP_ROOT/SMILES2DockingDesktop" "$@"
