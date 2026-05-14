#!/usr/bin/env python3
# Sebastian Claudiusz Magierowski May 4 2026
"""Nanopore + CT TIA analysis — reads tb_singleporeG.raw/tran1.tran.tran (psfascii).

Computes:
  - Time-domain traces: Ipore (pA) and Vout (mV)
  - Normalised pore-current PSD vs theoretical Lorentzian for a random telegraph signal

Simulation parameters (ft, fsamp, samples) are parsed directly from tb_singleporeG.scs,
which is the single source of truth. winsize = samples/32 (~32 Welch averages).
First 1% of samptime is skipped before computing statistics and PSD.

Theoretical normalised PSD for a Poisson random telegraph signal with explicit toggle:
  ft * S_two(f) / σ² = 1 / (1 + (π·f/ft)²)
  Corner at f = ft/π; DC value: 0 dB; -20 dB/decade above corner (dB20 scale).
"""

import os
import re    # for parsing Spectre netlist parameters with suffixes (e.g. 1k, 2.25G)
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.signal import welch
from psf_utils import PSF

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR   = os.path.join(SCRIPT_DIR, "../../..")
WATERMARK  = os.path.join(REPO_DIR, "docs", "emil_tran.png")
DEFAULT_RAW = os.path.join(
    SCRIPT_DIR,
    "../results/standalone/singleporeG/tb_singleporeG.raw/tran1.tran.tran",
)
DEFAULT_SCS = os.path.join(
    SCRIPT_DIR,
    "../testbenches/standalone/tb_singleporeG.scs",
)
OUT_DIR = os.path.join(SCRIPT_DIR, "../results/standalone/singleporeG")

_SPECTRE_SUFFIXES = {
    'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6,
    'm': 1e-3,  'k': 1e3,   'M': 1e6,  'G': 1e9,  'T': 1e12,
}

# Reads .scs file and returns a Python dict of all parameter values
# e.g., {'Vclk_hi': 1.0, 'Ki': 0.8, 'Cf': 2e-14, 'Ci': 5e-12, ...,}
def parse_spectre_params(scs_path):
    """Return dict of floats from all 'parameters' lines in a Spectre netlist."""
    with open(scs_path) as fh:
        text = fh.read()
    text = re.sub(r'\\\n', ' ', text)  # join backslash-continuation lines

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


# Load simulation parameters from testbench — single source of truth
_p      = parse_spectre_params(DEFAULT_SCS)
FT      = _p['ft']            # mean event rate (Hz)
FSAMP   = _p['fsamp']         # output sample rate (Hz)
SAMPLES = int(_p['samples'])  # total output samples
WINSIZE = SAMPLES // 32       # Welch segment length (~32 averages)
SKIP    = int(0.01 * SAMPLES) # drop first 1% for settling


def _add_watermark(fig):
    if os.path.exists(WATERMARK):
        wm_ax = fig.add_axes([0.1, 0.15, 0.75, 0.75], anchor='C', zorder=10)
        wm_ax.imshow(mpimg.imread(WATERMARK), alpha=0.08)
        wm_ax.axis('off')


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

# Formats selected entries from parse_spectre_params dict into two-line
# annotation string that gets printed in the SW corner of each plot.
def _param_text(p):
    return (
        f"ft={_si(p['ft'],'Hz')}  Ravg={_si(p['Ravg'],'Ω')}  gv={p['gv']:g}  "
        f"Cm={_si(p['Cm'],'F')}  Vbias={_si(p['Vbias'],'V')}\n"
        f"Rf={_si(p['Rf'],'Ω')}  Cf={_si(p['Cf'],'F')}  "
        f"Ci={_si(p['Ci'],'F')}  Cl={_si(p['Cl'],'F')}  "
        f"fsamp={_si(p['fsamp'],'Hz')}  N={int(p['samples'])}"
    )


def load(raw_path):
    psf = PSF(raw_path)
    t     = psf.get_sweep().abscissa
    ipore = psf.get_signal("AMporeout:p").ordinate
    vout  = psf.get_signal("out1").ordinate
    return t, ipore, vout


def plot_time(t, ipore, vout, out_dir):
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    axes[0].plot(t * 1e3, vout * 1e3, lw=0.6)
    axes[0].set_ylabel("TIA Output (mV)")
    axes[0].set_title(
        f"Nanopore + CT TIA  (Rf={_si(_p['Rf'],'Ω')}, ft={_si(_p['ft'],'Hz')}, {len(t)} pts)"
    )
    axes[0].grid(True)
    axes[1].plot(t * 1e3, ipore * 1e12, lw=0.6)
    axes[1].set_xlabel("Time (ms)")
    axes[1].set_ylabel("Pore Current (pA)")
    axes[1].grid(True)
    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "singleporeG_time.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def plot_psd(ipore, vout, out_dir):
    ip = ipore[SKIP:]
    vo = vout[SKIP:]

    sigma_I = np.std(ip)
    sigma_V = np.std(vo)
    print(f"  IporeStdDev_pA : {sigma_I*1e12:.3f} pA")
    print(f"  Vout1StdDev    : {sigma_V*1e3:.3f} mV")

    # Divide by sigma → unit variance; welch returns one-sided S_one.
    # Multiply by FT/2 → double-sided ft·S_two/σ²  (S_one = 2·S_two for f > 0).
    f_I, S_I = welch(ip / sigma_I, fs=FSAMP, window='boxcar', nperseg=WINSIZE, detrend=False)
    f_V, S_V = welch(vo / sigma_V, fs=FSAMP, window='boxcar', nperseg=WINSIZE, detrend=False)
    norm_I_dB = 20 * np.log10((FT/2) * S_I + 1e-30)
    norm_V_dB = 20 * np.log10((FT/2) * S_V + 1e-30)

    # Theoretical double-sided normalised Lorentzian for a toggle RTS:
    #   ft·S_two(f)/σ² = 1 / (1 + (π·f/ft)²)
    # DC: 0 dB.  Corner (−6 dB20): f = ft/π.
    f_th = np.logspace(np.log10(f_I[1]), np.log10(FSAMP/2), 2000)
    S_th_dB = 20 * np.log10(1.0 / (1 + (np.pi * f_th / FT)**2))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, f_sim, S_dB, label in [
        (axes[0], f_I, norm_I_dB, "Pore current"),
        (axes[1], f_V, norm_V_dB, "TIA output"),
    ]:
        ax.semilogx(f_sim[1:], S_dB[1:], lw=0.8, label="Simulation")
        ax.semilogx(f_th, S_th_dB, 'r--', lw=1.5, label="Lorentzian theory")
        ax.axvline(FT/np.pi, color='gray', ls=':', lw=1,
                   label=f"Corner ft/π = {FT/np.pi:.0f} Hz")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Normalised PSD  dB20(ft · S_two / σ²)")
        ax.set_title(f"{label} — normalised PSD")
        ax.set_xlim(f_I[1], FSAMP/2)
        ax.set_ylim(-60, 20)
        ax.legend(fontsize=8)
        ax.grid(True, which='both', ls=':')

    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.text(0.01, 0.01, _param_text(_p), fontsize=7.5, va='bottom', ha='left',
             family='monospace', color='0.35')
    _add_watermark(fig)
    path = os.path.join(out_dir, "singleporeG_psd.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    args = ap.parse_args()

    t, ipore, vout = load(args.raw)
    print(f"  Loaded {len(t)} points, "
          f"t = 0 to {t[-1]*1e3:.1f} ms  (expected ~{SAMPLES} pts at {1/FSAMP*1e6:.0f} µs)")

    os.makedirs(OUT_DIR, exist_ok=True)
    plot_time(t, ipore, vout, OUT_DIR)
    plot_psd(ipore, vout, OUT_DIR)


if __name__ == "__main__":
    main()
