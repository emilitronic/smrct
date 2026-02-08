#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski Feb 7 2026
#
"""Plot gm/Id vs Vgs from fet_gmId.sp simulation data."""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_DIR = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(DEVICE_DIR, "results", "gmId")
DATA_FILE = os.path.join(RESULTS_DIR, "gmId_data.txt")
PLOT_FILE = os.path.join(RESULTS_DIR, "fet_gmId_vs_vgs.png")

if not os.path.exists(DATA_FILE):
    print(f"Error: {DATA_FILE} not found. Run run_gmId.sh first.")
    sys.exit(1)

# Parse metadata from # key = value header lines
metadata = {}
with open(DATA_FILE) as f:
    for line in f:
        line = line.strip()
        if line.startswith("#") and "=" in line:
            key, val = line[1:].split("=", 1)
            metadata[key.strip()] = val.strip()
        elif not line.startswith("#"):
            break

W_um = float(metadata.get("W_um", "1"))
L_um = float(metadata.get("L_um", "0.15"))
device = metadata.get("device", "unknown")
corner = metadata.get("corner", "tt")
source = metadata.get("source", "unknown")
date = metadata.get("date", "unknown")

print(f"Source: {source}  Date: {date}")
print(f"Device: {device}  W = {W_um} um,  L = {L_um} um,  corner = {corner}")

# Data columns: v-sweep  vgs  id_ua  gm  gds  vth  gm_id
rows = []
with open(DATA_FILE) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append([float(x) for x in line.split()])
        except ValueError:
            continue
data = np.array(rows)

vgs   = data[:, 1]
id_ua = data[:, 2]
gm    = data[:, 3]
gds   = data[:, 4]
vth   = data[:, 5]
gm_id = data[:, 6]

# Format L for display
L_str = f"{L_um*1000:.0f}\\,nm" if L_um < 1 else f"{L_um:.1f}\\,\\mu m"

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(vgs, gm_id, 'b-o', markersize=4, linewidth=1.5)
ax.set_xlabel(r'$V_{GS}$ (V)', fontsize=13)
ax.set_ylabel(r'$g_m / I_D$ (V$^{-1}$)', fontsize=13)
ax.set_title(
    rf'sky130 nfet_01v8   $W = {W_um:.0f}\,\mu m$,  $L = {L_str}$,  corner = {corner}',
    fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xlim(vgs.min(), vgs.max())

fig.tight_layout()
fig.savefig(PLOT_FILE, dpi=150)
print(f"Plot saved to {PLOT_FILE}")
plt.show()
