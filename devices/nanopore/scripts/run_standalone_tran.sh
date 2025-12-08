#!/bin/bash
# Nanopore Transient Standalone Simulation Script
# Runs Spectre transient analysis directly using cad-spec

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"

NETLIST="$DEVICE_DIR/testbenches/standalone/tb_tran.scs"
RESULTS_DIR="$DEVICE_DIR/results/standalone/tran"
LOG_FILE="$RESULTS_DIR/spectre_tran.log"

mkdir -p "$RESULTS_DIR"

echo "=================================================="
echo "Nanopore Transient Standalone Simulation"
echo "=================================================="
echo "Netlist:      $NETLIST"
echo "Results dir:  $RESULTS_DIR"
echo "Log file:     $LOG_FILE"
echo "=================================================="

cd "$RESULTS_DIR"
cad-spec "$NETLIST" =log "$LOG_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "Transient simulation completed successfully!"
    echo "Results available in: $RESULTS_DIR"
else
    echo ""
    echo "ERROR: Transient simulation failed. Check log file:"
    echo "  $LOG_FILE"
    exit 1
fi
