"""Solid primitives in component coordinates (mm): boxes and axis-aligned cylinders, with
join and cut. Parts are built as unions of primitives minus clearance cuts, which keeps the
build scripts short and every dimension explicit.
"""
import adsk.core
import adsk.fusion

import dk

_AXIS = {"x": 0, "y": 1, "z": 2}


def _plane(comp, axis, offset):
    """Construction plane normal to axis at offset (mm)."""
    base = {"z": comp.xYConstructionPlane, "y": comp.xZConstructionPlane, "x": comp.yZConstructionPlane}[axis]
    if abs(offset) < 1e-9:
        return base
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(base, dk.V(offset))
    return comp.constructionPlanes.add(inp)


def _to_sketch(sk, p3):
    m = sk.transform.copy()
    m.invert()
    q = p3.copy()
    q.transformBy(m)
    return q


def _body_from(comp, sk, profile, axis, length, op, target=None):
    """Extrude profile by length (mm) toward +axis, whichever way the sketch normal points."""
    ext = comp.features.extrudeFeatures
    ops = {"new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
           "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
           "cut": adsk.fusion.FeatureOperations.CutFeatureOperation}
    normal = sk.transform.getCell(_AXIS[axis], 2)      # z column of the sketch frame
    dist = length if normal > 0 else -length
    inp = ext.createInput(profile, ops[op])
    inp.setDistanceExtent(False, dk.V(dist))
    if target is not None and op != "new":
        inp.participantBodies = [target]
    return ext.add(inp)


def box(comp, x0, x1, y0, y1, z0, z1, op="new", target=None):
    """Axis aligned box between the given coordinates (mm)."""
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    pl = _plane(comp, "z", z0)
    sk = comp.sketches.add(pl)
    a = _to_sketch(sk, dk.P(x0, y0, z0))
    b = _to_sketch(sk, dk.P(x1, y1, z0))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(a, b)
    f = _body_from(comp, sk, sk.profiles.item(0), "z", z1 - z0, op, target)
    return f.bodies.item(0) if op == "new" else target


def cylinder(comp, axis, c, r, a0, a1, op="new", target=None):
    """Cylinder of radius r along axis ('x', 'y' or 'z') through point c = (x, y, z) (the
    coordinate along the axis is ignored), from a0 to a1 along the axis (mm)."""
    a0, a1 = sorted((a0, a1))
    pl = _plane(comp, axis, a0)
    sk = comp.sketches.add(pl)
    p = list(c)
    p[_AXIS[axis]] = a0
    centre = _to_sketch(sk, dk.P(*p))
    sk.sketchCurves.sketchCircles.addByCenterRadius(centre, dk.cm(r))
    f = _body_from(comp, sk, sk.profiles.item(0), axis, a1 - a0, op, target)
    return f.bodies.item(0) if op == "new" else target


def join(comp, target, tools):
    if not tools:
        return target
    cf = comp.features.combineFeatures
    inp = cf.createInput(target, dk.collection(tools))
    inp.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cf.add(inp)
    return target


def cut(comp, target, tools, keep_tools=False):
    if not tools:
        return target
    cf = comp.features.combineFeatures
    inp = cf.createInput(target, dk.collection(tools))
    inp.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    inp.isKeepToolBodies = keep_tools
    cf.add(inp)
    return target


def bolt_circle(comp, axis, c, a0, a1, pcd=12.0, d=2.2, n=4, phase=0.0):
    """Cylinders for an n-hole bolt circle (returned as tool bodies to cut)."""
    import math
    tools = []
    i, j = [k for k in range(3) if k != _AXIS[axis]]
    for k in range(n):
        ang = phase + 2 * math.pi * k / n
        p = list(c)
        p[i] += pcd / 2 * math.cos(ang)
        p[j] += pcd / 2 * math.sin(ang)
        tools.append(cylinder(comp, axis, p, d / 2, a0, a1))
    return tools
