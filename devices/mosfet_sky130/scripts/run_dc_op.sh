#!/usr/bin/env bash
# Sebastian Claudiusz Magierowski Feb 7 2026
#
# Run the Sky130 NFET DC operating point test
# Creates a local .spiceinit with HSA mode, runs ngspice, then cleans up.

set -euo pipefail # 

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" # Get the directory of this script
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"       # Parent folder of script's directory (mosfet_sky130)
NETLIST="$DEVICE_DIR/ngspice/characterization/nfet_dc_op.sp"
RESULTS_DIR="$DEVICE_DIR/results/dc_op"

mkdir -p "$RESULTS_DIR"                     # Ensure results directory exists

# Create .spiceinit in the characterization dir (ngspice reads from cwd)
SPICEINIT="$DEVICE_DIR/ngspice/characterization/.spiceinit"
cat > "$SPICEINIT" << 'EOF'
set ngbehavior=hsa
set ng_nomodcheck
EOF

echo "Running: $NETLIST" 
echo "Results: $RESULTS_DIR"
echo ""

cd "$DEVICE_DIR/ngspice/characterization"
ngspice -b nfet_dc_op.sp 2>&1 | tee "$RESULTS_DIR/nfet_dc_op.log" # Save both stdout and stderr to log file

echo ""
echo "Done. Log saved to $RESULTS_DIR/nfet_dc_op.log"
