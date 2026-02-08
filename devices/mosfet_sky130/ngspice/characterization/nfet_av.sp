* nfet_av.sp - Intrinsic gain (av = gm/gds) vs Vds at constant Id
* Sebastian Claudiusz Magierowski Feb 7 2026
*
* sky130_fd_pr__nfet_01v8  W=1um L=150nm  Id=10uA
*
* Feedback circuit forces Vd ≈ Vds at constant drain current:
*   I_d sets the drain current to 10uA
*   Vds sets the drain voltage setpoint (swept)
*   E_opamp is an ideal VCVS with gain=100 acting as an op-amp:
*     - Non-inverting input (+) senses the drain voltage V(d)
*     - Inverting input (-) is the Vds setpoint
*     - Output drives the gate: Vg = 100*(V(d) - V(vds_set))
*     - Negative feedback: if V(d) rises above setpoint, Vg rises,
*       MOSFET sinks more current, V(d) falls back. Loop forces V(d) ≈ Vds.
*   This decouples the bias point from device characteristics, allowing
*   a clean Vds sweep while Id remains fixed by the current source.
*
* Requires: ngbehavior=hsa (set via .spiceinit or run_av.sh)
* W/L in microns (HSA scale=1e-6). Current source value is NOT scaled.
*
* To run:  mosfet_sky130/scripts $ ./run_av.sh
* To plot: mosfet_sky130/scripts $ conda activate mytorch && python3 plot_av.py

.include "../models/sky130_tt.lib"

* Device under test
XM1 d g 0 0 sky130_fd_pr__nfet_01v8 W=1 L=0.15

* Biasing
I_d 0 d DC 20u
Vds vds_set 0 DC 0.9
E_opamp g 0 d vds_set 100

* Save MOSFET operating point params as vectors across the DC sweep
* (.save directives required BEFORE .dc so ngspice records gm/gds as vectors at each
* sweep point, not just the final operating point)
.save v(d) v(g)
.save @m.xm1.msky130_fd_pr__nfet_01v8[id]
.save @m.xm1.msky130_fd_pr__nfet_01v8[gm]
.save @m.xm1.msky130_fd_pr__nfet_01v8[gds]

* DC sweep
.dc Vds 0.0 1.8 0.05

.control
run
let vd = v(d)
let vg = v(g)
let id_ua = @m.xm1.msky130_fd_pr__nfet_01v8[id] * 1e6
let gm = @m.xm1.msky130_fd_pr__nfet_01v8[gm]
let gds = @m.xm1.msky130_fd_pr__nfet_01v8[gds]
let av = gm / gds
set wr_singlescale
set wr_vecnames
wrdata av_data.txt vd vg id_ua gm gds av
quit
.endc

.end
