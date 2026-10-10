"""ROBOTIS X330 servo reference body (XL330-M288-T and XC330-M288-T share the envelope).

Source: ROBOTIS drawing "X330", 28 May 2020 (e-Manual download no. 1986):
    case 20 x 34 x 23 mm, horn dia 16 mm protruding 3 mm (26 mm overall)
    output axis centred on the 20 mm width, 9.5 mm from the horn end of the 34 mm length
    horn: 4 x dia 1.6 holes depth 3, PCD 12, M2 tapping screws
    case: M2 tapping holes dia 1.6 at the corners, 16 mm apart across the width and
          30 mm apart along the length; depth 3.0 on the horn face, 4.5 on the back face

Local frame: origin on the output axis at the horn-side case face, +z out through the
horn, +y toward the horn end of the case, x across the 20 mm width.
"""
import math

import adsk.core
import adsk.fusion

import dk

W, L, D = 20.0, 34.0, 23.0
AXIS_FROM_END = 9.5
HORN_D, HORN_H, HORN_PCD = 16.0, 3.0, 12.0
HOLE_D = 1.6
CASE_DX, CASE_DY = 16.0, 30.0
MASS_G = {"XL330-M288-T": 18.0, "XC330-M288-T": 23.0}

Y_TOP = AXIS_FROM_END            # case end nearest the axis
Y_BOT = AXIS_FROM_END - L        # far case end
Y_MID = (Y_TOP + Y_BOT) / 2
CASE_HOLES = [(sx * CASE_DX / 2, Y_MID + sy * CASE_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]


def volume_mm3():
    return W * L * D + math.pi * (HORN_D / 2) ** 2 * HORN_H


def material(model, body_volume_cm3):
    """Design material whose density gives the datasheet servo mass for this body volume.
    Fusion stores density in kg/m3."""
    des = dk.design()
    name = f"Servo {model}"
    m = des.materials.itemByName(name)
    if m is None:
        base = dk.app.materialLibraries.itemByName("Fusion Material Library").materials.itemByName("ABS Plastic")
        m = des.materials.addByCopy(base, name)
    rho_g_cm3 = MASS_G[model] / body_volume_cm3
    m.materialProperties.itemById("structural_Density").value = rho_g_cm3 * 1000.0
    return m


def build(parent, model, name, transform=None):
    """Add a servo reference occurrence to parent; returns the occurrence."""
    occ = dk.new_component(parent, name, transform)
    comp = occ.component
    sk = dk.sketch_on(comp, "xy", "case")
    dk.rect_center(sk, 0, Y_MID, W, L)
    case = dk.extrude(comp, sk.profiles.item(0), f"-{D} mm", "new", name="case")
    skh = dk.sketch_on(comp, "xy", "horn")
    dk.circle(skh, 0, 0, HORN_D)
    dk.extrude(comp, skh.profiles.item(0), HORN_H, "join", name="horn")
    # Horn screw holes (from the horn top face) and case tapping holes (both faces)
    horn_top = comp.constructionPlanes.createInput()
    horn_top.setByOffset(comp.xYConstructionPlane, dk.V(HORN_H))
    pl = comp.constructionPlanes.add(horn_top)
    skp = dk.sketch_on(comp, pl, "horn holes")
    for k in range(4):
        a = math.pi / 2 * k
        dk.circle(skp, HORN_PCD / 2 * math.cos(a), HORN_PCD / 2 * math.sin(a), HOLE_D)
    small = [skp.profiles.item(i) for i in range(skp.profiles.count)
             if skp.profiles.item(i).areaProperties().area < (math.pi * (HOLE_D / 20) ** 2) * 1.5]
    dk.extrude(comp, dk.collection(small), "-3 mm", "cut", name="horn holes")
    skf = dk.sketch_on(comp, "xy", "front holes")
    for x, y in CASE_HOLES:
        dk.circle(skf, x, y, HOLE_D)
    small = [skf.profiles.item(i) for i in range(skf.profiles.count)
             if skf.profiles.item(i).areaProperties().area < (math.pi * (HOLE_D / 20) ** 2) * 1.5]
    dk.extrude(comp, dk.collection(small), "-3 mm", "cut", name="front holes")
    back = comp.constructionPlanes.createInput()
    back.setByOffset(comp.xYConstructionPlane, dk.V(-D))
    plb = comp.constructionPlanes.add(back)
    skb = dk.sketch_on(comp, plb, "back holes")
    for x, y in CASE_HOLES:
        dk.circle(skb, x, y, HOLE_D)
    small = [skb.profiles.item(i) for i in range(skb.profiles.count)
             if skb.profiles.item(i).areaProperties().area < (math.pi * (HOLE_D / 20) ** 2) * 1.5]
    dk.extrude(comp, dk.collection(small), "4.5 mm", "cut", name="back holes")
    body = comp.bRepBodies.item(0)
    body.name = model
    body.material = material(model, body.volume)
    # The component Z axis is the output axis; joints reference it directly
    return occ
