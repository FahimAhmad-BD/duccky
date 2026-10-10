"""Duccky Fusion helpers, used by the build jobs in cad/build through the Claude Fusion Bridge.

All lengths passed to these helpers are in millimetres; Fusion's internal unit is cm,
so every value is converted with cm(). Geometry is driven by user parameters where a
dimension is a design input, so the model stays editable in Fusion.
"""
import adsk.core
import adsk.fusion

app = adsk.core.Application.get()


def cm(mm):
    return mm / 10.0


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def V(expr):
    """ValueInput from an expression string ('20 mm', 'servo_w + 2 mm') or a number in mm."""
    if isinstance(expr, (int, float)):
        return adsk.core.ValueInput.createByString(f"{expr} mm")
    return adsk.core.ValueInput.createByString(expr)


def design():
    return adsk.fusion.Design.cast(app.activeProduct)


def get_or_create_document(name):
    """Activate an open document called name, or create a new design document with that name
    (unsaved). Never touches other open documents."""
    for i in range(app.documents.count):
        d = app.documents.item(i)
        if d.name.split(" v")[0] == name:
            d.activate()
            return d
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct)
    des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    des.rootComponent.name = name
    return doc


def set_param(name, expr, unit="mm", comment=""):
    """Create or update a user parameter."""
    ups = design().userParameters
    p = ups.itemByName(name)
    if p:
        p.expression = expr if isinstance(expr, str) else f"{expr} {unit}"
        p.comment = comment
        return p
    val = adsk.core.ValueInput.createByString(expr if isinstance(expr, str) else f"{expr} {unit}")
    return ups.add(name, val, unit, comment)


def new_component(parent, name, transform=None):
    """Create an empty component as an occurrence of parent (a Component)."""
    m = transform or adsk.core.Matrix3D.create()
    occ = parent.occurrences.addNewComponent(m)
    occ.component.name = name
    return occ


def find_occurrence(parent, name):
    for i in range(parent.occurrences.count):
        o = parent.occurrences.item(i)
        if o.component.name == name:
            return o
    return None


def delete_occurrence(parent, name):
    o = find_occurrence(parent, name)
    if o:
        o.deleteMe()


def sketch_on(comp, plane="xy", name=None):
    planes = {"xy": comp.xYConstructionPlane, "xz": comp.xZConstructionPlane, "yz": comp.yZConstructionPlane}
    sk = comp.sketches.add(planes[plane] if isinstance(plane, str) else plane)
    if name:
        sk.name = name
    return sk


def rect_center(sk, cx, cy, w, h):
    return sk.sketchCurves.sketchLines.addCenterPointRectangle(P(cx, cy), P(cx + w / 2, cy + h / 2))


def circle(sk, cx, cy, d):
    return sk.sketchCurves.sketchCircles.addByCenterRadius(P(cx, cy), cm(d / 2))


def extrude(comp, profile, distance, op="new", symmetric=False, name=None):
    ops = {"new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
           "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
           "cut": adsk.fusion.FeatureOperations.CutFeatureOperation}
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(profile, ops[op])
    if symmetric:
        inp.setSymmetricExtent(V(distance), True)
    else:
        inp.setDistanceExtent(False, V(distance))
    f = ext.add(inp)
    if name:
        f.name = name
    return f


def largest_profile(sk):
    best, area = None, -1
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        a = pr.areaProperties().area
        if a > area:
            best, area = pr, a
    return best


def profiles_except_largest(sk):
    big = largest_profile(sk)
    return [sk.profiles.item(i) for i in range(sk.profiles.count) if sk.profiles.item(i) != big]


def collection(items):
    c = adsk.core.ObjectCollection.create()
    for it in items:
        c.add(it)
    return c


def set_material(body, name, library="Fusion Material Library"):
    lib = app.materialLibraries.itemByName(library)
    mat = lib.materials.itemByName(name) if lib else None
    if mat:
        body.material = mat
    return mat


def physical(comp_or_occ):
    """Mass (g), centre of mass (mm) and volume (mm3) of a component or occurrence."""
    pp = comp_or_occ.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
    c = pp.centerOfMass
    return {"mass_g": round(pp.mass * 1000, 2), "com_mm": [round(c.x * 10, 2), round(c.y * 10, 2), round(c.z * 10, 2)],
            "volume_mm3": round(pp.volume * 1000, 1)}
