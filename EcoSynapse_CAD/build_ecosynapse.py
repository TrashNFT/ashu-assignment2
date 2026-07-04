#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EcoSynapse Miniature MRF — parametric CAD generator (CadQuery -> STEP).
Builds every 3D-printed stage + frame as a solid body, exports:
  - one STEP per part (for 3D printing / editing)
  - one positioned multi-body assembly STEP (opens in Autodesk Fusion)
All dimensions in millimetres. Based on EcoSynapse Rev 3.1 manual + build photos.
"""
import os, math, time
import cadquery as cq

OUT = "/Users/kushu/ashu assign2/EcoSynapse_CAD"
PARTS_DIR = os.path.join(OUT, "parts")
os.makedirs(PARTS_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# Global parameters (edit these in Fusion via the imported bodies, or here)
# ----------------------------------------------------------------------------
WALL      = 3.0        # default printed wall thickness
M3_CLR    = 3.4        # M3 clearance hole
M3_INSERT = 4.0        # heat-set insert pilot hole (M3)
M4_CLR    = 4.5        # M4 clearance hole
BRG_OD    = 22.12      # 608ZZ outer race, +0.12 press-fit allowance
BRG_W     = 7.0        # 608ZZ width
SHAFT     = 8.0        # 8 mm shafts (608 bore)
SHAFT_CLR = 8.3        # rotating shaft clearance

# Chassis envelope (manual 2.2): 800 L x 380 W x 520 H
L, W, H = 800.0, 380.0, 520.0

# RGB colours (0-1) so OCC never rejects a name
COLORS = {
    "gray": (0.6, 0.6, 0.6), "dimgray": (0.35, 0.35, 0.35), "darkgray": (0.55, 0.55, 0.55),
    "silver": (0.75, 0.75, 0.78), "slategray": (0.44, 0.5, 0.56), "gainsboro": (0.86, 0.86, 0.86),
    "whitesmoke": (0.96, 0.96, 0.96), "lightgray": (0.8, 0.8, 0.8), "black": (0.15, 0.15, 0.15),
    "lightsteelblue": (0.69, 0.77, 0.87), "steelblue": (0.27, 0.51, 0.71), "aliceblue": (0.85, 0.9, 0.98),
    "lightblue": (0.68, 0.85, 0.9), "deepskyblue": (0.2, 0.6, 0.9), "seagreen": (0.18, 0.55, 0.34),
    "gold": (0.9, 0.75, 0.15), "khaki": (0.85, 0.78, 0.5), "burlywood": (0.78, 0.6, 0.4),
    "orange": (0.95, 0.6, 0.1), "orangered": (0.9, 0.3, 0.1), "red": (0.85, 0.2, 0.2),
}
def col(name):
    r, g, b = COLORS.get(name, (0.6, 0.6, 0.6))
    return cq.Color(r, g, b, 1.0)

PARTS = []   # (name, shape, location, color) for assembly + export

def add(name, shape, location=None, color="gray"):
    PARTS.append((name, shape, location, color))
    return shape

def loc(x=0, y=0, z=0, rx=0, ry=0, rz=0):
    T  = cq.Location(cq.Vector(x, y, z))
    Rx = cq.Location(cq.Vector(), cq.Vector(1, 0, 0), rx)
    Ry = cq.Location(cq.Vector(), cq.Vector(0, 1, 0), ry)
    Rz = cq.Location(cq.Vector(), cq.Vector(0, 0, 1), rz)
    return T * Rz * Ry * Rx

def sensor_boss(wp, face, pts, d=M3_INSERT):
    return wp.faces(face).workplane().pushPoints(pts).hole(d)

# ============================================================================
#  FRAME / CHASSIS
# ============================================================================
def base_panel():
    """6 mm plywood/acrylic base deck, with a mounting-hole grid."""
    p = cq.Workplane("XY").box(L, W, 6, centered=(True, True, False))
    # corner bolt holes for corner brackets
    xs = [-(L/2-20), (L/2-20)]
    ys = [-(W/2-20), (W/2-20)]
    pts = [(x, y) for x in xs for y in ys]
    p = p.faces(">Z").workplane().pushPoints(pts).hole(M4_CLR)
    return p

def foot():
    """Rubber-topped printed levelling foot, M4 threaded top."""
    f = (cq.Workplane("XY").circle(22).extrude(6)
         .faces(">Z").circle(16).extrude(20)
         .faces(">Z").hole(M4_CLR))
    return f

def corner_bracket():
    """L-bracket joining a 20x20 corner post to the base deck."""
    a = cq.Workplane("XY").box(45, 45, 5, centered=(False, False, False))
    a = a.faces(">Z").workplane().pushPoints([(15, 15), (32, 32)]).hole(M4_CLR)
    b = cq.Workplane("YZ").box(45, 45, 5, centered=(False, False, False)).translate((0, 0, 0))
    b = b.faces(">X").workplane().pushPoints([(15, 15), (32, 32)]).hole(M4_CLR)
    return a.union(b)

def post(height):
    """Stand-in for a 20x20 aluminium extrusion corner post (purchased)."""
    return cq.Workplane("XY").box(20, 20, height, centered=(True, True, False))

# ============================================================================
#  STAGE 0 — HOPPER + HAZARD DIVERTER
# ============================================================================
def hopper():
    """Square funnel 170->60 with mounting collar, anti-bridge rib,
       SG90 servo pocket + slot for the hazard-diverter flap."""
    top, bot, hh = 170.0, 62.0, 135.0
    outer = (cq.Workplane("XY").rect(top, top)
             .workplane(offset=hh).rect(bot, bot).loft(combine=True))
    inner = (cq.Workplane("XY", origin=(0, 0, -1)).rect(top-2*WALL, top-2*WALL)
             .workplane(offset=hh+2).rect(bot-2*WALL, bot-2*WALL).loft(combine=True))
    h = outer.cut(inner)
    # bottom mounting collar (flange with 4 holes)
    collar = (cq.Workplane("XY", origin=(0, 0, hh))
              .rect(bot+22, bot+22).extrude(8)
              .faces(">Z").rect(bot-2*WALL, bot-2*WALL, forConstruction=True))
    collar = (cq.Workplane("XY", origin=(0, 0, hh)).box(bot+24, bot+24, 8, centered=(True, True, False))
              .faces("<Z").rect(bot-2, bot-2).cutThruAll()
              .faces(">Z").workplane()
              .pushPoints([(-(bot/2+8), -(bot/2+8)), ((bot/2+8), -(bot/2+8)),
                           (-(bot/2+8), (bot/2+8)), ((bot/2+8), (bot/2+8))]).hole(M3_INSERT))
    h = h.union(collar)
    # top rim lip
    rim = cq.Workplane("XY").rect(top+6, top+6).extrude(4).faces(">Z").rect(top-2, top-2).cutThruAll()
    h = h.union(rim)
    # anti-bridging rib across the throat (inside)
    rib = cq.Workplane("XY", origin=(0, 0, hh-30)).box(bot-2*WALL, 4, 24, centered=(True, True, False))
    h = h.union(rib)
    # servo pocket + flap slot on one lower side wall
    servo_pocket = cq.Workplane("XY", origin=(bot/2+2, 0, hh-46)).box(6, 26, 14, centered=(True, True, False))
    h = h.cut(servo_pocket)
    flap_slot = cq.Workplane("XY", origin=(0, 0, hh+3)).box(bot-6, 3, 30, centered=(True, True, False))
    # (flap slot is illustrative; keep body solid) -> skip cut to avoid opening collar
    return h

def hazard_flap():
    """Solenoid/servo-latched diverter flap that routes hazards to HAZARD bin."""
    f = cq.Workplane("XY").box(58, 58, 3, centered=(True, True, False))
    # hinge knuckle
    hinge = (cq.Workplane("YZ", origin=(-29, 0, 0)).circle(4).extrude(58)
             .faces(">X").workplane())
    hinge = cq.Workplane("XZ", origin=(0, -29, 1.5)).circle(4).extrude(58).translate((0, 0, 0))
    f = f.union(cq.Workplane("XZ", origin=(0, 29, 1.5)).circle(4).extrude(-58))
    f = f.faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 0)]).hole(2.5)  # servo-horn link
    return f

# ============================================================================
#  STAGE 0.5 — COARSE SPLIT TROMMEL (wide slot) + cradle stands
# ============================================================================
def trommel_drum(od=180, length=220, slot_w=50, wall=3.0, rings=3, per_ring=5,
                 hub_bore=SHAFT_CLR, name="coarse"):
    """Slotted rotating drum with end hubs + drive-gear boss."""
    r = od/2.0
    drum = cq.Workplane("XY").circle(r).circle(r-wall).extrude(length)
    # end rings (solid annulus) at each end already part of tube; add spoked end caps w/ hub
    def endcap(z):
        cap = cq.Workplane("XY", origin=(0, 0, z)).circle(r).circle(r-wall).extrude(6 if z==0 else -6)
        hub = cq.Workplane("XY", origin=(0, 0, z)).circle(14).extrude(10 if z==0 else -10)
        hub = hub.faces(">Z" if z==0 else "<Z").hole(hub_bore)
        # 3 spokes
        spokes = cq.Workplane("XY", origin=(0, 0, (z + (5 if z==0 else -5))))
        sp = None
        for a in range(0, 360, 120):
            bar = (cq.Workplane("XY", origin=(0, 0, z)).transformed(rotate=(0, 0, a))
                   .box(r*2-2*wall, 8, 5, centered=(True, True, False)) if z==0 else
                   cq.Workplane("XY", origin=(0, 0, z-5)).transformed(rotate=(0, 0, a))
                   .box(r*2-2*wall, 8, 5, centered=(True, True, False)))
            sp = bar if sp is None else sp.union(bar)
        return cap.union(hub).union(sp)
    drum = drum.union(endcap(0)).union(endcap(length))
    # cut slots: rings along length x per_ring around circumference (staggered)
    slot_l = (length - 40) / rings - 10
    cutters = None
    for ri in range(rings):
        zc = 25 + ri * ((length - 50) / max(1, rings-1) if rings > 1 else 0) if rings > 1 else length/2
        zc = 25 + ri * ((length - 50) / (rings)) + slot_l/2
        stagger = (360/per_ring/2) if ri % 2 else 0
        for k in range(per_ring):
            a = k * (360/per_ring) + stagger
            slot = (cq.Workplane("XZ", origin=(0, 0, 0))
                    .transformed(offset=cq.Vector(0, zc, 0))
                    .box(slot_w, slot_l, od, centered=(True, True, True))
                    .translate((0, 0, 0)))
            # radial slot: make a box oriented radially by rotating around drum axis (Z)
            slot = (cq.Workplane("XY").transformed(rotate=(0, 0, a))
                    .transformed(offset=cq.Vector(0, 0, zc))
                    .box(od+4, slot_w, slot_l, centered=(True, True, True)))
            cutters = slot if cutters is None else cutters.union(slot)
    if cutters is not None:
        drum = drum.cut(cutters)
    return drum

def cradle_stand(bore=BRG_OD, drum_od=180, base_w=70):
    """V/semicircular stand with a 608 bearing pocket to carry a drum/roller shaft."""
    top_z = drum_od/2 + 30
    body = (cq.Workplane("XY").box(base_w, 40, 8, centered=(True, True, False))  # foot
            .faces(">Z").workplane()
            .pushPoints([(-(base_w/2-10), 0), ((base_w/2-10), 0)]).hole(M4_CLR))
    upright = (cq.Workplane("XZ", origin=(0, 0, 0)).moveTo(-20, 8)
               .lineTo(-14, top_z).lineTo(14, top_z).lineTo(20, 8).close()
               .extrude(16).translate((0, 8, 0)))
    # bearing pocket (blind, from front)
    pocket = cq.Workplane("XZ", origin=(0, 0, top_z-14)).workplane(offset=8).circle(bore/2).extrude(-BRG_W-1)
    pocket = (cq.Workplane("XY", origin=(0, 8+16, top_z-14)).transformed(rotate=(90, 0, 0))
              .circle(bore/2).extrude(BRG_W+1))
    stand = body.union(upright).cut(pocket)
    # thru shaft clearance
    stand = stand.cut(cq.Workplane("XY", origin=(0, 8+16, top_z-14)).transformed(rotate=(90, 0, 0)).circle(SHAFT_CLR/2).extrude(30))
    return stand

# ============================================================================
#  WET-PATH FUNNEL + TRAMP-METAL SENSOR MOUNT
# ============================================================================
def wet_funnel():
    """Rectangular funnel under the trommel slots -> shredder throat,
       with an M12 inductive (tramp-metal) sensor boss on the throat."""
    top_x, top_y, hh, throat = 200.0, 150.0, 120.0, 66.0
    outer = (cq.Workplane("XY").rect(top_x, top_y)
             .workplane(offset=hh).rect(throat+2*WALL, throat+2*WALL).loft(combine=True))
    inner = (cq.Workplane("XY", origin=(0, 0, -1)).rect(top_x-2*WALL, top_y-2*WALL)
             .workplane(offset=hh+2).rect(throat, throat).loft(combine=True))
    f = outer.cut(inner)
    # throat collar to bolt onto shredder inlet
    collar = (cq.Workplane("XY", origin=(0, 0, hh)).box(throat+2*WALL+20, throat+2*WALL+20, 8, centered=(True, True, False))
              .faces("<Z").rect(throat, throat).cutThruAll()
              .faces(">Z").workplane()
              .rect(throat+16, throat+16, forConstruction=True).vertices().hole(M3_INSERT))
    f = f.union(collar)
    # M12 inductive sensor boss on +X throat wall
    boss = (cq.Workplane("YZ", origin=(throat/2+WALL, 0, hh-24)).circle(11).extrude(10)
            .faces(">X").hole(12.4))
    boss = (cq.Workplane("XY", origin=(throat/2+WALL, 0, hh-26)).transformed(rotate=(0, 90, 0))
            .circle(11).extrude(10).faces(">Z").hole(12.4))
    f = f.union(boss)
    return f

def dry_chute():
    """Inclined U-trough carrying rigid items from trommel dry end to vibratory feeder."""
    length, width, side = 170.0, 90.0, 28.0
    base = cq.Workplane("XY").box(length, width, WALL, centered=(True, True, False))
    l = cq.Workplane("XY", origin=(0, width/2-WALL, 0)).box(length, WALL, side, centered=(True, True, False))
    r = cq.Workplane("XY", origin=(0, -(width/2-WALL), 0)).box(length, WALL, side, centered=(True, True, False))
    chute = base.union(l).union(r)
    # mounting tabs
    tab = (cq.Workplane("XY", origin=(-length/2+8, 0, 0)).box(16, width, WALL, centered=(True, True, False)))
    chute = chute.union(cq.Workplane("XY", origin=(length/2-8, 0, 0)).box(16, width+20, WALL, centered=(True, True, False))
                        .faces(">Z").workplane().pushPoints([(0, width/2+4), (0, -(width/2+4))]).hole(M3_CLR))
    return chute

# ============================================================================
#  STAGE 1 — SHREDDER (housing + 2 toothed rollers + motor mount)
# ============================================================================
def shredder_housing():
    ox, oy, oz = 150.0, 120.0, 95.0
    wall = 4.0
    cc = 46.0  # roller centre distance
    box = cq.Workplane("XY").box(ox, oy, oz, centered=(True, True, False))
    cav = cq.Workplane("XY", origin=(0, 0, 22)).box(ox-2*wall, oy-2*wall, oz, centered=(True, True, False))
    h = box.cut(cav)
    # top inlet
    h = h.cut(cq.Workplane("XY", origin=(0, 0, oz-1)).box(ox-2*wall-6, oy-2*wall-6, 10, centered=(True, True, False)))
    # bottom outlet
    h = h.cut(cq.Workplane("XY", origin=(0, 0, -1)).box(70, oy-2*wall-6, 40, centered=(True, True, False)))
    # bearing bores in +Y and -Y walls for the two rollers
    for yb in (oy/2, -oy/2):
        for xb in (cc/2, -cc/2):
            brg = (cq.Workplane("XY", origin=(xb, yb, 55)).transformed(rotate=(90, 0, 0))
                   .circle(BRG_OD/2).extrude(-BRG_W if yb > 0 else BRG_W))
            h = h.cut(brg)
            thru = (cq.Workplane("XY", origin=(xb, yb, 55)).transformed(rotate=(90, 0, 0))
                    .circle(SHAFT_CLR/2).extrude(-wall*2 if yb > 0 else wall*2))
            h = h.cut(thru)
    # motor mount plate on -Y wall (round-can geared motor: 37 mm)
    mm = (cq.Workplane("XY", origin=(cc/2, -oy/2-6, 55)).transformed(rotate=(90, 0, 0))
          .rect(60, 60).extrude(6))
    mm = mm.faces("<Y").workplane()  # ignore, add holes below via separate op
    plate = (cq.Workplane("XZ", origin=(cc/2, -oy/2-6, 55)).rect(64, 64).extrude(-6)
             .faces("<Y").workplane(centerOption="CenterOfBoundBox").hole(38)
             .faces("<Y").workplane(centerOption="CenterOfBoundBox")
             .pushPoints([(-25, 0), (25, 0), (0, 25), (0, -25)]).hole(M3_CLR))
    h = h.union(plate)
    # lid interlock switch mount pocket on top rim
    h = h.union(cq.Workplane("XY", origin=(ox/2-8, oy/2-14, oz)).box(14, 22, 8, centered=(True, True, False))
                .faces(">Z").workplane().pushPoints([(0, 6), (0, -6)]).hole(M3_CLR))
    # foot flanges
    for xb in (ox/2, -ox/2):
        h = h.union(cq.Workplane("XY", origin=(xb, 0, 0)).box(10, oy, 6, centered=(True, True, False))
                    .faces(">Z").workplane().pushPoints([(0, oy/2-8), (0, -(oy/2-8))]).hole(M4_CLR))
    return h

def shredder_roller():
    """Blunt-tooth counter-rotating roller, PETG, 8 mm shaft."""
    dia, length = 40.0, 100.0
    core = cq.Workplane("XY").circle(dia/2).extrude(length)
    # shaft stubs
    core = core.faces(">Z").circle(SHAFT/2).extrude(16).faces("<Z").circle(SHAFT/2).extrude(16)
    # blunt teeth: rows of trapezoid nubs around & along
    teeth = None
    rows, per = 5, 6
    for ri in range(rows):
        zc = 12 + ri * (length-24)/(rows-1)
        for k in range(per):
            a = k*(360/per) + (30 if ri % 2 else 0)
            tooth = (cq.Workplane("XY", origin=(0, 0, zc)).transformed(rotate=(0, 0, a))
                     .transformed(offset=cq.Vector(dia/2-1, 0, 0), rotate=(0, 0, 0))
                     .box(8, 10, 12, centered=(True, True, True)))
            teeth = tooth if teeth is None else teeth.union(tooth)
    core = core.union(teeth)
    # flat for grub screw on one shaft stub
    core = core.cut(cq.Workplane("XY", origin=(SHAFT/2-1.0, 0, length+8)).box(2, 6, 10, centered=(True, True, True)))
    return core

# ============================================================================
#  STAGE 2 — AUGER DEWATERING PRESS (screw + slotted tube + tray + probe mount)
# ============================================================================
def auger_screw():
    pitch, length, r_mid, flight_r, flight_t = 25.0, 170.0, 16.0, 8.5, 2.6
    shaft = cq.Workplane("XY").circle(9).extrude(length)
    shaft = shaft.faces(">Z").circle(SHAFT/2).extrude(18).faces("<Z").circle(SHAFT/2).extrude(18)
    helix = cq.Wire.makeHelix(pitch=pitch, height=length, radius=r_mid)
    path = cq.Workplane(obj=helix)
    prof = cq.Workplane("XZ").center(r_mid, 0).rect(flight_r*2, flight_t)
    flight = prof.sweep(path, isFrenet=True)
    return shaft.union(flight)

def auger_tube():
    od, idd, length = 60.0, 50.0, 190.0
    tube = cq.Workplane("XY").circle(od/2).circle(idd/2).extrude(length)
    # dewatering drain slots on lower half (rows of thin axial slots)
    cutters = None
    for row_a in range(-70, 71, 20):        # around lower half only
        for zc in range(25, int(length)-20, 22):
            slot = (cq.Workplane("XY", origin=(0, 0, zc)).transformed(rotate=(0, 0, row_a))
                    .transformed(offset=cq.Vector(0, 0, 0))
                    .box(od+4, 2.2, 12, centered=(True, True, True)))
            cutters = slot if cutters is None else cutters.union(slot)
    tube = tube.cut(cutters)
    # inlet end cap w/ bearing pocket + motor mount, outlet ring
    inlet = (cq.Workplane("XY", origin=(0, 0, 0)).circle(od/2).extrude(-8)
             .faces("<Z").workplane(centerOption="CenterOfBoundBox").circle(BRG_OD/2).extrude(-BRG_W)
             )
    inlet = inlet.faces("<Z").workplane(centerOption="CenterOfBoundBox").hole(SHAFT_CLR)
    # top inlet opening cut in tube wall
    tube = tube.cut(cq.Workplane("XY", origin=(0, od/2, length-30)).transformed(rotate=(90, 0, 0)).rect(40, 40).extrude(-8))
    tube = tube.union(inlet)
    # motor bracket at inlet
    br = (cq.Workplane("XY", origin=(0, 0, -8)).circle(od/2+10).extrude(-6)
          .faces("<Z").workplane(centerOption="CenterOfBoundBox").rect(50, 50, forConstruction=True).vertices().hole(M3_CLR))
    tube = tube.union(br)
    return tube

def auger_tray():
    """Liquid catch reservoir (Bin 1) under the auger tube, with drain spout."""
    lx, ly, lz, wall = 210.0, 90.0, 45.0, 3.0
    box = cq.Workplane("XY").box(lx, ly, lz, centered=(True, True, False))
    box = box.faces(">Z").shell(-wall)
    # drain spout
    spout = (cq.Workplane("XY", origin=(lx/2-1, 0, 8)).transformed(rotate=(0, 90, 0))
             .circle(6).extrude(16).faces(">Z").hole(8))
    box = box.union(spout)
    return box

def probe_mount():
    """Clip mount for a capacitive moisture strip (98x23 board) near auger outlet."""
    base = cq.Workplane("XY").box(40, 30, WALL, centered=(True, True, False))
    base = base.faces(">Z").workplane().pushPoints([(-14, 0), (14, 0)]).hole(M3_CLR)
    clip = (cq.Workplane("XY", origin=(0, 12, 0)).box(30, 4, 20, centered=(True, True, False))
            .faces(">Z").workplane())
    slot = cq.Workplane("XY", origin=(0, 8, 8)).box(26, 6, 24, centered=(True, True, False))
    return base.union(cq.Workplane("XY", origin=(0, 12, 0)).box(30, 4, 22, centered=(True, True, False))) \
               .union(cq.Workplane("XY", origin=(0, 6, 0)).box(30, 3, 22, centered=(True, True, False)))

# ============================================================================
#  STAGE 3 — FINE TROMMEL (small slots) + STAGE 4 AIR CLASSIFIER
# ============================================================================
def fine_trommel():
    return trommel_drum(od=95, length=140, slot_w=4, wall=3.0, rings=5, per_ring=8, name="fine")

def air_classifier():
    """Chamber with a 40 mm fan mount and two light/heavy lane dividers."""
    lx, ly, lz, wall = 120.0, 130.0, 140.0, 3.0
    box = cq.Workplane("XY").box(lx, ly, lz, centered=(True, True, False))
    box = box.faces(">Z").shell(-wall)
    # open top (drop-in) already open via shell top; cut a front opening
    box = box.cut(cq.Workplane("XY", origin=(0, ly/2, lz-40)).transformed(rotate=(90, 0, 0)).rect(lx-2*wall-10, 60).extrude(-wall*2))
    # fan mount on -X wall (40 mm fan: 32 mm hole, 4 x M3 at 32 mm square)
    fan = (cq.Workplane("XY", origin=(-lx/2, 0, lz/2)).transformed(rotate=(0, 90, 0))
           .circle(20).extrude(-wall*2))
    box = box.cut(fan)
    holes = (cq.Workplane("XY", origin=(-lx/2, 0, lz/2)).transformed(rotate=(0, 90, 0))
             .pushPoints([(16, 16), (-16, 16), (16, -16), (-16, -16)]).circle(1.6).extrude(-wall*2))
    box = box.cut(holes)
    # lane divider in the middle of the floor
    div = cq.Workplane("XY", origin=(10, 0, wall)).box(wall, ly-2*wall, 50, centered=(True, True, False))
    box = box.union(div)
    return box

# ============================================================================
#  VIBRATORY SINGULATION FEEDER (tray + leaf-spring flexures + motor pocket)
# ============================================================================
def vibratory_feeder():
    tx, ty, side, wall = 160.0, 70.0, 20.0, 3.0
    tray = cq.Workplane("XY").box(tx, ty, wall, centered=(True, True, False))
    tray = tray.union(cq.Workplane("XY", origin=(0, ty/2-wall, 0)).box(tx, wall, side, centered=(True, True, False)))
    tray = tray.union(cq.Workplane("XY", origin=(0, -(ty/2-wall), 0)).box(tx, wall, side, centered=(True, True, False)))
    tray = tray.union(cq.Workplane("XY", origin=(-tx/2+wall, 0, 0)).box(wall, ty, side, centered=(True, True, False)))
    # vib-motor pocket under the tray (cylindrical eccentric-mass motor ~ 10 mm)
    motor = cq.Workplane("XY", origin=(0, 0, -14)).box(30, 14, 14, centered=(True, True, False))
    tray = tray.union(motor)
    tray = tray.cut(cq.Workplane("XY", origin=(0, 0, -14)).transformed(rotate=(0, 90, 0)).circle(5.2).extrude(20))
    # 4 leaf-spring flexure legs
    for sx in (tx/2-14, -(tx/2-14)):
        for sy in (ty/2-10, -(ty/2-10)):
            leg = cq.Workplane("XY", origin=(sx, sy, -34)).box(10, 2.2, 34, centered=(True, True, False))
            foot = (cq.Workplane("XY", origin=(sx, sy, -40)).box(16, 16, 6, centered=(True, True, False))
                    .faces("<Z").workplane(centerOption="CenterOfBoundBox").hole(M3_CLR))
            tray = tray.union(leg).union(foot)
    return tray

# ============================================================================
#  CONVEYOR (side frames, rollers, belt, motor bracket, encoder disc+bracket)
# ============================================================================
BELT_W   = 120.0     # roller length / belt width
BELT_SPAN = 320.0    # roller-centre to roller-centre
ROLLER_D = 40.0

def conveyor_roller():
    r = cq.Workplane("XY").circle(ROLLER_D/2).extrude(BELT_W)
    r = r.faces(">Z").circle(SHAFT/2).extrude(20).faces("<Z").circle(SHAFT/2).extrude(20)
    # slight crown could be added; keep straight
    r = r.cut(cq.Workplane("XY", origin=(SHAFT/2-1, 0, BELT_W+12)).box(2, 6, 12, centered=(True, True, True)))
    return r

def conveyor_side():
    """Side frame plate with 2 bearing bores + deck mounting feet."""
    length = BELT_SPAN + 80
    plate = cq.Workplane("XY").box(length, 6, 70, centered=(True, True, False))
    for xb in (BELT_SPAN/2, -BELT_SPAN/2):
        bore = (cq.Workplane("XY", origin=(xb, 0, ROLLER_D/2+8)).transformed(rotate=(90, 0, 0))
                .circle(BRG_OD/2).extrude(4))
        plate = plate.cut(bore)
        plate = plate.cut(cq.Workplane("XY", origin=(xb, 0, ROLLER_D/2+8)).transformed(rotate=(90, 0, 0)).circle(SHAFT_CLR/2).extrude(-8))
    # mounting feet
    for xb in (length/2-20, -(length/2-20)):
        plate = plate.union(cq.Workplane("XY", origin=(xb, -8, 0)).box(30, 16, 6, centered=(True, True, False))
                            .faces(">Z").workplane().hole(M4_CLR))
    return plate

def conveyor_belt():
    """Racetrack belt loop skin wrapping the two rollers (visual + fit ref)."""
    r = ROLLER_D/2 + 1.5
    path = (cq.Workplane("XY").moveTo(-BELT_SPAN/2, r).lineTo(BELT_SPAN/2, r)
            .threePointArc((BELT_SPAN/2+r, 0), (BELT_SPAN/2, -r))
            .lineTo(-BELT_SPAN/2, -r)
            .threePointArc((-BELT_SPAN/2-r, 0), (-BELT_SPAN/2, r)).close())
    outer = path.extrude(BELT_W)
    inner = (cq.Workplane("XY").moveTo(-BELT_SPAN/2, r-1.5).lineTo(BELT_SPAN/2, r-1.5)
             .threePointArc((BELT_SPAN/2+r-1.5, 0), (BELT_SPAN/2, -(r-1.5)))
             .lineTo(-BELT_SPAN/2, -(r-1.5))
             .threePointArc((-BELT_SPAN/2-(r-1.5), 0), (-BELT_SPAN/2, r-1.5)).close()).extrude(BELT_W)
    return outer.cut(inner)

def motor_bracket_tt():
    """Bracket to mount a TT gear motor (70x22x37) to the driven roller shaft end."""
    plate = cq.Workplane("XY").box(50, 40, 4, centered=(True, True, False))
    plate = plate.faces(">Z").workplane().hole(SHAFT_CLR)
    # TT motor 2-hole pattern (holes 3.5 mm, ~ 18 mm apart)
    plate = plate.faces(">Z").workplane().pushPoints([(-9, 12), (9, 12)]).hole(3.5)
    plate = plate.union(cq.Workplane("XY", origin=(0, -18, 0)).box(50, 4, 30, centered=(True, True, False))
                        .faces(">Y").workplane().pushPoints([(-16, 12), (16, 12)]).hole(M3_CLR))
    return plate

def encoder_disc(slots=20):
    """Slotted optical encoder disc on the driven roller shaft."""
    r = 30.0
    disc = cq.Workplane("XY").circle(r).extrude(2).faces(">Z").hole(SHAFT_CLR)
    # hub
    disc = disc.union(cq.Workplane("XY", origin=(0, 0, 2)).circle(9).extrude(6).faces(">Z").hole(SHAFT_CLR))
    disc = disc.faces(">Z").workplane().pushPoints([(9, 0)]).hole(M3_INSERT)  # grub-screw side (approx)
    # cut slots near rim
    cutters = None
    for k in range(slots):
        a = k*(360/slots)
        s = (cq.Workplane("XY").transformed(rotate=(0, 0, a))
             .transformed(offset=cq.Vector(r-6, 0, 0)).box(8, 360/slots*0.5*r*math.pi/180*2, 4, centered=(True, True, True)))
        s = (cq.Workplane("XY", origin=(0, 0, -1)).transformed(rotate=(0, 0, a))
             .moveTo(r-9, -2.2).lineTo(r-1, -2.2).lineTo(r-1, 2.2).lineTo(r-9, 2.2).close().extrude(4))
        cutters = s if cutters is None else cutters.union(s)
    disc = disc.cut(cutters)
    return disc

def encoder_bracket():
    """U-bracket straddling the encoder disc rim holding an IR beam-break pair."""
    base = cq.Workplane("XY").box(24, 40, 4, centered=(True, True, False)).faces(">Z").workplane().pushPoints([(0,14),(0,-14)]).hole(M3_CLR)
    a1 = cq.Workplane("XY", origin=(0, 12, 0)).box(24, 4, 34, centered=(True, True, False))
    a2 = cq.Workplane("XY", origin=(0, -12, 0)).box(24, 4, 34, centered=(True, True, False))
    u = base.union(a1).union(a2)
    # emitter/receiver holes facing the gap
    u = u.cut(cq.Workplane("XY", origin=(0, 12, 26)).transformed(rotate=(90, 0, 0)).circle(2.6).extrude(6))
    u = u.cut(cq.Workplane("XY", origin=(0, -12, 26)).transformed(rotate=(90, 0, 0)).circle(2.6).extrude(-6))
    return u

# ============================================================================
#  MAGNET MOUNT + GENERIC SENSOR BRACKETS
# ============================================================================
def magnet_mount():
    """Cantilever arm holding a neodymium strip just above the belt (slotted for height)."""
    up = cq.Workplane("XY").box(18, 30, 90, centered=(True, True, False))
    up = up.cut(cq.Workplane("XY", origin=(0, 0, 30)).box(6, 40, 40, centered=(True, True, False)))  # height slot
    up = up.union(cq.Workplane("XY", origin=(0, 0, 0)).box(40, 40, 6, centered=(True, True, False))
                  .faces(">Z").workplane().pushPoints([(14, 14), (-14, -14)]).hole(M4_CLR))
    arm = (cq.Workplane("XY", origin=(0, 0, 78)).box(90, 26, 8, centered=(True, True, False)).translate((45, 0, 0)))
    arm = arm.faces("<Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(30, 0)]).rect(52, 12).cutBlind(-5)  # magnet pocket
    return up.union(arm)

def sensor_bracket(hole=12.4, kind="inductive"):
    """Generic sensor bracket w/ standard mounting-boss pattern (interchangeable)."""
    base = cq.Workplane("XY").box(40, 34, WALL, centered=(True, True, False))
    base = base.faces(">Z").workplane().pushPoints([(-14, 11), (14, 11), (-14, -11), (14, -11)]).hole(M3_INSERT)
    if kind == "inductive":
        col = (cq.Workplane("XY", origin=(0, 0, 0)).box(24, 24, 30, centered=(True, True, False))
               .faces(">Z").hole(hole))
        base = base.union(col)
    else:  # capacitive clip for 23 mm wide board
        base = base.union(cq.Workplane("XY", origin=(0, 12, 0)).box(30, 4, 26, centered=(True, True, False)))
        base = base.union(cq.Workplane("XY", origin=(0, 6.5, 0)).box(30, 3, 26, centered=(True, True, False)))
    return base

# ============================================================================
#  STAGE 8 — ESP32-CAM ENCLOSURE + LED RING + CAMERA GANTRY
# ============================================================================
def esp32cam_enclosure():
    ox, oy, oz, wall = 52.0, 44.0, 24.0, 2.5
    box = cq.Workplane("XY").box(ox, oy, oz, centered=(True, True, False))
    box = box.faces(">Z").shell(-wall)
    # front lens hole + LED-ring recess
    box = box.cut(cq.Workplane("XY", origin=(0, -oy/2, oz/2)).transformed(rotate=(90, 0, 0)).circle(5).extrude(-wall*2))
    box = box.union(cq.Workplane("XY", origin=(0, -oy/2, oz/2)).transformed(rotate=(90, 0, 0)).circle(34).circle(30).extrude(3))
    # internal PCB standoffs for 40x27 board (2 posts)
    for px, py in [(17, 11), (-17, 11), (17, -11), (-17, -11)]:
        box = box.union(cq.Workplane("XY", origin=(px, py, wall)).circle(3).extrude(4).faces(">Z").hole(M3_INSERT-1.6))
    # rear cable slot
    box = box.cut(cq.Workplane("XY", origin=(0, oy/2, wall+3)).box(14, wall*2, 8, centered=(True, True, False)))
    return box

def esp32cam_lid():
    ox, oy, wall = 52.0, 44.0, 2.5
    lid = cq.Workplane("XY").box(ox, oy, wall, centered=(True, True, False))
    lip = cq.Workplane("XY", origin=(0, 0, wall)).rect(ox-2*2.5-0.4, oy-2*2.5-0.4).extrude(4)
    lip = lip.faces(">Z").rect(ox-2*2.5-0.4-4, oy-2*2.5-0.4-4).cutThruAll()
    return lid.union(lip)

def camera_gantry():
    """Overhead arch carrying the camera enclosure above the belt."""
    height = 150.0
    footL = cq.Workplane("XY", origin=(0, BELT_W/2+14, 0)).box(40, 24, 6, centered=(True, True, False)).faces(">Z").workplane().hole(M4_CLR)
    footR = cq.Workplane("XY", origin=(0, -(BELT_W/2+14), 0)).box(40, 24, 6, centered=(True, True, False)).faces(">Z").workplane().hole(M4_CLR)
    postL = cq.Workplane("XY", origin=(0, BELT_W/2+14, 0)).box(18, 18, height, centered=(True, True, False))
    postR = cq.Workplane("XY", origin=(0, -(BELT_W/2+14), 0)).box(18, 18, height, centered=(True, True, False))
    beam = cq.Workplane("XY", origin=(0, 0, height-9)).box(18, BELT_W+28+18, 18, centered=(True, True, False))
    mount = (cq.Workplane("XY", origin=(0, 0, height-30)).box(60, 50, 6, centered=(True, True, False))
             .faces(">Z").workplane().rect(40, 30, forConstruction=True).vertices().hole(M3_CLR))
    return footL.union(footR).union(postL).union(postR).union(beam).union(mount)

# ============================================================================
#  STAGE 9 — SORTING GATE (servo bracket + paddle)
# ============================================================================
def servo_bracket_sg90():
    """SG90 servo cradle at the belt end (23x12.2 body, 32 mm tab span)."""
    base = cq.Workplane("XY").box(50, 40, 4, centered=(True, True, False)).faces(">Z").workplane().pushPoints([(-20,14),(20,14),(-20,-14),(20,-14)]).hole(M3_CLR)
    wallL = cq.Workplane("XY", origin=(0, 8, 0)).box(50, 4, 34, centered=(True, True, False))
    pocket = cq.Workplane("XY", origin=(0, 8, 12)).box(24, 12.5, 30, centered=(True, True, False))
    tabs = (cq.Workplane("XY", origin=(0, 8, 30)).box(34, 12.5, 2.5, centered=(True, True, False)))
    b = base.union(wallL)
    b = b.cut(pocket)
    b = b.cut(cq.Workplane("XY", origin=(0, 8, 30)).pushPoints([(-16, 0), (16, 0)]).circle(1).extrude(6))
    return b

def sort_paddle():
    """Servo-driven diverter paddle (fires on encoder-tracked position)."""
    p = cq.Workplane("XY").box(95, 30, 3, centered=(False, True, False))
    p = p.faces(">Z").workplane(centerOption="CenterOfBoundBox")
    # hub at pivot end
    hub = cq.Workplane("XY", origin=(0, 0, 0)).circle(9).extrude(6)
    hub = hub.faces(">Z").hole(6.5)  # servo-horn boss clearance
    hub = hub.faces(">Z").workplane().polygon(4, 6).cutBlind(-4)  # spline seat (approx square)
    paddle = cq.Workplane("XY").box(95, 30, 3, centered=(False, True, False)).union(hub)
    # small screw hole to secure horn
    paddle = paddle.faces(">Z[-1]").workplane(centerOption="CenterOfBoundBox")
    return cq.Workplane("XY").box(95, 30, 3, centered=(False, True, False)).union(hub)

# ============================================================================
#  MULTI-WAY CHUTE + BINS
# ============================================================================
def sorting_chute():
    """Fan of dividers creating 4 lanes (METAL/PLASTIC/PAPER/REJECT) sloping to bins."""
    lx, ly, lz, wall = 160.0, 300.0, 70.0, 3.0
    floor = cq.Workplane("XY").transformed(rotate=(0, -18, 0)).box(lx, ly, wall, centered=(True, True, False))
    part = floor
    # 3 internal + 2 outer dividers => 4 lanes across ly
    for yy in [-ly/2, -ly/4, 0, ly/4, ly/2]:
        d = cq.Workplane("XY", origin=(0, yy, 0)).transformed(rotate=(0, -18, 0)).box(lx, wall, 45, centered=(True, True, False))
        part = part.union(d)
    return part

def bin_box(lx=88, ly=88, lz=95, label=True):
    b = cq.Workplane("XY").box(lx, ly, lz, centered=(True, True, False))
    b = b.faces(">Z").shell(-3)
    # rolled lip
    b = b.union(cq.Workplane("XY", origin=(0, 0, lz)).rect(lx+6, ly+6).extrude(4).faces(">Z").rect(lx-4, ly-4).cutThruAll())
    # finger recess (label area) on +Y face
    if label:
        b = b.cut(cq.Workplane("XY", origin=(0, ly/2, lz-22)).transformed(rotate=(90, 0, 0)).rect(lx-24, 16).extrude(1.2))
    return b

# ============================================================================
#  CONTROL ELECTRONICS ENCLOSURE (base + lid)  — 170x110x55 (manual 2.2)
# ============================================================================
def control_enclosure_base():
    ox, oy, oz, wall = 172.0, 112.0, 55.0, 3.0
    box = cq.Workplane("XY").box(ox, oy, oz, centered=(True, True, False))
    box = box.faces(">Z").shell(-wall)
    # standoff bosses: 3x L298N (43x43), buck, PCF8574 — generic grid of M3 posts
    posts = [(-55, 30), (-55, -30), (-12, 30), (-12, -30), (31, 30), (31, -30), (66, 25), (66, -25)]
    for px, py in posts:
        box = box.union(cq.Workplane("XY", origin=(px, py, wall)).circle(3.2).extrude(6).faces(">Z").hole(M3_INSERT-1.4))
    # cable entry glands on -X wall
    box = box.cut(cq.Workplane("XY", origin=(-ox/2, 0, wall+10)).transformed(rotate=(0, 90, 0)).pushPoints([(0,-25),(0,0),(0,25)]).circle(4).extrude(wall*2))
    # base mounting ears
    for px in (ox/2, -ox/2):
        box = box.union(cq.Workplane("XY", origin=(px, 0, 0)).box(12, oy, 6, centered=(True, True, False))
                        .faces(">Z").workplane().pushPoints([(0, oy/2-8), (0, -(oy/2-8))]).hole(M4_CLR))
    return box

def control_enclosure_lid():
    ox, oy, wall = 172.0, 112.0, 3.0
    lid = cq.Workplane("XY").box(ox, oy, wall, centered=(True, True, False))
    # OLED window 27x27 (SSD1306 0.96")
    lid = lid.cut(cq.Workplane("XY", origin=(-55, 0, 0)).rect(26, 15).extrude(wall*2))
    # 3 push buttons (12 mm)
    lid = lid.cut(cq.Workplane("XY", origin=(20, 30, 0)).pushPoints([(-16,0),(0,0),(16,0)]).circle(6).extrude(wall*2))
    # power switch (rocker) rectangular
    lid = lid.cut(cq.Workplane("XY", origin=(55, -30, 0)).rect(20, 13).extrude(wall*2))
    # status LEDs (2 x 5 mm)
    lid = lid.cut(cq.Workplane("XY", origin=(55, 30, 0)).pushPoints([(-8,0),(8,0)]).circle(2.6).extrude(wall*2))
    # locating lip
    lip = cq.Workplane("XY", origin=(0, 0, wall)).rect(ox-2*3-0.4, oy-2*3-0.4).extrude(4)
    lip = lip.faces(">Z").rect(ox-2*3-0.4-4, oy-2*3-0.4-4).cutThruAll()
    return lid.union(lip)

# ============================================================================
#  BUILD + PLACE EVERYTHING
# ============================================================================
def build():
    t0 = time.time()
    # datums
    DECK = 34.0            # top of base panel
    BELT_Z = 190.0         # roller centre height

    # ---- frame (centred on the machine footprint: X 0..L, Y -W/2..W/2) ----
    CX = L/2.0
    add("frame_base_panel", base_panel(), loc(CX, 0, DECK-6), "burlywood")
    for sx in (L-30, 30):
        for sy in (W/2-30, -(W/2-30)):
            add("foot", foot(), loc(sx, sy, 0), "black")
            side = 1 if sx < CX else -1
            fside = 1 if sy < 0 else -1
            add("corner_bracket", corner_bracket(), loc(sx + side*22, sy + fside*22, DECK,
                                                        rz=(0 if side > 0 else 180)), "dimgray")
            add("frame_post", post(H-DECK-20), loc(sx, sy, DECK), "silver")
    # top rails — purchased extrusion stand-ins
    for sy in (W/2-30, -(W/2-30)):
        add("frame_rail_x", cq.Workplane("XY").box(L-40, 20, 20, centered=(True, True, False)),
            loc(CX, sy, H-20), "silver")
    for sx in (L-30, 30):
        add("frame_rail_y", cq.Workplane("XY").box(20, W-40, 20, centered=(True, True, False)),
            loc(sx, 0, H-20), "silver")

    # ---- Stage 0 hopper ----
    add("hopper", hopper(), loc(200, -40, 300), "lightsteelblue")
    add("hazard_flap", hazard_flap(), loc(200, 30, 295, rx=20), "orange")

    # ---- Stage 0.5 coarse trommel (axis along X, slight incline) ----
    add("coarse_trommel_drum", trommel_drum(), loc(210, -40, 250, ry=90, rz=0), "lightgray")
    add("trommel_cradle_stand", cradle_stand(drum_od=180), loc(110, -40, 130), "dimgray")
    add("trommel_cradle_stand", cradle_stand(drum_od=180), loc(330, -40, 130, rz=180), "dimgray")

    # ---- wet path funnel + tramp metal ----
    add("wet_funnel", wet_funnel(), loc(210, -40, 150), "lightsteelblue")
    add("dry_chute", dry_chute(), loc(300, -40, 200, ry=-12), "khaki")

    # ---- Stage 1 shredder ----
    add("shredder_housing", shredder_housing(), loc(210, -40, 60), "slategray")
    add("shredder_roller", shredder_roller(), loc(210-23, -40-50, 115, rx=-90), "gray")
    add("shredder_roller", shredder_roller(), loc(210+23, -40-50, 115, rx=-90), "gray")

    # ---- Stage 2 auger press (left side, along X, inclined) ----
    add("auger_tube", auger_tube(), loc(95, -120, 120, ry=90), "gainsboro")
    add("auger_screw", auger_screw(), loc(10, -120, 120, ry=90), "gray")
    add("auger_tray", auger_tray(), loc(95, -120, 55), "lightblue")
    add("auger_probe_mount", probe_mount(), loc(180, -120, 120), "seagreen")

    # ---- Stage 3 fine trommel + Stage 4 air classifier ----
    add("fine_trommel_drum", fine_trommel(), loc(120, -60, 175, ry=90), "lightgray")
    add("air_classifier", air_classifier(), loc(120, 20, 40), "aliceblue")

    # ---- vibratory feeder (dry path -> belt start) ----
    add("vibratory_feeder", vibratory_feeder(), loc(320, 0, 250), "gold")

    # ---- conveyor ----
    cx = 460.0
    add("conveyor_side", conveyor_side(), loc(cx, BELT_W/2+8, DECK), "dimgray")
    add("conveyor_side", conveyor_side(), loc(cx, -(BELT_W/2+8), DECK), "dimgray")
    add("conveyor_roller", conveyor_roller(), loc(cx-BELT_SPAN/2, -BELT_W/2, BELT_Z, rx=-90), "darkgray")
    add("conveyor_roller", conveyor_roller(), loc(cx+BELT_SPAN/2, -BELT_W/2, BELT_Z, rx=-90), "darkgray")
    add("conveyor_belt", conveyor_belt(), loc(cx, -BELT_W/2, BELT_Z, rx=-90), "black")
    add("conveyor_motor_bracket", motor_bracket_tt(), loc(cx+BELT_SPAN/2, BELT_W/2+16, BELT_Z, rx=-90), "dimgray")
    add("encoder_disc", encoder_disc(), loc(cx+BELT_SPAN/2, -(BELT_W/2+12), BELT_Z, rx=90), "whitesmoke")
    add("encoder_bracket", encoder_bracket(), loc(cx+BELT_SPAN/2, -(BELT_W/2+12), BELT_Z-40), "dimgray")

    # ---- belt-line sensors ----
    add("magnet_mount", magnet_mount(), loc(cx-120, BELT_W/2+24, DECK), "dimgray")
    add("sensor_inductive_mount", sensor_bracket(kind="inductive"), loc(cx-60, BELT_W/2+24, BELT_Z+30), "steelblue")
    add("sensor_capacitive_mount", sensor_bracket(kind="capacitive"), loc(cx-10, BELT_W/2+24, BELT_Z+22), "seagreen")

    # ---- camera gantry + ESP32-CAM ----
    add("camera_gantry", camera_gantry(), loc(cx+30, 0, DECK), "dimgray")
    add("esp32cam_enclosure", esp32cam_enclosure(), loc(cx+30, 22, DECK+120, rx=90), "black")
    add("esp32cam_lid", esp32cam_lid(), loc(cx+30, -6, DECK+120, rx=90), "dimgray")

    # ---- Stage 9 sorting gate ----
    add("servo_bracket_sg90", servo_bracket_sg90(), loc(cx+BELT_SPAN/2+30, 0, BELT_Z-10), "steelblue")
    add("sort_paddle", sort_paddle(), loc(cx+BELT_SPAN/2+30, 0, BELT_Z+18), "orangered")

    # ---- multi-way chute + bins ----
    add("sorting_chute", sorting_chute(), loc(660, 0, 90), "lightgray")
    labels = ["METAL", "PLASTIC", "PAPER", "REJECT"]
    for i, yy in enumerate([-120, -40, 40, 120]):
        add("bin_%s" % labels[i], bin_box(), loc(740, yy, DECK), "gainsboro")
    # hazard bin near hopper, liquid Bin1 near auger tray
    add("bin_HAZARD", bin_box(70, 70, 80), loc(200, 120, DECK), "red")
    add("bin1_liquid", bin_box(90, 70, 60), loc(95, -120, DECK), "deepskyblue")

    # ---- control enclosure (elevated on standoffs, rear edge) ----
    add("control_enclosure_base", control_enclosure_base(), loc(680, 130, DECK+25), "gray")
    add("control_enclosure_lid", control_enclosure_lid(), loc(680, 130, DECK+25+55), "dimgray")

    print("built %d part instances in %.1fs" % (len(PARTS), time.time()-t0))

# ============================================================================
#  EXPORT
# ============================================================================
def export_all():
    build()
    # unique parts -> individual STEP
    seen = {}
    t = time.time()
    for name, shape, location, color in PARTS:
        if name in ("frame_post", "frame_rail_x", "frame_rail_y"):
            continue  # purchased extrusion, not printed
        if name in seen:
            continue
        seen[name] = True
        path = os.path.join(PARTS_DIR, name + ".step")
        try:
            cq.exporters.export(shape, path)
        except Exception as e:
            print("  !! part export failed:", name, repr(e)[:120])
    print("exported %d unique parts in %.1fs" % (len(seen), time.time()-t))

    # positioned assembly
    t = time.time()
    assy = cq.Assembly(name="EcoSynapse_MiniMRF")
    for i, (name, shape, location, color) in enumerate(PARTS):
        try:
            assy.add(shape, name="%s_%d" % (name, i), loc=location or cq.Location(),
                     color=col(color))
        except Exception as e:
            print("  !! assembly add failed:", name, repr(e)[:120])
    apath = os.path.join(OUT, "EcoSynapse_MiniMRF_Assembly.step")
    try:
        assy.export(apath)
    except Exception as e:
        print("assy.export failed, trying save:", repr(e)[:120])
        assy.save(apath)
    print("assembly saved: %s  (%.1fs)" % (apath, time.time()-t))

if __name__ == "__main__":
    export_all()
