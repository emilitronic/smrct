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

The runner scripts (`scripts/run_*.sh`) handle `.spiceinit` creation automatically.

## Structure

```
ngspice/
  models/sky130_tt.lib                # Wrapper: PDK path + monte carlo params
  characterization/
    nfet_dc_op.sp                     # DC operating point (single bias)
    nfet_av.sp                        # Intrinsic gain av=gm/gds vs Vds at constant Id
    fet_gmId.sp                       # gm/Id vs Vgs (diode-connected, Vgs=Vds sweep)
scripts/
  run_dc_op.sh                        # Runner for nfet_dc_op.sp
  run_av.sh                           # Runner for nfet_av.sp  -> results/av/av_data.txt
  run_gmId.sh                         # Runner for fet_gmId.sp -> results/gmId/gmId_data.txt
  plot_av.py                          # Plot av and ro vs Vds
  plot_gmId.py                        # 2x2 plot: gm/Id, Id, gm*ro, fT vs Vgs/V*
  plot_fet.py                         # Combined 2x2 summary (gmId + av data)
results/
  dc_op/                              # DC operating point log
  av/
    av_data.txt                       # Columns: v-sweep vd vg id_ua gm gds av vstar
    nfet_av_vs_vds.png                # av and ro vs Vds plot
  gmId/
    gmId_data.txt                     # Columns: v-sweep vgs id_ua gm gds vth gm_id
                                      #          vstar ft_GHz vdsat vgsteff
    fet_gmId_vs_vgs.png               # 2x2 grid of gm/Id characterization plots
  fet_summary.png                     # Combined summary plot (from plot_fet.py)
```

## Simulations

### DC Operating Point (`nfet_dc_op.sp`)

Single-bias DC operating point for quick validation.

```bash
bash scripts/run_dc_op.sh
```

### Intrinsic Gain vs Vds (`nfet_av.sp`)

Sweeps Vds at constant drain current using a feedback bias circuit
(current source + VCVS opamp). Extracts av = gm/gds and ro = 1/gds.

```bash
bash scripts/run_av.sh
conda activate mytorch && python3 scripts/plot_av.py
```

### gm/Id Characterization (`fet_gmId.sp`)

Diode-connected NMOS (gate tied to drain) swept from Vgs = Vds = 0.05 to 1.8 V.
Extracts gm/Id, V\* = 2Id/gm, fT = gm/(2*pi*Cgg), vdsat, and vgsteff.

```bash
bash scripts/run_gmId.sh
conda activate mytorch && python3 scripts/plot_gmId.py
```

### Combined Summary (`plot_fet.py`)

Merges data from both `gmId_data.txt` and `av_data.txt` into a single 2x2 grid:

| Quadrant | Plot | Data source |
|----------|------|-------------|
| (1,1) Upper Left  | gm/Id and V\* vs Vgs (dual y-axis) | gmId_data.txt |
| (1,2) Upper Right | Id vs V\*                           | gmId_data.txt |
| (2,1) Lower Left  | av and ro vs Vds at constant Id     | av_data.txt   |
| (2,2) Lower Right | fT*gm/Id and fT vs V\* (dual y-axis) | gmId_data.txt |

```bash
conda activate mytorch && python3 scripts/plot_fet.py
```

## Metadata Pipeline

The runner scripts (`run_av.sh`, `run_gmId.sh`) parse W, L, device name, and other
parameters from the netlist using grep, then prepend `# key = value` header lines
to the ngspice wrdata output. The Python plot scripts read these headers to
automatically set plot titles and labels — changing W/L/Id in the netlist
propagates to the plots without editing the Python code.
