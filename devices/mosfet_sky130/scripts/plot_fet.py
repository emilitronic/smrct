#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski Feb 8 2026
#
# Combine device Vgs=Vds measurements with ro and intrinsic gain at fixed Id
# Combines results from fet_gmId.sp and nfet_av.sp into a 2x2 grid of key analog design metrics:
#
"""Combined FET characterization plot: 2x2 grid merging gm/Id and av data."""

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
GMID_DATA_FILE = os.path.join(DEVICE_DIR, "results", "gmId", "gmId_data.txt")
AV_DATA_FILE = os.path.join(DEVICE_DIR, "results", "av", "av_data.txt")
PLOT_FILE = os.path.join(DEVICE_DIR, "results", "fet_summary.png")

# ── Helper: parse # key = value metadata from a data file ──
def parse_metadata(filepath):
    metadata = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") and "=" in line:
                key, val = line[1:].split("=", 1)
                metadata[key.strip()] = val.strip()
            elif not line.startswith("#"):
                break
    return metadata

# ── Helper: load numeric rows (skip comments and text headers) ──
def load_data(filepath):
    rows = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                continue
    return np.array(rows)

# ══════════════════════════════════════════════════════════════════════════════
#  Load gm/Id data
# ══════════════════════════════════════════════════════════════════════════════
if not os.path.exists(GMID_DATA_FILE):
    print(f"Error: {GMID_DATA_FILE} not found. Run run_gmId.sh first.")
    sys.exit(1)

gmid_meta = parse_metadata(GMID_DATA_FILE)
gmid_data = load_data(GMID_DATA_FILE)

W_um    = float(gmid_meta.get("W_um", "1"))
L_um    = float(gmid_meta.get("L_um", "0.15"))
device  = gmid_meta.get("device", "unknown")
corner  = gmid_meta.get("corner", "tt")

print(f"gmId data: {gmid_meta.get('source','?')}  {gmid_meta.get('date','?')}")
print(f"  Device: {device}  W = {W_um} um,  L = {L_um} um,  corner = {corner}")

# Data columns: v-sweep vgs id_ua gm gds vth gm_id vstar ft_GHz vdsat vgsteff
vgs      = gmid_data[:, 1]
id_ua_gm = gmid_data[:, 2]
gm_gm    = gmid_data[:, 3]
gds_gm   = gmid_data[:, 4]
gm_id    = gmid_data[:, 6]
vstar    = gmid_data[:, 7] * 1e3   # V -> mV
ft_GHz   = gmid_data[:, 8]
vgsteff  = gmid_data[:, 10]

ft_gm_id = ft_GHz * gm_id    # GHz/V

# ══════════════════════════════════════════════════════════════════════════════
#  Load av data
# ══════════════════════════════════════════════════════════════════════════════
if not os.path.exists(AV_DATA_FILE):
    print(f"Error: {AV_DATA_FILE} not found. Run run_av.sh first.")
    sys.exit(1)

av_meta = parse_metadata(AV_DATA_FILE)
av_data = load_data(AV_DATA_FILE)

Id_uA = float(av_meta.get("Id_uA", "10"))
print(f"av data:   {av_meta.get('source','?')}  {av_meta.get('date','?')}")
print(f"  Id = {Id_uA} uA")

# Data columns: v-sweep vd vg id_ua gm gds av
vds_av = av_data[:, 0]
gds_av = av_data[:, 5]
av     = av_data[:, 6]
ro_av  = 1.0 / (gds_av + 1e-30)

# ══════════════════════════════════════════════════════════════════════════════
#  Format suptitle
# ══════════════════════════════════════════════════════════════════════════════
L_str = f"{L_um*1000:.0f}\\,nm" if L_um < 1 else f"{L_um:.1f}\\,\\mu m"
suptitle = rf'sky130 nfet_01v8   $W = {W_um:.0f}\,\mu m$,  $L = {L_str}$,  corner = {corner}'

fig, axes = plt.subplots(2, 2, figsize=(12, 9))

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PLOT (1,1) — Upper Left: gm/Id and V* vs Vgs (dual y-axis)                  ║
# ║    Left y-axis (blue):  gm/Id in V^-1     — linear scale                     ║
# ║    Right y-axis (red):  V* = 2Id/gm in mV — linear scale                     ║
# ║    x-axis: Vgs (V)                                                           ║
# ║    Data source: gmId_data.txt                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
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
ax1r.plot(vgs, vstar, 'r-o', markersize=2, linewidth=1.5, label=r'$V^*$')
ax1r.set_ylabel(r'$V^* = 2I_D/g_m$ (mV)', color='r')
ax1r.tick_params(axis='y', labelcolor='r')
ax1r.set_ylim(bottom=0)
ax1r.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_RIGHT, min_n_ticks=N_TICKS_RIGHT))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1r.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)
ax1.set_title(r'$g_m/I_D$ and $V^*$ vs $V_{GS}$')

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PLOT (1,2) — Upper Right: Id vs V*                                          ║
# ║    y-axis: Id in uA        — linear scale                                    ║
# ║    x-axis: V* = 2Id/gm in mV                                                 ║
# ║    Data source: gmId_data.txt                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
ax2 = axes[0, 1]
ax2.plot(vstar, id_ua_gm, 'b-o', markersize=3, linewidth=1.5)
ax2.set_xlabel(r'$V^*$ (mV)')
ax2.set_ylabel(r'$I_D$ ($\mu$A)', color='b')
ax2.set_xlim(0, 800)
vstar_mask = vstar <= 800
ax2.set_ylim(0, id_ua_gm[vstar_mask].max() * 1.05)
ax2.grid(True, alpha=0.3, which='both')
ax2.set_title(r'$I_D$ vs $V^*$')

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PLOT (2,1) — Lower Left: av and ro vs Vds (dual y-axis)                     ║
# ║    Left y-axis (blue):  av = gm/gds in V/V — linear scale                    ║
# ║    Right y-axis (red):  ro = 1/gds in kOhm — linear scale                    ║
# ║    x-axis: Vds (V)      (constant Id bias)                                   ║
# ║    Data source: av_data.txt                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
ax3 = axes[1, 0]
ax3.plot(vds_av, av, 'b-o', markersize=3, linewidth=1.5, label=r'$a_v$')
ax3.set_xlabel(r'$V_{DS}$ (V)')
ax3.set_ylabel(r'$a_v = g_m / g_{ds}$ (V/V)', color='b')
ax3.tick_params(axis='y', labelcolor='b')
ax3.set_xlim(vds_av.min(), vds_av.max())
ax3.set_ylim(bottom=0)
ax3.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_LEFT, min_n_ticks=N_TICKS_LEFT))
ax3.grid(True, alpha=0.3)

ax3r = ax3.twinx()
ax3r.plot(vds_av, ro_av * 1e-3, 'r-o', markersize=2, linewidth=1.5, label=r'$r_o$')
ax3r.set_ylabel(r'$r_o$ (k$\Omega$)', color='r')
ax3r.tick_params(axis='y', labelcolor='r')
ax3r.set_ylim(bottom=0)
ax3r.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_RIGHT, min_n_ticks=N_TICKS_RIGHT))

lines3, labels3 = ax3.get_legend_handles_labels()
lines3r, labels3r = ax3r.get_legend_handles_labels()
ax3.legend(lines3 + lines3r, labels3 + labels3r, loc='lower right', fontsize=10)
ax3.set_title(rf'Intrinsic gain $a_v$ and $r_o$ vs $V_{{DS}}$  ($I_D = {Id_uA:.0f}\,\mu A$)')

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PLOT (2,2) — Lower Right: fT·gm/Id and fT vs V* (dual y-axis)               ║
# ║    Left y-axis (blue):  fT·gm/Id in GHz/V — linear scale                     ║
# ║    Right y-axis (red):  fT in GHz          — linear scale                    ║
# ║    x-axis: V* = 2Id/gm in mV                                                 ║
# ║    Data source: gmId_data.txt                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
ax4 = axes[1, 1]
ax4.plot(vstar, ft_gm_id, 'b-o', markersize=3, linewidth=1.5, label=r'$f_T \cdot g_m/I_D$')
ax4.set_xlabel(r'$V^*$ (mV)')
ax4.set_ylabel(r'$f_T \cdot g_m/I_D$ (GHz/V)', color='b')
ax4.tick_params(axis='y', labelcolor='b')
ax4.set_xlim(0, 800)
ax4.set_ylim(bottom=0)
ax4.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_LEFT, min_n_ticks=N_TICKS_LEFT))
ax4.grid(True, alpha=0.3)

ax4r = ax4.twinx()
ax4r.plot(vstar, ft_GHz, 'r-o', markersize=2, linewidth=1.5, label=r'$f_T$')
ax4r.set_ylabel(r'$f_T$ (GHz)', color='r')
ax4r.tick_params(axis='y', labelcolor='r')
ax4r.set_ylim(bottom=0)
ax4r.yaxis.set_major_locator(MaxNLocator(nbins=N_TICKS_RIGHT, min_n_ticks=N_TICKS_RIGHT))

lines4, labels4 = ax4.get_legend_handles_labels()
lines4r, labels4r = ax4r.get_legend_handles_labels()
ax4.legend(lines4 + lines4r, labels4 + labels4r, loc='lower right', fontsize=10)
ax4.set_title(r'$f_T \cdot g_m/I_D$ and $f_T$ vs $V^*$')

fig.suptitle(suptitle, fontsize=13, y=0.99)
fig.tight_layout()
os.makedirs(os.path.dirname(PLOT_FILE), exist_ok=True)
fig.savefig(PLOT_FILE, dpi=150)
print(f"Plot saved to {PLOT_FILE}")
plt.show()
