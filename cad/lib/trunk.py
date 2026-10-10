"""Trunk frame in the robot frame (mm).

  floor   z = 1 to 3, under both hip yaw servos and the cartridge bay; horn clearance holes;
          countersunk M2 from below into each yaw servo's far end horn face holes
  deck    z = 26 to 29, resting on the yaw servo back faces (clamping them with 4 x M2
          each), bridging over the cartridge; four M2.5 standoffs up to the carrier board
          on the Radxa hole pattern (RK10)
  walls   left and right walls outside the yaw servos join floor and deck; the back is open
          for the cartridge, the front carries the neck mount
"""
import prim
import robot
import servo

T = 3.0
WALL = 2.5
HALF_Y = 48.0                          # outer half width: yaw servo outer face 44 + gap + wall
X0, X1 = -45.0, 45.0
DECK_Z0, DECK_Z1 = 26.0, 29.0          # yaw servo back face at 3 + 23 = 26
STANDOFF_D, STANDOFF_HOLE = 6.0, 2.2   # M2.5 self tapping into printed boss (2.2 mm pilot)


def yaw_servo_holes(side, hip_y):
    """(x, y) of the four case holes of a hip yaw servo in the robot frame. Local y -> +x,
    local x -> +y (leg.py pose), so case hole (lx, ly) maps to (ly, side * hip_y + lx)."""
    return [(ly, side * hip_y + lx) for lx, ly in servo.CASE_HOLES]


def board_holes():
    """Carrier mounting holes (H1 to H4 of ecad/gen/pcb.py) in the robot frame."""
    import importlib.util
    sbc, holes = (5.5, 1.0), [(3.575, 3.525), (61.4, 3.525), (3.575, 26.4), (61.4, 26.4)]
    out = []
    for hx, hy in holes:
        bx, by = sbc[0] + hx, sbc[1] + hy
        out.append((bx - robot.BOARD_W / 2, robot.BOARD_H / 2 - by))
    return out


def frame(comp, hip_y):
    """Floor, deck and side walls as one body."""
    parts = [prim.box(comp, X0, X1, -HALF_Y, HALF_Y, robot.FLOOR_Z0, robot.FLOOR_Z1),
             prim.box(comp, X0, X1, -HALF_Y, HALF_Y, DECK_Z0, DECK_Z1)]
    for s in (1, -1):
        y0, y1 = sorted((s * (HALF_Y - WALL), s * HALF_Y))
        parts.append(prim.box(comp, X0, X1, y0, y1, robot.FLOOR_Z0, DECK_Z1))
    for bx, by in board_holes():
        parts.append(prim.cylinder(comp, "z", (bx, by, 0), STANDOFF_D / 2, DECK_Z1, robot.BOARD_Z))
    main = parts[0]
    prim.join(comp, main, parts[1:])
    tools = []
    for s in (1, -1):
        # Horn clearance through the floor, and the yaw link plate (r 12) swings below it
        tools.append(prim.cylinder(comp, "z", (0, s * hip_y, 0), 9.0, robot.FLOOR_Z0 - 0.5, robot.FLOOR_Z1 + 0.5))
        for x, y in yaw_servo_holes(s, hip_y):
            # floor: only the far end pair (x = -22.5); the near pair sits inside the horn clearance zone
            if x < -10:
                tools.append(prim.cylinder(comp, "z", (x, y, 0), 1.1, robot.FLOOR_Z0 - 0.5, robot.FLOOR_Z1 + 3.5))
                tools.append(prim.cylinder(comp, "z", (x, y, 0), 2.1, robot.FLOOR_Z0 - 0.5, robot.FLOOR_Z0 + 1.2))
            # deck: all four, counterbored from the top
            tools.append(prim.cylinder(comp, "z", (x, y, 0), 1.1, DECK_Z0 - 4.5, DECK_Z1 + 0.5))
            tools.append(prim.cylinder(comp, "z", (x, y, 0), 2.1, DECK_Z1 - 1.2, DECK_Z1 + 0.5))
    for bx, by in board_holes():
        tools.append(prim.cylinder(comp, "z", (bx, by, 0), STANDOFF_HOLE / 2, DECK_Z1 - 2.0, robot.BOARD_Z + 0.5))
    # Cable pass-throughs in the deck beside the yaw servos (servo cables up to the carrier)
    for s in (1, -1):
        y0, y1 = sorted((s * (hip_y - 10 - 2), s * (hip_y - 10 - 8)))
        tools.append(prim.box(comp, 12.0, 30.0, y0, y1, DECK_Z0 - 0.5, DECK_Z1 + 0.5))
    # Lightening (RK1: every gram above the hips counts). Deck window between the yaw servos,
    # inside the standoff pattern; floor under the cartridge reduced to two 6 mm rails; side
    # wall windows between floor and deck.
    tools.append(prim.box(comp, -22.0, 22.0, -18.0, 18.0, DECK_Z0 - 0.5, DECK_Z1 + 0.5))
    cx0, cx1, cy0, cy1, cz0, cz1 = robot.cartridge_box()
    tools.append(prim.box(comp, cx0 + 4.0, cx1 - 4.0, cy0 + 6.0, cy1 - 6.0, robot.FLOOR_Z0 - 0.5, robot.FLOOR_Z1 + 0.5))
    for s in (1, -1):
        y0, y1 = sorted((s * (HALF_Y - WALL - 0.5), s * (HALF_Y + 0.5)))
        tools.append(prim.box(comp, -35.0, 35.0, y0, y1, robot.FLOOR_Z1 + 3.0, DECK_Z0 - 3.0))
    prim.cut(comp, main, tools)
    main.name = "trunk frame"
    return main
