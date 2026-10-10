# Primitive test: boxes and cylinders along each axis must land exactly where requested.
import importlib, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim
for mod in (dk, prim):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    comp = dk.design().rootComponent
    checks = {
        "box": prim.box(comp, 0, 10, 20, 25, -5, 2),
        "cyl_x": prim.cylinder(comp, "x", (0, 40, 7), 3, 5, 15),
        "cyl_y": prim.cylinder(comp, "y", (30, 0, 7), 3, -10, -2),
        "cyl_z": prim.cylinder(comp, "z", (50, 50, 0), 3, -8, -1),
    }
    for name, b in checks.items():
        bb = b.boundingBox
        lo = [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z)]
        hi = [round(v * 10, 2) for v in (bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]
        print(name, lo, hi)
finally:
    doc.close(False)
