* Sky130 NFET DC Operating Point Test
* Sebastian Claudiusz Magierowski Feb 7 2026
*
* sky130_fd_pr__nfet_01v8  W=10um L=150nm
* Vgs=0.6V  Vds=0.9V  tt corner
*
* Requires: ngbehavior=hsa (set via .spiceinit or run_dc_op.sh)
* W/L in microns (HSA scale=1e-6)

.include "../../ngspice/models/sky130_tt.lib"

* Supply voltages
Vgs gate 0 0.6
Vds drain 0 0.9

* NMOS: drain gate source body
XM1 drain gate 0 0 sky130_fd_pr__nfet_01v8 W=10 L=0.15

.op

.control
op
let id = @m.xm1.msky130_fd_pr__nfet_01v8[id]
let id_uA = id * 1e6
let gm = @m.xm1.msky130_fd_pr__nfet_01v8[gm]
let gm_mS = gm * 1e3
let gds = @m.xm1.msky130_fd_pr__nfet_01v8[gds]
let vth = @m.xm1.msky130_fd_pr__nfet_01v8[vth]
let vdsat = @m.xm1.msky130_fd_pr__nfet_01v8[vdsat]
let vdsat_mV = vdsat * 1e3
let gds_uS = gds * 1e6
let ro_kOhm = 1/gds * 1e-3
let gm_id = gm/id
let av = gm/gds
echo "===== DC Operating Point Results ====="
echo ""
echo "  Id      = $&id_uA uA"
echo "  gm      = $&gm_mS mS"
echo "  gds     = $&gds_uS uS"
echo "  Vth     = $&vth V"
echo "  Vdsat   = $&vdsat_mV mV"
echo ""
echo "Derived metrics:"
echo "  gm/Id   = $&gm_id V^-1"
echo "  ro      = $&ro_kOhm kOhm"
echo "  Av      = $&av"
quit
.endc

.end
