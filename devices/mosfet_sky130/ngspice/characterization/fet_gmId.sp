* fet_gmId.sp - gm/Id vs Vgs characterization (diode-connected)
* Sebastian Claudiusz Magierowski Feb 7 2026
*
* sky130_fd_pr__nfet_01v8  W=1um  L=150nm  tt corner
*
* Diode-connected topology: gate tied to drain so Vgs = Vds.
* Single voltage source swept from 0 to 1.8V.
*
* Requires: ngbehavior=hsa (set via .spiceinit or run_gmId.sh)
* W/L in microns (HSA scale=1e-6)
*
* To run:  mosfet_sky130/scripts $ ./run_gmId.sh
* To plot: mosfet_sky130/scripts $ conda activate mytorch && python3 plot_gmId.py

.include "../models/sky130_tt.lib"

* Device under test (diode-connected: gate = drain)
XM1 d d 0 0 sky130_fd_pr__nfet_01v8 W=1 L=0.15

* Bias
Vds d 0 DC 0.9

* Save MOSFET operating point params as vectors across the DC sweep
.save v(d)
.save @m.xm1.msky130_fd_pr__nfet_01v8[id]
.save @m.xm1.msky130_fd_pr__nfet_01v8[gm]
.save @m.xm1.msky130_fd_pr__nfet_01v8[gds]
.save @m.xm1.msky130_fd_pr__nfet_01v8[vth]
.save @m.xm1.msky130_fd_pr__nfet_01v8[cgg]

* DC sweep (Vgs = Vds since diode-connected)
.dc Vds 0.05 1.8 0.05

.control
run
let vgs = v(d)
let id_ua = @m.xm1.msky130_fd_pr__nfet_01v8[id] * 1e6
let gm = @m.xm1.msky130_fd_pr__nfet_01v8[gm]
let gds = @m.xm1.msky130_fd_pr__nfet_01v8[gds]
let vth = @m.xm1.msky130_fd_pr__nfet_01v8[vth]
let id_raw = @m.xm1.msky130_fd_pr__nfet_01v8[id]
let gm_id = gm / (id_raw + 1e-18)
let vstar = 2 * id_raw / (gm + 1e-18)
let cgg = @m.xm1.msky130_fd_pr__nfet_01v8[cgg]
let pi = 4 * atan(1)
let ft_GHz = gm / (cgg + 1e-30) / (2 * pi) * 1e-9
set wr_singlescale
set wr_vecnames
wrdata gmId_data.txt vgs id_ua gm gds vth gm_id vstar ft_GHz
quit
.endc

.end
