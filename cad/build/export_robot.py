# Build the robot (no board STEP: its mass comes from the budget) and export, for every part,
# solid volume, surface area, centre of mass and inertia about the centre of mass, plus the
# joint frames, to cad/export/robot.json. The scratch document is closed at the end.
import importlib, json, math, runpy, sys
from pathlib import Path
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts, assembly
for mod in (dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts, assembly):
    importlib.reload(mod)

OUT = Path(r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\export\robot.json")

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    root = dk.design().rootComponent
    entries = assembly.build(root, include_board=False)
    parts = []
    for e in entries:
        o = e["occurrence"]
        pp = o.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        c = pp.centerOfMass
        ok, ixx, iyy, izz, ixy, iyz, ixz = pp.getXYZMomentsOfInertia()   # kg cm^2 about the world origin
        m = pp.mass                                                       # kg, solid with the assigned material
        cx, cy, cz = c.x, c.y, c.z                                        # cm
        # Parallel axis: move the inertia to the centre of mass (kg cm^2), then to kg m^2
        Ic = [ixx - m * (cy * cy + cz * cz), iyy - m * (cx * cx + cz * cz), izz - m * (cx * cx + cy * cy),
              ixy + m * cx * cy, iyz + m * cy * cz, ixz + m * cx * cz]
        parts.append({
            "name": e["name"], "kind": e["kind"], "link": e["link"], "model": e.get("model"),
            "solid_mass_kg": m, "volume_m3": pp.volume * 1e-6, "area_m2": pp.area * 1e-4,
            "com_m": [cx / 100, cy / 100, cz / 100],
            "inertia_com_kgm2": [v * 1e-4 for v in Ic],   # ixx iyy izz ixy iyz ixz
        })
    g = leg.geometry()
    h = head.layout()
    mm = lambda *v: [x / 1000 for x in v]
    joints = []
    for side, tag in ((1, "L"), (-1, "R")):
        y = side * g["hip_y"]
        joints += [
            {"name": f"{tag}_hip_yaw", "parent": "trunk", "child": f"{tag}_hip_yaw_link", "origin": mm(0, y, 0), "axis": [0, 0, 1]},
            {"name": f"{tag}_hip_roll", "parent": f"{tag}_hip_yaw_link", "child": f"{tag}_hip_roll_link", "origin": mm(0, y, g["z_roll"]), "axis": [1, 0, 0]},
            {"name": f"{tag}_hip_pitch", "parent": f"{tag}_hip_roll_link", "child": f"{tag}_thigh", "origin": mm(0, y, g["z_pitch"]), "axis": [0, 1, 0]},
            {"name": f"{tag}_knee", "parent": f"{tag}_thigh", "child": f"{tag}_shank", "origin": mm(0, y, g["z_knee"]), "axis": [0, 1, 0]},
            {"name": f"{tag}_ankle", "parent": f"{tag}_shank", "child": f"{tag}_foot", "origin": mm(0, y, g["z_ankle"]), "axis": [0, 1, 0]},
        ]
    joints += [
        {"name": "neck_pitch", "parent": "trunk", "child": "neck_link", "origin": mm(h["x_neck"], 0, h["z_neck"]), "axis": [0, 1, 0]},
        {"name": "head_pitch", "parent": "neck_link", "child": "head_pitch_link", "origin": mm(h["x_head_pitch"], 0, h["z_head_pitch"]), "axis": [0, 1, 0]},
        {"name": "head_yaw", "parent": "head_pitch_link", "child": "head_yaw_link", "origin": mm(h["x_yaw"], 0, h["z_yaw_horn"]), "axis": [0, 0, 1]},
        {"name": "head_roll", "parent": "head_yaw_link", "child": "head", "origin": mm(h["x_yaw"], 0, h["z_roll"]), "axis": [1, 0, 0]},
        {"name": "beak", "parent": "head", "child": "mandible", "origin": mm(h["x_beak"], 0, h["z_beak"]), "axis": [0, 1, 0]},
    ]
    P = runpy.run_path(leg.PARAMS)
    for j in joints:
        key = "lim_" + j["name"].split("_", 1)[1] if j["name"][:2] in ("L_", "R_") else "lim_" + j["name"]
        src = P["LEG"] if j["name"][:2] in ("L_", "R_") else P["HEAD"]
        j["limit"] = list(src[key])
    sole_z = g["z_sole"] / 1000
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"frame": "robot: x forward, y left, z up, origin at the hip yaw horn faces",
                               "sole_z_m": sole_z, "parts": parts, "joints": joints}, indent=2), encoding="utf-8")
    print(len(parts), "parts,", len(joints), "joints ->", OUT)
finally:
    doc.close(False)
