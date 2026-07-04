# EcoSynapse MiniMRF — CAD Package (for Autodesk Fusion)

Parametric 3D CAD for the **EcoSynapse Miniature MRF** waste-segregation prototype
(Rev 3.1 manual + build photos). Every printed part is a clean **solid B-rep** exported
as **STEP (.step / AP214)** — Fusion imports these as fully editable bodies, *not* dumb mesh.

- **Overall envelope:** 800 (L) × 380 (W) × 520 (H) mm — two-tier bench unit.
- **Units:** millimetres. **Origin:** X = length (0→800), Y = width (−190→+190), Z = height (0 = floor).
- **Format:** STEP. All solids are watertight and manifold (3D-print ready).

---

## 1. What's in this folder

```
EcoSynapse_CAD/
├── EcoSynapse_MiniMRF_Assembly.step   ← THE FULL MACHINE (open this first in Fusion)
├── parts/                             ← 41 individual printable parts (one STEP each)
├── previews/                          ← rendered iso / front / top views
├── build_ecosynapse.py                ← the parametric source (edit + regenerate, see §6)
└── README.md
```

- **`EcoSynapse_MiniMRF_Assembly.step`** — all parts pre-positioned in space as the complete
  machine (a multi-body / multi-component STEP). Use this to see how everything fits and to
  take reference dimensions.
- **`parts/*.step`** — each part on its own, in a sensible print orientation. Send these to
  the slicer (Fusion → *Utilities → Make / 3D Print*, or export STL).

---

## 2. How to open in Autodesk Fusion

**The whole machine**
1. Fusion → **File ▸ Open** (or *Upload* to a project) → pick `EcoSynapse_MiniMRF_Assembly.step`.
2. Fusion asks to convert the STEP → click **OK**. It lands as one component tree with every
   part as a child component, correctly located.
3. Right-click any body → **Edit** — because it's B-rep, you can push/pull faces, change hole
   sizes, add fillets, etc. (A STEP has no timeline history, so edits are direct-modelling —
   that's normal and fully editable.)

**A single part to print**
- **File ▸ Open** the individual `parts/<name>.step`, then **Make ▸ 3D Print** or right-click the
  body → **Save As Mesh (STL)**.

> Tip: if you'd rather have a *parametric timeline* model, regenerate from the Python source in
> §6 and re-import, or rebuild the feature you care about natively — the STEP already gives you
> exact geometry to trace over.

---

## 3. Parts list (41 printed parts) & the joints designed in

All fasteners are **M3 / M4**. Bearing bores are for **608ZZ (22 mm OD × 8 mm bore × 7 mm)**.
Shafts are **8 mm**. "Insert boss" = pilot hole sized for an M3 **heat-set threaded insert**.

### Frame / chassis
| Part | Joints & features |
|---|---|
| `frame_base_panel` | 6 mm plywood/acrylic deck; 4× M4 clearance holes for corner brackets |
| `corner_bracket` (×4) | L-bracket; 2× M4 into deck + 2× M4 into corner post |
| `foot` (×4) | Ø44 base, M4 top hole (levelling / rubber pad) |
| *(frame posts & top rails are 20×20 aluminium extrusion — buy, not print; shown as stand-ins)* |

### Stage 0 — Hopper + hazard reject
| Part | Joints & features |
|---|---|
| `hopper` | 170→62 mm square funnel; bottom **collar with 4× M3 inserts** to bolt to trommel/chute; anti-bridging rib inside; SG90 pocket + flap slot |
| `hazard_flap` | Diverter flap with hinge knuckles + servo-horn link hole |

### Stage 0.5 — Coarse split trommel
| Part | Joints & features |
|---|---|
| `coarse_trommel_drum` | Ø180 × 220, ~50 mm slots; spoked end caps with **Ø8.3 shaft hubs** + grub-screw boss |
| `trommel_cradle_stand` (×2) | Upright with **608 bearing pocket (Ø22.12)** + M4 feet |

### Wet path
| Part | Joints & features |
|---|---|
| `wet_funnel` | Funnel to shredder throat; **M12 boss (Ø12.4)** for tramp-metal inductive sensor; M3-insert collar |
| `dry_chute` | U-trough, dry items → vibratory feeder; M3 mounting tabs |

### Stage 1 — Shredder
| Part | Joints & features |
|---|---|
| `shredder_housing` | 4 walls, top inlet + bottom outlet; **4× 608 bearing bores** (two rollers); Ø38 motor face + 4× M3; interlock-switch pocket; M4 feet |
| `shredder_roller` (×2) | Ø40 blunt-tooth roller, 8 mm shaft stubs, grub-screw flat (counter-rotating pair) |

### Stage 2 — Auger dewatering press
| Part | Joints & features |
|---|---|
| `auger_tube` | Ø60 slotted tube (2.2 mm drain slots); end cap with **608 pocket** + 4× M3 motor flange; top inlet window |
| `auger_screw` | 25 mm-pitch Archimedes helix, Ø8 shaft stubs |
| `auger_tray` | Liquid catch reservoir ("Bin 1") with drain spout |
| `auger_probe_mount` | Clip for capacitive moisture strip at cake outlet |

### Stage 3–4 — Fine trommel + air classifier
| Part | Joints & features |
|---|---|
| `fine_trommel_drum` | Ø95 × 140, ~4 mm slots; hubbed end caps |
| `air_classifier` | Chamber with **40 mm fan mount** (Ø32 + 4× M3 at 32 mm) + light/heavy divider |

### Vibratory singulation feeder
| Part | Joints & features |
|---|---|
| `vibratory_feeder` | Tray with **4 printed leaf-spring flexure legs** (M3 feet) + eccentric-mass vib-motor pocket |

### Conveyor
| Part | Joints & features |
|---|---|
| `conveyor_side` (×2) | Side plate, **2× 608 bearing bores**, M4 deck feet |
| `conveyor_roller` (×2) | Ø40 × 120 roller, 8 mm shafts, grub-screw flat |
| `conveyor_belt` | Racetrack belt loop (fit/visual reference; real belt = rubber band material) |
| `conveyor_motor_bracket` | TT-motor 2-hole pattern + shaft clearance |
| `encoder_disc` | Ø60 slotted disc (20 slots) on driven-roller shaft — belt position ref |
| `encoder_bracket` | U-bracket straddling the disc, 2 holes for IR beam-break pair |

### Belt-line sensors & vision
| Part | Joints & features |
|---|---|
| `magnet_mount` | Height-slotted cantilever with neodymium-strip pocket (Stage 5) |
| `sensor_inductive_mount` | **Ø12.4 barrel bore** + 4× M3 standard boss pattern (Stage 6) |
| `sensor_capacitive_mount` | 23 mm board clip + 4× M3 (Stage 7) |
| `camera_gantry` | Overhead arch, 150 mm above belt; 4× M3 camera mount |
| `esp32cam_enclosure` | Box with lens hole + LED-ring recess + **4 PCB standoffs (40×27)** + cable slot |
| `esp32cam_lid` | Snap lid with locating lip |

### Stage 9 — Actuated sort + bins
| Part | Joints & features |
|---|---|
| `servo_bracket_sg90` | SG90 cradle (23×12.5 pocket, 32 mm tab holes) at belt end |
| `sort_paddle` | Diverter paddle with servo-horn boss |
| `sorting_chute` | 4-lane fan (METAL / PLASTIC / PAPER / REJECT) sloping to bins |
| `bin_METAL`, `bin_PLASTIC`, `bin_PAPER`, `bin_REJECT` | 88 mm bins, rolled lip, label recess |
| `bin_HAZARD` | 70 mm hazard bin |
| `bin1_liquid` | Liquid catch bin under auger |

### Control electronics
| Part | Joints & features |
|---|---|
| `control_enclosure_base` | 172×112×55 box; **standoff bosses** for 3× L298N + buck + PCF8574; 3 cable glands; M4 mounting ears |
| `control_enclosure_lid` | **OLED window (26×15)**, 3× 12 mm buttons, rocker-switch slot, 2× LED holes, locating lip |

---

## 4. Electronics fitment (space reserved in the model)

Cavities / mounts are sized to the real Rev 3.1 BOM components:

| Component | Where it fits |
|---|---|
| ESP32-CAM (AI-Thinker) + LED ring | `esp32cam_enclosure` (4 standoffs, lens hole, ring recess) |
| 3× L298N (43×43) + LM2596 buck + PCF8574 expander | `control_enclosure_base` standoff grid |
| SSD1306 0.96" OLED | `control_enclosure_lid` window |
| Buttons / rocker switch / status LEDs | `control_enclosure_lid` cutouts |
| SG90 servos (×2) | `servo_bracket_sg90`, `hopper` flap pocket |
| Inductive prox LJ12A3 (M12) ×3 | `wet_funnel` boss, `sensor_inductive_mount`, (hopper throat) |
| Capacitive moisture sensor ×2 | `auger_probe_mount`, `sensor_capacitive_mount` |
| Geared DC motors ×4 (shredder/auger/2 trommels) | motor faces on `shredder_housing`, `auger_tube`, trommel drives |
| TT gear motor (conveyor) | `conveyor_motor_bracket` |
| Eccentric-mass vib motor | `vibratory_feeder` pocket |
| IR beam-break pairs (encoder + trommel exit) | `encoder_bracket` (+ mount on trommel exit) |
| 608ZZ bearings ×10 | all bearing pockets (shredder, trommels, conveyor, auger) |

---

## 5. Tolerancing & print notes (from manual §10.3)

- **Bearing bores** printed at **nominal + 0.12 mm** (Ø22.12) for a light press fit — don't overheat on insertion.
- **Threaded-insert bosses:** holes sized for M3 heat-set inserts (≈Ø4.0), not raw thread Ø.
- **Sensor faces:** keep flat within 0.2 mm — inductive/capacitive sensing range is standoff-sensitive.
- **Materials:** PLA for structural/chute parts; **PETG** for wear/wet parts (shredder rollers & housing,
  auger screw & tube, both trommels, vibratory tray).
- **Layer height:** 0.2 mm PLA structural, 0.15 mm PETG wear parts.
- **Trommel slot width:** print 40/50/60 mm coupons first and pass real test items before the full drum.
- **Shafts:** 8 mm rod; rotating clearance holes are Ø8.3.

---

## 6. Regenerating / changing dimensions (parametric source)

`build_ecosynapse.py` builds everything with CadQuery. To change a size, edit the parameters at the
top (or any part function) and re-run:

```bash
python3 -m venv env && ./env/bin/pip install cadquery
./env/bin/python build_ecosynapse.py     # rewrites parts/*.step + the assembly
```

Key global params: `WALL`, `M3_INSERT`, `M4_CLR`, `BRG_OD`, `SHAFT`, `BELT_W`, `BELT_SPAN`, `ROLLER_D`,
and the envelope `L, W, H`. Each stage is its own function, so you can tune one part without touching others.

---

## 7. Assembly order (matches build photos)

Left → right along the deck: **hopper → coarse trommel (on 2 cradles) → wet funnel + shredder + auger
press (front-left, liquid bin under) → dry chute → vibratory feeder → conveyor belt (magnet, inductive,
capacitive sensors along it, encoder on the driven roller) → camera gantry over the belt → sorting
paddle → 4-lane chute → METAL/PLASTIC/PAPER/REJECT bins.** Control enclosure sits on standoffs at the
rear-right corner; hazard bin near the hopper.
