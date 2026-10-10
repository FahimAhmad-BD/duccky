"""Left leg layout in the leg frame (mm): origin on the hip yaw axis at the yaw horn face,
x forward, y outward (left), z up. All joints at zero (straight leg).

Arrangement and offsets follow analysis/layout/leg_layout.py and analysis/sizing/params.py:
    hip yaw   vertical in the trunk, horn down, horn face at z = 0
    hip roll  horizontal under the yaw horn, axis along x at z = -yaw_to_roll, horn forward
    hip pitch hanging below the roll servo, axis along y at z = -(yaw_to_roll + roll_to_pitch),
              horn outward, horn end up
    knee      in the thigh, axis along y, thigh below the pitch axis, horn outward, horn end down
    ankle     lying in the foot, axis along y, case pointing forward, horn outward
Each servo pose is (origin, x axis, y axis, z axis) of its local frame (servo.py) in the leg frame.
"""
import runpy

import adsk.core

import dk
import servo

PARAMS = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\analysis\sizing\params.py"


def geometry():
    p = runpy.run_path(PARAMS)
    L = p["LEG"]
    mm = lambda v: v * 1000.0
    g = {"yaw_to_roll": mm(L["yaw_to_roll"]), "roll_to_pitch": mm(L["roll_to_pitch"]),
         "thigh": mm(L["thigh"]), "shank": mm(L["shank"]), "ankle_to_sole": mm(L["ankle_to_sole"]),
         "foot": [mm(v) for v in L["foot"]], "foot_ankle_x": mm(L["foot_ankle_x"]), "hip_y": mm(L["hip_y"])}
    g["z_roll"] = -g["yaw_to_roll"]
    g["z_pitch"] = g["z_roll"] - g["roll_to_pitch"]
    g["z_knee"] = g["z_pitch"] - g["thigh"]
    g["z_ankle"] = g["z_knee"] - g["shank"]
    g["z_sole"] = g["z_ankle"] - g["ankle_to_sole"]
    return g


def servo_poses(g):
    half = servo.D / 2            # 11.5: centres the case depth on the joint line
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    neg = lambda v: tuple(-c for c in v)
    return {
        "hip_yaw":   ("XL330-M288-T", (0, 0, servo.HORN_H), Y, X, neg(Z)),
        "hip_roll":  ("XL330-M288-T", (half, 0, g["z_roll"]), neg(Z), Y, X),
        "hip_pitch": ("XC330-M288-T", (0, half, g["z_pitch"]), neg(X), Z, Y),
        "knee":      ("XC330-M288-T", (0, half, g["z_knee"]), X, neg(Z), Y),
        "ankle":     ("XC330-M288-T", (0, half, g["z_ankle"]), neg(Z), neg(X), Y),
    }


def matrix(origin, xa, ya, za):
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(dk.P(*origin), adsk.core.Vector3D.create(*xa),
                              adsk.core.Vector3D.create(*ya), adsk.core.Vector3D.create(*za))
    return m
