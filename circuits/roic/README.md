# circuits/roic — ROIC System-Level Models

S. Magierowski — original SM_ROIC library May 2023, smrct port May 20 2026

Behavioural (VerilogA) models and testbenches for a multi-channel nanopore
Readout Integrated Circuit (ROIC).  The goal is rapid system-level simulation
and design-space exploration before committing to transistor-level implementation.

---

## VerilogA building blocks

The shared models live in `models/verilogA/` at the repo root:

| Model | Description |
|---|---|
| `sm_gm_so.va` | Single-ended Gm-cell — core of the DT integrator TIA |
| `sm_gm_do.va` | Differential Gm-cell (clean baseline, no supply/limiting) |
| `sm_gm_do2.va` | Differential Gm-cell with supply current and soft rail limiting |
| `sm_sw_no.va` | Normally-open switch, finite ron/roff — use for reset switches |
| `sm_ideal_sw.va` | Ideal switch (reference only — convergence issues with cap loads) |

All Gm-cells share the same parameterisation:
`GBW`, `gain`, `EFF` (gm/Id), `Rin`, `Vin_off`, `Iout_max`, `slew_rate`, `Vsoft`.
Internal parameters `Cout`, `Gm`, `Rout`, `Vin_max` are derived at `initial_step`.

---

## Testbenches

### tb_TIA1 — DT Integrator TIA

```
testbenches/standalone/tb_TIA1.scs
scripts/run_TIA1.sh
scripts/analyze_TIA1.py
```

Confirms integrate-and-dump action of a `sm_gm_so`-based TIA against a
step-ramp current input (0 → 200 pA).  Equivalent to the original
`SM_ROIC/tb_TIA1/ad_basicsim1` ADE setup.

Key parameters: `Cf=20fF`, `Cm=5pF`, `fs=1kHz`, `Ki=0.625`, `Vdd=1.5V`.

Expected result: `Vint ≈ 696 mV` per integration cycle (matches original ADE measurement).

**Run:**
```bash
cd circuits/roic/scripts
./run_TIA1.sh && python3 analyze_TIA1.py
```

Outputs in `results/standalone/TIA1/`:
- `TIA1_time.png` — clk / Iin / ipTIA / opTIA time-domain traces
- `TIA1_vint.png` — integrated output swing per clock cycle vs ADE reference

---

## Relationship to nanopore device

The DT TIA here (`sm_gm_so` + `sm_sw_no`) is the circuit-level realisation
of the integrate-and-dump topology simulated behaviourally in
`devices/nanopore/testbenches/standalone/tb_singleporeG_DT.scs`, which uses
an ideal VCVS op-amp.  Key differences:

| | tb_singleporeG_DT | tb_TIA1 |
|---|---|---|
| Op-amp | Ideal VCVS (gain=1e6) | sm_gm_so (GBW=10M, gain=50) |
| Input | Nanopore random telegraph | PWL current ramp |
| Purpose | Signal statistics / PSD | Circuit settling / Vint |
