#!/usr/bin/env python3
"""
Nanopore I-V Analysis Script
Sebastian Claudiusz Magierowski Nov 23 2025

Analyzes I–V sweep results from the standalone nanopore Spectre flow.

Current implementation
----------------------
- Operates on CSV exports of I–V data in
  devices/nanopore/results/standalone/iv/
- Generates I–V plots (linear, optional log |I|)
- Computes basic metrics:
    * Small-signal conductance around 0 V
    * Corresponding resistance estimate
    * On/off currents at user-defined voltages
- Writes metrics to JSON and plain-text files

Future work (not implemented)
-----------------------------
- Native Spectre PSF / psfascii parsing (no CSV step)
- Batch processing of multiple sweeps and corners
- More advanced device models and fitting

Requirements
------------
- numpy
- matplotlib
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Nanopore standalone I–V analysis helper.\n\n"
            "Default behaviour:\n"
            "  * Resolve the standalone results directory relative to this script\n"
            "  * Auto-detect a single CSV file with I–V data\n"
            "  * Generate plots and basic metrics in an 'analysis' subdirectory"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help=(
            "Directory containing I–V results (CSV and/or PSF). "
            "If not provided, defaults to "
            "devices/nanopore/results/standalone/iv/ relative to this script."
        ),
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help=(
            "CSV file with I–V data. If a relative path is given, it is "
            "interpreted inside --results-dir. If omitted, the script will "
            "auto-detect a single CSV file in the results directory."
        ),
    )
    parser.add_argument(
        "--v-col",
        type=str,
        default="V",
        help="Voltage column name in the CSV header.",
    )
    parser.add_argument(
        "--i-col",
        type=str,
        default="I",
        help="Current column name in the CSV header.",
    )
    parser.add_argument(
        "--v-on",
        type=float,
        default=0.6,
        help="Voltage at which to report 'on' current.",
    )
    parser.add_argument(
        "--v-off",
        type=float,
        default=0.0,
        help="Voltage at which to report 'off' / leakage current.",
    )
    parser.add_argument(
        "--delta-g0",
        type=float,
        default=0.05,
        help=(
            "Half-width of the voltage window around 0 V used to estimate "
            "small-signal conductance (fit region is [-delta_g0, +delta_g0])."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help=(
            "Output directory for plots and metric files. "
            "If not provided, defaults to <results-dir>/analysis."
        ),
    )
    parser.add_argument(
        "--log-plot",
        action="store_true",
        help="Also generate a log10(|I|) vs. V plot.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def resolve_results_dir(args_results_dir: Optional[str]) -> Path:
    """
    Resolve the results directory. If args_results_dir is given, use it.
    Otherwise, use devices/nanopore/results/standalone/iv relative to
    this script location.
    """
    script_dir = Path(__file__).resolve().parent
    device_dir = script_dir.parent
    default_results_dir = device_dir / "results" / "standalone" / "iv"

    if args_results_dir is not None:
        return Path(args_results_dir).expanduser().resolve()

    return default_results_dir


def find_csv_file(results_dir: Path, input_arg: Optional[str]) -> Path:
    """
    Determine which CSV file to use.

    Priority:
    1) If input_arg is provided, use that file (absolute or relative to results_dir).
    2) Otherwise, auto-detect a single *.csv file in results_dir.
    """
    if input_arg is not None:
        candidate = Path(input_arg)
        if not candidate.is_absolute():
            candidate = results_dir / candidate
        candidate = candidate.resolve()

        if not candidate.exists():
            raise FileNotFoundError(f"Specified input CSV not found: {candidate}")

        return candidate

    csv_files = list(results_dir.glob("*.csv"))
    if len(csv_files) == 0:
        raise FileNotFoundError(
            f"No CSV files found in {results_dir}.\n"
            "Export I–V data to CSV (e.g., via OCEAN or an internal psf2csv "
            "utility) and re-run, or specify a file with --input."
        )

    if len(csv_files) > 1:
        raise RuntimeError(
            "Multiple CSV files found in {0}:\n  {1}\n"
            "Please specify one explicitly via --input <file>.".format(
                results_dir, "\n  ".join(str(f) for f in csv_files)
            )
        )

    return csv_files[0]


# ---------------------------------------------------------------------------
# Data loading and metrics
# ---------------------------------------------------------------------------

def load_iv_csv(path: Path,
                v_col_name: str,
                i_col_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load I–V data from a CSV file.

    The first line is treated as a comma-separated header. The voltage and
    current columns are selected by name.
    """
    with path.open("r") as f:
        header_line = f.readline().strip()

    header = [h.strip() for h in header_line.split(",") if h.strip()]
    if not header:
        raise ValueError(f"Empty or invalid header in CSV file: {path}")

    try:
        idx_v = header.index(v_col_name)
    except ValueError:
        raise ValueError(
            f"Voltage column '{v_col_name}' not found in {path}.\n"
            f"Available columns: {header}"
        )

    try:
        idx_i = header.index(i_col_name)
    except ValueError:
        raise ValueError(
            f"Current column '{i_col_name}' not found in {path}.\n"
            f"Available columns: {header}"
        )

    data = np.loadtxt(path, delimiter=",", skiprows=1, usecols=(idx_v, idx_i))

    if data.ndim == 1:
        v = np.array([data[0]], dtype=float)
        i = np.array([data[1]], dtype=float)
    else:
        v = data[:, 0].astype(float)
        i = data[:, 1].astype(float)

    return v, i


def compute_small_signal_g0(v: np.ndarray,
                            i: np.ndarray,
                            window: float) -> Tuple[float, float]:
    """
    Estimate small-signal conductance g0 and corresponding resistance R0
    around 0 V using a simple linear fit in a symmetric window.
    """
    if window <= 0:
        raise ValueError("delta_g0 window must be positive.")

    mask = np.abs(v) <= window
    if mask.sum() >= 2:
        v_fit = v[mask]
        i_fit = i[mask]
    else:
        # Fallback: use the two samples closest to 0 V
        idx = np.argsort(np.abs(v))[:2]
        v_fit = v[idx]
        i_fit = i[idx]

    coeffs = np.polyfit(v_fit, i_fit, 1)  # i ≈ g0 * v + b
    g0 = float(coeffs[0])
    r0 = float("inf") if g0 == 0.0 else float(1.0 / g0)
    return g0, r0


def current_at(v: np.ndarray, i: np.ndarray, target_v: float) -> float:
    """
    Return the current at the sample whose voltage is closest to target_v.
    """
    if v.size == 0:
        raise ValueError("Empty voltage array.")
    idx = int(np.argmin(np.abs(v - target_v)))
    return float(i[idx])


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def make_plots(v: np.ndarray,
               i: np.ndarray,
               out_dir: Path,
               make_log: bool) -> None:
    """
    Generate I–V plots and save them under out_dir.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Linear I–V plot
    fig, ax = plt.subplots()
    ax.plot(v, i, marker="o", linestyle="-")
    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("Current (A)")
    ax.set_title("Nanopore I–V Curve")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(out_dir / "iv_curve.png", dpi=300)
    plt.close(fig)

    if make_log:
        fig, ax = plt.subplots()
        ax.plot(v, np.log10(np.abs(i) + 1e-30), marker="o", linestyle="-")
        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("log10(|I|) (A)")
        ax.set_title("Nanopore I–V Curve (log scale)")
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(out_dir / "iv_curve_log.png", dpi=300)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    print("=" * 50)
    print("Nanopore I-V Analysis")
    print("=" * 50)

    results_dir = resolve_results_dir(args.results_dir)
    print(f"Results directory: {results_dir}")

    if not results_dir.exists():
        print()
        print("ERROR: Results directory not found.")
        print("Run the standalone simulation first using:")
        print("  ./scripts/run_standalone_iv.sh")
        return 1

    # Detect PSF presence to hint at future native support
    psf_candidates = list(results_dir.glob("*.psf"))
    psf_dir = results_dir / "psf"
    if psf_dir.exists():
        psf_candidates.extend(list(psf_dir.glob("*")))
    if psf_candidates:
        print()
        print("Note: PSF files detected. Native PSF parsing is not implemented")
        print("in this version; analysis currently expects CSV exports of I–V")
        print("data in the results directory.")

    # Resolve CSV input
    try:
        csv_path = find_csv_file(results_dir, args.input)
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print()
        print(f"ERROR: {e}")
        return 1

    print()
    print(f"Using CSV file: {csv_path}")

    # Load data
    try:
        v, i = load_iv_csv(csv_path, args.v_col, args.i_col)
    except Exception as e:
        print()
        print(f"ERROR while reading CSV: {e}")
        return 1

    # Resolve output directory
    out_dir = (
        Path(args.out_dir).expanduser().resolve()
        if args.out_dir is not None
        else results_dir / "analysis"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Compute metrics
    try:
        g0, r0 = compute_small_signal_g0(v, i, args.delta_g0)
        ion = current_at(v, i, args.v_on)
        ioff = current_at(v, i, args.v_off)
    except Exception as e:
        print()
        print(f"ERROR while computing metrics: {e}")
        return 1

    metrics = {
        "csv_file": str(csv_path),
        "v_on_V": args.v_on,
        "v_off_V": args.v_off,
        "delta_g0_window_V": args.delta_g0,
        "g0_S": g0,
        "R0_ohm": r0,
        "Ion_A": ion,
        "Ioff_A": ioff,
    }

    # Write metrics
    metrics_json = out_dir / "iv_metrics.json"
    metrics_txt = out_dir / "iv_metrics.txt"

    with metrics_json.open("w") as f_json:
        json.dump(metrics, f_json, indent=2)

    with metrics_txt.open("w") as f_txt:
        f_txt.write("Nanopore I–V Metrics\n")
        f_txt.write("====================\n\n")
        for key, value in metrics.items():
            f_txt.write(f"{key}: {value}\n")

    print()
    print("Computed metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    # Plots
    print()
    print(f"Generating plots in: {out_dir}")
    make_plots(v, i, out_dir, args.log_plot)

    print()
    print("Analysis complete.")
    print(f"  Metrics: {metrics_json}")
    print(f"           {metrics_txt}")
    print("  Plots:   iv_curve.png")
    if args.log_plot:
        print("           iv_curve_log.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
