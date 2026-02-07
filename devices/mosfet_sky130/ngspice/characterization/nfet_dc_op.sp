* Sky130 NFET DC Operating Point Test
* Sebastian Claudiusz Magierowski Feb 7 2026
*
* sky130_fd_pr__nfet_01v8  W=1um L=150nm
* Vgs=0.6V  Vds=0.9V  tt corner
*
* Requires: ngbehavior=hsa (set via .spiceinit or run_dc_op.sh)
* W/L in microns (HSA scale=1e-6)

.include "../../ngspice/models/sky130_tt.lib"

* Supply voltages
Vgs gate 0 0.6
Vds drain 0 0.9

* NMOS: drain gate source body
XM1 drain gate 0 0 sky130_fd_pr__nfet_01v8 W=1 L=0.15

.op

.control
op
let id = @m.xm1.msky130_fd_pr__nfet_01v8[id]
let gm = @m.xm1.msky130_fd_pr__nfet_01v8[gm]
let gds = @m.xm1.msky130_fd_pr__nfet_01v8[gds]
let vth = @m.xm1.msky130_fd_pr__nfet_01v8[vth]
let vdsat = @m.xm1.msky130_fd_pr__nfet_01v8[vdsat]
echo "===== DC Operating Point Results ====="
echo ""
print id gm gds vth vdsat
echo ""
echo "Derived metrics:"
let gm_id = gm/id
let ro = 1/gds
let av = gm/gds
print gm_id ro av
quit
.endc

.end
