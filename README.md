# Duccky v1.0

A production intent digital twin of a 28 cm, 15 DOF bipedal duck robot: parametric CAD, wiring, URDF and MJCF, reinforcement learning policies, and the robot runtime, all generated from one master design and built with free tools only.

Inspired by Pollen Robotics' Microduck. Duccky is a clean sheet design and contains no Microduck mechanical files.

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Requirements, DOF, mass and power budgets | Done, [DCK-00](docs/00_requirements.md) |
| 1 | Sim first actuator sizing and servo selection | Done, [DCK-01](docs/01_actuator_sizing.md) |
| 2 | Electrical architecture, KiCad carrier board, harness | Done, [DCK-02](docs/02_electrical.md) |
| 3 | Mechanical CAD in Fusion with DFM rules | Next |
| 4 | Engineering validation: FEA, tolerance stacks, range of motion, power | Planned |
| 5 | Robot description: URDF, MJCF, ROS 2 package | Planned |
| 6 | RL training and sim to sim transfer | Planned |
| 7 | Software in the loop runtime | Planned |
| 8 | Manufacturing package: BOM, drawings, print and assembly guides | Planned |
| 9 | Portfolio site with browser simulation | Planned |

## Key decisions so far

| Decision | Choice |
|---|---|
| Actuation | 6 × ROBOTIS XC330-M288-T (hip pitch, knee, ankle), 9 × XL330-M288-T, knee assist spring 0.10 N m/rad |
| Mass | 825 g against an 850 g limit |
| Compute | Radxa ZERO 3W, 4 GB, 16 GB eMMC |
| Battery | Tool-free 2S cartridge, 2 × Molicel INR-18650-P28A, 20.6 Wh |
| Height | 28.1 cm in nominal stance |
| Leg | 5 DOF, no ankle roll, thigh 56 mm, shank 50 mm |

## Repository layout

```
cad/          Fusion API scripts, STEP, STL, drawings
ecad/         KiCad project, BOM, harness definition
description/  generated URDF, MJCF, ROS 2 package
analysis/     sizing, FEA, tolerance stacks, power budget
training/     RL environments, configs, ONNX policies
runtime/      robot software, hardware abstraction layer, sim drivers
docs/         design record
web/          browser demo
```

## Toolchain

Fusion (personal use) · FreeCAD FEM and TechDraw · KiCad · MuJoCo · Blender · Python · GitHub Pages. All free.

## License

Code: Apache 2.0. Design files and documentation: CC BY 4.0. Third party assets keep their own licenses, listed in [docs/asset_register.md](docs/asset_register.md).

Author: Fahim Ahmad
