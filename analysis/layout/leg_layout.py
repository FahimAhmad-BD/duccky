"""Leg layout from real servo geometry (Phase 3).

The Phase 0 joint offsets in analysis/sizing/params.py were placeholders. This script
derives the offsets the X330 servo bodies actually allow, with clearance for each
joint's full travel, for the chosen arrangement:

  hip yaw   servo vertical in the trunk, horn down
  hip roll  servo lying horizontal under the yaw horn (axis along x, case pointing inward),
            fixed to the yaw bracket; its horn and idler carry the roll U-bracket
  hip pitch servo hanging below the roll servo in the roll U-bracket (axis along y, horn end up)
  knee      servo in the thigh, horn end down; the shank U-bracket hangs from it
  ankle     servo lying in the foot (axis along y, case pointing forward); the shank's lower
            U-bracket drives it, so no servo body sits below the ankle axis inside the shank

Servo data (ROBOTIS X330 drawing): case 20 x 34 x 23 mm, axis 9.5 mm from the horn end,
horn and idler bosses 3 mm. Printed plate thickness PLATE, running clearance GAP.

Run: python leg_layout.py   prints the derived offsets and the resulting standing height.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sizing"))
import params as P  # noqa: E402

W, L, AXIS_END = 20.0, 34.0, 9.5      # servo width, length, axis to horn end
PLATE, GAP = 3.0, 1.0                 # printed wall thickness, running clearance (mm)
ROLL_TRAVEL = max(abs(v) for v in P.LEG["lim_hip_roll"])


def yaw_to_roll():
    # Roll servo lies horizontal, width (20 mm) vertical, so its top face is W/2 above the
    # roll axis. Yaw horn face -> bracket plate -> gap -> roll servo top.
    return PLATE + GAP + W / 2


def roll_to_pitch():
    # The roll U-bracket's bottom plate rotates about the roll axis under the fixed roll
    # servo (bottom face W/2 below the axis). A plate edge at half width b = (23 + 2 mm) / 2
    # (pitch servo depth plus side walls) and depth h below the axis rises to
    # h cos(t) - b sin(t) at roll t; it must stay below the servo bottom plus GAP.
    b = (23.0 + 2.0) / 2
    t = ROLL_TRAVEL
    h = (W / 2 + GAP + b * math.sin(t)) / math.cos(t)
    # Pitch servo hangs below that plate, horn end up: axis AXIS_END below its top face.
    return h + PLATE + AXIS_END


def ankle_to_sole():
    # Ankle servo lies in the foot with its width vertical: case bottom W/2 below the axis,
    # then the sole plate.
    return W / 2 + PLATE


def main():
    y2r, r2p, a2s = yaw_to_roll(), roll_to_pitch(), ankle_to_sole()
    old = (P.LEG["yaw_to_roll"] * 1000, P.LEG["roll_to_pitch"] * 1000, P.LEG["ankle_to_sole"] * 1000)
    print(f"yaw_to_roll    {y2r:6.1f} mm   (Phase 0 placeholder {old[0]:.0f})")
    print(f"roll_to_pitch  {r2p:6.1f} mm   (Phase 0 placeholder {old[1]:.0f})")
    print(f"ankle_to_sole  {a2s:6.1f} mm   (Phase 0 placeholder {old[2]:.0f})")
    added = (y2r - old[0]) + (r2p - old[1]) + (a2s - old[2])
    print(f"leg stack grows by {added:.1f} mm over Phase 0")
    return y2r, r2p, a2s


if __name__ == "__main__":
    main()
