#!/usr/bin/env bash
# Sebastian Claudiusz Magierowski Feb 7 2026
#
# Run the Sky130 NFET intrinsic gain vs Vds characterization
# Creates .spiceinit with HSA mode, runs ngspice, copies results.
# Parses W, L, Id from the netlist and prepends metadata to av_data.txt.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"
SIM_DIR="$DEVICE_DIR/ngspice/characterization"
NETLIST="$SIM_DIR/nfet_av.sp"
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

# Parse W, L, Id from the netlist (HSA mode: W/L in um, current in A)
W_um=$(grep -i "^XM1" "$NETLIST" | grep -oE 'W=[0-9.]+' | cut -d= -f2)
L_um=$(grep -i "^XM1" "$NETLIST" | grep -oE 'L=[0-9.]+' | cut -d= -f2)
Id_raw=$(grep -i "^I_d" "$NETLIST" | grep -oE 'DC [0-9.]+[a-zA-Z]*' | awk '{print $2}')
# Convert Id to uA (handle u suffix)
Id_uA=$(echo "$Id_raw" | sed 's/u$//' | awk '{printf "%.4g", $1}')
# Extract device name from XM1 line
device=$(grep -i "^XM1" "$NETLIST" | grep -oE 'sky130_fd_pr__[a-z0-9_]+')

# Prepend metadata header to the wrdata output
if [ -f "$SIM_DIR/av_data.txt" ]; then
    {
        echo "# source = nfet_av.sp"
        echo "# date = $(date '+%Y-%m-%d %H:%M:%S')"
        echo "# device = $device"
        echo "# W_um = $W_um"
        echo "# L_um = $L_um"
        echo "# Id_uA = $Id_uA"
        echo "# corner = tt"
        cat "$SIM_DIR/av_data.txt"
    } > "$RESULTS_DIR/av_data.txt"
    rm "$SIM_DIR/av_data.txt"
    echo ""
    echo "Data saved to $RESULTS_DIR/av_data.txt"
fi

echo "Done."
