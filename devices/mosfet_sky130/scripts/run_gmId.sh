#!/usr/bin/env bash
# Sebastian Claudiusz Magierowski Feb 7 2026
#
# Run the Sky130 FET gm/Id vs Vgs characterization
# Creates .spiceinit with HSA mode, runs ngspice, prepends metadata to output.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"
SIM_DIR="$DEVICE_DIR/ngspice/characterization"
NETLIST="$SIM_DIR/fet_gmId.sp"
RESULTS_DIR="$DEVICE_DIR/results/gmId"

mkdir -p "$RESULTS_DIR"

# Create .spiceinit in the characterization dir (ngspice reads from cwd)
cat > "$SIM_DIR/.spiceinit" << 'EOF'
set ngbehavior=hsa
set ng_nomodcheck
EOF

echo "Running: fet_gmId.sp"
echo "Results: $RESULTS_DIR"
echo ""

cd "$SIM_DIR"
ngspice -b fet_gmId.sp 2>&1 | tee "$RESULTS_DIR/fet_gmId.log"

# Parse W, L, device from the netlist
W_um=$(grep -i "^XM1" "$NETLIST" | grep -oE 'W=[0-9.]+' | cut -d= -f2)
L_um=$(grep -i "^XM1" "$NETLIST" | grep -oE 'L=[0-9.]+' | cut -d= -f2)
device=$(grep -i "^XM1" "$NETLIST" | grep -oE 'sky130_fd_pr__[a-z0-9_]+')

# Prepend metadata header to the wrdata output
if [ -f "$SIM_DIR/gmId_data.txt" ]; then
    {
        echo "# source = fet_gmId.sp"
        echo "# date = $(date '+%Y-%m-%d %H:%M:%S')"
        echo "# device = $device"
        echo "# W_um = $W_um"
        echo "# L_um = $L_um"
        echo "# corner = tt"
        echo "# topology = diode-connected (Vgs=Vds)"
        cat "$SIM_DIR/gmId_data.txt"
    } > "$RESULTS_DIR/gmId_data.txt"
    rm "$SIM_DIR/gmId_data.txt"
    echo ""
    echo "Data saved to $RESULTS_DIR/gmId_data.txt"
fi

echo "Done."
