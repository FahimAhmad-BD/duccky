# Build the whole robot as designed so far and LEAVE THE DOCUMENT OPEN for viewing:
# both legs (servos and printed parts), trunk frame, battery cartridge, carrier board,
# neck and head. The document is not saved; save it from Fusion if you want to keep it.
import importlib, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts
for mod in (dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts):
    importlib.reload(mod)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
des = dk.design()
root = des.rootComponent
g = leg.geometry()
mat = dk.printed_material()


def part(name, fn, t=None, mirror=False):
    o = dk.new_component(root, name, t)
    body = fn(o.component)
    if mirror:
        feats = o.component.features
        feats.mirrorFeatures.add(feats.mirrorFeatures.createInput(dk.collection([body]), o.component.xZConstructionPlane))
        feats.removeFeatures.add(body)
    for i in range(o.component.bRepBodies.count):
        o.component.bRepBodies.item(i).material = mat
    return o


# Legs
for side, tag in ((1, "L"), (-1, "R")):
    for joint, pose in leg.servo_poses(g).items():
        model, m = robot.leg_matrix(pose, side)
        servo.build(root, model, f"{joint}_{tag}", m)
    t = adsk.core.Matrix3D.create()
    t.translation = adsk.core.Vector3D.create(0, dk.cm(side * g["hip_y"]), 0)
    for name, fn in (("yaw_link", legparts.yaw_link), ("roll_link", lambda c, gg: legparts.roll_link(c, gg)[0]),
                     ("thigh", legparts.thigh), ("shank", legparts.shank), ("foot", legparts.foot)):
        part(f"{name}_{tag}", lambda c, fn=fn: fn(c, g), t, mirror=side < 0)
# Trunk and battery
part("trunk_frame", lambda c: trunk.frame(c, g["hip_y"]))
part("cartridge_tray", cartridge.tray)
part("cartridge_lid", cartridge.lid)
cells = dk.new_component(root, "cells")
cartridge.cells(cells.component)
# Neck and head
h = head.layout()
for name, (model, o, xa, ya, za) in head.servo_poses(h).items():
    servo.build(root, model, name, leg.matrix(o, xa, ya, za))
part("neck_mount", lambda c: headparts.neck_mount(c, h))
part("neck_plate_horn", lambda c: headparts.neck_plate(c, h, 1))
part("neck_plate_idler", lambda c: headparts.neck_plate(c, h, -1))
part("head_base", lambda c: headparts.head_base(c, h))
part("head_yaw_link", lambda c: headparts.yaw_link(c, h))
part("head_shell", lambda c: headparts.head_shell(c, h))
# Carrier board (slow STEP import, last)
board = robot.import_step(root, robot.CARRIER_STEP, "carrier board")
if board:
    robot.place_board(board)
print("total", dk.physical(root))
vp = app.activeViewport
cam = vp.camera
cam.isFitView = True
cam.eye = adsk.core.Point3D.create(60, 45, 20)
cam.target = adsk.core.Point3D.create(0, 0, -2)
cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
vp.camera = cam
vp.fit()
snapshot("robot_iso", 1400, 1400, fit=False)
