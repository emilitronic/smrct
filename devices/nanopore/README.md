# Nanopore Device Model

Behavioral Spectre model of a solid-state nanopore with voltage-controlled conductance,
membrane capacitance, and series access resistances.

<p align="left">
  <img src="../../docs/nanopore_psd_example.png" width="400" />
</p>

## Model topology

```
bias ──[AMporeres]──┬── Rpore ── Rvar(VCG) ── Racc ──┬── out
                    │                                │
                  [AMporecap]──── Cmem ──────────────┘
```

Three terminals: `bias` (cis electrode), `out` (trans / TIA input), `ctrl` (modulation).

The voltage-controlled conductance (VCG, `sm_vcg.va`) implements:

```
G(ctrl) = (1 + gv·Vctrl) / Ravg
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Ravg`    | 2.25 GΩ | Baseline pore resistance (ONT reference) |
| `gv`      | 0.5     | Conductance modulation gain |
| `Rp`      | 1 Ω     | Series pore resistance (placeholder) |
| `Ra`      | 1 Ω     | Access resistance (placeholder) |
| `Cm`      | 5 pF    | Membrane capacitance |

## Testbenches

| File | Analysis | Description |
|------|----------|-------------|
| `testbenches/standalone/tb_iv.scs` | DC sweep | I-V curve, ctrl=0, bias −1→+1 V |
| `testbenches/standalone/tb_tran.scs` | Transient | Voltage pulse, RC current response |
| `testbenches/standalone/tb_singleporeG.scs` | Transient | CT TIA readout with random translocation events |

## Running simulations

Requires Spectre (sourced via CMC) and `AHDLCMI_GCC_HOME` set for VerilogA — see `CLAUDE.md`.

```bash
cd devices/nanopore/scripts

./run_iv.sh           && python3 analyze_iv.py
./run_tran.sh         && python3 analyze_tran.py
./run_singleporeG.sh  && python3 analyze_singleporeG.py
./run_singleporeG_DT.sh && python3 analyze_singleporeG_DT.py
```

Results and plots land in `results/standalone/{iv,tran,singleporeG}/`.
