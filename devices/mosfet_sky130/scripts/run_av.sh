#!/usr/bin/env bash
# Sebastian Claudiusz Magierowski Feb 7 2026
#
# Run the Sky130 NFET intrinsic gain vs Vds characterization
# Creates .spiceinit with HSA mode, runs ngspice, copies results.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"
SIM_DIR="$DEVICE_DIR/ngspice/characterization"
RESULTS_DIR="$DEVICE_DIR/results/av"

mkdir -p "$RESULTS_DIR"

# Create .spiceinit in the characterization dir (ngspice reads from cwd)
cat > "$SIM_DIR/.spiceinit" << 'EOF'
set ngbehavior=hsa
set ng_nomodcheck
EOF

echo "Running: nfet_av.sp"
echo "Results: $RESULTS_DIR"
echo ""

cd "$SIM_DIR"
ngspice -b nfet_av.sp 2>&1 | tee "$RESULTS_DIR/nfet_av.log"

# Move data file to results
if [ -f "$SIM_DIR/av_data.txt" ]; then
    mv "$SIM_DIR/av_data.txt" "$RESULTS_DIR/av_data.txt"
    echo ""
    echo "Data saved to $RESULTS_DIR/av_data.txt"
fi

echo "Done."
