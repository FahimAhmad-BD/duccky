"""Robot level layout in the robot frame (mm): x forward, y left, z up, origin on the robot
centre line at the hip yaw horn faces (z = 0). Leg frames sit at y = +-hip_y.

Trunk packaging (Phase 3):
  floor            z = 1 to 3; hip yaw servos stand on it, horn faces at z = 0 below it
  battery          2S cartridge lying between the yaw servos (cells along x), low over the hips
  carrier board    horizontal above the yaw servos; board x along robot x (right edge with
                   USB-C, speaker and head connectors at the front), computer on top
  neck             neck pitch servo at the front top
"""
import os

import adsk.core

import dk
import leg

CARRIER_STEP = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\ecad\carrier\carrier_mech.step"

FLOOR_Z0, FLOOR_Z1 = 1.0, 3.0
BOARD_W, BOARD_H, BOARD_T = 76.0, 62.0, 1.6
BOARD_Z = 31.0                         # board underside: yaw servo top (26) + clamp plate (3) + gap
CELL_D, CELL_L = 18.6, 65.2            # Molicel INR-18650-P28A (retailer size, DCK-02 RK7)
CART_WALL = 2.0
TRUNK = (90.0, 80.0, 70.0)             # outer envelope from the sizing model (x, y, z)


def place_board(occ):
    """KiCad's STEP is right handed (STEP y = -KiCad y) with the top side at +z, which
    matches the robot frame with board x along robot x. Translate so the board outline is
    centred on the robot axis with its underside at BOARD_Z."""
    bb = occ.boundingBox
    t = adsk.core.Matrix3D.create()
    cx = (bb.minPoint.x + bb.maxPoint.x) / 2
    cy = (bb.minPoint.y + bb.maxPoint.y) / 2
    t.translation = adsk.core.Vector3D.create(-cx, -cy, dk.cm(BOARD_Z) - bb.minPoint.z)
    occ.transform = t
    return occ


def cartridge_box():
    """Outer envelope of the battery cartridge (x0, x1, y0, y1, z0, z1)."""
    length = CELL_L + 2 * CART_WALL + 4.0          # contacts and spring at the ends
    width = 2 * CELL_D + 3 * CART_WALL
    height = CELL_D + 2 * CART_WALL
    x0 = -length / 2 - 5.0                         # biased back so the slot opens at the rear
    return (x0, x0 + length, -width / 2, width / 2, FLOOR_Z1, FLOOR_Z1 + height)


def mirror_pose(pose):
    """Right leg servo pose from a left leg pose: mirror y, then flip local x to keep the
    frame right handed (the servo case is symmetric across its width)."""
    model, o, xa, ya, za = pose
    my = lambda v: (v[0], -v[1], v[2])
    return model, my(o), tuple(-c for c in my(xa)), my(ya), my(za)


def leg_matrix(pose, side):
    """Servo matrix in the robot frame for side +1 (left) or -1 (right)."""
    g_hip_y = leg.geometry()["hip_y"]
    model, o, xa, ya, za = pose if side > 0 else mirror_pose(pose)
    o = (o[0], o[1] + side * g_hip_y, o[2])
    return model, leg.matrix(o, xa, ya, za)


def import_step(parent, path, name):
    """Import a STEP file as a new component under parent and place it."""
    im = dk.app.importManager
    opts = im.createSTEPImportOptions(path)
    before = parent.occurrences.count
    im.importToTarget(opts, parent)
    occ = parent.occurrences.item(parent.occurrences.count - 1) if parent.occurrences.count > before else None
    if occ:
        occ.component.name = name
    return occ
