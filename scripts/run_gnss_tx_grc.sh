#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
FLOWGRAPH_PATH="${PROJECT_ROOT}/flowgraphs/gnss_tx_main.grc"
CUSTOM_BLOCKS_PATH="${PROJECT_ROOT}/grc/blocks"
SYSTEM_BLOCKS_PATH="/usr/share/gnuradio/grc/blocks"

MODE="companion"
HEADLESS=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [--run] [--companion] [--headless]

Launch the main GNU Radio flowgraph with the project's custom GRC blocks.

Options:
  --companion  Open gnss_tx_main.grc in GNU Radio Companion (default)
  --run        Run gnss_tx_main.grc directly via grcc -r
  --headless   Force offscreen Qt when used with --run
  -h, --help   Show this help message
EOF
}

while (($# > 0)); do
    case "$1" in
        --companion|--open)
            MODE="companion"
            ;;
        --run)
            MODE="run"
            ;;
        --headless)
            HEADLESS=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown argument: $1" >&2
            echo "" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

if [[ ! -f "${FLOWGRAPH_PATH}" ]]; then
    echo "[ERROR] Flowgraph not found: ${FLOWGRAPH_PATH}" >&2
    exit 1
fi

if [[ ! -d "${CUSTOM_BLOCKS_PATH}" ]]; then
    echo "[ERROR] Custom GRC block path not found: ${CUSTOM_BLOCKS_PATH}" >&2
    exit 1
fi

if [[ -n "${GRC_BLOCKS_PATH:-}" ]]; then
    export GRC_BLOCKS_PATH="${SYSTEM_BLOCKS_PATH}:${CUSTOM_BLOCKS_PATH}:${GRC_BLOCKS_PATH}"
else
    export GRC_BLOCKS_PATH="${SYSTEM_BLOCKS_PATH}:${CUSTOM_BLOCKS_PATH}"
fi

case "${MODE}" in
    companion)
        if ! command -v gnuradio-companion >/dev/null 2>&1; then
            echo "[ERROR] gnuradio-companion was not found in PATH." >&2
            exit 1
        fi

        echo "[INFO] Opening GNU Radio Companion with ${FLOWGRAPH_PATH}"
        exec gnuradio-companion "${FLOWGRAPH_PATH}"
        ;;
    run)
        if ! command -v grcc >/dev/null 2>&1; then
            echo "[ERROR] grcc was not found in PATH." >&2
            exit 1
        fi

        if [[ "${HEADLESS}" == "1" ]]; then
            export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
        elif [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" && -z "${QT_QPA_PLATFORM:-}" ]]; then
            echo "[ERROR] No display server detected. Re-run with --headless or set DISPLAY/QT_QPA_PLATFORM." >&2
            exit 1
        fi

        echo "[INFO] Running ${FLOWGRAPH_PATH} via grcc -r"
        exec grcc -r "${FLOWGRAPH_PATH}"
        ;;
esac
