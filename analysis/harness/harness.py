"""Duccky v1.0 wiring harness definition (Phase 2).

Every cable is listed with its endpoints, connectors, wire, the joints it crosses and
its length. Length = straight run + one service loop per crossed joint + slack, where

    straight run  = link length between the two ends (params.py) + CONNECTOR_ALLOWANCE
    service loop  = LOOP_RADIUS x joint travel (rad), the arc the cable wraps as the
                    joint moves through its full range
    slack         = SLACK per cable for crimp rework and routing

Assumptions (stated, to be replaced by CAD routes in Phase 3):
    LOOP_RADIUS          12 mm   cable crosses each joint about half a servo depth (26 mm / 2) from the axis
    CONNECTOR_ALLOWANCE  20 mm   connector exit to connector entry around the servo bodies
    SLACK                10 mm
    TRUNK_RUN            allocations for runs inside the trunk, fixed once the trunk is in CAD

Servo bodies are fixed to the proximal link and their horns drive the distal link, so a
cable from servo k to servo k+1 crosses joint k.

Run: python harness.py   (writes harness.json and harness.md next to this file)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sizing"))
import params as P  # noqa: E402

LOOP_RADIUS = 12.0
CONNECTOR_ALLOWANCE = 20.0
SLACK = 10.0
TRUNK_RUN = {"leg": 80.0, "neck": 60.0, "head_board": 70.0}

SERVO_CABLE = {"connector": "JST EHR-03 both ends, SEH-001T-P0.6 crimps",
               "wire": "3 x 22 AWG high flex silicone (UL3135)", "pinout": "1 GND, 2 VDD 5.0 V, 3 DATA"}
HEAD_CABLE = {"connector": "JST GHR-10V-S both ends, SSHL-002T-P0.2 crimps",
              "wire": "10 x 28 AWG high flex silicone", "pinout": "per carrier J14"}


def travel(lim):
    return lim[1] - lim[0]


L, H = P.LEG, P.HEAD
JOINTS = {
    "hip_yaw": travel(L["lim_hip_yaw"]), "hip_roll": travel(L["lim_hip_roll"]),
    "hip_pitch": travel(L["lim_hip_pitch"]), "knee": travel(L["lim_knee"]), "ankle": travel(L["lim_ankle"]),
    "neck_pitch": travel(H["lim_neck_pitch"]), "head_pitch": travel(H["lim_head_pitch"]),
    "head_yaw": travel(H["lim_head_yaw"]), "head_roll": travel(H["lim_head_roll"]),
}
M = 1000.0  # m -> mm


def _vlen(key_vec, key_scalar):
    """Length (m) of a head offset given as a vector, or the older scalar parameter."""
    v = H.get(key_vec)
    return (sum(c * c for c in v) ** 0.5) if v else H[key_scalar]


NECK_LEN, PITCH_TO_YAW, YAW_TO_ROLL = (_vlen("neck_vec", "neck_len"), _vlen("pitch_to_yaw_vec", "pitch_to_yaw"),
                                       _vlen("yaw_to_roll_vec", "yaw_to_roll"))


def cable(cid, frm, to, links_mm, crosses, kind, trunk=0.0, note=""):
    straight = sum(links_mm) + CONNECTOR_ALLOWANCE + trunk
    loops = {j: round(LOOP_RADIUS * JOINTS[j], 1) for j in crosses}
    length = straight + sum(loops.values()) + SLACK
    spec = SERVO_CABLE if kind == "servo" else HEAD_CABLE
    return {"id": cid, "from": frm, "to": to, "crosses": crosses, "straight_mm": round(straight, 1),
            "service_loops_mm": loops, "length_mm": round(length, 1),
            "cut_length_mm": int(5 * round((length + 2.5) / 5)), **spec, "note": note}


def build():
    out = []
    for side, j_a, j_b, chain in (("left", "J7", "J8", 1), ("right", "J9", "J10", 2)):
        s = side[0].upper()
        out += [
            cable(f"{s}1", f"carrier {j_a} (chain {chain})", f"{side} hip yaw servo", [], [], "servo",
                  trunk=TRUNK_RUN["leg"], note="power branch A: hip yaw, hip roll, hip pitch"),
            cable(f"{s}2", f"{side} hip yaw servo", f"{side} hip roll servo", [L["yaw_to_roll"] * M], ["hip_yaw"], "servo"),
            cable(f"{s}3", f"{side} hip roll servo", f"{side} hip pitch servo", [L["roll_to_pitch"] * M], ["hip_roll"], "servo"),
            cable(f"{s}4", f"carrier {j_b} (chain {chain})", f"{side} knee servo",
                  [L["yaw_to_roll"] * M, L["roll_to_pitch"] * M, L["thigh"] * M], ["hip_yaw", "hip_roll", "hip_pitch"],
                  "servo", trunk=TRUNK_RUN["leg"], note="power branch B: knee, ankle; follows branch A through the hip"),
            cable(f"{s}5", f"{side} knee servo", f"{side} ankle servo", [L["shank"] * M], ["knee"], "servo"),
        ]
    out += [
        cable("N1", "carrier J11 (chain 3)", "neck pitch servo", [], [], "servo", trunk=TRUNK_RUN["neck"]),
        cable("N2", "neck pitch servo", "head pitch servo", [NECK_LEN * M], ["neck_pitch"], "servo"),
        cable("N3", "head pitch servo", "head yaw servo", [PITCH_TO_YAW * M], ["head_pitch"], "servo"),
        cable("N4", "head yaw servo", "head roll servo", [YAW_TO_ROLL * M], ["head_yaw"], "servo",
              note="crosses head yaw (5.8 rad travel): route along the yaw axis"),
        cable("N5", "head roll servo", "beak servo", [H["beak_len"] * M / 2], ["head_roll"], "servo"),
        cable("HB", "carrier J14", "head board", [NECK_LEN * M, PITCH_TO_YAW * M, YAW_TO_ROLL * M],
              ["neck_pitch", "head_pitch", "head_yaw", "head_roll"], "head", trunk=TRUNK_RUN["head_board"],
              note="runs beside N1 to N4"),
    ]
    return out


def write(cables):
    (HERE / "harness.json").write_text(json.dumps({"assumptions": {
        "loop_radius_mm": LOOP_RADIUS, "connector_allowance_mm": CONNECTOR_ALLOWANCE, "slack_mm": SLACK,
        "trunk_runs_mm": TRUNK_RUN}, "cables": cables}, indent=2) + "\n", encoding="utf-8")
    rows = ["| Cable | From | To | Joints crossed | Straight (mm) | Service loops (mm) | Cut length (mm) |",
            "|---|---|---|---|---|---|---|"]
    for c in cables:
        loops = ", ".join(f"{j} {v:g}" for j, v in c["service_loops_mm"].items()) or "none"
        rows.append(f"| {c['id']} | {c['from']} | {c['to']} | {', '.join(c['crosses']) or 'none'} | "
                    f"{c['straight_mm']:g} | {loops} | {c['cut_length_mm']} |")
    (HERE / "harness.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows))


if __name__ == "__main__":
    write(build())
