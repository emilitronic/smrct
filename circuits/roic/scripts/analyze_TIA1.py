#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski May 20 2026
"""ROIC DT integrator TIA analysis — reads tb_TIA1.raw/tran1.tran.tran (psfascii).

Computes:
  - Time-domain traces: clk, Iin (pA), opTIA (mV), ipTIA (mV)
  - Vint: integrated output swing per clock cycle (end-of-integration minus
    start-of-integration), extracted by detecting clk edges — equivalent to
    the Ocean SKILL Vint expression used in the original ADE setup

Simulation parameters are parsed directly from tb_TIA1.scs (single source of truth).
"""

import os
import re
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from psf_utils import PSF

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_DIR    = os.path.join(SCRIPT_DIR, "../../..")
WATERMARK   = os.path.join(REPO_DIR, "docs", "emil_tran.png")
DEFAULT_RAW = os.path.join(
    SCRIPT_DIR,
    "../results/standalone/TIA1/tb_TIA1.raw/tran1.tran.tran",
)
DEFAULT_SCS = os.path.join(
    SCRIPT_DIR,
    "../testbenches/standalone/tb_TIA1.scs",
)
OUT_DIR = os.path.join(SCRIPT_DIR, "../results/standalone/TIA1")

_SPECTRE_SUFFIXES = {
    'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6,
    'm': 1e-3,  'k': 1e3,   'M': 1e6,  'G': 1e9,  'T': 1e12,
}


def parse_spectre_params(scs_path):
    """Return dict of floats from all 'parameters' lines in a Spectre netlist."""
    with open(scs_path) as fh:
        text = fh.read()
    text = re.sub(r'\\\n', ' ', text)

    def _sub_suffix(m):
        return f"({m.group(1)}*{_SPECTRE_SUFFIXES[m.group(2)]})"

    params = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('parameters'):
            continue
        rest = re.sub(r'//.*', '', line[len('parameters'):]).strip()
        for m in re.finditer(r'(\w+)\s*=\s*(\S+)', rest):
            key, val_str = m.group(1), m.group(2)
            val_py = re.sub(
                r'(\d+\.?\d*(?:[eE][+-]?\d+)?)([fpnumkMGT])\b',
                _sub_suffix, val_str,
            )
            try:
                params[key] = float(eval(val_py, {"__builtins__": {}}, params))
            except Exception:
                pass
    return params


_p  = parse_spectre_params(DEFAULT_SCS)
VTH = 0.8   # sm_sw_no vth used in tb_TIA1

_SI_PREFIXES = [
    (1e12,'T'),(1e9,'G'),(1e6,'M'),(1e3,'k'),
    (1,''),(1e-3,'m'),(1e-6,'µ'),(1e-9,'n'),(1e-12,'p'),(1e-15,'f'),
]


def _si(val, unit=''):
    for thr, pre in _SI_PREFIXES:
        if abs(val) >= thr * 0.9995:
            return f"{val/thr:g} {pre}{unit}".rstrip()
    return f"{val:g}{' '+unit if unit else ''}"


def _add_watermark(fig):
    if os.path.exists(WATERMARK):
        wm_ax = fig.add_axes([0.1, 0.15, 0.75, 0.75], anchor='C', zorder=10)
        wm_ax.imshow(mpimg.imread(WATERMARK), alpha=0.08)
        wm_ax.axis('off')


def _param_text(p):
    return (
        f"fs={_si(p['fs'],'Hz')}  Ki={p['Ki']:g}  Cf={_si(p['Cf'],'F')}  "
        f"Cm={_si(p['Cm'],'F')}  Vdd={_si(p['Vdd'],'V')}\n"
        f"Vtrans={_si(p['Vtrans'],'V')}  Vop={_si(p['Vop'],'V')}  "
        f"stopTime={_si(p['stopTime'],'s')}"
    )


def load(raw_path):
    psf   = PSF(raw_path)
    t     = psf.get_sweep().abscissa
    optia = psf.get_signal("opTIA").ordinate
    iptia = psf.get_signal("ipTIA").ordinate
    clk   = psf.get_signal("clk").ordinate
    return t, optia, iptia, clk


def iin_analytical(t, p):
    """Reconstruct Ii2 current drained from ipTIA (positive = into ipTIA).

    PWL: wave=[(Ts/10) 0  Ts -200p] with Ii2 (0 ipTIA) convention means
    200 pA flows into ipTIA after Ts.  Before Ts/10 the current is zero.
    """
    ts  = p['Ts']
    iin = np.zeros_like(t)
    ramp = (t >= ts / 10) & (t <= ts)
    iin[ramp] = 200e-12 * (t[ramp] - ts / 10) / (ts - ts / 10)
    iin[t > ts] = 200e-12
    return iin


def vint_per_cycle(t, optia, clk):
    """Return (t_eoi, Vint) arrays — one value per complete clock cycle.

    Vint = V(opTIA) at end-of-integration minus V(opTIA) at start-of-integration,
    matching the Ocean SKILL expression from the original ADE setup.
    End-of-integration   = just before clk rising edge  (reset starts)
    Start-of-integration = just after  clk falling edge (reset ends)
    """
    rising  = np.where((clk[:-1] < VTH) & (clk[1:] >= VTH))[0]
    falling = np.where((clk[:-1] >= VTH) & (clk[1:] < VTH))[0]

    vint_vals, t_vals = [], []
    for r in rising:
        # find the most recent falling edge before this rising edge
        prev_fall = falling[falling < r]
        if len(prev_fall) == 0:
            continue
        f = prev_fall[-1]
        vint_vals.append(optia[r] - optia[f])
        t_vals.append(t[r])
    return np.array(t_vals), np.array(vint_vals)


def plot_time(t, optia, iptia, clk, iin, out_dir):
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    axes[0].plot(t * 1e3, clk, lw=0.8)
    axes[0].set_ylabel("Clk (V)")
    axes[0].set_title(
        f"ROIC DT Integrator TIA  (Ki={_p['Ki']:g}, Ts={_si(_p['Ts'],'s')}, "
        f"Cf={_si(_p['Cf'],'F')}, Cm={_si(_p['Cm'],'F')})"
    )
    axes[0].grid(True)

    axes[1].plot(t * 1e3, iin * 1e12, lw=0.8)
    axes[1].set_ylabel("Iin (pA)")
    axes[1].grid(True)

    axes[2].plot(t * 1e3, iptia * 1e3, lw=0.8)
    axes[2].set_ylabel("ipTIA (mV)")
    axes[2].grid(True)

    axes[3].plot(t * 1e3, optia * 1e3, lw=0.8)
    axes[3].set_ylabel("opTIA (mV)")
    axes[3].set_xlabel("Time (ms)")
    axes[3].grid(True)

    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "TIA1_time.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def plot_vint(t, optia, clk, out_dir):
    t_cyc, vint = vint_per_cycle(t, optia, clk)

    print(f"  Vint per cycle (mV): {vint*1e3}")
    print(f"  Last cycle Vint    : {vint[-1]*1e3:.1f} mV  (expected ~696 mV from ADE)")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(np.arange(len(vint)), vint * 1e3, width=0.6)
    ax.set_xlabel("Clock cycle index")
    ax.set_ylabel("Vint (mV)")
    ax.set_title(
        f"Integrated output swing per cycle  "
        f"(Cf={_si(_p['Cf'],'F')}, Ki={_p['Ki']:g}, Ts={_si(_p['Ts'],'s')})"
    )
    ax.axhline(696, color='r', ls='--', lw=1, label="ADE reference: 696 mV")
    ax.legend(fontsize=8)
    ax.grid(True, axis='y')

    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "TIA1_vint.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    args = ap.parse_args()

    t, optia, iptia, clk = load(args.raw)
    iin = iin_analytical(t, _p)
    print(f"  Loaded {len(t)} points, t = 0 to {t[-1]*1e3:.1f} ms")

    os.makedirs(OUT_DIR, exist_ok=True)
    plot_time(t, optia, iptia, clk, iin, OUT_DIR)
    plot_vint(t, optia, clk, OUT_DIR)


if __name__ == "__main__":
    main()
