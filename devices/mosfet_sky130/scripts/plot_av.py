#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski Feb 7 2026
#
"""Plot intrinsic gain (av = gm/gds) vs Vds from nfet_av.sp simulation data."""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_DIR = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(DEVICE_DIR, "results", "av")
DATA_FILE = os.path.join(RESULTS_DIR, "av_data.txt")
PLOT_FILE = os.path.join(RESULTS_DIR, "nfet_av_vs_vds.png")

if not os.path.exists(DATA_FILE):
    print(f"Error: {DATA_FILE} not found. Run run_av.sh first.")
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
Id_uA = float(metadata.get("Id_uA", "10"))
corner = metadata.get("corner", "tt")
source = metadata.get("source", "unknown")
date = metadata.get("date", "unknown")

print(f"Source: {source}  Date: {date}")
print(f"W = {W_um} um,  L = {L_um} um,  Id = {Id_uA} uA,  corner = {corner}")

# Data columns: v-sweep  vd  vg  id_ua  gm  gds  av
# Skip comment lines (#) and the wrdata vector-names header (starts with text)
rows = []
with open(DATA_FILE) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append([float(x) for x in line.split()])
        except ValueError:
            continue  # skip wrdata header line (v-sweep vd vg ...)
data = np.array(rows)

vds = data[:, 0]
vd  = data[:, 1]
vg  = data[:, 2]
id_ua = data[:, 3]
gm  = data[:, 4]
gds = data[:, 5]
av  = data[:, 6]
ro  = 1.0 / (gds + 1e-30)  # output resistance in Ohms

# Format L for display: use nm if < 1um
L_str = f"{L_um*1000:.0f}\\,nm" if L_um < 1 else f"{L_um:.1f}\\,\\mu m"

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(vds, av, 'b-o', markersize=4, linewidth=1.5, label=r'$a_v$')
ax.set_xlabel(r'$V_{DS}$ (V)', fontsize=13)
ax.set_ylabel(r'Intrinsic Gain $a_v = g_m / g_{ds}$ (V/V)', fontsize=13, color='b')
ax.tick_params(axis='y', labelcolor='b')
ax.set_title(
    rf'sky130 nfet_01v8   $W = {W_um:.0f}\,\mu m$,  $L = {L_str}$,  $I_D = {Id_uA:.0f}\,\mu A$',
    fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xlim(vds.min(), vds.max())
ax.set_ylim(bottom=0)

axr = ax.twinx()
axr.plot(vds, ro * 1e-3, 'r-o', markersize=3, linewidth=1.5, label=r'$r_o$')
axr.set_ylabel(r'$r_o$ (k$\Omega$)', fontsize=13, color='r')
axr.tick_params(axis='y', labelcolor='r')
axr.set_ylim(bottom=0)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = axr.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=11)

fig.tight_layout()
fig.savefig(PLOT_FILE, dpi=150)
print(f"Plot saved to {PLOT_FILE}")
plt.show()
