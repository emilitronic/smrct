#!/bin/bash
# Sebastian Claudiusz Magierowski May 20 2026
# Run ROIC DT integrator TIA simulation (standalone Spectre)
# Requires: Spectre on PATH (source /CMC/scripts/cadence.spectre23.10.063.csh)
#           AHDLCMI_GCC_HOME set for VerilogA compilation on seqo
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CIRCUIT_DIR="$(dirname "$SCRIPT_DIR")"
NETLIST="$CIRCUIT_DIR/testbenches/standalone/tb_TIA1.scs"
RESULTS_DIR="$CIRCUIT_DIR/results/standalone/TIA1"
LOG_FILE="$RESULTS_DIR/spectre.log"

if ! command -v spectre >/dev/null 2>&1; then
    echo "ERROR: 'spectre' not found in PATH."
    echo "  source /CMC/scripts/cadence.spectre23.10.063.csh"
    exit 1
fi

if [ -z "$AHDLCMI_GCC_HOME" ]; then
    echo "WARNING: AHDLCMI_GCC_HOME not set — VerilogA compilation may fail."
    echo "  export AHDLCMI_GCC_HOME=\$HOME/.local/ahdlgcc"
fi

mkdir -p "$RESULTS_DIR"

echo "=================================================="
echo "ROIC DT Integrator TIA Simulation (tb_TIA1)"
echo "Netlist: $NETLIST"
echo "Results: $RESULTS_DIR"
echo "=================================================="

spectre "$NETLIST" -outdir "$RESULTS_DIR" -format psfascii =log "$LOG_FILE"

echo ""
echo "Done. Results in $RESULTS_DIR"
