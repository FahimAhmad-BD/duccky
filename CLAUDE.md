# CLAUDE.md: Duccky v1.0 project brief

This file carries the full project context into Claude Code. Read it before doing anything in this repository.

## 1. Project

Duccky v1.0 is a production intent **digital twin** of a 28 cm, 15 DOF bipedal duck robot, built as a portfolio project by Fahim Ahmad. Nothing is physically built. The goal is a design that could be manufactured later without redesign, so design for manufacturing (DFM) applies to every part.

Inspired by Pollen Robotics' Microduck (https://store.pollen-robotics.com/products/microduck). Duccky is a clean sheet design.

The twin has five layers, all derived from one source of truth so they cannot drift apart:

1. **Geometric twin:** parametric Fusion CAD of every part, including COTS parts and the routed wiring harness.
2. **Physical twin:** MJCF and URDF with inertials from CAD, joint limits from CAD, actuator models from datasheets.
3. **Electrical twin:** KiCad schematic and PCB with real part numbers, harness definition, power budget validated against simulated current.
4. **Behavioral twin:** RL policies trained in MuJoCo (walk, stand up, crouch, beak grasp).
5. **Software twin:** the robot runtime that would ship, running unchanged against the simulator through a hardware abstraction layer.

## 2. Hard rules

1. **Zero cost.** Only free tools, free licenses and free community assets. No paid services, APIs, cloud tokens or add-ins. GPU training uses free Kaggle or Colab quotas, or the local machine.
2. **Fusion is the mechanical CAD master** (personal use license). It is available on the user's Windows machine. STEP and STL exports work on the free tier; IGES, SAT and SMT do not. Fusion simulation needs paid cloud tokens, so FEA goes to FreeCAD FEM with CalculiX. Keep the robot in as few Fusion documents as possible, since the free tier limits active documents.
3. **CAD workflow:** write Fusion API Python scripts that build parts and the assembly with named user parameters, joints and materials. The user runs them from Utilities > Scripts and Add-Ins. A second export script dumps STEP, per part STL, and a JSON of joint frames, axes, limits, masses and inertias. URDF and MJCF are generated from that JSON. Fusion stays the single source of truth.
4. **No Pollen Microduck meshes or CAD** in the design. They are CC BY-NC-SA. Pollen's Apache 2.0 code (microduck, microduck_rl) may be used as a reference for training and runtime architecture.
5. **Every purchased part is real**, currently sold, with a published datasheet. Log every third party asset with source and license in `docs/asset_register.md`.
6. **No invented facts.** Every number in the design record traces to a source, a calculation or a simulation in this repo. Look up current specs instead of recalling them.

## 3. User preferences

1. Communication is direct and concise, with no filler. Prose over bullet lists unless structure helps.
2. **No dashes in prose** (no em dashes, no en dashes used as punctuation).
3. Make a reasonable assumption and state it instead of asking, unless the choice is expensive to undo.
4. Give direct recommendations, not hedged option lists.
5. Formal documents: publication ready, no meta commentary, fully justified body text when exported.
6. Code always goes in files, never long inline snippets.
7. **Version control:** the repository is the private GitHub repo `duccky` (branch `main`). When a phase is complete, commit its work and push to GitHub, then tag the commit `phase-N`. Commit fixes between phases as they happen.
8. User background: mechanical design and manufacturing (B.Sc. IPE, SolidWorks CSWP). Engineering project manager in robotics and automation. Strong in CAD and DFM, newer to software, Linux and ROS 2. Explain software concepts plainly; skip mechanical basics.

## 4. Toolchain (all free)

| Layer | Tool |
|---|---|
| Mechanical CAD | Fusion (personal use) |
| FEA, tolerance checks, 2D drawings | FreeCAD (FEM with CalculiX, TechDraw) |
| Electronics | KiCad |
| Simulation | MuJoCo (Python bindings) |
| RL training | microduck_rl recipe (mjlab, MuJoCo Warp, PPO, ONNX export) on free GPU |
| Renders and video | Blender |
| Hosting and demo | GitHub, GitHub Pages with MuJoCo WebAssembly |

User hardware: Asus A15 laptop, Ryzen 9 8945H, 32 GB RAM, RTX 4060. Windows on the internal drive; Ubuntu 24.04 with ROS 2 Jazzy on an external SSD.

## 5. Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Requirements, DOF, mass and power budgets | **Done.** `docs/00_requirements.md` |
| 1 | Sim first actuator sizing and servo selection | **Done.** `docs/01_actuator_sizing.md`, `analysis/sizing/` |
| 2 | Electrical architecture, KiCad carrier board, harness | **In progress.** Compute selected (DCK-02 §1); next is component selection (§9 item 2) |
| 3 | Mechanical CAD in Fusion with DFM rules | Planned |
| 4 | Engineering validation: load derived FEA, tolerance stacks, range of motion and interference, thermal and power | Planned |
| 5 | Robot description: URDF, MJCF, ROS 2 package, generated from Fusion JSON | Planned |
| 6 | RL training, sim to sim transfer and robustness sweeps | Planned |
| 7 | Software in the loop runtime | Planned |
| 8 | Manufacturing package: BOM, drawings, print and assembly guides, harness drawing | Planned |
| 9 | Portfolio: README, renders, videos, browser demo | Planned |

## 6. Frozen decisions

**DOF (15):** each leg has hip yaw, hip roll, hip pitch, knee and ankle pitch (no ankle roll, so lateral balance is dynamic). Neck and head have neck pitch, head pitch, head yaw and head roll. Plus one beak joint.

**Actuators (Phase 1 result, configuration G):**

| Joints | Servo | Stall torque | No load speed | Mass |
|---|---|---|---|---|
| Hip pitch, knee, ankle (6) | ROBOTIS XC330-M288-T | 0.93 N m at 5 V | 81 rpm | 23 g |
| All other joints (9) | ROBOTIS XL330-M288-T | 0.52 N m at 5 V | 104 rpm | 18 g |

Each knee has a parallel assist torsion spring, 0.10 N m/rad, with its rest angle at a straight knee. Both servos share a 20 × 34 mm footprint and the ROBOTIS Protocol 2.0 TTL bus, so one servo pocket design serves every joint. All XL330 fails (knee 106 % of stall at peak). All STS3215 passes but weighs 1338 g and does not fit.

**Geometry (`analysis/sizing/params.py`):**
* Thigh 56 mm, shank 50 mm, hip lateral offset 34 mm.
* Foot 75 × 36 × 8 mm, ankle 6 mm behind the foot centre.
* Nominal stance: hip pitch −0.40, knee 0.80, ankle −0.40 rad.
* Height 28.1 cm, hip pitch axis at 11.2 cm, total mass 813 g against an 850 g limit.

**Pass rules:**
1. Peak demand at or below 70 % of stall.
2. Walking demand at or below 40 % of stall.
3. Walking demand at or below the torque available at half the peak gait joint speed.

**Electrical baseline:**
* 2S Li-ion pack, NP-F550 type, swappable without tools.
* 5.0 V servo rail sized for at least 11 A peak (six loaded servos stalling at 1.8 A each).
* Separate 5 V compute rail, pack protection, main switch, fuse and a hardware torque disable line.
* Servo bus: one daisy chain per leg plus one for the neck and head.
* Sensors: wide angle camera, 8 × 8 ToF sensor, trunk IMU (head IMU optional), microphone and speaker.
* Compute: **Radxa ZERO 3W, 4 GB RAM, 16 GB eMMC** (decided in DCK-02 §1). Raspberry Pi Zero 2W is the fallback on the same 65 × 30 mm footprint. Each servo chain gets its own UART (UART3, UART4, UART5; UART9 spare).

**Software baseline:**
* Python runtime with a 50 Hz control process owning the servo bus, IMU reads, ONNX inference and the safety layer (fall detection, torque cut, current and thermal watchdogs).
* Separate processes for gamepad, camera and ToF.
* A hardware abstraction layer with real drivers and MuJoCo emulated drivers. The emulation covers bus latency and quantization, IMU noise, ToF raycasts and camera renders.

## 7. Open risks

| ID | Risk | Mitigation |
|---|---|---|
| RK1 | Hip pitch walking demand at 38 % of stall against a 40 % limit | Keep trunk payload low and centred over the hips; rerun sizing with Fusion mass properties |
| RK2 | Knee pass depends on the assist spring | Source a purchasable torsion spring in Phase 3 and model its real rate |
| RK3 | Mass allocations may grow in CAD | 37 g margin; rerun `compare.py` from the Fusion JSON on every CAD drop |
| RK4 | XL330 and XC330 figures came from reseller pages | Confirm against the ROBOTIS e-Manual before freezing the BOM |

## 8. Repository layout

```
CLAUDE.md          this brief
README.md          public project page and phase table
docs/              design record (DCK-00 requirements, DCK-01 sizing, asset register)
analysis/sizing/   Phase 1 sizing model and studies
  params.py        single source of truth for the sizing model
  build_model.py   generates the primitive MJCF from params.py
  sizing.py        load cases S1 to S3, D1, D2; writes results/<tag>/
  compare.py       servo configurations A to G, scoring, tables and plot
  render.py        headless render of the model
  results/         outputs of the last run
cad/  ecad/  description/  training/  runtime/  web/   reserved for later phases
```

**Reproduce Phase 1:**

```bash
cd analysis/sizing
pip install -r requirements.txt
python compare.py
```

On Linux, rendering needs `MUJOCO_GL=osmesa` (or `egl`) and `PYOPENGL_PLATFORM` set to the same value.

## 9. Next task: Phase 2, electrical architecture

Phase 2 comes before CAD because board size and connector placement drive the trunk layout. Deliverables:

1. **Compute selection.** Choose the SBC (RK3566 class versus Pi Zero 2W) on NPU or CPU headroom for 50 Hz ONNX inference plus camera, size, mass, power and community support. Record the decision with sources.
2. **Component selection with real part numbers:**
   * IMU
   * 8 × 8 ToF sensor (VL53L5CX class)
   * camera
   * microphone and speaker amplifier
   * servo bus transceiver (half duplex TTL)
   * 5 V servo regulator (at least 11 A peak)
   * compute regulator
   * pack protection, fuse and switch
   * connectors (JST or Molex families compatible with the servo cables)
   * battery holder for the NP-F550 type pack
3. **Block diagram and power tree**, with a current budget per rail.
4. **KiCad project in `ecad/`:** schematic, carrier board PCB with an outline sized to fit the trunk, and STEP export for Fusion.
5. **Harness definition:** every cable with endpoints, connector part numbers, wire gauge, length per segment, and service loop length sized to full joint travel.
6. **Update the docs:**
   * `docs/02_electrical.md`
   * the mass budget in `docs/00_requirements.md` with real component masses
   * `docs/asset_register.md` with every footprint and 3D model used
7. **Rerun Phase 1** if the trunk payload mass changes.

After Phase 2 comes Phase 3: the Fusion API scripts for the leg first (one servo pocket design, idler bearing opposite each servo horn, heat set insert bosses, harness channels), then the trunk, head and shells. Cosmetic shells use uniform walls and draft so a molded version is possible later.

## 10. References

* Microduck runtime (Apache 2.0): https://github.com/pollen-robotics/microduck
* Microduck RL training (Apache 2.0 code; the reference model uses XL330 servos and a BAM actuator model): https://github.com/pollen-robotics/microduck_rl
* XL330-M288-T specs: https://www.generationrobots.com/en/403817-dynamixel-xl330-m288-t-servo-motor.html
* XC330-M288-T specs: https://besomi.com/jo_en/xc330-m288-t-dynamixel-robx0029.html
* MuJoCo: https://github.com/google-deepmind/mujoco
