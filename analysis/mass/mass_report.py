"""Mass report from the Fusion export (cad/export/robot.json).

Printed parts: printed mass = density x (skin + infill x core), with
    skin  = surface area x SKIN (three 0.4 mm perimeters, top and bottom layers comparable)
    core  = solid volume - skin (not below zero)
    INFILL = 0.25 (gyroid, typical for structural FDM parts); PETG 1.27 g/cm3 (Prusament TDS)
Servos: ROBOTIS e-Manual masses (assigned in Fusion). Cells: retailer mass (DCK-02 RK7).
Items not modelled in CAD keep their DCK-00 / DCK-02 allocations, placed at a stated point.

Run: python mass_report.py   writes mass_report.json and mass_report.md next to this file.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORT = HERE.parents[1] / "cad" / "export" / "robot.json"
RHO = 1270.0            # kg/m3
SKIN = 0.0012           # m
INFILL = 0.25
LIMIT_KG = 0.850
CELL_KG, CELL_COUNT = 0.046, 2      # Molicel INR-18650-P28A, retailer mass (DCK-02 RK7)

# Not in CAD: (name, kg, link, point m in the robot frame, basis)
ALLOCATIONS = [
    ("carrier PCB and connectors", 0.025, "trunk", (0.0, 0.0, 0.033), "DCK-00 allocation"),
    ("Radxa ZERO 3W", 0.015, "trunk", (0.0, 0.015, 0.040), "DCK-00 allocation (no Radxa figure, DCK-02 1.5)"),
    ("IMU and small sensors", 0.004, "trunk", (0.0, 0.0, 0.034), "DCK-00 allocation"),
    ("speaker and microphone", 0.004, "trunk", (0.03, -0.03, 0.05), "DCK-02 2.2"),
    ("wiring harness", 0.020, "trunk", (0.0, 0.0, 0.03), "DCK-00 allocation"),
    ("fasteners and inserts", 0.020, "trunk", (0.0, 0.0, 0.02), "DCK-00 allocation"),
    ("idlers and horn screws, 15 joints", 0.030, "trunk", (0.0, 0.0, -0.06), "allocation 2 g per joint (FPX330-H101 mass not published)"),
    ("head payload: camera, depth and mic board", 0.012, "head", (0.08, 0.0, 0.125), "DCK-00 allocation"),
    ("beak servo XL330-M288-T", 0.018, "head", (0.09, 0.0, 0.11), "e-Manual; beak not yet in CAD"),
    ("beak", 0.010, "head", (0.11, 0.0, 0.105), "DCK-00 allocation; beak not yet in CAD"),
    ("outer shells", 0.035, "trunk", (0.0, 0.0, 0.04), "DCK-00 allocation; shells not yet in CAD"),
]


def printed_mass(p):
    skin = min(p["area_m2"] * SKIN, p["volume_m3"])
    return RHO * (skin + INFILL * (p["volume_m3"] - skin))


def main():
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    rows = []
    for p in data["parts"]:
        if p["kind"] == "printed":
            m = printed_mass(p)
        elif p["kind"] == "cell":
            m = CELL_KG * CELL_COUNT          # source mass, independent of the CAD material
        else:
            m = p["solid_mass_kg"]
        rows.append({"name": p["name"], "kind": p["kind"], "link": p["link"], "mass_kg": m,
                     "solid_kg": p["solid_mass_kg"], "com_m": p["com_m"]})
    for name, m, link, pt, basis in ALLOCATIONS:
        rows.append({"name": name, "kind": "allocation", "link": link, "mass_kg": m, "com_m": list(pt), "basis": basis})
    total = sum(r["mass_kg"] for r in rows)
    com = [sum(r["mass_kg"] * r["com_m"][i] for r in rows) / total for i in range(3)]
    by_kind, by_link = {}, {}
    for r in rows:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + r["mass_kg"]
        by_link[r["link"]] = by_link.get(r["link"], 0) + r["mass_kg"]
    out = {"assumptions": {"rho_kg_m3": RHO, "skin_m": SKIN, "infill": INFILL},
           "total_kg": total, "com_m": com, "margin_kg": LIMIT_KG - total,
           "by_kind_kg": by_kind, "by_link_kg": by_link, "rows": rows}
    (HERE / "mass_report.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    lines = ["| Group | Mass (g) |", "|---|---|"]
    for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v * 1000:.0f} |")
    lines.append(f"| **Total** | **{total * 1000:.0f}** |")
    lines += ["", "| Link | Mass (g) |", "|---|---|"]
    for k, v in sorted(by_link.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v * 1000:.1f} |")
    lines += ["", "| Printed part | Solid (g) | Printed (g) |", "|---|---|---|"]
    for r in sorted((r for r in rows if r["kind"] == "printed"), key=lambda r: -r["mass_kg"]):
        lines.append(f"| {r['name']} | {r['solid_kg'] * 1000:.1f} | {r['mass_kg'] * 1000:.1f} |")
    lines.append("")
    lines.append(f"Total {total * 1000:.0f} g against {LIMIT_KG * 1000:.0f} g (margin {(LIMIT_KG - total) * 1000:+.0f} g); "
                 f"centre of mass at x {com[0] * 1000:.1f}, y {com[1] * 1000:.1f}, z {com[2] * 1000:.1f} mm.")
    (HERE / "mass_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
