"""Whole robot assembly used by the preview and export jobs.

build(root) creates every servo reference and printed part as its own component and returns
a list of entries {name, occurrence, kind, link}:
  kind  'printed' (PETG part), 'servo' (datasheet mass), 'cell' (battery cell), 'board'
  link  the kinematic link the part rides on, for the robot description and mass report
"""
import adsk.core

import cartridge
import dk
import head
import headparts
import leg
import legparts
import robot
import servo
import trunk

LEG_LINKS = {"hip_yaw": "trunk", "hip_roll": "hip_yaw_link", "hip_pitch": "hip_roll_link",
             "knee": "thigh", "ankle": "foot"}
LEG_PARTS = {"yaw_link": "hip_yaw_link", "roll_link": "hip_roll_link", "thigh": "thigh",
             "shank": "shank", "foot": "foot"}
HEAD_SERVO_LINKS = {"neck_pitch": "trunk", "head_pitch": "head_pitch_link", "head_yaw": "head_pitch_link",
                    "head_roll": "head_yaw_link", "beak": "head"}


def build(root, include_board=True):
    entries = []
    g = leg.geometry()
    mat = dk.printed_material()

    def part(name, fn, link, t=None, mirror=False):
        o = dk.new_component(root, name, t)
        body = fn(o.component)
        if mirror:
            feats = o.component.features
            feats.mirrorFeatures.add(feats.mirrorFeatures.createInput(dk.collection([body]),
                                                                     o.component.xZConstructionPlane))
            feats.removeFeatures.add(body)
        for i in range(o.component.bRepBodies.count):
            o.component.bRepBodies.item(i).material = mat
        entries.append({"name": name, "occurrence": o, "kind": "printed", "link": link})
        return o

    for side, tag in ((1, "L"), (-1, "R")):
        for joint, pose in leg.servo_poses(g).items():
            model, m = robot.leg_matrix(pose, side)
            o = servo.build(root, model, f"{joint}_{tag} {model}", m)
            link = LEG_LINKS[joint] if LEG_LINKS[joint] == "trunk" else f"{tag}_{LEG_LINKS[joint]}"
            entries.append({"name": f"servo_{joint}_{tag}", "occurrence": o, "kind": "servo", "link": link,
                            "model": model})
        t = adsk.core.Matrix3D.create()
        t.translation = adsk.core.Vector3D.create(0, dk.cm(side * g["hip_y"]), 0)
        builders = {"yaw_link": legparts.yaw_link, "roll_link": lambda c, gg: legparts.roll_link(c, gg)[0],
                    "thigh": legparts.thigh, "shank": legparts.shank, "foot": legparts.foot}
        for name, fn in builders.items():
            part(f"{name}_{tag}", lambda c, fn=fn: fn(c, g), f"{tag}_{LEG_PARTS[name]}", t, mirror=side < 0)
        spring = dk.new_component(root, f"knee_spring_{tag}", t)
        body = legparts.knee_spring(spring.component, g)
        if side < 0:
            feats = spring.component.features
            feats.mirrorFeatures.add(feats.mirrorFeatures.createInput(dk.collection([body]),
                                                                     spring.component.xZConstructionPlane))
            feats.removeFeatures.add(body)
        steel = dk.printed_material("Music wire (spring)", 7.85)
        for i in range(spring.component.bRepBodies.count):
            spring.component.bRepBodies.item(i).material = steel
        entries.append({"name": f"knee_spring_{tag}", "occurrence": spring, "kind": "spring", "link": f"{tag}_shank"})

    part("trunk_frame", lambda c: trunk.frame(c, g["hip_y"]), "trunk")
    part("cartridge_tray", cartridge.tray, "trunk")
    part("cartridge_lid", cartridge.lid, "trunk")
    cells = dk.new_component(root, "cells")
    bodies = cartridge.cells(cells.component)
    cell_mat = dk.printed_material("Li-ion cell (46 g)", cartridge.CELL_MASS_G / bodies[0].volume)
    for b in bodies:
        b.material = cell_mat
    entries.append({"name": "cells", "occurrence": cells, "kind": "cell", "link": "trunk"})

    h = head.layout()
    for name, (model, o, xa, ya, za) in head.servo_poses(h).items():
        occ = servo.build(root, model, f"{name} {model}", leg.matrix(o, xa, ya, za))
        entries.append({"name": f"servo_{name}", "occurrence": occ, "kind": "servo",
                        "link": HEAD_SERVO_LINKS[name], "model": model})
    part("neck_mount", lambda c: headparts.neck_mount(c, h), "trunk")
    part("neck_plate_horn", lambda c: headparts.neck_plate(c, h, 1), "neck_link")
    part("neck_plate_idler", lambda c: headparts.neck_plate(c, h, -1), "neck_link")
    part("head_base", lambda c: headparts.head_base(c, h), "head_pitch_link")
    part("head_yaw_link", lambda c: headparts.yaw_link(c, h), "head_yaw_link")
    part("head_shell", lambda c: headparts.head_shell(c, h), "head")
    part("mandible", lambda c: headparts.mandible(c, h), "mandible")

    if include_board:
        board = robot.import_step(root, robot.CARRIER_STEP, "carrier board")
        if board:
            robot.place_board(board)
            entries.append({"name": "carrier_board", "occurrence": board, "kind": "board", "link": "trunk"})
    return entries
