"""
Duccky v1.0 servo configuration study (Phase 1).

Each configuration assigns a servo to every joint. The sizing load cases are
rerun with that configuration's real servo masses, then every joint is scored
against the servo assigned to it.

Pass rules (per joint):
  R1  peak demand (static edge CoP, hip hinge, squat, drop)  <= 70 % of stall
  R2  walking demand (core CoP x dynamic factor)              <= 40 % of stall
  R3  walking demand <= torque available at half the peak gait joint speed,
      using a linear torque-speed line from stall to no-load speed. Peak stance
      torque does not coincide with peak swing speed, so half speed is used.

Outputs: results/compare.json, results/compare.md, results/demand_vs_capacity.png
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
RES = HERE / "results"
KGCM = 0.0980665

# Published figures; sources listed in docs/01_actuator_sizing.md
SERVOS = {
    "XL330-M288-T": {"maker": "ROBOTIS", "stall_Nm": 0.52, "noload_rpm": 103, "mass_kg": 0.018,
                     "envelope_mm": "20 x 34 x 26", "volt": "5.0"},
    "XC330-M288-T": {"maker": "ROBOTIS", "stall_Nm": 0.93, "noload_rpm": 81, "mass_kg": 0.023,
                     "envelope_mm": "20 x 34 x 26", "volt": "5.0"},
    "STS3032":      {"maker": "Feetech", "stall_Nm": 4.5 * KGCM, "noload_rpm": 111, "mass_kg": 0.020,
                     "envelope_mm": "~32 x 12 x 28", "volt": "6.0"},
    "STS3215":      {"maker": "Feetech", "stall_Nm": 19.5 * KGCM, "noload_rpm": None, "mass_kg": 0.055,
                     "envelope_mm": "45 x 24.7 x 35", "volt": "6.0"},
}

JOINTS = ["hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle",
          "neck_pitch", "head_pitch", "head_yaw", "head_roll", "beak"]
LOADED = ("hip_pitch", "knee", "ankle")


def uniform(s):
    return {j: s for j in JOINTS}


def mixed(strong, light):
    return {j: (strong if j in LOADED else light) for j in JOINTS}


CONFIGS = {
    "A_all_XL330": uniform("XL330-M288-T"),
    "B_all_STS3032": uniform("STS3032"),
    "C_STS3215_legs_XL330_rest": mixed("STS3215", "XL330-M288-T"),
    "D_all_STS3215": uniform("STS3215"),
    "E_XC330_legs_XL330_rest": mixed("XC330-M288-T", "XL330-M288-T"),
    "F_all_XC330": uniform("XC330-M288-T"),
    "G_E_plus_knee_spring": mixed("XC330-M288-T", "XL330-M288-T"),
}
# Extra design parameters per configuration (passed to sizing.py --set)
# Lee Spring LTL048J 04 / LTR048J 04 (music wire): 31.68 kg mm at 180 deg -> 0.0989 N m/rad
CONFIG_SET = {"G_E_plus_knee_spring": {"LEG.knee_spring_k": 0.0989}}
SELECTED = "G_E_plus_knee_spring"
RULE_PEAK, RULE_WALK = 0.70, 0.40


def run(tag, assign):
    over = {j: SERVOS[s]["mass_kg"] for j, s in assign.items()}
    subprocess.run([sys.executable, str(HERE / "sizing.py"), "--tag", tag,
                    "--override", json.dumps(over), "--set", json.dumps(CONFIG_SET.get(tag, {}))],
                   check=True, capture_output=True, cwd=HERE)
    return json.loads((RES / tag / "summary.json").read_text())


def score(summary, assign):
    rows, ok_all = {}, True
    for j in JOINTS:
        sv = SERVOS[assign[j]]
        dem = summary["demand"][j]
        stall = sv["stall_Nm"]
        if sv["noload_rpm"]:
            w0 = sv["noload_rpm"] * 2 * math.pi / 60
            avail = stall * max(0.0, 1 - 0.5 * dem["speed_rad_s"] / w0)
        else:
            avail = None
        r1 = dem["peak"] <= RULE_PEAK * stall
        r2 = dem["walk_peak"] <= RULE_WALK * stall
        r3 = True if avail is None else dem["walk_peak"] <= avail
        rows[j] = {"servo": assign[j], "walk_Nm": dem["walk_peak"], "peak_Nm": dem["peak"],
                   "speed_rad_s": dem["speed_rad_s"], "stall_Nm": round(stall, 3),
                   "walk_pct": round(100 * dem["walk_peak"] / stall, 1),
                   "peak_pct": round(100 * dem["peak"] / stall, 1),
                   "avail_half_speed_Nm": None if avail is None else round(avail, 3),
                   "R1": r1, "R2": r2, "R3": r3 if avail is not None else "no speed data",
                   "pass": bool(r1 and r2 and r3)}
        ok_all &= rows[j]["pass"]
    return rows, ok_all


def main():
    out = {}
    for tag, assign in CONFIGS.items():
        s = run(tag, assign)
        rows, ok = score(s, assign)
        out[tag] = {"robot_mass_kg": s["robot_mass_kg"], "pass": ok,
                    "dynamic_upright": s["dynamic_upright"], "joints": rows}
        fails = [f"{j} ({r['walk_pct']}% walk / {r['peak_pct']}% peak)" for j, r in rows.items() if not r["pass"]]
        print(f"{tag:28s} {s['robot_mass_kg']*1000:6.0f} g  {'PASS' if ok else 'FAIL'}  {', '.join(fails)}")
    (RES / "compare.json").write_text(json.dumps(out, indent=2))

    # Markdown table for the docs
    lines = ["| Configuration | Mass (g) | Result | Joints failing |", "|---|---|---|---|"]
    for tag, v in out.items():
        fails = ", ".join(f"{j} {r['walk_pct']:.0f}% / {r['peak_pct']:.0f}%" for j, r in v["joints"].items()
                          if not r["pass"]) or "none"
        lines.append(f"| {tag} | {v['robot_mass_kg']*1000:.0f} | {'PASS' if v['pass'] else 'FAIL'} | {fails} |")
    sel = out[SELECTED]["joints"]
    lines += ["", f"Selected configuration {SELECTED}, per joint:", "",
              "| Joint | Servo | Walk (N m) | Peak (N m) | Stall (N m) | Walk % | Peak % | Avail. at half gait speed (N m) | Speed (rad/s) |",
              "|---|---|---|---|---|---|---|---|---|"]
    for j, r in sel.items():
        lines.append(f"| {j} | {r['servo']} | {r['walk_Nm']:.3f} | {r['peak_Nm']:.3f} | {r['stall_Nm']:.2f} | "
                     f"{r['walk_pct']:.0f} | {r['peak_pct']:.0f} | {r['avail_half_speed_Nm']} | {r['speed_rad_s']:.2f} |")
    (RES / "compare.md").write_text("\n".join(lines) + "\n")
    plot(out)


def plot(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    j = ["hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle", "neck_pitch", "head_pitch"]
    sel = out[SELECTED]["joints"]
    x = range(len(j))
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150)
    ax.bar([i - 0.2 for i in x], [sel[k]["walk_Nm"] for k in j], 0.4, label="Walking demand", color="#4C78A8")
    ax.bar([i + 0.2 for i in x], [sel[k]["peak_Nm"] for k in j], 0.4, label="Peak demand", color="#9ECAE9")
    for i, k in enumerate(j):
        st = sel[k]["stall_Nm"]
        ax.hlines(st * RULE_WALK, i - 0.42, i + 0.42, colors="#E45756", linestyles="--", lw=1.4,
                  label="40 % stall (walk limit)" if i == 0 else None)
        ax.hlines(st * RULE_PEAK, i - 0.42, i + 0.42, colors="#54A24B", lw=1.4,
                  label="70 % stall (peak limit)" if i == 0 else None)
        ax.text(i, st * RULE_PEAK + 0.015, sel[k]["servo"].split("-")[0], ha="center", fontsize=7, color="#444")
    ax.set_xticks(list(x), j, rotation=20)
    ax.set_ylabel("Torque (N m)")
    ax.set_title(f"Duccky v1.0, {SELECTED} ({out[SELECTED]['robot_mass_kg']*1000:.0f} g): "
                 "demand vs servo limits")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(RES / "demand_vs_capacity.png")


if __name__ == "__main__":
    main()
