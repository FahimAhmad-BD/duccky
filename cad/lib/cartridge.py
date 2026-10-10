"""2S battery cartridge (DCK-02 section 2.3) in the robot frame (mm).

Two Molicel INR-18650-P28A cells lie along x side by side inside a printed tray and lid,
split at the cell centre line. The front end (+x) holds the S-8252 protection board and the
four blade contacts (B+, mid-cell, B-, NTC) that meet spring contacts on the trunk; the back
end has a finger recess for pulling the cartridge out of the rear slot.
"""
import prim
import robot

CLEAR = 0.3                 # radial clearance around each cell
FRONT_BAY = 4.0             # protection board and contacts at the +x end (cartridge_box allowance)
CELL_MASS_G = 46.0          # retailer figure per cell (DCK-02 RK7)


def cells_y():
    w = robot.CELL_D + robot.CART_WALL
    return (-w / 2, w / 2)


def _geom():
    x0, x1, y0, y1, z0, z1 = robot.cartridge_box()
    zc = z0 + robot.CART_WALL + robot.CELL_D / 2
    cx0 = x0 + robot.CART_WALL
    cx1 = cx0 + robot.CELL_L
    return x0, x1, y0, y1, z0, z1, zc, cx0, cx1


def tray(comp):
    x0, x1, y0, y1, z0, z1, zc, cx0, cx1 = _geom()
    body = prim.box(comp, x0, x1, y0, y1, z0, zc)
    tools = [prim.cylinder(comp, "x", (0, yc, zc), robot.CELL_D / 2 + CLEAR, cx0, cx1) for yc in cells_y()]
    # Front bay for the protection board, open to the contacts face
    tools.append(prim.box(comp, cx1, x1 - robot.CART_WALL, y0 + robot.CART_WALL, y1 - robot.CART_WALL,
                          z0 + robot.CART_WALL, zc + 0.5))
    # Contact windows through the front face: B+, mid, B-, NTC
    for k in range(4):
        yk = y0 + 8.0 + k * (y1 - y0 - 16.0) / 3
        tools.append(prim.box(comp, x1 - robot.CART_WALL - 0.5, x1 + 0.5, yk - 1.5, yk + 1.5, z0 + 3.0, zc - 1.0))
    # Finger recess at the back end
    tools.append(prim.box(comp, x0 - 0.5, x0 + 1.0, -8.0, 8.0, z0 + robot.CART_WALL, zc + 0.5))
    prim.cut(comp, body, tools)
    body.name = "cartridge tray"
    return body


def lid(comp):
    x0, x1, y0, y1, z0, z1, zc, cx0, cx1 = _geom()
    body = prim.box(comp, x0, x1, y0, y1, zc, z1)
    tools = [prim.cylinder(comp, "x", (0, yc, zc), robot.CELL_D / 2 + CLEAR, cx0, cx1) for yc in cells_y()]
    tools.append(prim.box(comp, cx1, x1 - robot.CART_WALL, y0 + robot.CART_WALL, y1 - robot.CART_WALL,
                          zc - 0.5, z1 - robot.CART_WALL))
    prim.cut(comp, body, tools)
    body.name = "cartridge lid"
    return body


def cells(comp):
    """Cell reference bodies (cylinders) for mass and interference."""
    x0, x1, y0, y1, z0, z1, zc, cx0, cx1 = _geom()
    return [prim.cylinder(comp, "x", (0, yc, zc), robot.CELL_D / 2, cx0, cx1) for yc in cells_y()]
