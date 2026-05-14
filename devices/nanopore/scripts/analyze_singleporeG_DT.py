#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski May 14 2026
"""Nanopore + DT TIA analysis — reads tb_singleporeG_DT.raw/tran1.tran.tran (psfascii).

Computes:
  - Full time-domain traces: clk, Ipore (pA), Vout (mV)
  - Zoomed time-domain: 20 clock cycles after settling — shows integrate-and-dump
  - Normalised pore-current PSD vs theoretical Lorentzian for a random telegraph signal

Simulation parameters (ft, Ki, Ts, fsamp, samples, ...) are parsed directly from
tb_singleporeG_DT.scs, which is the single source of truth.
First 1% of samptime is skipped to allow DT circuit to settle past power-on transient.
"""

import os
import re
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.signal import welch
from psf_utils import PSF

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_DIR    = os.path.join(SCRIPT_DIR, "../../..")
WATERMARK   = os.path.join(REPO_DIR, "docs", "emil_tran.png")
DEFAULT_RAW = os.path.join(
    SCRIPT_DIR,
    "../results/standalone/singleporeG_DT/tb_singleporeG_DT.raw/tran1.tran.tran",
)
DEFAULT_SCS = os.path.join(
    SCRIPT_DIR,
    "../testbenches/standalone/tb_singleporeG_DT.scs",
)
OUT_DIR = os.path.join(SCRIPT_DIR, "../results/standalone/singleporeG_DT")

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
                _sub_suffix,
                val_str,
            )
            try:
                params[key] = float(eval(val_py, {"__builtins__": {}}, params))
            except Exception:
                pass
    return params


_p      = parse_spectre_params(DEFAULT_SCS)
FT      = _p['ft']
FSAMP   = _p['fsamp']
SAMPLES = int(_p['samples'])
WINSIZE = SAMPLES // 32
SKIP    = int(0.01 * SAMPLES)

_SI_PREFIXES = [
    (1e12,'T'),(1e9,'G'),(1e6,'M'),(1e3,'k'),
    (1,''),(1e-3,'m'),(1e-6,'µ'),(1e-9,'n'),(1e-12,'p'),(1e-15,'f'),
]


def _si(val, unit=''):
    """Format val with the largest SI prefix that keeps the coefficient ≥ 1."""
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
        f"ft={_si(p['ft'],'Hz')}  Ravg={_si(p['Ravg'],'Ω')}  gv={p['gv']:g}  "
        f"Cm={_si(p['Cm'],'F')}  Vbias={_si(p['Vbias'],'V')}  Vref={_si(p['Vref'],'V')}\n"
        f"Ki={p['Ki']:g}  Ts={_si(p['Ts'],'s')}  Cf={_si(p['Cf'],'F')}  "
        f"Ci={_si(p['Ci'],'F')}  Cl={_si(p['Cl'],'F')}  "
        f"fsamp={_si(p['fsamp'],'Hz')}  N={int(p['samples'])}"
    )


def load(raw_path):
    psf   = PSF(raw_path)
    t     = psf.get_sweep().abscissa
    ipore = psf.get_signal("AMporeout:p").ordinate
    vout  = psf.get_signal("out1").ordinate
    clk   = psf.get_signal("clk").ordinate
    return t, ipore, vout, clk


def plot_time(t, ipore, vout, clk, out_dir):
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(t * 1e3, clk, lw=0.6)
    axes[0].set_ylabel("Clk (V)")
    axes[0].set_title(
        f"Nanopore + DT TIA  (Ki={_p['Ki']:g}, Ts={_si(_p['Ts'],'s')}, "
        f"Cf={_si(_p['Cf'],'F')}, ft={_si(_p['ft'],'Hz')}, {len(t)} pts)"
    )
    axes[0].grid(True)

    axes[1].plot(t * 1e3, ipore * 1e12, lw=0.6)
    axes[1].set_ylabel("Pore Current (pA)")
    axes[1].grid(True)

    axes[2].plot(t * 1e3, vout * 1e3, lw=0.6)
    axes[2].set_ylabel("TIA Output (mV)")
    axes[2].set_xlabel("Time (ms)")
    axes[2].grid(True)

    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "singleporeG_DT_time.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def plot_time_zoom(t, ipore, vout, clk, out_dir):
    """20 clock cycles starting after SKIP — shows integrate-and-dump clearly."""
    t_start = t[SKIP]
    t_end   = t_start + 20 * _p['Ts']
    mask    = (t >= t_start) & (t <= t_end)

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(t[mask] * 1e3, clk[mask], lw=0.8)
    axes[0].set_ylabel("Clk (V)")
    axes[0].set_title(
        f"Nanopore + DT TIA — 20 clock cycles  "
        f"(Ki={_p['Ki']:g}, Ts={_si(_p['Ts'],'s')}, Cf={_si(_p['Cf'],'F')})"
    )
    axes[0].grid(True)

    axes[1].plot(t[mask] * 1e3, ipore[mask] * 1e12, lw=0.8)
    axes[1].set_ylabel("Pore Current (pA)")
    axes[1].grid(True)

    axes[2].plot(t[mask] * 1e3, vout[mask] * 1e3, lw=0.8)
    axes[2].set_ylabel("TIA Output (mV)")
    axes[2].set_xlabel("Time (ms)")
    axes[2].grid(True)

    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "singleporeG_DT_zoom.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def plot_psd(ipore, out_dir):
    ip      = ipore[SKIP:]
    sigma_I = np.std(ip)
    print(f"  IporeStdDev_pA : {sigma_I*1e12:.3f} pA")

    f_I, S_I = welch(ip / sigma_I, fs=FSAMP, window='boxcar', nperseg=WINSIZE, detrend=False)
    norm_I_dB = 20 * np.log10((FT/2) * S_I + 1e-30)

    f_th    = np.logspace(np.log10(f_I[1]), np.log10(FSAMP/2), 2000)
    S_th_dB = 20 * np.log10(1.0 / (1 + (np.pi * f_th / FT)**2))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(f_I[1:], norm_I_dB[1:], lw=0.8, label="Simulation")
    ax.semilogx(f_th, S_th_dB, 'r--', lw=1.5, label="Lorentzian theory")
    ax.axvline(FT/np.pi, color='gray', ls=':', lw=1,
               label=f"Corner ft/π = {FT/np.pi:.0f} Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Normalised PSD  dB20(ft · S_two / σ²)")
    ax.set_title("Pore current — normalised PSD  (Nanopore + DT TIA)")
    ax.set_xlim(f_I[1], FSAMP/2)
    ax.set_ylim(-60, 20)
    ax.legend(fontsize=8)
    ax.grid(True, which='both', ls=':')

    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "singleporeG_DT_psd.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    args = ap.parse_args()

    t, ipore, vout, clk = load(args.raw)
    print(f"  Loaded {len(t)} points, "
          f"t = 0 to {t[-1]*1e3:.1f} ms  (expected ~{SAMPLES} pts at {1/FSAMP*1e6:.0f} µs)")

    os.makedirs(OUT_DIR, exist_ok=True)
    plot_time(t, ipore, vout, clk, OUT_DIR)
    plot_time_zoom(t, ipore, vout, clk, OUT_DIR)
    plot_psd(ipore, OUT_DIR)


if __name__ == "__main__":
    main()
