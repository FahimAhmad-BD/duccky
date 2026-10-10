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
3. **CAD workflow:** write Fusion API Python scripts that build parts and the assembly with named user parameters, joints and materials. Claude runs them directly through the standalone Claude Fusion Bridge add-in (private repo `FahimAhmad-BD/claude-fusion-bridge`, cloned at `C:\Users\fahim\dev\claude-fusion-bridge`, installed in Fusion with Run on Startup; install only that one copy): `bash cad/tools/fusion_run.sh <job.py>` drops the job in `%USERPROFILE%/Documents/ClaudeFusion/bridge/inbox` and prints the result JSON, including viewport PNG paths that Claude reads to check the geometry. Build scripts are committed in `cad/` so the model can always be regenerated. A second export script dumps STEP, per part STL, and a JSON of joint frames, axes, limits, masses and inertias. URDF and MJCF are generated from that JSON. Fusion stays the single source of truth.
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
| Electronics | KiCad 10 |
| Simulation | MuJoCo (Python bindings) |
| RL training | microduck_rl recipe (mjlab, MuJoCo Warp, PPO, ONNX export) on free GPU |
| Renders and video | Blender |
| Hosting and demo | GitHub, GitHub Pages with MuJoCo WebAssembly |

User hardware: Asus A15 laptop, Ryzen 9 8945H, 32 GB RAM, RTX 4060. Windows on the internal drive; Ubuntu 24.04 with ROS 2 Jazzy on an external SSD.

**All work runs on Windows** (user decision, 2026-10-10). Installed: Git, GitHub CLI, Python 3.12 (venv at `%USERPROFILE%\.venvs\duccky`, outside OneDrive; run Python with `%USERPROFILE%\.venvs\duccky\Scripts\python.exe`), KiCad 10. Linux only tools (RL stack, ROS 2) are tried natively first, then in WSL2 if needed. Phase 1 reproduces on Windows with identical numbers.

## 5. Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Requirements, DOF, mass and power budgets | **Done.** `docs/00_requirements.md` |
| 1 | Sim first actuator sizing and servo selection | **Done.** `docs/01_actuator_sizing.md`, `analysis/sizing/` |
| 2 | Electrical architecture, KiCad carrier board, harness | **Done** (tag `phase-2`). `docs/02_electrical.md`, `ecad/`, `analysis/harness/`. Head board deferred (RK9) |
| 3 | Mechanical CAD in Fusion with DFM rules | **In progress.** Done: servo reference (`cad/lib/servo.py`), leg layout (`analysis/layout/leg_layout.py`), left leg parts with zero interference over all joint ranges (`cad/build/leg_build.py`), whole-robot packaging with mirrored right leg, cartridge, board STEP and trunk frame (`cad/build/robot_skeleton.py`, 66 g frame, trunk widened to 96 mm). Next: cartridge part, neck and head, shells, knee spring (RK2), saved master document, export JSON |
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
* Thigh 52 mm, shank 46 mm, hip lateral offset 34 mm; hip yaw to roll 14 mm, roll to pitch 30.7 mm, ankle to sole 13 mm (Phase 3 layout from servo geometry, `analysis/layout/leg_layout.py`, DCK-01 §10).
* Foot 75 × 36 × 8 mm, ankle 6 mm behind the foot centre. Leg arrangement: roll servo horizontal under the yaw horn, pitch servo hanging in the roll bracket, knee servo in the thigh, ankle servo lying in the foot.
* Nominal stance: hip pitch −0.40, knee 0.80, ankle −0.40 rad.
* Height about 29.7 cm, total mass 825 g against an 850 g limit (DCK-01 §10).

**Pass rules:**
1. Peak demand at or below 70 % of stall.
2. Walking demand at or below 40 % of stall.
3. Walking demand at or below the torque available at half the peak gait joint speed.

**Electrical baseline:**
* Tool-free 2S cartridge: 2 × Molicel INR-18650-P28A, S-8252 cell protection, four blade contacts (B+, mid-cell, B−, NTC), 105 g, 20.6 Wh. Charged in the robot over USB-C by a BQ25887 (robot off while charging). Replaces the NP-F550 type (no datasheet), user decision 2026-10-10.
* 5.0 V servo rail: TPS56C215 12 A buck; its EN pin is the hardware torque disable line (default off). Design peak 11.0 A.
* 5.0 V compute rail: TPS62933 3 A buck, design peak 2.4 A. Input: main switch and TPS25982 eFuse (15 A limit). Full part list and header pin map in DCK-02 §2 and §3.
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
| RK1 | Hip pitch walking demand at 38.4 % of stall against a 40 % limit | Keep trunk payload low and centred over the hips; rerun sizing with Fusion mass properties |
| RK2 | Knee pass depends on the assist spring | Source a purchasable torsion spring in Phase 3 and model its real rate |
| RK3 | Mass allocations may grow in CAD | 25 g margin; rerun `compare.py` from the Fusion JSON on every CAD drop |
| RK4 | Closed: servo figures confirmed in the ROBOTIS e-Manual (XL330 103 rpm, 26 mm deep) | |
| RK5 to RK10 | ZERO 3W header power (closed), cartridge and cell mass, head yaw cable travel and camera FPC, head board datasheets, ZERO 3W hole pattern | See DCK-02 §6 |

## 8. Repository layout

```
CLAUDE.md          this brief
README.md          public project page and phase table
docs/              design record (DCK-00 requirements, DCK-01 sizing, DCK-02 electrical, asset register)
analysis/sizing/   Phase 1 sizing model and studies
  params.py        single source of truth for the sizing model
  build_model.py   generates the primitive MJCF from params.py
  sizing.py        load cases S1 to S3, D1, D2; writes results/<tag>/
  compare.py       servo configurations A to G, scoring, tables and plot
  render.py        headless render of the model
  results/         outputs of the last run
analysis/harness/  harness.py: cable list and lengths from params.py
ecad/gen/          generators: carrier.py (schematic), pcb.py (placement), route.py (Freerouting),
                   cleanup.py, library.py; build_carrier.sh runs the whole chain
ecad/carrier/      generated KiCad project, ERC and DRC reports, carrier.step for Fusion
ecad/lib/          custom symbols and footprints
cad/tools/         fusion_run.sh and Fusion jobs (bridge add-in lives in its own repo)
description/  training/  runtime/  web/   reserved for later phases
```

**Reproduce Phase 1:**

```bash
cd analysis/sizing
pip install -r requirements.txt
python compare.py
```

On Linux, rendering needs `MUJOCO_GL=osmesa` (or `egl`) and `PYOPENGL_PLATFORM` set to the same value.

## 9. Next task: Phase 3, mechanical CAD in Fusion

Phase 2 is done: compute, parts, power tree, carrier board (`ecad/carrier`, regenerated by `bash ecad/gen/build_carrier.sh`) and harness (`analysis/harness/harness.py`). Open items carried in: the head board (RK9, needs the VL53L8CX and T5848 datasheets downloaded by hand) ; RK10 (ZERO 3W hole pattern) is closed from Radxa's DXF.

Phase 3 deliverables:

1. Done 2026-10-10: the Claude Fusion Bridge is installed as a junction in `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\ClaudeFusionBridge` pointing at the clone, loads on Fusion startup, and passes `cad/tools/jobs/ping.py` and `geometry_test.py`. Work in scratch or Duccky documents, never in documents the user has open.
2. Fusion API scripts in `cad/`, leg first: one servo pocket for the 20 × 34 × 26 mm envelope, idler bearing opposite each horn, heat set insert bosses, harness channels with the service loops from `analysis/harness`, knee assist torsion spring (RK2).
3. Trunk around the carrier board STEP (`ecad/carrier/carrier.step`, 76 × 62 mm, four M2.5 standoffs on the ZERO 3W pattern) and the 2S cartridge, mounted low and centred over the hip pitch axes (RK1, RK6).
4. Head and neck with the camera FPC routed as a clock spring around head yaw (RK8); shells with uniform walls and draft.
5. Export script: STEP, per part STL, and the JSON of joint frames, axes, limits, masses and inertias; rerun `analysis/sizing/compare.py` and `analysis/harness/harness.py` from it.

## 10. References

* Microduck runtime (Apache 2.0): https://github.com/pollen-robotics/microduck
* Microduck RL training (Apache 2.0 code; the reference model uses XL330 servos and a BAM actuator model): https://github.com/pollen-robotics/microduck_rl
* XL330-M288-T e-Manual: https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/
* XC330-M288-T e-Manual: https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/
* MuJoCo: https://github.com/google-deepmind/mujoco
