# Build the left leg (servo references and printed parts) in a scratch document, then check
# interference at the zero pose and with each joint at its limits (others at zero).
# Prints part masses, interference volumes, and saves views. Set KEEP = True to leave the
# document open for inspection.
import importlib
import math
import runpy
import sys

LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts
for mod in (dk, prim, servo, leg, legparts):
    importlib.reload(mod)

KEEP = False

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    des = dk.design()
    root = des.rootComponent
    g = leg.geometry()
    occ = {}
    for joint, (model, o, xa, ya, za) in leg.servo_poses(g).items():
        occ["servo_" + joint] = servo.build(root, model, f"{joint} {model}", leg.matrix(o, xa, ya, za))
    builders = {"yaw_link": legparts.yaw_link, "roll_link": lambda c, gg: legparts.roll_link(c, gg)[0],
                "thigh": legparts.thigh, "shank": legparts.shank, "foot": legparts.foot}
    for name, fn in builders.items():
        o = dk.new_component(root, name)
        body = fn(o.component, g)
        bs = o.component.bRepBodies
        if bs.count != 1:
            print(f"WARNING {name}: {bs.count} bodies")
        for i in range(bs.count):
            bs.item(i).material = dk.printed_material()
        occ[name] = o
        print(f"{name}: {dk.physical(o)}")

    def interference(label):
        items = dk.collection([occ[k] for k in occ])
        inp = des.createInterferenceInput(items)
        inp.areCoincidentFacesIncluded = False
        res = des.analyzeInterference(inp)
        hits = []
        for i in range(res.count):
            r = res.item(i)
            v = r.interferenceBody.volume * 1000 if r.interferenceBody else 0
            if v > 0.5:
                n1 = r.entityOne.parentComponent.name
                n2 = r.entityTwo.parentComponent.name
                bb = r.interferenceBody.boundingBox
                lo = [round(c * 10, 1) for c in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z)]
                hi = [round(c * 10, 1) for c in (bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]
                hits.append(f"{n1} x {n2}: {v:.1f} mm3 at {lo}..{hi}")
        print(f"[{label}] interference: {hits or 'none'}")

    interference("zero pose")

    p = runpy.run_path(leg.PARAMS)["LEG"]
    chains = {
        "hip_roll": ("x", g["z_roll"], ["roll_link", "servo_hip_pitch", "thigh", "servo_knee", "shank", "servo_ankle", "foot"], p["lim_hip_roll"]),
        "hip_pitch": ("y", g["z_pitch"], ["thigh", "servo_knee", "shank", "servo_ankle", "foot"], p["lim_hip_pitch"]),
        "knee": ("y", g["z_knee"], ["shank", "servo_ankle", "foot"], p["lim_knee"]),
        "ankle": ("y", g["z_ankle"], ["foot", "servo_ankle"], p["lim_ankle"]),
    }
    base = {k: occ[k].transform.copy() for k in occ}
    for joint, (axis, z, moving, lim) in chains.items():
        for ang in lim:
            rot = adsk.core.Matrix3D.create()
            vec = adsk.core.Vector3D.create(1, 0, 0) if axis == "x" else adsk.core.Vector3D.create(0, 1, 0)
            rot.setToRotation(ang, vec, dk.P(0, 0, z))
            for k in moving:
                m = base[k].copy()
                m.transformBy(rot)
                occ[k].transform = m
            interference(f"{joint} {ang:+.2f} rad")
            for k in moving:
                occ[k].transform = base[k]

    vp = app.activeViewport
    cam = vp.camera
    zc = dk.cm(g["z_ankle"] / 2)
    for view, eye in (("front", (60, 0, zc)), ("side", (0, 60, zc)), ("iso", (40, 35, zc + 15))):
        cam.isFitView = True
        cam.eye = adsk.core.Point3D.create(*eye)
        cam.target = adsk.core.Point3D.create(0, 0, zc)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        vp.camera = cam
        vp.fit()
        snapshot(view, 1200, 1200, fit=False)
finally:
    if not KEEP:
        doc.close(False)
