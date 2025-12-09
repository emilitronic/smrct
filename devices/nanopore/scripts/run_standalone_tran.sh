#!/bin/bash
# Nanopore transient standalone simulation
#
# By default this uses "cad-spec", a local wrapper for Cadence spectre used at EMIL.
# On other setups you can call it with a different command, e.g.:
#   ./run_standalone_tran.sh spectre

set -e

SPECTRE_CMD="${1:-cad-spec}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"

NETLIST="$DEVICE_DIR/testbenches/standalone/tb_tran.scs"
RESULTS_DIR="$DEVICE_DIR/results/standalone/tran"
LOG_FILE="$RESULTS_DIR/spectre_tran.log"

if [ ! -f "$NETLIST" ]; then
    echo "ERROR: Netlist not found:"
    echo "  $NETLIST"
    exit 1
fi

if ! command -v "$SPECTRE_CMD" >/dev/null 2>&1; then
    echo "ERROR: Command '$SPECTRE_CMD' not found in PATH."
    echo "       Use your local spectre wrapper, for example:"
    echo "         ./run_standalone_tran.sh spectre"
    exit 1
fi

mkdir -p "$RESULTS_DIR"

echo "=================================================="
echo "Nanopore Transient Standalone Simulation"
echo "=================================================="
echo "Netlist:      $NETLIST"
echo "Results dir:  $RESULTS_DIR"
echo "Log file:     $LOG_FILE"
echo "Spectre cmd:  $SPECTRE_CMD"
echo "=================================================="

cd "$RESULTS_DIR"

if "$SPECTRE_CMD" "$NETLIST" =log "$LOG_FILE"; then
    echo
    echo "Transient simulation completed successfully."
    echo "Results available in:"
    echo "  $RESULTS_DIR"
else
    echo
    echo "ERROR: Transient simulation failed. Check log file:"
    echo "  $LOG_FILE"
    exit 1
fi
