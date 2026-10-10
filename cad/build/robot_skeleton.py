# Whole robot packaging check: both legs (servos and printed parts, right leg mirrored),
# carrier board from its STEP, battery cartridge and trunk envelopes. Reports interference
# and saves views. Scratch document, closed at the end.
import importlib
import sys

LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts, robot, trunk
for mod in (dk, prim, servo, leg, legparts, robot, trunk):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    des = dk.design()
    root = des.rootComponent
    g = leg.geometry()
    occ = {}
    poses = leg.servo_poses(g)
    for side, tag in ((1, "L"), (-1, "R")):
        for joint, pose in poses.items():
            model, m = robot.leg_matrix(pose, side)
            occ[f"{joint}_{tag}"] = servo.build(root, model, f"{joint}_{tag} {model}", m)
        for name, fn in {"yaw_link": legparts.yaw_link, "roll_link": lambda c, gg: legparts.roll_link(c, gg)[0],
                         "thigh": legparts.thigh, "shank": legparts.shank, "foot": legparts.foot}.items():
            t = adsk.core.Matrix3D.create()
            t.translation = adsk.core.Vector3D.create(0, dk.cm(side * g["hip_y"]), 0)
            o = dk.new_component(root, f"{name}_{tag}", t)
            body = fn(o.component, g)
            if side < 0:
                feats = o.component.features
                mi = feats.mirrorFeatures.createInput(dk.collection([body]), o.component.xZConstructionPlane)
                feats.mirrorFeatures.add(mi)
                feats.removeFeatures.add(body)
            for i in range(o.component.bRepBodies.count):
                o.component.bRepBodies.item(i).material = dk.printed_material()
            if o.component.bRepBodies.count != 1:
                print(f"WARNING {name}_{tag}: {o.component.bRepBodies.count} bodies")
            occ[f"{name}_{tag}"] = o
    # Trunk frame
    tf = dk.new_component(root, "trunk_frame")
    tb = trunk.frame(tf.component, g["hip_y"])
    tb.material = dk.printed_material()
    print("trunk frame:", dk.physical(tf))
    occ["trunk_frame"] = tf
    # Battery cartridge envelope
    cb = dk.new_component(root, "cartridge envelope")
    prim.box(cb.component, *robot.cartridge_box())
    occ["cartridge"] = cb
    # Carrier board from KiCad
    board = robot.import_step(root, robot.CARRIER_STEP, "carrier board")
    if board:
        robot.place_board(board)
    print("board imported:", board is not None)
    if board:
        occ["board"] = board
    # Report
    items = dk.collection(list(occ.values()))
    inp = des.createInterferenceInput(items)
    inp.areCoincidentFacesIncluded = False
    res = des.analyzeInterference(inp)
    hits = []
    for i in range(res.count):
        r = res.item(i)
        v = r.interferenceBody.volume * 1000 if r.interferenceBody else 0
        if v > 0.5:
            hits.append(f"{r.entityOne.parentComponent.name} x {r.entityTwo.parentComponent.name}: {v:.1f} mm3")
    print("interference:", hits or "none")
    print("cartridge box:", [round(v, 1) for v in robot.cartridge_box()])
    vp = app.activeViewport
    cam = vp.camera
    for view, eye in (("front", (80, 0, 2)), ("top", (0, 0, 80)), ("iso", (50, 40, 30))):
        cam.isFitView = True
        cam.eye = adsk.core.Point3D.create(*eye)
        cam.target = adsk.core.Point3D.create(0, 0, -5)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1) if view != "top" else adsk.core.Vector3D.create(1, 0, 0)
        vp.camera = cam
        vp.fit()
        snapshot(view, 1200, 1200, fit=False)
finally:
    doc.close(False)
