#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski Feb 7 2026
#
"""Plot gm/Id characterization: 2x2 grid of key analog design metrics."""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Number of major ticks on left and right y-axes (for dual-axis plots)
N_TICKS_LEFT = 6
N_TICKS_RIGHT = 5

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

# Data columns: v-sweep vgs id_ua gm gds vth gm_id vstar ft_GHz vdsat vgsteff
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

vgs     = data[:, 1]
id_ua   = data[:, 2]
gm      = data[:, 3]
gds     = data[:, 4]
vth     = data[:, 5]
gm_id   = data[:, 6]
vstar   = data[:, 7] * 1e3   # V -> mV
ft_GHz  = data[:, 8]
vdsat   = data[:, 9]
vgsteff = data[:, 10]

# Derived
ro = 1.0 / (gds + 1e-30)
gm_ro = gm * ro
ft_gm_id = ft_GHz * gm_id    # GHz/V

# Format L for display
L_str = f"{L_um*1000:.0f}\\,nm" if L_um < 1 else f"{L_um:.1f}\\,\\mu m"
suptitle = rf'sky130 nfet_01v8   $W = {W_um:.0f}\,\mu m$,  $L = {L_str}$,  corner = {corner}'

fig, axes = plt.subplots(2, 2, figsize=(12, 9))

# ── (1,1) gm/Id and V* vs Vgs ──
ax1 = axes[0, 0]
ax1.plot(vgs, gm_id, 'b-o', markersize=3, linewidth=1.5, label=r'$g_m/I_D$')
ax1.set_xlabel(r'$V_{GS}$ (V)')
ax1.set_ylabel(r'$g_m / I_D$ (V$^{-1}$)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.set_xlim(vgs.min(), vgs.max())
ax1.set_ylim(bottom=0)
ax1.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_LEFT, min_n_ticks=N_TICKS_LEFT))
ax1.grid(True, alpha=0.3)

ax1r = ax1.twinx()
ax1r.plot(vgs, vstar, 'r-s', markersize=2, linewidth=1.5, label=r'$V^*$')
ax1r.set_ylabel(r'$V^* = 2I_D/g_m$ (mV)', color='r')
ax1r.tick_params(axis='y', labelcolor='r')
ax1r.set_ylim(bottom=0)
ax1r.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_RIGHT, min_n_ticks=N_TICKS_RIGHT))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1r.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=10)
ax1.set_title(r'$g_m/I_D$ and $V^*$ vs $V_{GS}$')

# ── (1,2) Id vs V* ──
ax2 = axes[0, 1]
ax2.semilogy(vstar, id_ua, 'b-o', markersize=3, linewidth=1.5)
ax2.set_xlabel(r'$V^*$ (mV)')
ax2.set_ylabel(r'$I_D$ ($\mu$A)')
ax2.set_xlim(left=0)
ax2.grid(True, alpha=0.3, which='both')
ax2.set_title(r'$I_D$ vs $V^*$')

# ── (2,1) gm·ro vs Vds ──
ax3 = axes[1, 0]
ax3.plot(vgs, gm_ro, 'b-o', markersize=3, linewidth=1.5)
ax3.set_xlabel(r'$V_{DS}$ (V)')
ax3.set_ylabel(r'$g_m \cdot r_o$ (V/V)')
ax3.set_xlim(vgs.min(), vgs.max())
ax3.set_ylim(bottom=0)
ax3.grid(True, alpha=0.3)
ax3.set_title(r'Intrinsic gain $g_m \cdot r_o$ vs $V_{DS}$')

# ── (2,2) fT·gm/Id vs V* ──
ax4 = axes[1, 1]
ax4.plot(vstar, ft_gm_id, 'b-o', markersize=3, linewidth=1.5)
ax4.set_xlabel(r'$V^*$ (mV)')
ax4.set_ylabel(r'$f_T \cdot g_m/I_D$ (GHz/V)')
ax4.set_xlim(left=0)
ax4.set_ylim(bottom=0)
ax4.grid(True, alpha=0.3)
ax4.set_title(r'$f_T \cdot g_m/I_D$ vs $V^*$')

fig.suptitle(suptitle, fontsize=13, y=0.99)
fig.tight_layout()
fig.savefig(PLOT_FILE, dpi=150)
print(f"Plot saved to {PLOT_FILE}")
plt.show()
