"""Printed leg parts for the left leg, built in the leg frame of cad/lib/leg.py (mm).

Rules applied to every joint ("one servo pocket" design):
  * Output links are U brackets: a plate on the horn face and a plate on the idler face
    (ROBOTIS FPX330-H101 idler), 4 x M2 on a 12 mm pitch circle on each side. Horn and idler
    outer faces sit 14.5 mm either side of the servo mid plane, so output plates occupy
    |s| = 14.5 to 17.5 mm (s is the coordinate along the joint axis).
  * Servos sit in pockets screwed through the two far end case holes on each face
    (countersunk M2, so nothing protrudes). Pocket walls occupy |s| = 11.5 to 13.5 mm, inside
    the output plates with 1 mm running clearance, and clear the horn and idler (r 9.5 mm).
  * Where a link rotates past a neighbouring servo, the link is trimmed to keep GAP outside
    that servo's swept radius about the joint axis.
"""
import math

import prim
import servo

T = 3.0          # wall and plate thickness
WALL = 2.0       # pocket wall thickness
GAP = 1.0        # running clearance
FACE = servo.D / 2                    # 11.5: case face from servo mid plane
OUT0 = FACE + servo.HORN_H            # 14.5: horn and idler outer faces
OUT1 = OUT0 + T                       # 17.5: output plate outer faces
POCK1 = FACE + WALL                   # 13.5: pocket wall outer faces
HUB_CLEAR = 9.5                       # pocket wall clearance radius around horn and idler
PLATE_R = 10.5                        # output plate radius around the axis
SCREW_D, CBORE_D, CBORE_H = 2.2, 4.2, 1.2
# Far end corner of a servo case seen from its axis: (half width, 34 - 9.5)
SERVO_FAR_R = math.hypot(servo.W / 2, servo.L - servo.AXIS_FROM_END)       # 26.5


def _annulus_cut(comp, axis, c, r, s0, s1, extent=200.0):
    """Tool body that removes everything outside radius r about the axis through c, for the
    slab s0..s1 along that axis."""
    i, j = [k for k in range(3) if k != "xyz".index(axis)]
    lo = [c[0] - extent, c[1] - extent, c[2] - extent]
    hi = [c[0] + extent, c[1] + extent, c[2] + extent]
    lo["xyz".index(axis)], hi["xyz".index(axis)] = s0, s1
    tool = prim.box(comp, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    keep = prim.cylinder(comp, axis, c, r, s0 - 1, s1 + 1)
    prim.cut(comp, tool, [keep])
    return tool


def _inside_cut(comp, axis, c, r, s0, s1):
    return prim.cylinder(comp, axis, c, r, s0, s1)


def _screw(comp, axis, centre, s_face, outward, depth):
    """Countersunk style M2 hole: through hole into the case plus counterbore on the outer face.
    s_face: coordinate of the wall outer face along axis; outward: +1 or -1."""
    c = list(centre)
    hole = prim.cylinder(comp, axis, c, SCREW_D / 2, s_face - outward * depth, s_face + outward * 0.5)
    cb = prim.cylinder(comp, axis, c, CBORE_D / 2, s_face - outward * CBORE_H, s_face + outward * 0.5)
    return [hole, cb]


def output_plates(comp, axis, centre, r, arm_to, arm_half, sides=(1, -1)):
    """Horn and idler plates around an axis plus arms running to arm_to along the leg's z.
    Returns the list of bodies (not joined: the two sides only connect through the rest of
    the part, and Fusion leaves a disjoint tool body separate, so callers join everything
    in one combine). axis is 'x' or 'y'; centre is a point on the axis."""
    bodies = []
    k = "xyz".index(axis)
    for s in sides:
        s0, s1 = sorted((s * OUT0 + centre[k], s * OUT1 + centre[k]))
        bodies.append(prim.cylinder(comp, axis, centre, r, s0, s1))
        lo, hi = [None] * 3, [None] * 3
        lo[k], hi[k] = s0, s1
        other = 1 - k if k < 2 else 0          # x <-> y
        lo[other], hi[other] = centre[other] - arm_half, centre[other] + arm_half
        lo[2], hi[2] = centre[2], arm_to
        bodies.append(prim.box(comp, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    return bodies


def _union(comp, bodies):
    main = bodies[0]
    prim.join(comp, main, bodies[1:])
    return main


def bolt_holes(comp, axis, centre, sides=(1, -1)):
    k = "xyz".index(axis)
    tools = []
    for s in sides:
        s0, s1 = sorted((s * OUT0 + centre[k] - s * 0.5, s * OUT1 + centre[k] + s * 0.5))
        tools += prim.bolt_circle(comp, axis, centre, s0, s1, pcd=servo.HORN_PCD, d=SCREW_D)
        tools.append(prim.cylinder(comp, axis, centre, 1.6, s0, s1))     # horn screw access
    return tools


# ---------------------------------------------------------------- part builders (left leg)

def yaw_link(comp, g):
    """Hip yaw output: plate on the yaw horn (z = 0 down to -T) carrying the roll servo
    pocket. Roll servo lies under it: case faces at x = +-11.5, far end at y = -24.5."""
    zr = g["z_roll"]
    yf = servo.Y_BOT                                      # -24.5, roll servo far end
    main = prim.cylinder(comp, "z", (0, 0, 0), 12.0, -T, 0)
    parts = [prim.box(comp, -POCK1, POCK1, yf - WALL, 0, -T, 0)]
    zb = zr - servo.W / 2                                 # roll servo bottom
    for s in (1, -1):
        parts.append(prim.box(comp, s * FACE, s * POCK1, yf - WALL, -12.0, zb, -T))
    parts.append(prim.box(comp, -POCK1, POCK1, yf - WALL, yf, zb, -T))
    prim.join(comp, main, parts)
    tools = prim.bolt_circle(comp, "z", (0, 0, 0), -T - 0.5, 0.5, pcd=servo.HORN_PCD, d=SCREW_D)
    tools.append(prim.cylinder(comp, "z", (0, 0, 0), 1.6, -T - 0.5, 0.5))
    yh = servo.Y_MID - servo.CASE_DY / 2                  # far end hole row, -22.5
    for dz in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "x", (0, yh, zr - dz), POCK1, 1, WALL + 3.0)
        tools += _screw(comp, "x", (0, yh, zr - dz), -POCK1, -1, WALL + 4.5)
    prim.cut(comp, main, tools)
    main.name = "hip yaw link"
    return main


def roll_link(comp, g):
    """Hip roll output U: plates on the roll horn (front) and idler (back), a bottom plate
    under the roll servo, and the hip pitch servo pocket hanging below it."""
    zr, zp = g["z_roll"], g["z_pitch"]
    plate_top = zr - (servo.W / 2 + GAP + 12.5 * math.sin(0.40)) / math.cos(0.40)
    plate_bot = plate_top - T
    pocket_bot = zp - (servo.L - servo.AXIS_FROM_END) - WALL
    parts = output_plates(comp, "x", (0, 0, zr), PLATE_R, plate_bot, POCK1)
    parts += [prim.box(comp, -OUT1, OUT1, -servo.D / 2 + 1.0, servo.D / 2 - 1.0, plate_bot, plate_top)]
    for s in (1, -1):
        parts.append(prim.box(comp, -OUT1, OUT1, s * FACE, s * POCK1, pocket_bot, plate_bot))
    main = _union(comp, parts)
    tools = bolt_holes(comp, "x", (0, 0, zr))
    for s in (1, -1):
        tools.append(_inside_cut(comp, "y", (0, 0, zp), HUB_CLEAR, min(s * FACE, s * POCK1) - 0.5, max(s * FACE, s * POCK1) + 0.5))
    # Stay inside the pitch servo's far corner radius so the thigh and knee servo can pass
    tools.append(_annulus_cut(comp, "y", (0, 0, zp), SERVO_FAR_R, -POCK1 - 0.5, POCK1 + 0.5))
    zh = zp - (servo.L - servo.AXIS_FROM_END) + 2.0       # far end hole row (2 mm from the end)
    for x in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "y", (x, 0, zh), POCK1, 1, WALL + 3.0)
        tools += _screw(comp, "y", (x, 0, zh), -POCK1, -1, WALL + 4.5)
    prim.cut(comp, main, tools)
    main.name = "hip roll link"
    return main, plate_top


def thigh(comp, g):
    """Hip pitch output U (horn outward, idler inward) running down to the knee servo pocket.
    The knee servo hangs horn end down; its far end (top) is held at z_knee + 24.5."""
    zp, zk = g["z_pitch"], g["z_knee"]
    top_far = zk + (servo.L - servo.AXIS_FROM_END)        # knee servo top face
    # The block joining the arms to the knee pocket stays 20 mm or more from the knee axis
    # and within the arm width, so the shank rails pass it at full knee flexion (2.2 rad).
    block_bot = zk + 20.0
    parts = output_plates(comp, "y", (0, 0, zp), PLATE_R, block_bot, PLATE_R)
    for s in (1, -1):
        parts.append(prim.box(comp, -POCK1, POCK1, s * FACE, s * POCK1, block_bot, top_far + 3.0))
        parts.append(prim.box(comp, -PLATE_R, PLATE_R, s * POCK1, s * OUT1, block_bot, top_far + 3.0))
    parts.append(prim.box(comp, -POCK1, -servo.W / 2, -FACE, FACE, block_bot, top_far + 3.0))   # back web
    parts += thigh_spring_features(comp, g)
    main = _union(comp, parts)
    tools = bolt_holes(comp, "y", (0, 0, zp))
    # Keep the thigh outside the pitch servo and roll link swept radius
    tools.append(_inside_cut(comp, "y", (0, 0, zp), SERVO_FAR_R + GAP, -POCK1 - 0.5, POCK1 + 0.5))
    zh = zk + (servo.L - servo.AXIS_FROM_END) - 2.0       # knee far end hole row
    for x in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "y", (x, 0, zh), OUT1, 1, OUT1 - FACE + 3.0)
        tools += _screw(comp, "y", (x, 0, zh), -OUT1, -1, OUT1 - FACE + 4.5)
    prim.cut(comp, main, tools)
    main.name = "thigh"
    return main


def shank(comp, g):
    """Double U: knee horn and idler plates at the top, ankle horn and idler plates at the
    bottom, joined by two side rails."""
    zk, za = g["z_knee"], g["z_ankle"]
    r_ankle = g["ankle_to_sole"] - T - GAP                # plate radius that clears the sole plate
    rail = 9.0
    parts = output_plates(comp, "y", (0, 0, zk), PLATE_R, za, rail)
    for s in (1, -1):
        s0, s1 = sorted((s * OUT0, s * OUT1))
        parts.append(prim.cylinder(comp, "y", (0, 0, za), r_ankle, s0, s1))
    # Front web: below the knee servo (15 mm or more from the knee axis) and 28 mm or more
    # above the ankle axis, outside the ankle servo's swept radius (26.5 mm). A back web would
    # hit the knee servo at full knee flexion.
    web_top = zk - 12.5
    web_bot = max(zk - 18.5, za + SERVO_FAR_R + GAP)
    parts.append(prim.box(comp, rail, rail + T, -OUT1, OUT1, web_bot, web_top))
    parts += shank_spring_features(comp, g)
    main = _union(comp, parts)
    tools = bolt_holes(comp, "y", (0, 0, zk)) + bolt_holes(comp, "y", (0, 0, za))
    # Back web must not cross the servo bodies between the side plates
    prim.cut(comp, main, tools)
    main.name = "shank"
    return main


def foot(comp, g):
    """Sole plate and the pocket for the ankle servo lying forward (far end at +x)."""
    za, zs = g["z_ankle"], g["z_sole"]
    fx, fy, fz = g["foot"]
    cx = -g["foot_ankle_x"]
    far = servo.L - servo.AXIS_FROM_END                   # 24.5, case front end from the axis
    main = prim.box(comp, cx - fx / 2, cx + fx / 2, -fy / 2, fy / 2, zs, zs + T)
    parts = []
    zt = za + servo.W / 2
    for s in (1, -1):
        parts.append(prim.box(comp, HUB_CLEAR + GAP, far + WALL, s * FACE, s * POCK1, zs + T, zt))
    parts.append(prim.box(comp, far, far + WALL, -POCK1, POCK1, zs + T, zt))
    prim.join(comp, main, parts)
    tools = []
    xh = far - 2.0
    for dz in (servo.CASE_DX / 2, -servo.CASE_DX / 2):
        tools += _screw(comp, "y", (xh, 0, za + dz), POCK1, 1, WALL + 3.0)
        tools += _screw(comp, "y", (xh, 0, za + dz), -POCK1, -1, WALL + 4.5)
    prim.cut(comp, main, tools)
    main.name = "foot"
    return main


# ---------------------------------------------------------------- knee assist spring (RK2)
# Lee Spring LTL048J 04 / LTR048J 04, music wire: OD 15.72 mm, wire 1.22 mm, body length
# 7.42 mm, suggested mandrel 11.51 mm, 31.68 kg mm at 180 deg (0.0989 N m/rad). It sits on
# the inner (idler) side of the knee, coaxial with the knee axis, around a mandrel boss on the
# shank; its legs bear on a shank peg and on a thigh peg in front of the knee.
SPRING_OD, SPRING_WIRE, SPRING_L, SPRING_MANDREL = 15.72, 1.22, 7.42, 11.51


def _spring_slab():
    s0 = -(OUT1 + 0.5)
    return s0 - SPRING_L, s0                          # y range on the inner side of the left leg


def knee_spring(comp, g):
    """Reference body: the spring coil as a tube (for mass and interference)."""
    zk = g["z_knee"]
    y0, y1 = _spring_slab()
    outer = prim.cylinder(comp, "y", (0, 0, zk), SPRING_OD / 2, y0, y1)
    inner = prim.cylinder(comp, "y", (0, 0, zk), SPRING_OD / 2 - SPRING_WIRE, y0 - 0.5, y1 + 0.5)
    prim.cut(comp, outer, [inner])
    outer.name = "knee spring LTx048J04"
    return outer


def shank_spring_features(comp, g):
    """Mandrel boss and the shank-side leg peg (joined to the shank)."""
    zk = g["z_knee"]
    y0, y1 = _spring_slab()
    boss = prim.cylinder(comp, "y", (0, 0, zk), SPRING_MANDREL / 2, y0 - 0.5, -OUT1 + 0.01)
    peg = prim.cylinder(comp, "y", (0, 0, zk - 14.0), 1.5, y0 - 0.5, -OUT1 + 0.01)
    return [boss, peg]


def thigh_spring_features(comp, g):
    """Tab down from the thigh's inner arm in front of the knee and the thigh-side leg peg."""
    zk = g["z_knee"]
    y0, y1 = _spring_slab()
    tab = prim.box(comp, 6.0, 14.0, -OUT1, -OUT0, zk + PLATE_R + GAP, zk + 20.0 + 0.01)
    peg = prim.cylinder(comp, "y", (10.0, 0, zk + 13.0), 1.5, y0 - 0.5, -OUT0)
    return [tab, peg]
