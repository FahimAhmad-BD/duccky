# Neck and head servo skeleton with the trunk frame: reports servo-to-servo clearances and
# interference with neck pitch and head pitch swept over their ranges (head base rigid).
import importlib, runpy, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, robot, trunk, head
for mod in (dk, prim, servo, leg, robot, trunk, head):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    des = dk.design()
    root = des.rootComponent
    h = head.layout()
    print({k: round(v, 1) for k, v in h.items()})
    occ = {}
    for name, (model, o, xa, ya, za) in head.servo_poses(h).items():
        occ[name] = servo.build(root, model, name, leg.matrix(o, xa, ya, za))
    tf = dk.new_component(root, "trunk_frame")
    trunk.frame(tf.component, leg.geometry()["hip_y"])
    occ["trunk_frame"] = tf
    # Computer envelope above the carrier (65 x 30 board, 12 mm stack above the board top)
    sbc = dk.new_component(root, "computer envelope")
    prim.box(sbc.component, -32.5, 32.5, 0.0, 30.0, robot.BOARD_Z + robot.BOARD_T, robot.BOARD_Z + robot.BOARD_T + 12.0)
    occ["sbc"] = sbc

    def check(label):
        inp = des.createInterferenceInput(dk.collection(list(occ.values())))
        inp.areCoincidentFacesIncluded = False
        res = des.analyzeInterference(inp)
        hits = [f"{res.item(i).entityOne.parentComponent.name} x {res.item(i).entityTwo.parentComponent.name}: "
                f"{res.item(i).interferenceBody.volume * 1000:.0f} mm3" for i in range(res.count)
                if res.item(i).interferenceBody and res.item(i).interferenceBody.volume * 1000 > 0.5]
        print(f"[{label}]", hits or "none")

    check("zero")
    H = runpy.run_path(leg.PARAMS)["HEAD"]
    base = {k: occ[k].transform.copy() for k in occ}
    head_parts = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]
    def hits_at(a_neck, a_head):
        r1 = adsk.core.Matrix3D.create()
        r1.setToRotation(a_neck, adsk.core.Vector3D.create(0, 1, 0), dk.P(h["x_neck"], 0, h["z_neck"]))
        r2 = adsk.core.Matrix3D.create()
        r2.setToRotation(a_head, adsk.core.Vector3D.create(0, 1, 0), dk.P(h["x_head_pitch"], 0, h["z_head_pitch"]))
        # Neck servo is fixed in the trunk; the head base (head pitch, yaw, roll servos) turns
        # about the head pitch axis, and everything above the neck turns about the neck axis.
        for k in ["head_pitch", "head_yaw", "head_roll"]:
            m = base[k].copy()
            m.transformBy(r2)
            m.transformBy(r1)
            occ[k].transform = m
        inp = des.createInterferenceInput(dk.collection(list(occ.values())))
        inp.areCoincidentFacesIncluded = False
        res = des.analyzeInterference(inp)
        return [f"{res.item(i).entityOne.parentComponent.name} x {res.item(i).entityTwo.parentComponent.name}"
                for i in range(res.count) if res.item(i).interferenceBody and res.item(i).interferenceBody.volume * 1000 > 0.5]

    # Clear range of each joint alone (the other at zero), in 0.1 rad steps
    for label, idx in (("neck_pitch", 0), ("head_pitch", 1)):
        for sign in (1, -1):
            last, hit = 0.0, None
            for k in range(1, 17):
                a = sign * 0.1 * k
                angles = (a, 0.0) if idx == 0 else (0.0, a)
                hs = hits_at(*angles)
                if hs:
                    hit = hs
                    break
                last = a
            print(f"{label} clear to {last:+.1f} rad" + (f" (next step hits {hit})" if hit else " (no hit to 1.6)"))
    for k in head_parts:
        occ[k].transform = base[k]
    vp = app.activeViewport
    cam = vp.camera
    cam.isFitView = True
    cam.eye = adsk.core.Point3D.create(5, 40, 8)
    cam.target = adsk.core.Point3D.create(3, 0, 8)
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    vp.camera = cam
    vp.fit()
    snapshot("side", 1200, 1000, fit=False)
finally:
    doc.close(False)
