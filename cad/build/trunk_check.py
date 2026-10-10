# Trunk check without the slow board import: trunk frame, hip yaw servos, battery cartridge
# (tray, lid, cells). Reports masses and interference, and saves views.
import importlib, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, robot, trunk, cartridge
for mod in (dk, prim, servo, leg, robot, trunk, cartridge):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    des = dk.design()
    root = des.rootComponent
    g = leg.geometry()
    occ = {}
    for side, tag in ((1, "L"), (-1, "R")):
        model, m = robot.leg_matrix(leg.servo_poses(g)["hip_yaw"], side)
        occ[f"yaw_{tag}"] = servo.build(root, model, f"hip_yaw_{tag} {model}", m)
    tf = dk.new_component(root, "trunk_frame")
    trunk.frame(tf.component, g["hip_y"]).material = dk.printed_material()
    occ["trunk_frame"] = tf
    for name, fn in (("cartridge_tray", cartridge.tray), ("cartridge_lid", cartridge.lid)):
        o = dk.new_component(root, name)
        fn(o.component).material = dk.printed_material()
        occ[name] = o
        print(name, dk.physical(o))
    co = dk.new_component(root, "cells")
    for b in cartridge.cells(co.component):
        pass
    # Cell density from the 46 g mass over the reference cylinder volume
    vol = co.component.bRepBodies.item(0).volume
    m = dk.printed_material("Li-ion cell (46 g)", cartridge.CELL_MASS_G / vol)
    for i in range(co.component.bRepBodies.count):
        co.component.bRepBodies.item(i).material = m
    occ["cells"] = co
    print("cells", dk.physical(co))
    inp = des.createInterferenceInput(dk.collection(list(occ.values())))
    inp.areCoincidentFacesIncluded = False
    res = des.analyzeInterference(inp)
    hits = [f"{res.item(i).entityOne.parentComponent.name} x {res.item(i).entityTwo.parentComponent.name}: "
            f"{res.item(i).interferenceBody.volume * 1000:.1f} mm3" for i in range(res.count)
            if res.item(i).interferenceBody and res.item(i).interferenceBody.volume * 1000 > 0.5]
    print("interference:", hits or "none")
    vp = app.activeViewport
    cam = vp.camera
    cam.isFitView = True
    cam.eye = adsk.core.Point3D.create(-30, 25, 20)
    cam.target = adsk.core.Point3D.create(0, 0, 1.5)
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    vp.camera = cam
    vp.fit()
    snapshot("trunk_rear_iso", 1200, 1000, fit=False)
finally:
    doc.close(False)
