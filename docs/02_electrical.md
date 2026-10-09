# Duccky v1.0: Electrical Architecture

**Document:** DCK-02 · **Revision:** draft · **Phase:** 2 · **Status:** In progress

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

To be completed in Phase 2.

## 3. Block diagram and power tree

To be completed in Phase 2.

## 4. Carrier board

To be completed in Phase 2.

## 5. Harness

To be completed in Phase 2.
