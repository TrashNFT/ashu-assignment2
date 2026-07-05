# EcoSynapse AI Waste Sorter — Fusion Assembly (matches the labelled photo)

A clean **inline 7-stage** waste-segregation machine, modelled to match the annotated reference
image. Every part is a watertight **STEP solid** (Fusion opens these as editable bodies, not mesh),
the whole thing is **collision-checked** (no two parts share volume except intended bolt/bearing
contacts), and every support is **bolted to the base with modelled screws**.

```
Hopper → Coarse Grid (rotating drum) → One-Item Gate → Conveyor →
Metal Detection (inductive) → AI Camera (ESP32-CAM) → Sorting Gate (servo) → bins
```

- **Footprint:** ~820 (L) × 180 (W) base; ~250 mm tall at the gantries.
- **Units:** mm. **X** = length, **Y** = width (belt centre `Y=0`), **Z** = height (0 = table).
- **Format:** STEP (AP214). **Fasteners:** M4 (structure ↔ base), M3 (components).
- **Bearings:** 608ZZ (Ø22 bore) at the drum and both conveyor rollers. **Shafts:** 8 mm.

---

## Files

```
EcoSynapse_Assembly_Fusion/
├── EcoSynapse_AI_Waste_Sorter_Assembly.step   ← OPEN THIS in Fusion (full machine, all bodies + screws)
├── parts/                                      ← 25 individual printable parts (one STEP each)
├── previews/  iso.png · front.png · top.png
└── build_linear.py                             ← parametric source (edit + regenerate)
```

### Open in Fusion
1. **File ▸ Open** → `EcoSynapse_AI_Waste_Sorter_Assembly.step` → **OK** to convert.
   Every part lands as a located component; bodies are editable (push/pull, change holes, add fillets).
2. To print a part: open the matching `parts/<name>.step` → **Make ▸ 3D Print** (or Save As Mesh → STL).

---

## The 7 stages (and the parts in each)

| # | Stage (photo label) | Parts | Key features |
|---|---|---|---|
| 1 | **Hopper** – mixed waste input | `hopper` | Funnel on 4 legs, foot bolted to base (4× M4), side outlet feeds the drum |
| 2 | **Coarse Grid** – small waste falls through | `trommel_cage`, `trommel_drum`, `smallwaste_bin` | Slotted drum on **2× 608 bearings** in a bolted square cage; fines drop to the clear bin |
| 3 | **One-Item Gate** – servo door | `gate_arch`, `gate_servo`, `gate_door` | Arch over the belt infeed; SG90 on a shelf drives a door that releases one item at a time |
| 4 | **Conveyor Belt** | `conveyor_side` ×2, `conveyor_roller` ×2, `conveyor_belt`, `conveyor_motor` | Two side frames (**608 bores**), TT gear-motor drive on the left roller |
| 5 | **Metal Detection** – inductive sensor | `gantry_metal`, `inductive_sensor` | Arch with a downward clamp holding an M12 inductive sensor over the belt |
| 6 | **AI Camera** – ESP32-CAM | `gantry_camera`, `esp32cam` | Arch with a down-facing plate; 4× M3 hold the ESP32-CAM looking at the belt |
| 7 | **Sorting Gate** – servo | `sort_stand`, `sort_servo`, `sort_paddle`, `diverter_fin` ×3 | Side post + SG90 sweeping a paddle; 3 angled fins route items into the bins |
| — | **Bins** | `metal_bin`, `plastic_bin`, `paper_bin`, `others_bin` | Clear + blue/green/red, sit on the table in front of the discharge |
| — | **Controller** | `control_box`, `control_lid` | ESP32 box with OLED window, switch, LED & cable-gland cutouts; bolted to the base |
| — | **Frame** | `base_plate` | Base drilled with every mount hole; 4× rubber feet; corner posts (extrusion, buy-not-print) |

---

## How the parts fasten (rigid, non-intersecting)

- **Every support → base:** each foot has M4 clearance holes; the **base plate is drilled at the exact
  matching world positions**, and an **M4 socket-head screw is modelled at every hole** (the brass
  bodies in the assembly). So the hopper, cage, both conveyor sides, all four arches/stands, the fins,
  and the control box all bolt down — nothing floats.
- **Components → supports (M3):** inductive-sensor clamp, ESP32-CAM plate (4×), and the servo cradles
  carry M3 holes; M3 screws are modelled at those points too.
- **Rotary joints:** the drum and both rollers ride on **608ZZ bearings** pressed into the cage /
  side-frame bores (Ø22.12 = nominal + 0.12 press-fit). 8 mm shafts, grub-screw flats where driven.
- **Collision check:** `build_linear.py` runs a pairwise solid-intersection test after placing every
  part. The build is clean except for these **intended contact interfaces**, which are *supposed* to
  touch and are not modelling errors:
  - `trommel_cage ↔ trommel_drum` — drum shaft seated in its bearing bore.
  - `diverter_fin ↔ base_plate` — fin feet resting flat on the deck (bolted face contact).
  - `sort_stand ↔ sort_servo` — servo seated in its mounting cradle.

  No part passes *through* another (no hopper-through-cage, no bins-through-frame, no motor-in-roller).

---

## Print / tolerance notes

- Bearing bores: Ø22.12 (nominal + 0.12) light press fit for 608ZZ.
- Screw holes: M3 = Ø3.4, M4 = Ø4.5 clearance (open bosses to Ø4.0 if using M3 heat-set inserts).
- Materials: PLA for structure/chutes; PETG for the drum and any wear surfaces.
- Sensor mount faces held flat so the inductive/capacitive standoff stays in spec.

---

## Regenerate / resize

`build_linear.py` is fully parametric. Change a value at the top (`BELT_W`, `DRUM_D`, envelope, etc.)
or any part function and re-run:

```bash
python3 -m venv env && ./env/bin/pip install cadquery
./env/bin/python build_linear.py     # rewrites parts/*.step + the assembly, and prints the collision report
```
