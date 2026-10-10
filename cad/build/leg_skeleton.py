# Leg skeleton: the five servo references of the left leg placed per cad/lib/leg.py, plus a
# foot sole plate, in a scratch document. Reports pairwise minimum distances between servo
# bodies and screenshots front, side and iso views, then closes the document.
import importlib
import sys

LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, servo, leg
for mod in (dk, servo, leg):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    root = dk.design().rootComponent
    g = leg.geometry()
    print({k: round(v, 1) for k, v in g.items() if isinstance(v, float)})
    occs = {}
    for joint, (model, o, xa, ya, za) in leg.servo_poses(g).items():
        occs[joint] = servo.build(root, model, f"{joint} {model}", leg.matrix(o, xa, ya, za))
    # Foot sole plate under the ankle servo
    fx, fy, fz = g["foot"]
    cx = -g["foot_ankle_x"]
    foot = dk.new_component(root, "foot sole")
    pl = foot.component.constructionPlanes.createInput()
    pl.setByOffset(foot.component.xYConstructionPlane, dk.V(g["z_sole"]))
    plane = foot.component.constructionPlanes.add(pl)
    sk = dk.sketch_on(foot.component, plane)
    dk.rect_center(sk, cx, servo.D / 2, fx, fy)
    dk.extrude(foot.component, sk.profiles.item(0), 3.0, "new")
    # Pairwise clearances between servo bodies
    names = list(occs)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = occs[names[i]].bRepBodies.item(0)
            b = occs[names[j]].bRepBodies.item(0)
            r = app.measureManager.measureMinimumDistance(a, b)
            if r.value < 1.0:   # report pairs closer than 10 mm
                print(f"clearance {names[i]} - {names[j]}: {r.value * 10:.2f} mm")
    vp = app.activeViewport
    cam = vp.camera
    zc = dk.cm(g["z_ankle"] / 2)
    for view, eye in (("front", (60, 1.15, zc)), ("side", (0.0, 60, zc)), ("iso", (40, 40, zc + 20))):
        cam.isFitView = True
        cam.eye = adsk.core.Point3D.create(*eye)
        cam.target = adsk.core.Point3D.create(0, 1.15, zc)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        vp.camera = cam
        vp.fit()
        snapshot(view, 1200, 1200, fit=False)
finally:
    doc.close(False)
