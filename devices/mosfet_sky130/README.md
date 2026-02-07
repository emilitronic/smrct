# Sky130 MOSFET Characterization

## PDK Location

Installed via **volare**:
```
/Users/seb/Research/ChipStuff/Tech/Chipathon23/pdk/volare/sky130/versions/
  41c0908b47130d5675ff8484255b43f66463a7d6/sky130A/
```

Model library: `libs.tech/ngspice/sky130.lib.spice`

## ngspice Setup

**Critical**: Sky130 requires `ngbehavior=hsa` set *before* circuit loading.
This must be in a `.spiceinit` file (ngspice reads from cwd or `~/.spiceinit`),
not in a `.control` block.

HSA mode does two things:
1. Resolves subcircuit-scoped BSIM4 binned model names correctly
2. Sets `scale=1e-6` — W/L values are in **microns without the `u` suffix**
   - `W=1 L=0.15` means W=1um, L=150nm

The runner script `scripts/run_dc_op.sh` handles `.spiceinit` creation automatically.

## Structure

```
ngspice/
  models/sky130_tt.lib           # Wrapper: PDK path + monte carlo params
  characterization/nfet_dc_op.sp # DC operating point (single bias)
scripts/
  run_dc_op.sh                   # Runner (sets up .spiceinit, runs ngspice)
results/
  dc_op/                         # Simulation output logs
```

## Quick Test

```bash
bash scripts/run_dc_op.sh
```

Expected output for nfet_01v8 W=1um L=150nm at Vgs=0.6V Vds=0.9V (tt):
- Id ~ 386 nA (subthreshold — Vgs < Vth)
- Vth ~ 769 mV
- gm/Id ~ 22
- Av (gm/gds) ~ 25
