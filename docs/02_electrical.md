# Duccky v1.0: Electrical Architecture

**Document:** DCK-02 · **Revision:** A · **Phase:** 2 · **Status:** Complete; head board pending (RK9)

## 1. Compute selection

### 1.1 Result

Duccky v1.0 uses the **Radxa ZERO 3W** (Rockchip RK3566) with 4 GB LPDDR4 and on board eMMC. The **Raspberry Pi Zero 2 W** is the fallback. Both boards measure 65 × 30 mm, so the trunk bay and carrier board outline hold either one without change.

### 1.2 Requirements

The board must run the 50 Hz control process (servo bus, IMU, ONNX policy inference, safety layer) alongside separate camera, ToF and gamepad processes (DCK-00, F6 and F7). It must accept a MIPI CSI camera, expose at least three UARTs for the servo bus chains, and fit the trunk.

### 1.3 Comparison

| Criterion | Radxa ZERO 3W | Raspberry Pi Zero 2 W |
|---|---|---|
| SoC | Rockchip RK3566 | RP3A0 system in package |
| CPU | 4 × Cortex-A55, up to 1.6 GHz | 4 × Cortex-A53, 1 GHz |
| NPU | 0.8 TOPS (512 INT8 MAC) | none |
| RAM | 1, 2, 4 or 8 GB LPDDR4 | 512 MB |
| Storage | eMMC 0 to 64 GB, plus microSD | microSD only |
| Camera | 4 lane MIPI CSI, 22 pin 0.5 mm FPC | CSI-2 |
| Wireless | Wi-Fi 6, Bluetooth 5.4 | 2.4 GHz 802.11n, Bluetooth 4.2 |
| UARTs on 40 pin header | UART3, UART4, UART5, UART9 (UART2 is the debug console) | one full UART plus mini UART |
| Power input | 5 V only, 5 V / 2 A supply recommended | 5 V |
| Size | 65 × 30 mm | 65 × 30 mm |
| Production commitment | not published | until at least January 2030 |

### 1.4 Decision

The ZERO 3W is selected for four reasons:

1. **Proven reference.** Pollen Robotics' Microduck runtime runs a 50 Hz loop driving fifteen Dynamixel servos from ONNX policies on a Radxa ZERO 3W. That is the same servo count, bus and loop rate as Duccky.
2. **Memory.** The camera stream, ONNX runtime and Python processes don't fit comfortably in 512 MB. The 4 GB variant removes that constraint.
3. **NPU.** The 0.8 TOPS NPU can run vision models such as object detection for the beak grasp task without loading the CPU that runs the control loop.
4. **UARTs.** Four general purpose UARTs on the header let each servo chain (left leg, right leg, neck and head) own its own port. That avoids a USB adapter and keeps bus latency deterministic.

The Pi Zero 2 W offers a published production commitment and broader community support. It stays the fallback because it shares the footprint, but it has a single full UART, so it would need the three servo chains merged onto one bus.

Configuration: 4 GB RAM with 16 GB eMMC. eMMC replaces the microSD card, which can lose contact under the impact loads of falls.

### 1.5 Power and mass

Radxa recommends a 5 V / 2 A supply for the ZERO 3W and does not publish a power consumption figure, so the compute rail is sized for 2 A to the board plus the camera, ToF, audio and USB loads (Section 3). Radxa does not publish the board mass either. The DCK-00 allocation of 15 g stays until the mass is measured or a vendor figure becomes available.

### 1.6 Sources

* Radxa ZERO 3W overview: https://docs.radxa.com/en/zero/zero3
* Radxa ZERO 3W hardware interface (power input, 40 pin header, CSI): https://docs.radxa.com/en/zero/zero3/hardware-design/hardware-interface
* Raspberry Pi Zero 2 W product page: https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/
* RK3566/RK3568 NPU, 0.8 TOPS with 512 INT8 MAC: https://www.cnx-software.com/2020/12/01/rockchip-rk3568-processor-to-power-edge-computing-and-nvr-applications/ and https://pine64.org/documentation/PineTab2/Further_information/Specifications
* Microduck runtime on RK3566, 50 Hz, fifteen servos: https://github.com/pollen-robotics/microduck
* Microduck bring up notes naming the Radxa ZERO 3W: https://github.com/pollen-robotics/microduck/tree/main/docs/project

## 2. Component selection

### 2.1 Servos (confirmed against the ROBOTIS e-Manual)

The e-Manual confirms the Phase 1 figures and closes risk RK4, with two corrections: the XL330 no-load speed is 103 rpm (the reseller listed 104), and the XL330 is 26 mm deep (listed as 25). Phase 1 was rerun with 103 rpm.

| Servo | Stall torque at 5.0 V | No-load speed at 5.0 V | Stall current at 5.0 V | Standby current | Mass | Envelope |
|---|---|---|---|---|---|---|
| XL330-M288-T | 0.52 N m | 103 rpm | 1.47 A | 17 mA | 18 g | 20 × 34 × 26 mm |
| XC330-M288-T | 0.93 N m | 81 rpm | 1.80 A | 17 mA | 23 g | 20 × 34 × 26 mm |

Both run from 3.7 to 6.0 V (5.0 V recommended). Their bus is a TTL multidrop line at 3.3 V logic that tolerates 5 V, at 57.6 kbps by default and up to 4 Mbps. Each servo has two JST B3B-EH-A headers (pin 1 GND, pin 2 VDD, pin 3 DATA), and the cables use JST EHR-03 housings with SEH-001T-P0.6 crimps on 21 AWG wire.

### 2.2 Selected parts

| Function | Part | Key data | Location |
|---|---|---|---|
| Computer | Radxa ZERO 3W, 4 GB, 16 GB eMMC | RK3566, 5 V input | Trunk |
| Camera | Radxa Camera 8M 219 (Sony IMX219) | 3280 × 2464, on Radxa's supported list for the ZERO 3W, 22 pin to 15 pin FPC cable | Head |
| IMU | CEVA BNO085 | 9 axis with onboard sensor fusion, I2C, 28 pin LGA 5.2 × 3.8 mm | Carrier board, trunk |
| Depth sensor | ST VL53L8CX | 8 × 8 zones, 400 cm, 65° diagonal field of view, 60 Hz; AVDD 3.3 V, core and IO 1.8 V | Head board |
| Microphone | TDK T5848 (MMICT5848-00-012) | I2S MEMS, 1.62 to 1.98 V supply, 3.5 × 2.65 × 0.98 mm | Head board, away from the trunk speaker |
| Audio amplifier | Analog Devices MAX98357A | I2S class D, 3.2 W into 4 Ω at 5 V, 2.5 to 5.5 V supply | Carrier board |
| Speaker | Same Sky CMS-18132-18SP | 8 Ω, 1 W, 18 × 13 × 2.5 mm, 1.9 g | Trunk shell, printed back cavity |
| Servo bus buffer | 74LVC2G241, three units (TI SN74LVC2G241 or Nexperia 74LVC2G241) | Dual buffer with separate output enables, 1.65 to 5.5 V, 5 V tolerant inputs | Carrier board |
| Servo rail regulator | TI TPS56C215 | 12 A synchronous buck, up to 17 V input, 0.6 to 5.5 V output, 3.5 × 3.5 mm QFN | Carrier board |
| Compute rail regulator | TI TPS62933 | 3 A synchronous buck, 3.8 to 30 V input | Carrier board |
| Input protection and switch | TI TPS25982 eFuse | 2.7 to 24 V, current limit adjustable 2 to 15 A, 2.7 mΩ, current monitor output | Carrier board |
| Battery cells | 2 × Molicel INR-18650-P28A | 2800 mAh typical, 3.6 V nominal, 35 A maximum discharge | Battery cartridge |
| Cell protection | ABLIC S-8252 with dual N channel MOSFET | 2 series cells: overcharge, overdischarge, discharge and charge overcurrent | Cartridge board |
| Charger | TI BQ25887 | 2S boost charger with cell balancing, 3.9 to 6.2 V input from USB-C, 2 A charge current | Carrier board |
| Servo connectors | JST B3B-EH-A headers, EHR-03 housings | Same family as the servos | Carrier board and harness |

Passive and glue parts (1.8 V and 3.3 V LDOs, I2C and I2S level translators, cartridge MOSFETs, backup fuse, USB-C receptacle) are chosen during schematic capture from parts with KiCad library footprints and listed in the BOM.

### 2.3 Battery

The battery is a tool-free cartridge holding two Molicel INR-18650-P28A cells in series (2S), giving 7.2 V nominal, 8.4 V when full and 20.6 Wh (2 × 10.3 Wh typical). This replaces the NP-F550 type pack in DCK-00, because no NP-F pack sold today has a manufacturer datasheet.

The cartridge carries the S-8252 protection board, a 10 kΩ NTC thermistor and four blade contacts: B+, mid-cell, B− and thermistor. The mid-cell contact lets the BQ25887 balance the cells, so the pack charges inside the robot from a USB-C port. The robot is powered off while charging, because the BQ25887 has no power path. Spare cartridges charge in the robot or on any 2S balance charger.

The cartridge mass is allocated at 105 g: two cells at about 46 g each (a retailer figure, since Molicel's sheet does not list mass) plus 13 g for the board, contacts and printed housing.

### 2.4 Sources

* XL330-M288-T e-Manual: https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/
* XC330-M288-T e-Manual: https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/
* Radxa ZERO 3 camera support: https://docs.radxa.com/en/zero/zero3/accessories/camera
* Radxa Camera 8M 219: https://docs.radxa.com/en/accessories/camera/camera-8m-219
* BNO085 (DigiKey): https://www.digikey.com/en/products/detail/ceva-technologies-inc/BNO085/9445941
* VL53L8CX (ST, DS14161): https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
* T5848 (TDK): https://invensense.tdk.com/products/digital/t5848/
* MAX98357A (Analog Devices): https://www.analog.com/en/products/max98357a.html
* CMS-18132-18SP datasheet: https://cdn.eicom.ru/media/PDF/8020010.pdf
* 74LVC2G241 (Nexperia): https://www.nexperia.com/products/logic/buffers-drivers-transceivers/buffers-inverters-drivers/74LVC2G241GD.html
* TPS56C215: https://www.ti.com/product/TPS56C215
* TPS62933: https://www.ti.com/product/TPS62933
* TPS25982: https://www.ti.com/product/TPS25982
* BQ25887: https://www.ti.com/product/BQ25887
* S-8252 (ABLIC): https://www.ablic.com/en/semicon/datasheets/power-management-ic/lithium-ion-battery-protection-ic/s-8252/
* INR-18650-P28A data sheet: https://www.imrbatteries.com/content/molicel_p28a.pdf

### 2.5 Parts rejected

| Part | Reason |
|---|---|
| TDK ICS-43434 microphone | Past its June 2026 last time buy date at DigiKey |
| Knowles SPH0645LM4H-B microphone | Listed as obsolete |
| VL53L5CX depth sensor | Superseded by the VL53L8CX, which has lower power and better ambient light performance |
| NP-F550 type pack | No pack sold today has a manufacturer datasheet (rule 5) |

## 3. Block diagram and power tree

### 3.1 Power tree

```
2S cartridge (6.0 to 8.4 V, S-8252 protection)
  └─ blade contacts ─ main switch ─ TPS25982 eFuse (15 A limit, current monitor to ADC)
        ├─ TPS56C215 ── 5.0 V SERVO rail, 12 A ── 3 servo chains (left leg, right leg, neck and head)
        │                 EN = torque enable (SBC GPIO, held low by default)
        └─ TPS62933 ─── 5.0 V COMPUTE rail, 3 A
                          ├─ Radxa ZERO 3W (header 5 V pins) ── camera (CSI)
                          ├─ MAX98357A ── speaker
                          ├─ 3.3 V LDO (TLV75533) ── BNO085, bus buffers, ADC, I2C pull-ups
                          └─ head board link (5 V) ── local 3.3 V and 1.8 V LDOs for the VL53L8CX and T5848
USB-C (5 V) ── BQ25887 charger ── cartridge (balanced through the mid-cell contact)
```

The servo regulator's enable pin is the hardware torque disable line. It defaults low through a pull-down, so the servo rail stays off until the runtime raises it. The safety layer drops it on a fall, a current fault or a watchdog timeout, and the main switch removes it physically.

### 3.2 Current budget

| Rail | Load | Current | Basis |
|---|---|---|---|
| Servo 5.0 V | Six leg servos stalling at once (hip pitch, knee, ankle) | 10.8 A | 6 × 1.80 A, e-Manual |
| | Nine XL330 at standby | 0.15 A | 9 × 17 mA, e-Manual |
| | **Design peak** | **11.0 A**, regulator 12 A | |
| Compute 5.0 V | Radxa ZERO 3W with camera | 2.0 A | Radxa's recommended supply rating |
| | MAX98357A driving 1 W | 0.25 A | 1 W ÷ 5 V ÷ 0.92 efficiency, ADI figure at 1 W into 8 Ω |
| | IMU, ToF, mic, buffers, LDO losses | 0.15 A | Allocation, replaced after schematic capture |
| | **Design peak** | **2.4 A**, regulator 3 A | |
| Battery input | Both rails at design peak, 90 % converter efficiency (assumed), cells at 6.0 V | 12.4 A | (5 × 11.0 + 5 × 2.4) ÷ 0.9 ÷ 6.0; eFuse limit 15 A, cells rated 35 A |

Average walking current and runtime are set in Phase 6 from simulated servo current. A 20.6 Wh pack meets the 45 minute target if average power stays below about 25 W, which is 20.6 Wh × 0.9 efficiency × 60/45.

### 3.3 Computer header allocation

| Header pin | Function | Use |
|---|---|---|
| 3, 5 | UART3 RX, TX | Servo chain 1, left leg |
| 16, 18 | UART4 RX, TX | Servo chain 2, right leg |
| 33, 32 | UART5 RX, TX | Servo chain 3, neck and head |
| 7, 11, 15 | GPIO | Bus direction for chains 1, 2, 3 |
| 27, 28 | I2C4 SDA, SCL | BNO085, BQ25887 (trunk) |
| 29, 31 | I2C5 SCL, SDA | VL53L8CX (head board, level shifted) |
| 12, 35, 40, 38 | I2S3 SCLK, LRCK, SDO, SDI | Amplifier (SDO) and microphone (SDI), shared clocks |
| 36 | GPIO | Torque enable (servo regulator EN) |
| 22, 37 | GPIO | BNO085 interrupt, reset |
| 19, 23 | GPIO | VL53L8CX interrupt, LPn |
| 21, 24 | GPIO | Amplifier shutdown, charger interrupt |
| 2, 4 / 6, 9, 14, 20, 25, 30, 34, 39 | 5 V / GND | Power in from the compute rail |

UART2 (pins 8 and 10) remains the debug console. Pins 3 and 5 carry I2C pull-up resistors on the ZERO 3W, which is harmless for a UART because the line idles high.

## 4. Carrier board

### 4.1 Board

| Item | Value |
|---|---|
| Outline | 76 × 62 mm rectangle, fits the 90 × 80 mm trunk section |
| Stackup | 4 layers: F.Cu signals and local pours, In1 GND plane, In2 servo rail plane (below the computer) and signals, B.Cu signals and power pours |
| Computer | Radxa ZERO 3W above the board on a 2 × 20 socket; the four M2.5 holes follow Radxa's 57.8 × 22.9 mm pattern (RK10) and double as the trunk standoffs |
| Parts | 121 footprints, all on the top side |
| Net classes | Default 0.20 mm track and 0.15 mm clearance; Power 0.30 mm; HighCurrent 0.40 mm escapes into pours |
| High current paths | B.Cu and F.Cu pours for VBAT (battery entry to eFuse) and VSYS (eFuse to both regulators), In2 plane for the 5.0 V servo rail, stitched with vias |
| Verification | KiCad ERC: one warning (amplifier exposed pad typed "unspecified" in the KiCad symbol). KiCad DRC with schematic parity and all severities: 0 violations, 0 unconnected pads, 0 footprint errors |
| 3D model | `ecad/carrier/carrier.step`; KiCad ships no body for the XT30PW-M (pads only; modelled in Phase 3), the RNN package, the 1.23 mm pad TQFN-16 or the RGE0024M; for those three, KiCad bodies of the same package outline stand in (`MODEL_SUBST` in `ecad/gen/pcb.py`) |

Connector placement follows the trunk: battery (XT30), cell sense, main switch and debug UART on the left edge; USB-C charge port, speaker and head board link on the right edge; six servo ports along the bottom edge, two per chain.

### 4.2 How the board is produced

The board is generated, not drawn, so every revision is reproducible from the repository:

1. `ecad/gen/carrier.py` defines the circuit with values traced to the datasheets cited in sections 2 and 3 and writes `ecad/carrier/carrier.kicad_sch`; nets connect by label so the schematic reads as a netlist.
2. `ecad/gen/pcb.py` loads the footprints from the netlist, places connectors and ICs at fixed positions and places every passive next to the IC pin it serves, then adds the planes and pours.
3. `ecad/gen/route.py` autoroutes with Freerouting, adds the power pours and stitching vias; `cleanup.py` removes vias that DRC reports as dangling.
4. `ecad/gen/build_carrier.sh` runs the whole chain, then ERC, DRC, STEP export (`ecad/carrier/carrier.step` for Fusion) and renders.

A designer reviewing the layout in KiCad should still check the switching loops of the two buck converters and the charger, which the autorouter does not optimise for, before the board is released for fabrication in Phase 8.

## 5. Harness

### 5.1 Topology

Each leg uses both ports of its chain. Port A feeds hip yaw, hip roll and hip pitch; port B feeds knee and ankle. Both branches share the chain's data line. The split keeps each JST EH contact within its 3 A rating in normal use: branch A draws at most 4.7 A only if all three of its servos stall together (1.47 + 1.47 + 1.80 A, e-Manual), and branch B 3.6 A. A full leg on one connector would see 8.3 A. The neck chain runs neck pitch, head pitch, head yaw, head roll and beak in series from port J11, with J12 spare. The head board cable runs beside the neck servo cables. The camera FPC runs from the computer directly to the head.

### 5.2 Cables

Generated by `analysis/harness/harness.py` from the link lengths and joint limits in `analysis/sizing/params.py`.

| Cable | From | To | Joints crossed | Straight (mm) | Service loops (mm) | Cut length (mm) |
|---|---|---|---|---|---|---|
| L1 | carrier J7 (chain 1) | left hip yaw servo | none | 100 | none | 110 |
| L2 | left hip yaw servo | left hip roll servo | hip yaw | 36 | 12 | 60 |
| L3 | left hip roll servo | left hip pitch servo | hip roll | 32 | 9.6 | 55 |
| L4 | carrier J8 (chain 1) | left knee servo | hip yaw, hip roll, hip pitch | 184 | 12, 9.6, 38.4 | 255 |
| L5 | left knee servo | left ankle servo | knee | 70 | 27.6 | 110 |
| R1 to R5 | right leg, chain 2 (J9, J10) | as L1 to L5 | as left | as left | as left | as left |
| N1 | carrier J11 (chain 3) | neck pitch servo | none | 80 | none | 90 |
| N2 | neck pitch servo | head pitch servo | neck pitch | 45 | 30 | 90 |
| N3 | head pitch servo | head yaw servo | head pitch | 34 | 36 | 80 |
| N4 | head yaw servo | head roll servo | head yaw | 32 | 69.6 | 115 |
| N5 | head roll servo | beak servo | head roll | 40 | 10.8 | 65 |
| HB | carrier J14 | head board | neck pitch, head pitch, head yaw, head roll | 141 | 30, 36, 69.6, 10.8 | 300 |

Servo cables: JST EHR-03 housings at both ends with SEH-001T-P0.6 crimps (the servo's own connector system, e-Manual), 3 × 22 AWG high flex silicone wire, pin 1 GND, pin 2 5.0 V, pin 3 DATA. Head board cable: JST GHR-10V-S housings with SSHL-002T-P0.2 crimps, 10 × 28 AWG high flex silicone wire, pinned per carrier J14.

Each length is the straight run plus a service loop for every joint the cable crosses, plus 10 mm slack. A service loop is 12 mm (about half a servo depth from the joint axis) times the joint's full travel. Runs inside the trunk are allocations (80 mm per leg, 60 mm neck, 70 mm head board), and the straight runs add 20 mm for routing around the servo bodies. The Phase 3 CAD replaces these assumptions with measured routes, and the script recomputes every length.

## 6. Open risks

| ID | Risk | Mitigation |
|---|---|---|
| RK5 | Closed. The Radxa ZERO 3W product brief states that 5 V can be supplied through header pins 2 and 4, which is how the carrier powers it | Source: https://dl2.radxa.com/zero3/docs/hw/3w/radxa_zero_3w_product_brief.pdf |
| RK6 | Hip pitch walking demand rose to 38.4 % of stall (limit 40 %) with the 105 g cartridge | Mount the cartridge low and centred over the hip pitch axes in CAD; recheck with Fusion mass properties |
| RK7 | Cell mass is a retailer figure | Weigh or source a manufacturer figure before the BOM is frozen |
| RK8 | Head yaw travels 5.8 rad. Cables N4 and HB need 70 mm service loops there, and the camera's 150 mm FPC cannot follow that travel as a free loop | In Phase 3, route cables along the yaw axis and coil the FPC as a clock spring around it, or reduce head yaw travel; recompute the harness from CAD |
| RK10 | Closed. Hole and header positions taken from Radxa's DXF (radxa_zero_3w_v1110_top.dxf): four Ø2.82 mm holes on a 57.8 × 22.9 mm pattern, header centre 3.325 mm from the long edge. The Pi Zero values first assumed were up to 0.175 mm off and are replaced | Source: https://dl.radxa.com/zero3/docs/hw/3w/radxa_zero_3w_2d_dxf.zip |
| RK9 | Head board (VL53L8CX, T5848) is not yet designed: the ST and TDK datasheets could not be retrieved automatically (ST blocks scripted downloads, TDK requires a form) | Download both datasheets manually, then design the head board; the carrier already provides its connector (J14) |
