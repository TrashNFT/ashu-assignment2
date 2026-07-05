#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EcoSynapse AI Waste Sorter — inline 7-stage assembly (matches the labelled photo).
Hopper -> Coarse Grid (rotating drum) -> One-Item Gate -> Conveyor ->
Metal Detection (inductive) -> AI Camera (ESP32-CAM) -> Sorting Gate (servo) -> bins.
Supports bolt to the base (M4); components fasten with M3 screws (modelled).
Layout is collision-checked: no two parts share volume (> a small face-contact sliver).
Units mm.  X = length, Y = width (belt centre Y=0), Z = height (0 = table).
"""
import os, math, time
import cadquery as cq

OUT = "/Users/kushu/ashu assign2/EcoSynapse_Assembly_Fusion"
PARTS_DIR = os.path.join(OUT, "parts")
os.makedirs(PARTS_DIR, exist_ok=True)

# ---------------- global params ----------------
WALL   = 3.0
M3_CLR = 3.4
M4_CLR = 4.5
BRG_OD = 22.12
BRG_W  = 7.0
SHAFT  = 8.0
SHAFT_CLR = 8.4

BASE_X0, BASE_L, BASE_W, BASE_T = -30.0, 820.0, 180.0, 12.0
DECK = BASE_T
FT   = 5.0

DRUM_D, DRUM_LEN, DRUM_CZ = 120.0, 165.0, 120.0
CAGE = 200.0
BELT_TOP, ROLL_D, BELT_W = 118.0, 44.0, 90.0
ROLL_CZ = BELT_TOP - ROLL_D/2
BELT_X0, BELT_X1 = 400.0, 580.0
BELT_SPAN = BELT_X1 - BELT_X0
GANTRY_TOP = 250.0
POSTY = BELT_W/2 + 43        # 88 : arch posts clear the conveyor side frames

COLORS = {
    "black": (0.13,0.13,0.13), "steel": (0.72,0.74,0.77), "dark": (0.28,0.30,0.33),
    "gray": (0.6,0.6,0.6), "belt": (0.10,0.10,0.11), "clear": (0.80,0.86,0.90),
    "blue": (0.13,0.34,0.72), "green": (0.14,0.5,0.24), "red": (0.75,0.16,0.16),
    "servo": (0.15,0.35,0.75), "pcb": (0.10,0.34,0.20), "gold": (0.85,0.7,0.2),
    "brass": (0.80,0.62,0.26), "white": (0.93,0.93,0.93), "orange":(0.9,0.55,0.1),
}
def col(n):
    r,g,b = COLORS.get(n,(0.6,0.6,0.6)); return cq.Color(r,g,b,1.0)

def loc(x=0,y=0,z=0,rx=0,ry=0,rz=0):
    T=cq.Location(cq.Vector(x,y,z))
    Rx=cq.Location(cq.Vector(),cq.Vector(1,0,0),rx)
    Ry=cq.Location(cq.Vector(),cq.Vector(0,1,0),ry)
    Rz=cq.Location(cq.Vector(),cq.Vector(0,0,1),rz)
    return T*Rz*Ry*Rx

PARTS = []
BASE_HOLES = []
SCREWS = []

def add(name, shape, location=None, color="gray"):
    PARTS.append((name, shape, location, color)); return shape

def mount(name, part, x, y, foot_pts, color, z=DECK, screw="M4"):
    add(name, part, loc(x, y, z), color)
    for (fx, fy) in foot_pts:
        BASE_HOLES.append((x+fx, y+fy))
        SCREWS.append((x+fx, y+fy, z+FT, screw))

def comp_screw(wx, wy, z_top, size="M3"):
    SCREWS.append((wx, wy, z_top, size))

# ---------------- fasteners ----------------
def screw(size="M4", length=16.0):
    hr, hh, sr = (3.6,3.6,1.95) if size=="M4" else (2.75,3.0,1.55)
    head = cq.Workplane("XY").circle(hr).extrude(hh).edges(">Z").chamfer(0.6)
    shank = cq.Workplane("XY").circle(sr).extrude(-length)
    return head.union(shank)

def foot_plate(w, d, t=FT, inset=9, hole=M4_CLR):
    p = cq.Workplane("XY").box(w, d, t, centered=(True, True, False))
    pts = [(w/2-inset, d/2-inset), (-(w/2-inset), d/2-inset),
           (w/2-inset, -(d/2-inset)), (-(w/2-inset), -(d/2-inset))]
    p = p.faces(">Z").workplane().pushPoints(pts).hole(hole)
    return p, pts

# ============================================================
#  BASE
# ============================================================
def base_plate():
    b = cq.Workplane("XY").box(BASE_L, BASE_W, BASE_T, centered=(True, True, False)).translate((BASE_X0 + BASE_L/2, 0, 0))
    uniq = {(round(x,2), round(y,2)) for (x, y) in BASE_HOLES}
    if uniq:
        b = b.faces(">Z").workplane(centerOption="ProjectedOrigin", origin=(0,0,BASE_T)) \
             .pushPoints(list(uniq)).hole(M4_CLR)
    return b

# ============================================================
#  STAGE 1 — HOPPER (foot on deck, outlet at drum-axis height)
# ============================================================
def hopper():
    topx, topy, botx, boty = 120.0, 130.0, 62.0, 62.0
    fh, leg = 100.0, 96.0
    outer = (cq.Workplane("XY", origin=(0,0,leg)).rect(botx,boty)
             .workplane(offset=fh).rect(topx,topy).loft(combine=True))
    inner = (cq.Workplane("XY", origin=(0,0,leg-1)).rect(botx-2*WALL,boty-2*WALL)
             .workplane(offset=fh+2).rect(topx-2*WALL,topy-2*WALL).loft(combine=True))
    f = outer.cut(inner)
    f = f.union(cq.Workplane("XY", origin=(0,0,leg+fh)).rect(topx+6,topy+6).extrude(4)
                .faces(">Z").rect(topx-2,topy-2).cutThruAll())
    # outlet on +X side near funnel bottom (feeds the drum end)
    f = f.cut(cq.Workplane("XY", origin=(botx/2,0,leg+9)).transformed(rotate=(0,90,0)).rect(46, boty-2*WALL).extrude(12))
    fp, pts = foot_plate(topx+16, topy+16)
    legs = None
    for (lx, ly) in pts:
        l = cq.Workplane("XY", origin=(lx,ly,0)).box(12,12,leg, centered=(True,True,False))
        legs = l if legs is None else legs.union(l)
    return fp.union(legs).union(f), pts

# ============================================================
#  STAGE 2 — COARSE GRID drum + square cage
# ============================================================
def trommel_drum():
    r = DRUM_D/2
    drum = cq.Workplane("XY").circle(r).circle(r-WALL).extrude(DRUM_LEN)
    for z, d in ((0,1), (DRUM_LEN,-1)):
        drum = drum.union(cq.Workplane("XY", origin=(0,0,z)).circle(r).circle(r-WALL).extrude(6*d))
        drum = drum.union(cq.Workplane("XY", origin=(0,0,z)).circle(13).extrude(10*d))
        for a in (0,120,240):
            drum = drum.union(cq.Workplane("XY", origin=(0,0, z if d>0 else z-5)).transformed(rotate=(0,0,a))
                              .box(2*r-2*WALL, 8, 5, centered=(True, True, False)))
    drum = drum.union(cq.Workplane("XY", origin=(0,0,DRUM_LEN)).circle(SHAFT/2).extrude(22))
    drum = drum.union(cq.Workplane("XY", origin=(0,0,0)).circle(SHAFT/2).extrude(-22))
    cutters = None
    rings, per = 5, 10
    slot_l = (DRUM_LEN-40)/rings - 8
    for ri in range(rings):
        zc = 20 + ri*((DRUM_LEN-40)/rings) + slot_l/2
        for k in range(per):
            a = k*(360/per) + (18 if ri%2 else 0)
            s = (cq.Workplane("XY").transformed(rotate=(0,0,a))
                 .transformed(offset=cq.Vector(0,0,zc)).box(DRUM_D+4, 12, slot_l, centered=True))
            cutters = s if cutters is None else cutters.union(s)
    return drum.cut(cutters)

def trommel_cage():
    half = CAGE/2
    bar = 12.0
    length = DRUM_LEN + 2*BRG_W + 26
    axz = DRUM_CZ - DECK - FT           # drum axis height in cage-local frame (foot at 0)
    def endframe(sign):
        x = sign*length/2
        d = -bar*sign                     # extrude INWARD (toward drum) so cage length == `length`
        outer = cq.Workplane("YZ", origin=(x,0,0)).rect(CAGE, CAGE).extrude(d)
        inner = cq.Workplane("YZ", origin=(x,0,0)).rect(CAGE-2*bar, CAGE-2*bar).extrude(d - sign)
        fr = outer.cut(inner)
        cross = cq.Workplane("YZ", origin=(x,0, axz-half)).rect(CAGE-2*bar, 22).extrude(d)
        hub = cq.Workplane("YZ", origin=(x,0, axz-half)).circle(18).extrude(d - 6*sign)
        pocket = cq.Workplane("YZ", origin=(x,0, axz-half)).circle(BRG_OD/2).extrude(d)
        thru = cq.Workplane("YZ", origin=(x,0, axz-half)).circle(SHAFT_CLR/2).extrude(d - 8*sign)
        return fr.union(cross).union(hub).cut(pocket).cut(thru)
    cage = endframe(1).union(endframe(-1))
    for (cy, cz) in [(half-bar/2, half-bar/2), (-(half-bar/2), half-bar/2),
                     (half-bar/2, -(half-bar/2)), (-(half-bar/2), -(half-bar/2))]:
        cage = cage.union(cq.Workplane("XY", origin=(0, cy, cz)).box(length, bar, bar, centered=True))
    cage = cage.translate((0, 0, half))          # bottom on deck
    feet, pts = None, []
    for sx in (length/2-14, -(length/2-14)):
        for sy in (half-8, -(half-8)):
            f = (cq.Workplane("XY", origin=(sx, sy, 0)).box(24, 22, FT, centered=(True, True, False))
                 .faces(">Z").workplane().hole(M4_CLR))
            feet = f if feet is None else feet.union(f); pts.append((sx, sy))
    return cage.union(feet), pts

# ============================================================
#  ARCH (shared) — 2 posts on feet + top beam, carries a tool
# ============================================================
def arch(top_z, tool):
    postH = top_z - DECK
    part, pts = None, []
    for sy in (POSTY, -POSTY):
        foot = (cq.Workplane("XY", origin=(0,sy,0)).box(34,30,FT, centered=(True,True,False))
                .faces(">Z").workplane().pushPoints([(11,0),(-11,0)]).hole(M4_CLR))
        post = cq.Workplane("XY", origin=(0,sy,0)).box(16,16,postH, centered=(True,True,False))
        seg = foot.union(post)
        part = seg if part is None else part.union(seg)
    pts = [(11,POSTY),(-11,POSTY),(11,-POSTY),(-11,-POSTY)]
    beam = cq.Workplane("XY", origin=(0,0,postH-8)).box(16, 2*POSTY+16, 16, centered=(True,True,False))
    part = part.union(beam)
    top = DECK + postH
    if tool == "inductive":
        stalk = cq.Workplane("XY", origin=(0,0,top-16)).box(18,18,top-(BELT_TOP+40), centered=(True,True,False)).translate((0,0,-(top-(BELT_TOP+40))))
        clampz = BELT_TOP + 40
        clamp = (cq.Workplane("XY", origin=(0,0,clampz)).box(30,30,14, centered=(True,True,False)).faces(">Z").hole(13.2))
        part = part.union(stalk).union(clamp)
    elif tool == "camera":
        platez = BELT_TOP + 60
        stalk = cq.Workplane("XY", origin=(0,0,top-8)).box(18,18,top-8-platez, centered=(True,True,False)).translate((0,0,-(top-8-platez)))
        plate = (cq.Workplane("XY", origin=(0,0,platez)).box(52,44,5, centered=(True,True,False))
                 .faces(">Z").workplane().rect(40,30, forConstruction=True).vertices().hole(M3_CLR))
        part = part.union(stalk).union(plate)
    elif tool in ("gate", "sort"):
        shelfz = top - 16
        shelf = (cq.Workplane("XY", origin=(0,0,shelfz)).box(40,34,5, centered=(True,True,False))
                 .faces(">Z").workplane().pushPoints([(15,0),(-15,0)]).hole(M3_CLR))
        shelf = shelf.faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(7)   # servo-horn shaft clearance
        part = part.union(shelf)
    return part, pts

# tool bodies (hang in open space, fastened by screws — no solid overlap)
def inductive_sensor():
    # short M12 barrel that hangs just under the clamp (no insertion -> no overlap)
    b = cq.Workplane("XY").circle(5.75).extrude(-28)
    return b.union(cq.Workplane("XY", origin=(0,0,-28)).circle(6.0).extrude(-3))

def esp32cam():
    board = cq.Workplane("XY").box(40,27,4, centered=(True,True,False))
    cam = cq.Workplane("XY", origin=(6,0,4)).box(8,8,6, centered=(True,True,False)).faces(">Z").circle(3.2).extrude(2)
    con = cq.Workplane("XY", origin=(-16,0,4)).box(6,16,3, centered=(True,True,False))
    return board.union(cam).union(con)

def sg90():
    body = cq.Workplane("XY").box(23,12.2,22, centered=(True,True,False))
    tabs = cq.Workplane("XY", origin=(0,0,22)).box(32,12.2,2.5, centered=(True,True,False)) \
           .faces(">Z").workplane().pushPoints([(13.5,0),(-13.5,0)]).hole(2)
    boss = cq.Workplane("XY", origin=(0,0,24.5)).circle(5.8).extrude(2)
    horn = cq.Workplane("XY", origin=(0,0,26.5)).circle(2.4).extrude(4)
    return body.union(tabs).union(boss).union(horn)

def gate_door():
    # thin across-belt door plate; hangs below the gate servo (built z 0..40)
    return cq.Workplane("XY").box(3, 80, 40, centered=(True, True, False))

def sort_stand():
    """Side post beside the belt discharge; cradle offset toward the belt holds the servo."""
    foot, pts = foot_plate(40, 30)
    post = cq.Workplane("XY").box(16, 16, 118, centered=(True, True, False))
    cradle = cq.Workplane("XY", origin=(0,-14,96)).box(30, 19, 24, centered=(True, True, False))
    cradle = cradle.cut(cq.Workplane("XY", origin=(0,-14,99)).box(26, 15, 28, centered=(True, True, False)))
    cradle = cradle.faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(15,-14),(-15,-14)]).hole(2)
    return foot.union(post).union(cradle), pts

def sort_paddle():
    """Horizontal sorting paddle that sweeps just above the belt surface."""
    arm = cq.Workplane("XY").box(18, 92, 4, centered=(True, False, False)).translate((0, -92, 0))
    hub = cq.Workplane("XY").circle(8).extrude(5).faces(">Z").hole(6.2)
    return arm.union(hub)

# ============================================================
#  CONVEYOR
# ============================================================
def conv_side():
    length = BELT_SPAN + 50
    h = ROLL_CZ - DECK + ROLL_D/2 + 8
    plate = cq.Workplane("XY").box(length, 6, h, centered=(True, True, False))
    zc = ROLL_CZ - DECK
    for xb in (BELT_SPAN/2, -BELT_SPAN/2):
        plate = plate.cut(cq.Workplane("XY", origin=(xb,0,zc)).transformed(rotate=(90,0,0)).circle(BRG_OD/2).extrude(4))
        plate = plate.cut(cq.Workplane("XY", origin=(xb,0,zc)).transformed(rotate=(90,0,0)).circle(SHAFT_CLR/2).extrude(-8))
    feet, pts = None, []
    for xb in (length/2-16, -(length/2-16)):
        f = (cq.Workplane("XY", origin=(xb,0,0)).box(30, 22, FT, centered=(True, True, False))
             .faces(">Z").workplane().pushPoints([(0,6),(0,-6)]).hole(M4_CLR))
        feet = f if feet is None else feet.union(f); pts += [(xb,6),(xb,-6)]
    return plate.union(feet), pts

def conv_roller():
    r = cq.Workplane("XY").circle(ROLL_D/2).extrude(BELT_W)
    r = r.faces(">Z").circle(SHAFT/2).extrude(18).faces("<Z").circle(SHAFT/2).extrude(18)
    return r.cut(cq.Workplane("XY", origin=(SHAFT/2-1,0,BELT_W+10)).box(2,6,10, centered=True))

def conv_belt():
    r = ROLL_D/2 + 1.5
    def rr(rad):
        return (cq.Workplane("XY").moveTo(-BELT_SPAN/2, rad).lineTo(BELT_SPAN/2, rad)
                .threePointArc((BELT_SPAN/2+rad,0),(BELT_SPAN/2,-rad)).lineTo(-BELT_SPAN/2,-rad)
                .threePointArc((-BELT_SPAN/2-rad,0),(-BELT_SPAN/2,rad)).close())
    return rr(r).extrude(BELT_W).cut(rr(r-1.5).extrude(BELT_W))

def tt_motor():
    body = cq.Workplane("XY").box(37,22,19, centered=(True,True,False))
    body = body.union(cq.Workplane("XY", origin=(0,0,9.5)).transformed(rotate=(0,90,0)).circle(4.5).extrude(22))
    return body

# ============================================================
#  SORTING FINS + BINS + CONTROL BOX
# ============================================================
def diverter_fin():
    fin = cq.Workplane("XY").transformed(rotate=(-25,0,0)).box(52,4,95, centered=(True,True,False))
    foot = (cq.Workplane("XY").box(34,26,FT, centered=(True,True,False))
            .faces(">Z").workplane().pushPoints([(11,0),(-11,0)]).hole(M4_CLR))
    return fin.union(foot), [(11,0),(-11,0)]

def bin_box(lx=56, ly=100, lz=118, label=True):
    b = cq.Workplane("XY").box(lx, ly, lz, centered=(True, True, False))
    b = b.faces(">Z").shell(-2.5)
    b = b.union(cq.Workplane("XY", origin=(0,0,lz)).rect(lx+6, ly+6).extrude(4).faces(">Z").rect(lx-4, ly-4).cutThruAll())
    if label:
        b = b.cut(cq.Workplane("XY", origin=(0,ly/2,lz-30)).transformed(rotate=(90,0,0)).rect(lx-16, 20).extrude(1.2))
    return b

def control_box():
    ox, oy, oz = 100.0, 70.0, 80.0
    box = cq.Workplane("XY").box(ox, oy, oz, centered=(True, True, False)).faces(">Z").shell(-3)
    box = box.cut(cq.Workplane("XY", origin=(ox/2,0,oz-24)).transformed(rotate=(0,90,0)).rect(15,26).extrude(6))
    box = box.cut(cq.Workplane("XY", origin=(ox/2,0,oz-50)).transformed(rotate=(0,90,0)).rect(13,20).extrude(6))
    box = box.cut(cq.Workplane("XY", origin=(ox/2,26,oz-24)).transformed(rotate=(0,90,0)).circle(2.6).extrude(6))
    box = box.cut(cq.Workplane("XY", origin=(-ox/2,0,20)).transformed(rotate=(0,90,0)).pushPoints([(0,-20),(0,20)]).circle(4).extrude(6))
    feet, pts = None, []
    for sx in (ox/2-8, -(ox/2-8)):
        f = (cq.Workplane("XY", origin=(sx,0,0)).box(12, oy, FT, centered=(True, True, False))
             .faces(">Z").workplane().pushPoints([(0,oy/2-8),(0,-(oy/2-8))]).hole(M4_CLR))
        feet = f if feet is None else feet.union(f); pts += [(sx,oy/2-8),(sx,-(oy/2-8))]
    return box.union(feet), pts

def control_lid():
    ox, oy = 100.0, 70.0
    lid = cq.Workplane("XY").box(ox, oy, 3, centered=(True, True, False))
    lip = cq.Workplane("XY", origin=(0,0,3)).rect(ox-6.4, oy-6.4).extrude(4).faces(">Z").rect(ox-10.4, oy-10.4).cutThruAll()
    return lid.union(lip)

# ============================================================
#  BUILD & PLACE
# ============================================================
def build():
    t0 = time.time()

    SHELF = BELT_TOP + 72 - 16          # gate/sort servo shelf height (=174)
    SERVO_Z = SHELF - 2 - 22            # servo body base so horn reaches the shelf (=150)

    # 1 hopper
    hop, hpts = hopper()
    mount("hopper", hop, 54, 0, hpts, "black")

    # 2 coarse grid
    cage, cpts = trommel_cage()
    CX = 240.0
    mount("trommel_cage", cage, CX, 0, cpts, "steel")
    add("trommel_drum", trommel_drum(), loc(CX-DRUM_LEN/2, 0, DRUM_CZ, ry=90), "dark")
    add("smallwaste_bin", bin_box(90,70,70, label=False), loc(CX, -155, 0), "clear")

    # 3 one-item gate (arch) at the belt infeed
    ga, gpts = arch(BELT_TOP+72, "gate")
    GX = 362.0
    mount("gate_arch", ga, GX, 0, gpts, "steel")
    add("gate_servo", sg90(), loc(GX, 0, SERVO_Z), "servo")
    add("gate_door", gate_door(), loc(GX, 0, 104), "gray")            # hangs below servo (104..144)
    comp_screw(GX+15, 0, SHELF+5, "M3"); comp_screw(GX-15, 0, SHELF+5, "M3")

    # 4 conveyor
    cs, spts = conv_side()
    CXc = (BELT_X0+BELT_X1)/2
    mount("conveyor_side", cs, CXc,  (BELT_W/2+8), spts, "steel")
    mount("conveyor_side", cs, CXc, -(BELT_W/2+8), spts, "steel")
    add("conveyor_roller", conv_roller(), loc(BELT_X0, -BELT_W/2, ROLL_CZ, rx=-90), "steel")
    add("conveyor_roller", conv_roller(), loc(BELT_X1, -BELT_W/2, ROLL_CZ, rx=-90), "steel")
    add("conveyor_belt", conv_belt(), loc(CXc, -BELT_W/2, ROLL_CZ, rx=-90), "belt")
    add("conveyor_motor", tt_motor(), loc(BELT_X0, 78, ROLL_CZ), "dark")   # left-roller drive, outboard

    # 5 metal detection
    gm, gmpts = arch(GANTRY_TOP, "inductive")
    MX = 450.0
    mount("gantry_metal", gm, MX, 0, gmpts, "steel")
    add("inductive_sensor", inductive_sensor(), loc(MX, 0, BELT_TOP+35), "gold")   # tip hangs under clamp

    # 6 AI camera
    gc, gcpts = arch(GANTRY_TOP, "camera")
    KX = 525.0
    mount("gantry_camera", gc, KX, 0, gcpts, "steel")
    add("esp32cam", esp32cam(), loc(KX, 0, BELT_TOP+60-4-2, rx=180), "pcb")
    for (dx,dy) in [(20,15),(-20,15),(20,-15),(-20,-15)]:
        comp_screw(KX+dx, dy, BELT_TOP+60+5, "M3")

    # 7 sorting gate (side servo + paddle) + fins + bins
    ss, sspts = sort_stand()
    SX = 575.0
    mount("sort_stand", ss, SX, 82, sspts, "steel")
    add("sort_servo", sg90(), loc(SX, 68, DECK+90), "servo")             # in the offset cradle, shaft up
    add("sort_paddle", sort_paddle(), loc(SX, 64, BELT_TOP+16), "orange") # sweeps above the belt
    fin, fpts = diverter_fin()
    for fx in (635, 700, 765):
        mount("diverter_fin", fin, fx, -30, fpts, "black")
    add("metal_bin",   bin_box(), loc(500, -160, 0), "clear")
    add("plastic_bin", bin_box(), loc(635, -160, 0), "blue")
    add("paper_bin",   bin_box(), loc(700, -160, 0), "green")
    add("others_bin",  bin_box(), loc(765, -160, 0), "red")

    # control box
    cb, cbpts = control_box()
    mount("control_box", cb, 700, 50, cbpts, "black")
    add("control_lid", control_lid(), loc(700, 50, DECK+80), "dark")

    # base + screws
    add("base_plate", base_plate(), loc(0,0,0), "black")
    for (wx, wy, ztop, size) in SCREWS:
        add("screw_%s" % size, screw(size, 18 if size=="M4" else 12), loc(wx, wy, ztop), "brass")

    print("built %d part instances, %d screws in %.1fs" % (len(PARTS), len(SCREWS), time.time()-t0))

# ============================================================
#  INTERSECTION CHECK
# ============================================================
def placed_solid(shape, location):
    obj = shape.val() if isinstance(shape, cq.Workplane) else shape
    try:    return obj.located(location) if location else obj
    except Exception: return obj

def bbox_overlap(a, b, tol=-0.2):
    return not (a.xmax < b.xmin-tol or b.xmax < a.xmin-tol or
                a.ymax < b.ymin-tol or b.ymax < a.ymin-tol or
                a.zmax < b.zmin-tol or b.zmax < a.zmin-tol)

def check_intersections(thresh=25.0):
    solids = []
    for (name, shape, location, color) in PARTS:
        if name.startswith("screw"): continue
        s = placed_solid(shape, location)
        try: solids.append((name, s, s.BoundingBox()))
        except Exception: pass
    flags = []
    for i in range(len(solids)):
        for j in range(i+1, len(solids)):
            ni, si, bi = solids[i]; nj, sj, bj = solids[j]
            if not bbox_overlap(bi, bj): continue
            try:
                inter = si.intersect(sj); v = inter.Volume() if inter is not None else 0.0
            except Exception: v = 0.0
            if v > thresh: flags.append((round(v,1), ni, nj))
    flags.sort(reverse=True)
    if not flags:
        print("INTERSECTION CHECK: CLEAN (no overlaps > %.0f mm^3)" % thresh)
    else:
        print("INTERSECTION CHECK: %d overlapping pairs" % len(flags))
        for v,a,b in flags[:50]: print("   %8.1f  %s <-> %s" % (v,a,b))
    return flags

# ============================================================
#  EXPORT
# ============================================================
def export_all():
    seen = {}
    for (name, shape, location, color) in PARTS:
        if name.startswith("screw") or name == "conveyor_belt": continue
        if name in seen: continue
        seen[name] = True
        try: cq.exporters.export(shape, os.path.join(PARTS_DIR, name + ".step"))
        except Exception as e: print("  part fail", name, repr(e)[:90])
    print("exported %d unique parts" % len(seen))
    assy = cq.Assembly(name="EcoSynapse_AI_Waste_Sorter")
    for i, (name, shape, location, color) in enumerate(PARTS):
        try: assy.add(shape, name="%s_%d" % (name, i), loc=location or cq.Location(), color=col(color))
        except Exception as e: print("  assy fail", name, repr(e)[:80])
    apath = os.path.join(OUT, "EcoSynapse_AI_Waste_Sorter_Assembly.step")
    try: assy.export(apath)
    except Exception: assy.save(apath)
    print("assembly:", apath)

if __name__ == "__main__":
    build()
    check_intersections()
    export_all()
