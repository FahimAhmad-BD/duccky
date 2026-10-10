"""Neck and head layout in the robot frame (mm).

  neck pitch  XL330 fixed at the trunk's front top, lying, axis along y, horn outward (+y),
              case pointing back over the computer
  neck link   double U from the neck pitch horn/idler, running forward (NECK_ANGLE above horizontal) to the
              head pitch horn/idler NECK_LEN away: the head base stays outside the neck servo's
              swept radius (26.5 mm), so the neck can turn far without collision
  head base   head pitch servo (lying, case pointing forward) with the head yaw servo standing
              on it, horn up, its 34 mm length along x so it stays within +-10 mm in y (inside
              the neck link plates) and its axis directly above the head pitch axis
  head roll   XL330 lying on the yaw output, axis along x, horn forward
  head        shell on the roll horn and idler, carrying camera, depth and mic board
  beak        XL330 standing in the head front, horn end down; the lower mandible hangs from its
              horn and idler and opens downward
Poses are (model, origin, x axis, y axis, z axis) of each servo's local frame (servo.py).
"""
import math

import servo

NECK_X, NECK_Z = 30.0, 58.0       # neck pitch axis; its case runs back to x = 5.5, above the computer
NECK_LEN = 38.0                   # neck pitch axis to head pitch axis
NECK_ANGLE = math.radians(0.0)    # neck link horizontal, forward: keeps the head low (height limit 30 cm)
GAP, PLATE = 1.0, 3.0
YAW_HUB = 1.5                     # yaw link hub height on the horn
HEAD_WALL = 2.0                   # head shell wall (headparts.head_shell)


def layout():
    x_hp = NECK_X + NECK_LEN * math.cos(NECK_ANGLE)
    z_hp = NECK_Z + NECK_LEN * math.sin(NECK_ANGLE)
    x_yaw = x_hp                                                # yaw axis above the head pitch axis
    z_yaw_case = z_hp + servo.W / 2 + PLATE                     # yaw case bottom on a plate over the pitch case
    z_yaw_face = z_yaw_case + servo.D
    z_yaw_horn = z_yaw_face + servo.HORN_H
    # yaw link: 1.5 mm hub on the horn, then a 3 mm plate above the collar screw heads
    z_roll = z_yaw_horn + YAW_HUB + PLATE + GAP + servo.W / 2
    # Beak servo stands in the head front, horn end down, its axis at the head floor level
    roll_plate_out = servo.D / 2 + servo.HORN_H + PLATE                # 17.5: roll horn plate outer face
    x_beak = x_yaw + roll_plate_out + GAP + servo.W / 2                 # case clear of the roll horn plate
    z_beak = z_yaw_horn + 6.0 + HEAD_WALL + servo.AXIS_FROM_END         # case bottom on the head floor
    return {"x_neck": NECK_X, "z_neck": NECK_Z, "x_head_pitch": x_hp, "z_head_pitch": z_hp,
            "x_yaw": x_yaw, "z_yaw_face": z_yaw_face, "z_yaw_horn": z_yaw_horn, "z_roll": z_roll,
            "x_beak": x_beak, "z_beak": z_beak}


def servo_poses(h):
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    neg = lambda v: tuple(-c for c in v)
    half = servo.D / 2
    return {
        "neck_pitch": ("XL330-M288-T", (h["x_neck"], half, h["z_neck"]), Z, X, Y),
        "head_pitch": ("XL330-M288-T", (h["x_head_pitch"], half, h["z_head_pitch"]), neg(Z), neg(X), Y),
        "head_yaw":   ("XL330-M288-T", (h["x_yaw"], 0, h["z_yaw_face"]), Y, neg(X), Z),
        "head_roll":  ("XL330-M288-T", (h["x_yaw"] + half, 0, h["z_roll"]), Z, neg(Y), X),
        "beak":       ("XL330-M288-T", (h["x_beak"], half, h["z_beak"]), X, neg(Z), Y),
    }
