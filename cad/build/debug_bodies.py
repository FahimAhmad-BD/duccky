# Debug: build each leg part alone and list the bodies left in its component.
import importlib, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts
for mod in (dk, prim, servo, leg, legparts):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    root = dk.design().rootComponent
    g = leg.geometry()
    for name, fn in {"yaw_link": legparts.yaw_link, "roll_link": lambda c, gg: legparts.roll_link(c, gg)[0],
                     "thigh": legparts.thigh, "shank": legparts.shank, "foot": legparts.foot}.items():
        o = dk.new_component(root, name)
        body = fn(o.component, g)
        bs = o.component.bRepBodies
        print(name, "returned:", body.name, "| bodies:",
              [(bs.item(i).name, round(bs.item(i).volume * 1000, 1)) for i in range(bs.count)])
finally:
    doc.close(False)
