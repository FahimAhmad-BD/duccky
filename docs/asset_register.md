# Asset Register

Every third party model, library, dataset and code source used in Duccky v1.0, with its license. Assets under licenses that forbid redistribution or commercial use are not placed in this repository.

| ID | Asset | Used for | Source | License | In repo |
|---|---|---|---|---|---|
| A01 | microduck_rl training stack | Reference for RL recipe and actuator modelling approach | github.com/pollen-robotics/microduck_rl | Apache 2.0 (code); robot meshes CC BY-NC-SA, not used | No, referenced only |
| A02 | microduck runtime | Reference for runtime architecture | github.com/pollen-robotics/microduck | Apache 2.0 | No, referenced only |
| A03 | MuJoCo | Simulation | github.com/google-deepmind/mujoco | Apache 2.0 | Dependency |
| A04 | KiCad 10 and its bundled libraries | Schematic, PCB, DRC, STEP export | kicad.org | GPL 3 (application); libraries CC BY-SA 4.0 with the KiCad library exception, which allows use in designs without the design taking on the license | Dependency; library symbols are embedded in `ecad/carrier/carrier.kicad_sch` as KiCad requires |
| A05 | KiCad footprints used on the carrier: Capacitor_SMD, Resistor_SMD, Inductor_SMD (Coilcraft XAL7030, XAL5030, 1008), Package_DFN_QFN (Texas_RNN0018A, Texas_RGE0024H, TQFN-16 3x3), Package_TO_SOT_SMD (SOT-583-8, SOT-23-5), Package_SO (TSSOP-10, VSSOP-8), Package_LGA (LGA-28 5.2x3.8), Connector_AMASS (XT30PW-M), Connector_JST (EH, GH, SH), Connector_USB (GCT USB4105), Connector_PinSocket_2.54mm (2x20), MountingHole | Carrier PCB | KiCad library | CC BY-SA 4.0 with library exception | Referenced from the KiCad install |
| A06 | KiCad 3D models for the footprints above, including the VQFN-24 4x4 body reused for the TPS25982 | Board STEP for Fusion | KiCad library | CC BY-SA 4.0 with library exception | Embedded in the exported STEP |
| A07 | Duccky custom symbols TPS25982 and BNO085, footprint Texas_RGE0024M_TPS25982 | Carrier board | Drawn in this repo from TI SLVSEI3D (drawing 4223975/B) and CEVA 1000-3927 v1.17 | Project license (CC BY 4.0) | `ecad/lib` |
| A08 | Freerouting 2.5.0 | PCB autorouting (run locally, output only) | github.com/freerouting/freerouting | GPL 3 | No, tool only |
| A09 | Microsoft Build of OpenJDK 21 and 25 | Runs Freerouting | learn.microsoft.com/java/openjdk | GPL 2 with Classpath Exception | No, tool only |
| A10 | pypdf, pypdfium2 | Reading manufacturer datasheets during design | PyPI | BSD 3 / Apache 2.0 and BSD | No, tool only |
| A11 | Claude Fusion Bridge | Drives Fusion from Claude Code | private repo FahimAhmad-BD/claude-fusion-bridge (same author) | Apache 2.0 | No, separate repo |
| A12 | Radxa ZERO 3W 2D DXF (v1.11) | Hole and header positions on the carrier | dl.radxa.com/zero3/docs/hw/3w/radxa_zero_3w_2d_dxf.zip | Radxa published documentation | No, dimensions only |

Servo, compute and mechanical CAD models are added here as they are sourced in Phase 3.
