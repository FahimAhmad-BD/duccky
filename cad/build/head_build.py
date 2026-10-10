# Neck and head: servos and printed parts with the trunk frame and computer envelope.
# Interference at zero and over each joint's range, plus roll with yaw combinations.
import importlib, runpy, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts, robot, trunk, head, headparts
for mod in (dk, prim, servo, leg, legparts, robot, trunk, head, headparts):
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
    sbc = dk.new_component(root, "computer envelope")
    prim.box(sbc.component, -32.5, 32.5, 0.0, 30.0, robot.BOARD_Z + robot.BOARD_T, robot.BOARD_Z + robot.BOARD_T + 12.0)
    occ["sbc"] = sbc
    builders = {"neck_mount": lambda c: headparts.neck_mount(c, h),
                "neck_plate_horn": lambda c: headparts.neck_plate(c, h, 1),
                "neck_plate_idler": lambda c: headparts.neck_plate(c, h, -1),
                "head_base": lambda c: headparts.head_base(c, h),
                "yaw_link": lambda c: headparts.yaw_link(c, h),
                "head_shell": lambda c: headparts.head_shell(c, h)}
    for name, fn in builders.items():
        o = dk.new_component(root, name)
        fn(o.component)
        bs = o.component.bRepBodies
        if bs.count != 1:
            print(f"WARNING {name}: {bs.count} bodies")
        for i in range(bs.count):
            bs.item(i).material = dk.printed_material()
        occ[name] = o
        print(name, dk.physical(o))

    def hits():
        inp = des.createInterferenceInput(dk.collection(list(occ.values())))
        inp.areCoincidentFacesIncluded = False
        res = des.analyzeInterference(inp)
        return [f"{res.item(i).entityOne.parentComponent.name} x {res.item(i).entityTwo.parentComponent.name}: "
                f"{res.item(i).interferenceBody.volume * 1000:.0f}"
                for i in range(res.count) if res.item(i).interferenceBody and res.item(i).interferenceBody.volume * 1000 > 0.5]

    print("[zero]", hits() or "none")
    HP = runpy.run_path(leg.PARAMS)["HEAD"]
    base = {k: occ[k].transform.copy() for k in occ}
    chain = {
        "neck_pitch": (("y", (h["x_neck"], 0, h["z_neck"])), ["neck_plate_horn", "neck_plate_idler", "head_pitch", "head_base", "head_yaw", "yaw_link", "head_roll", "head_shell"]),
        "head_pitch": (("y", (h["x_head_pitch"], 0, h["z_head_pitch"])), ["head_pitch", "head_base", "head_yaw", "yaw_link", "head_roll", "head_shell"]),
        "head_yaw": (("z", (h["x_yaw"], 0, 0)), ["yaw_link", "head_roll", "head_shell"]),
        "head_roll": (("x", (0, 0, h["z_roll"])), ["head_shell"]),
    }

    def pose(angles):
        for k in occ:
            occ[k].transform = base[k]
        # apply from the tip of the chain back to the root so each rotation uses the parent frame
        for joint in ("head_roll", "head_yaw", "head_pitch", "neck_pitch"):
            a = angles.get(joint, 0.0)
            if not a:
                continue
            (ax, pt), moving = chain[joint]
            r = adsk.core.Matrix3D.create()
            vec = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ax]
            r.setToRotation(a, adsk.core.Vector3D.create(*vec), dk.P(*pt))
            for k in moving:
                m = occ[k].transform.copy()
                m.transformBy(r)
                occ[k].transform = m

    tests = []
    for j, key in (("neck_pitch", "lim_neck_pitch"), ("head_pitch", "lim_head_pitch"), ("head_roll", "lim_head_roll")):
        for a in HP[key]:
            tests.append({j: a})
    for a in (-2.9, -1.6, 1.6, 2.9):
        tests.append({"head_yaw": a})
    for y in (0.0, 0.8, 1.6, 2.4):
        for r in HP["lim_head_roll"]:
            tests.append({"head_yaw": y, "head_roll": r})
    for t in tests:
        pose(t)
        print(t, hits() or "none")
    pose({})
    vp = app.activeViewport
    cam = vp.camera
    cam.isFitView = True
    cam.eye = adsk.core.Point3D.create(30, 25, 12)
    cam.target = adsk.core.Point3D.create(5, 0, 8)
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    vp.camera = cam
    vp.fit()
    snapshot("head_iso", 1200, 1000, fit=False)
finally:
    doc.close(False)
