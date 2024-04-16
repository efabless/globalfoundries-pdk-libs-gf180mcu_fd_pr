v {xschem version=3.4.5 file_version=1.2

* Copyright 2022 GlobalFoundries PDK Authors
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     https://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.

}
G {}
K {}
V {}
S {}
E {}
B 2 580 -540 1170 -80 {flags=graph
y1=-0.00015
y2=3.9e-21
ypos1=0
ypos2=2
divy=5
subdivy=1
unity=u
x1=0
x2=3.3
divx=5
subdivx=1
node="i(vd)
i(@m.xm1.m0[id])"
color="4 4"

unitx=1
dataset=-1}
N 30 -230 70 -230 {
lab=G}
N 110 -310 110 -260 {
lab=D}
N 110 -230 210 -230 {
lab=B}
N 110 -200 110 -130 {
lab=S}
C {devices/code_shown.sym} 10 -700 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {devices/lab_pin.sym} 30 -230 0 0 {name=l1 sig_type=std_logic lab=G}
C {devices/lab_pin.sym} 110 -310 0 0 {name=l2 sig_type=std_logic lab=D}
C {devices/lab_pin.sym} 110 -130 0 0 {name=l3 sig_type=std_logic lab=S}
C {devices/lab_pin.sym} 210 -230 0 1 {name=l4 sig_type=std_logic lab=B}
C {devices/code_shown.sym} 250 -590 0 0 {name=NGSPICE only_toplevel=true
value="
vg g 0 3.3
vd d 0 0.5
vs s 0 0
vb b 0 0
.save
+ @m.xm1.m0[gm]
+ @m.xm1.m0[gds]
+ @m.xm1.m0[cgs]
+ @m.xm1.m0[cgd]
+ @m.xm1.m0[csg]
+ @m.xm1.m0[cdg]
+ v(@m.xm1.m0[vth])
+ v(@m.xm1.m0[vdsat])

.option savecurrents
.control
save all
op
remzerovec
write test_nfet_03v3.raw
set appendwrite
dc vd 0 3.3 0.01 vg 0 3.3 0.3
remzerovec
write test_nfet_03v3.raw
.endc
"}
C {devices/title.sym} 160 -30 0 0 {name=l5 author="GlobalFoundries PDK Authors"}
C {symbols/nfet_03v3.sym} 90 -230 0 0 {name=M1
L=0.28u
W=0.22u
nf=1
mult=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X
}
C {devices/launcher.sym} 635 -575 0 0 {name=h1
descr="Click left mouse button here with control key
pressed to load/unload waveforms in graph."
tclcommand="
xschem raw_read $netlist_dir/[file tail [file rootname [xschem get current_name]]].raw dc
"
}
C {devices/ngspice_get_value.sym} 30 -460 0 0 {name=r1 node=@m.xm1.m0[gm]
descr="gm="}
C {devices/ngspice_get_value.sym} 30 -420 0 0 {name=r2 node=@m.xm1.m0[gds]
descr="gds="}
C {devices/launcher.sym} 90 -90 0 0 {name=h5
descr="Annotate OP" 
tclcommand="xschem annotate_op"
}
C {devices/ngspice_get_value.sym} 30 -380 0 0 {name=r3 node=v(@m.xm1.m0[vdsat])
descr="vdsat="}
C {devices/ngspice_get_value.sym} 30 -340 0 0 {name=r4 node=v(@m.xm1.m0[vth])
descr="vth="}
C {devices/ngspice_get_value.sym} 130 -460 0 0 {name=r5 node=@m.xm1.m0[cgs]
descr="cgs="}
C {devices/ngspice_get_value.sym} 130 -430 0 0 {name=r6 node=@m.xm1.m0[cgd]
descr="cgd="}
C {devices/ngspice_get_value.sym} 130 -390 0 0 {name=r7 node=@m.xm1.m0[csg]
descr="csg="}
C {devices/ngspice_get_value.sym} 130 -360 0 0 {name=r8 node=@m.xm1.m0[cdg]
descr="cdg="}
C {devices/noconn.sym} 110 -280 0 0 {name=l6}
C {devices/noconn.sym} 110 -180 0 0 {name=l7}
C {devices/noconn.sym} 50 -230 3 0 {name=l8}
C {devices/noconn.sym} 170 -230 3 0 {name=l9}
