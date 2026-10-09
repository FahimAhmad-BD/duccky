# Duccky v1.0: Requirements and Budgets

**Document:** DCK-00 · **Revision:** B · **Phase:** 0 · **Status:** Baseline for Phase 2 electrical and Phase 3 CAD

## 1. Purpose

Duccky v1.0 is a digital twin of a small bipedal duck robot, designed to production intent so that it can be manufactured without redesign. The project delivers a geometric, physical, electrical, behavioral and software twin, all generated from one master design. It is inspired by Pollen Robotics' Microduck and shares no mechanical files with it. Pollen's Apache 2.0 software is used as a reference for training and runtime architecture only.

## 2. Ground rules

| ID | Rule |
|---|---|
| GR1 | Zero cost. Only free tools, free licenses and free community assets. |
| GR2 | Fusion (personal use license) is the mechanical CAD master. STEP is the exchange format. |
| GR3 | Every purchased part in the BOM is a real, currently sold part with a published datasheet. |
| GR4 | Community CAD models are used only under licenses that allow redistribution in a public repository. Every asset is logged with source and license. |
| GR5 | No Pollen Microduck meshes or CAD (CC BY-NC-SA) inside the Duccky design. |
| GR6 | Every numeric claim in the design record traces to a source, a calculation, or a simulation run in this repository. |

## 3. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| F1 | Walk on flat ground with velocity commands (forward, lateral, turn) | RL policy in sim, sim to sim transfer |
| F2 | Stand up unaided from front and back falls | RL policy in sim |
| F3 | Crouch and pick up a 30 g object with the beak | RL policy in sim, beak torque check |
| F4 | Gamepad teleoperation through the robot runtime | Software in the loop test |
| F5 | Fall detection with torque cut within one control cycle | Software in the loop test |
| F6 | 50 Hz control loop running ONNX policy inference on the onboard computer | Runtime timing test against emulated hardware |
| F7 | Sensors: wide angle camera, 8×8 ToF ranging sensor, IMU in trunk (second IMU in head optional), microphone, speaker | Present in CAD, ECAD and sim |
| F8 | Swappable battery without tools | CAD review |

## 4. Physical targets

| Parameter | Target | Phase 1 model |
|---|---|---|
| Overall height (nominal stance) | 25 to 30 cm | 28.1 cm |
| Total mass | ≤ 850 g | 813 g |
| Hip pitch axis height (nominal stance) | | 11.2 cm |
| Nominal stance | Slight crouch, knee never locked | Knee 0.80 rad |
| Runtime | ≥ 45 min mixed use | Verified in Phase 6 from simulated current |
| Process | FDM printed structure and shells, purchased fasteners, bearings and electronics | |

## 5. Degrees of freedom

Fifteen actuated joints. The leg has no ankle roll, so lateral balance is dynamic, which matches the reference platform and saves two actuators per robot.

| Group | Joints | Count |
|---|---|---|
| Each leg | hip yaw, hip roll, hip pitch, knee, ankle pitch | 2 × 5 |
| Neck and head | neck pitch, head pitch, head yaw, head roll | 4 |
| Beak | beak open and close | 1 |
| **Total** | | **15** |

Joint limits used in sizing (rad): hip yaw ±0.50, hip roll ±0.40, hip pitch ±1.60, knee −0.10 to 2.20, ankle ±1.40, neck pitch −1.50 to 1.00, head pitch ±1.50, head yaw ±2.90, head roll ±0.45, beak 0 to 0.90.

## 6. Mass budget

| Item | Mass (g) | Basis |
|---|---|---|
| Servos, 6 × XC330-M288-T (hip pitch, knee, ankle) | 138 | Vendor datasheet, 23 g each |
| Servos, 9 × XL330-M288-T (all other joints) | 162 | Vendor datasheet, 18 g each |
| Battery, NP-F550 type 2S Li-ion pack | 85 | Allocation, confirm from pack datasheet in Phase 2 |
| Compute board | 15 | Allocation |
| Carrier PCB and connectors | 25 | Allocation |
| IMU and small sensors | 4 | Allocation |
| Speaker and microphone | 12 | Allocation |
| Wiring harness | 20 | Allocation |
| Fasteners, inserts and bearings (trunk) | 20 | Allocation |
| Printed trunk structure | 85 | Allocation |
| Printed trunk shells | 35 | Allocation |
| Leg structure, printed, both legs | 148 | Allocation |
| Neck, head structure, head payload, beak | 64 | Allocation |
| **Total** | **813** | Phase 1 model, `analysis/sizing` |

Allocations are replaced by Fusion mass properties in Phase 3. The budget carries 37 g of margin against the 850 g limit.

## 7. Electrical baseline

| Item | Baseline | Status |
|---|---|---|
| Servo bus | ROBOTIS Protocol 2.0 over half duplex TTL, single daisy chain per leg plus one for neck and head | XL330 and XC330 share the 20 × 34 mm footprint and the bus |
| Servo rail | 5.0 V regulated from 2S pack | Recommended voltage for both servo models |
| Servo rail sizing | Worst case simultaneous stall of the six loaded leg servos is 6 × 1.8 A = 10.8 A. The rail regulator is sized for ≥ 11 A peak; continuous rating is set in Phase 2 from simulated current profiles | Stall currents from vendor datasheets |
| Compute rail | Separate 5 V regulator, isolated from servo transients | |
| Protection | Pack protection board, main switch, fuse, hardware torque disable line | |

## 8. Software baseline

Robot runtime in Python on the onboard computer, structured as a control process that owns the servo bus at 50 Hz, reads the IMU, runs ONNX inference and applies joint targets, with separate processes for gamepad, camera and ToF. A hardware abstraction layer lets the same runtime drive either real hardware drivers or the MuJoCo emulation. RL training follows the published Microduck recipe: MuJoCo, PPO, domain randomization, ONNX export, run on free GPU quotas.

## 9. Risks carried into Phase 3

| ID | Risk | Mitigation |
|---|---|---|
| RK1 | Hip pitch walking demand is at 38 % of stall against a 40 % limit | Keep trunk payload low and centred over the hips in CAD; recheck with Fusion mass properties |
| RK2 | The knee pass depends on the parallel assist spring (0.10 N m/rad) | Select a purchasable torsion spring in Phase 3 and model its real rate; without it the knee runs at 45 % of stall while walking |
| RK3 | Mass allocations may grow in CAD | 37 g margin; each Phase 3 drop reruns the sizing study automatically from the exported JSON |
