"""Printed neck and head parts in the robot frame (mm), around the servo layout of head.py.

Same rules as the leg (legparts.py): servos sit in pockets screwed through far end case holes,
outputs are plates on the horn and the FPX330-H101 idler (4 x M2 on a 12 mm circle), pocket
walls at |s| = 11.5 to 13.5 mm and output plates at 14.5 to 17.5 mm along the joint axis.

  neck mount   fixed to the trunk: pocket for the neck pitch servo (far end at the back) hung from
               a crossbar behind the neck axis, which rests on posts up from the trunk side walls
  neck plates  two separate side plates (horn side, idler side) from the neck pitch servo to the
               head pitch servo; any bridge between them would meet the board, the trunk or the
               head somewhere in the 2.2 rad neck sweep, and the two servos close the frame
  head base    pocket for the head pitch servo (far end at the front), a 3 mm spacer plate on it,
               and a collar over the yaw servo's top face screwed into its four horn face holes
  yaw link     hub on the yaw horn and a plate carrying the head roll servo pocket
  head shell   horn and idler plates on the roll servo and a shell whose cavity is the roll
               servo envelope swept over the roll range
"""
import math

import adsk.core
import adsk.fusion

import dk
import head as H
import prim
import servo
from legparts import (CBORE_D, CBORE_H, FACE, GAP, HUB_CLEAR, OUT0, OUT1, PLATE_R, POCK1,
                      SCREW_D, T, WALL, _screw, _union, bolt_holes, output_plates)

TRUNK_TOP = 72.0
SIDE_Y0, SIDE_Y1 = 45.5, 48.0          # trunk side walls (trunk.py)


def neck_mount(comp, h):
    xn, zn = h["x_neck"], h["z_neck"]
    x_far = xn - (servo.L - servo.AXIS_FROM_END)                  # 5.5, case back end
    x_hub = xn - HUB_CLEAR - GAP                                  # walls stop before the hub zone
    z0, z1 = zn - servo.W / 2 - 2.0, zn + servo.W / 2 + 2.0
    parts = []
    for s in (1, -1):
        parts.append(prim.box(comp, x_far - WALL, x_hub, s * FACE, s * POCK1, z0, TRUNK_TOP))
        parts.append(prim.box(comp, x_far - WALL, x_far + 6.0, s * SIDE_Y0, s * SIDE_Y1, 29.0, TRUNK_TOP))   # posts
    parts.append(prim.box(comp, x_far - WALL, x_far, -POCK1, POCK1, z0, TRUNK_TOP))                       # end wall
    parts.append(prim.box(comp, x_far - WALL, x_far + 6.0, -SIDE_Y1, SIDE_Y1, TRUNK_TOP - T, TRUNK_TOP))  # crossbar
    main = _union(comp, parts)
    tools = []
    xh = xn - (servo.L - servo.AXIS_FROM_END) + 2.0               # far end hole row, 7.5
    for dz in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "y", (xh, 0, zn + dz), POCK1, 1, WALL + 3.0)
        tools += _screw(comp, "y", (xh, 0, zn + dz), -POCK1, -1, WALL + 4.5)
    prim.cut(comp, main, tools)
    main.name = "neck mount"
    return main


def neck_plate(comp, h, side):
    """side +1: horn side plate; -1: idler side plate."""
    xn, xh, z = h["x_neck"], h["x_head_pitch"], h["z_neck"]
    s0, s1 = sorted((side * OUT0, side * OUT1))
    parts = [prim.cylinder(comp, "y", (xn, 0, z), PLATE_R, s0, s1),
             prim.cylinder(comp, "y", (xh, 0, z), PLATE_R, s0, s1),
             prim.box(comp, xn, xh, s0, s1, z - 7.0, z + 7.0)]
    main = _union(comp, parts)
    tools = bolt_holes(comp, "y", (xn, 0, z), sides=(side,)) + bolt_holes(comp, "y", (xh, 0, z), sides=(side,))
    prim.cut(comp, main, tools)
    main.name = "neck plate " + ("horn side" if side > 0 else "idler side")
    return main


def head_base(comp, h):
    xh, zh = h["x_head_pitch"], h["z_head_pitch"]
    x_front = xh + (servo.L - servo.AXIS_FROM_END)                # 92.5, pitch case far end
    x_back = xh - servo.AXIS_FROM_END                              # 58.5
    z_top = zh + servo.W / 2                                       # 68, pitch case top
    z_collar0 = h["z_yaw_face"]                                    # yaw top face (94)
    z_collar1 = z_collar0 + 2.0
    x_hub = xh + HUB_CLEAR + GAP
    parts = [prim.box(comp, x_back, x_front, -POCK1, POCK1, z_top, z_top + T)]        # spacer plate
    for s in (1, -1):
        parts.append(prim.box(comp, x_hub, x_front + WALL, s * FACE, s * POCK1, zh - servo.W / 2 - 2.0, z_top))
        parts.append(prim.box(comp, x_back, x_front + WALL, s * FACE, s * POCK1, z_top, z_collar1))
    parts.append(prim.box(comp, x_front, x_front + WALL, -POCK1, POCK1, zh - servo.W / 2 - 2.0, z_collar1))
    parts.append(prim.box(comp, x_back, x_front + WALL, -POCK1, POCK1, z_collar0, z_collar1))       # collar
    main = _union(comp, parts)
    tools = [prim.cylinder(comp, "z", (xh, 0, 0), HUB_CLEAR, z_collar0 - 0.5, z_collar1 + 0.5)]      # yaw horn
    # Head pitch servo far end screws (y axis)
    xr = xh + (servo.L - servo.AXIS_FROM_END) - 2.0
    for dz in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "y", (xr, 0, zh - dz), POCK1, 1, WALL + 3.0)
        tools += _screw(comp, "y", (xr, 0, zh - dz), -POCK1, -1, WALL + 4.5)
    # Collar screws into the yaw servo's four horn face holes (z axis, from the top)
    for lx, ly in servo.CASE_HOLES:
        x, y = xh - ly, lx                                         # yaw pose: local y -> -x, local x -> +y
        tools.append(prim.cylinder(comp, "z", (x, y, 0), SCREW_D / 2, z_collar0 - 3.0, z_collar1 + 0.5))
    prim.cut(comp, main, tools)
    main.name = "head base"
    return main


def yaw_link(comp, h):
    xy, zr = h["x_yaw"], h["z_roll"]
    z0 = h["z_yaw_horn"]
    z_hub1 = z0 + H.YAW_HUB
    z_plate1 = z_hub1 + T
    half = servo.D / 2
    yfar = -(servo.Y_BOT)                                          # roll case far end at +24.5
    parts = [prim.cylinder(comp, "z", (xy, 0, 0), 8.6, z0, z_hub1),
             prim.box(comp, xy - half - WALL, xy + half + WALL, -12.0, yfar + WALL, z_hub1, z_plate1)]
    for s in (1, -1):
        x0, x1 = sorted((xy + s * half, xy + s * (half + WALL)))
        parts.append(prim.box(comp, x0, x1, 12.0, yfar + WALL, z_plate1, zr + servo.W / 2))
    parts.append(prim.box(comp, xy - half - WALL, xy + half + WALL, yfar, yfar + WALL, z_plate1, zr + servo.W / 2))
    main = _union(comp, parts)
    tools = prim.bolt_circle(comp, "z", (xy, 0, 0), z0 - 0.5, z_plate1 + 0.5, pcd=servo.HORN_PCD, d=SCREW_D)
    tools.append(prim.cylinder(comp, "z", (xy, 0, 0), 1.6, z0 - 0.5, z_plate1 + 0.5))
    yh = yfar - 2.0
    for dz in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "x", (0, yh, zr + dz), xy + half + WALL, 1, WALL + 3.0)
        tools += _screw(comp, "x", (0, yh, zr + dz), xy - half - WALL, -1, WALL + 4.5)
    prim.cut(comp, main, tools)
    main.name = "yaw link"
    return main


def _rotated_box(comp, box, axis_point, angle):
    """Box body rotated about the x axis through axis_point by angle (rad)."""
    return _rotate_x(comp, prim.box(comp, *box), axis_point, angle)


def _rotate_x(comp, b, axis_point, angle):
    """Rotate body b about the x axis through axis_point by angle (rad)."""
    if abs(angle) < 1e-9:
        return b                                                   # Fusion rejects an identity move
    m = adsk.core.Matrix3D.create()
    m.setToRotation(angle, adsk.core.Vector3D.create(1, 0, 0), dk.P(*axis_point))
    mf = comp.features.moveFeatures
    mi = mf.createInput2(dk.collection([b]))
    mi.defineAsFreeMove(m)
    mf.add(mi)
    return b


def head_shell(comp, h, roll_range=0.45, wall=2.5):
    """Horn and idler plates on the roll servo and a box shell around it. The cavity is the roll
    servo plus yaw link envelope swept over the roll range (five poses), plus GAP."""
    xy, zr = h["x_yaw"], h["z_roll"]
    half = servo.D / 2
    yfar = -(servo.Y_BOT) + WALL                                   # 26.5 incl. the pocket end wall
    env = (xy - half - WALL - GAP, xy + half + WALL + GAP, -12.0 - GAP, yfar + GAP,
           h["z_yaw_horn"] - GAP, zr + servo.W / 2 + GAP)
    # Outer shell: bounds of the swept envelope plus the wall
    reach = max(math.hypot(yy, zz - zr) for yy in (env[2], env[3]) for zz in (env[4], env[5]))
    top = zr + reach * 1.0 + wall
    sx0, sx1 = xy - OUT1, xy + OUT1 + 22.0
    sy, sz0 = reach + wall, h["z_yaw_horn"] + 6.0
    shell = prim.box(comp, sx0, sx1, -sy, sy, sz0, top)
    # Hollow to a uniform wall, then add the roll plates and their arms down to the bottom wall
    inner = prim.box(comp, sx0 + wall, sx1 - wall, -sy + wall, sy - wall, sz0 + wall, top - wall)
    prim.cut(comp, shell, [inner])
    parts = output_plates(comp, "x", (xy, 0, zr), PLATE_R, sz0, PLATE_R)
    main = _union(comp, [shell] + parts)
    tools = []
    for k in range(5):
        tools.append(_rotated_box(comp, env, (xy, 0, zr), -roll_range + k * roll_range / 2))
    # Keep clear of the head base, which stays put while the head yaws and rolls: a cylinder about
    # the yaw axis covering the head base footprint up to the collar, at each roll pose
    base_r = math.hypot(servo.L - servo.AXIS_FROM_END + WALL, POCK1) + GAP          # 30.2
    z_clear = h["z_yaw_face"] + 2.0 + GAP                                            # collar top + gap
    for k in range(5):
        cyl = prim.cylinder(comp, "z", (xy, 0, 0), base_r, h["z_yaw_horn"] - 40.0, z_clear)
        tools.append(_rotate_x(comp, cyl, (xy, 0, zr), -roll_range + k * roll_range / 2))
    tools += bolt_holes(comp, "x", (xy, 0, zr))
    prim.cut(comp, main, tools)
    main.name = "head shell"
    return main
