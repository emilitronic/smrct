#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski Feb 7 2026
#
"""Plot intrinsic gain (av = gm/gds) vs Vds from nfet_av.sp simulation data."""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_DIR = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(DEVICE_DIR, "results", "av")
DATA_FILE = os.path.join(RESULTS_DIR, "av_data.txt")
PLOT_FILE = os.path.join(RESULTS_DIR, "nfet_av_vs_vds.png")

if not os.path.exists(DATA_FILE):
    print(f"Error: {DATA_FILE} not found. Run run_av.sh first.")
    sys.exit(1)

# wrdata format with wr_singlescale + wr_vecnames:
#   header line with vector names
#   columns: v-sweep  vd  vg  id_ua  gm  gds  av
data = np.loadtxt(DATA_FILE, skiprows=1)

vds = data[:, 0]   # sweep variable (Vds setpoint)
vd  = data[:, 1]   # actual drain voltage
vg  = data[:, 2]
id_ua = data[:, 3]
gm  = data[:, 4]
gds = data[:, 5]
av  = data[:, 6]

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(vds, av, 'b-o', markersize=4, linewidth=1.5)
ax.set_xlabel(r'$V_{DS}$ (V)', fontsize=13)
ax.set_ylabel(r'Intrinsic Gain $a_v = g_m / g_{ds}$ (V/V)', fontsize=13)
ax.set_title(r'sky130 nfet_01v8   $W = 1\,\mu m$,  $L = 150\,nm$,  $I_D = 20\,\mu A$',
             fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xlim(0.0, 1.8)

fig.tight_layout()
fig.savefig(PLOT_FILE, dpi=150)
print(f"Plot saved to {PLOT_FILE}")
plt.show()
