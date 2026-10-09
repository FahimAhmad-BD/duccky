"""
Duccky v1.0 actuator sizing (Phase 1).

Runs five load cases on the primitive model and writes a joint torque and speed
demand table. Servo scoring is done in compare.py.

  S1  single support: full robot weight as a vertical ground reaction on one
      sole, CoP swept over the sole centre and edges, crouch 0.4 to 2.0 rad
  S2  double support hip hinge: trunk pitched forward 0..80 deg, the posture
      a get-up passes through
  S3  head and beak: neck and head pitch swept over their range, beak holding
      a 30 g object at the tip
  D1  dynamic squat, full contact physics, slow and fast
  D2  drop landing from 20 mm in nominal stance (impact transient)

Joint speed demand comes from a sinusoidal gait estimate (see GAIT).
Static cases compute joint torque directly from gravity moments, so they do not
depend on controller gains. Dynamic cases use stiff, torque-unlimited PD servos
and report the torque the mechanism demanded.

Servo scoring against these demands lives in compare.py, which reruns this
script with the mass of each candidate configuration.

Usage:  python sizing.py [--servo-mass 0.018] [--override JSON] [--set JSON] [--tag name]
"""
import argparse
import csv
import json
import math
from pathlib import Path

import mujoco
import numpy as np

import build_model
import params as P

G = 9.81
HERE = Path(__file__).parent
OUT = HERE / "results"
LEG_J = ["hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle"]
HEAD_J = ["neck_pitch", "head_pitch", "head_yaw", "head_roll", "beak"]

# Gait speed estimate: step frequency and joint amplitudes (rad, half peak-to-peak)
GAIT = {"step_hz": 2.5,
        "amp": {"hip_yaw": 0.15, "hip_roll": 0.12, "hip_pitch": 0.35, "knee": 0.50, "ankle": 0.30,
                "neck_pitch": 0.20, "head_pitch": 0.30, "head_yaw": 1.00, "head_roll": 0.20, "beak": 0.45}}
DYNAMIC_FACTOR = 1.5  # applied to S1 nominal-stance torque (CoP in central 60 % of sole) for walking peaks

RULE_PEAK = 0.70  # see compare.py; recorded in the summary for traceability
RULE_WALK = 0.40


# ----------------------------------------------------------------------------- helpers
def load(servo_mass, overrides=None):
    xml = build_model.build(servo_mass, overrides=overrides)
    m = mujoco.MjModel.from_xml_string(xml)
    return m, mujoco.MjData(m), xml


def jid(m, name):
    return mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, name)


def setq(m, d, name, v):
    d.qpos[m.jnt_qposadr[jid(m, name)]] = v


def set_crouch(m, d, c, sides=("left", "right")):
    for s in sides:
        setq(m, d, f"{s}_hip_pitch", -c / 2)
        setq(m, d, f"{s}_knee", c)
        setq(m, d, f"{s}_ankle", -c / 2)


def subtree_bodies(m, root):
    out, stack = [], [root]
    while stack:
        b = stack.pop()
        out.append(b)
        stack.extend(i for i in range(m.nbody) if m.body_parentid[i] == b and i != b)
    return set(out)


def gravity_moment(m, d, joint, bodies):
    """|moment| of gravity on `bodies` about the axis of `joint` (N m)."""
    j = jid(m, joint)
    a, p = d.xaxis[j], d.xanchor[j]
    tau = 0.0
    for b in bodies:
        r = d.xipos[b] - p
        tau += np.dot(a, np.cross(r, np.array([0, 0, -m.body_mass[b] * G])))
    return abs(tau)


def quat_axis(axis, ang):
    q = np.zeros(4)
    mujoco.mju_axisAngle2Quat(q, np.array(axis, float), ang)
    return q


def qmul(a, b):
    q = np.zeros(4)
    mujoco.mju_mulQuat(q, a, b)
    return q


# ----------------------------------------------------------------------------- S1
def stance_torques(m, d, side, cop, weight):
    """Joint torques on one stance leg carrying `weight` (N) as a vertical ground
    reaction at world point `cop`, plus gravity of the leg's own distal links.
    Computed on the distal side of each joint, so it holds for any trunk motion
    that produces that ground reaction."""
    out = {}
    for jn in LEG_J:
        j = jid(m, f"{side}_{jn}")
        a, p = d.xaxis[j], d.xanchor[j]
        tau = np.dot(a, np.cross(cop - p, np.array([0, 0, weight])))
        for b in subtree_bodies(m, m.jnt_bodyid[j]):
            tau += np.dot(a, np.cross(d.xipos[b] - p, np.array([0, 0, -m.body_mass[b] * G])))
        out[jn] = abs(tau)
    return out


def sole_points(m, d, side, frac):
    """Sole centre plus edge points scaled by `frac` (1.0 = full sole outline)."""
    b = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{side}_foot")
    s = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, f"{side}_sole_site")
    R, c = d.xmat[b].reshape(3, 3), d.site_xpos[s]
    hx, hy = P.LEG["foot"][0] / 2 * frac, P.LEG["foot"][1] / 2 * frac
    pts = [(0, 0)] + [(x, y) for x in (-hx, 0, hx) for y in (-hy, 0, hy) if (x, y) != (0, 0)]
    return [c + R @ np.array([x, y, 0]) for x, y in pts]


def case_single_support(m, d):
    """Whole robot weight on the left leg. The leg has no ankle roll, so the robot
    is balanced dynamically and the centre of pressure (CoP) wanders over the sole.
    Torque is evaluated for the CoP at the sole centre and at its edges."""
    W = float(m.body_subtreemass[1]) * G
    rows = []
    for c in np.linspace(0.4, 2.0, 17):
        mujoco.mj_resetData(m, d)
        set_crouch(m, d, c)
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)
        row = {"crouch_rad": round(float(c), 3)}
        for label, frac in (("core", 0.6), ("edge", 1.0)):
            worst = {jn: 0.0 for jn in LEG_J}
            for cop in sole_points(m, d, "left", frac):
                t = stance_torques(m, d, "left", cop, W)
                worst = {jn: max(worst[jn], t[jn]) for jn in LEG_J}
            # knee assist spring carries part of the stance load
            worst["knee"] = max(0.0, worst["knee"] - P.LEG["knee_spring_k"] * c)
            for jn in LEG_J:
                row[f"{label}_{jn}"] = round(worst[jn], 4)
        rows.append(row)
    return rows


# ----------------------------------------------------------------------------- S2
def case_hip_hinge(m, d):
    all_b = set(range(1, m.nbody))
    rows = []
    for deg in range(0, 85, 5):
        th = math.radians(deg)
        mujoco.mj_resetData(m, d)
        c = 1.4  # crouched legs, as when the robot is getting up
        set_crouch(m, d, c)
        d.qpos[3:7] = quat_axis((0, 1, 0), th)
        for s in ("left", "right"):
            setq(m, d, f"{s}_hip_pitch", -c / 2 - th)
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)
        row = {"trunk_pitch_deg": deg}
        for jn in ("hip_pitch", "knee", "ankle"):
            child = m.jnt_bodyid[jid(m, f"left_{jn}")]
            prox = all_b - subtree_bodies(m, child)
            tau = gravity_moment(m, d, f"left_{jn}", prox) / 2  # two legs share
            if jn == "knee":
                tau = abs(tau - P.LEG["knee_spring_k"] * c)
            row[jn] = round(tau, 4)
        rows.append(row)
    return rows


# ----------------------------------------------------------------------------- S3
def case_head(m, d):
    rows = []
    beak_obj = 0.030
    for npitch in np.linspace(*P.HEAD["lim_neck_pitch"], 11):
        for hpitch in np.linspace(*P.HEAD["lim_head_pitch"], 11):
            mujoco.mj_resetData(m, d)
            set_crouch(m, d, -2 * P.STANCE["hip_pitch"])
            setq(m, d, "neck_pitch", npitch)
            setq(m, d, "head_pitch", hpitch)
            setq(m, d, "head_roll", P.HEAD["lim_head_roll"][1])
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            row = {"neck_pitch": round(float(npitch), 3), "head_pitch": round(float(hpitch), 3)}
            for jn in HEAD_J:
                child = m.jnt_bodyid[jid(m, jn)]
                row[jn] = gravity_moment(m, d, jn, subtree_bodies(m, child))
            # object held at beak tip adds to every head-chain joint
            beak_b = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "beak")
            tip = d.xpos[beak_b] + d.xmat[beak_b].reshape(3, 3) @ np.array([P.HEAD["beak_len"], 0, 0])
            for jn in HEAD_J:
                j = jid(m, jn)
                r = tip - d.xanchor[j]
                row[jn] = round(row[jn] + abs(np.dot(d.xaxis[j], np.cross(r, [0, 0, -beak_obj * G]))), 4)
            rows.append(row)
    return rows


# ----------------------------------------------------------------------------- D1, D2
JOINTS = build_model.JOINTS


def stance_ctrl(m, c):
    ctrl = np.zeros(m.nu)
    for i, j in enumerate(JOINTS):
        s = j.split("_")[0]
        if j.endswith("hip_pitch"):
            ctrl[i] = -c / 2
        elif j.endswith("knee"):
            ctrl[i] = c
        elif j.endswith("ankle"):
            ctrl[i] = -c / 2
    return ctrl


def settle(m, d, c, t=1.0):
    mujoco.mj_resetData(m, d)
    set_crouch(m, d, c)
    d.qpos[2] += 0.001
    d.ctrl[:] = stance_ctrl(m, c)
    for _ in range(int(t / m.opt.timestep)):
        mujoco.mj_step(m, d)


def case_squat(m, d, hz, cycles=3):
    c0, c1 = 0.6, 1.8
    settle(m, d, c0)
    peak = np.zeros(m.nu)
    upright = True
    n = int(cycles / hz / m.opt.timestep)
    for k in range(n):
        t = k * m.opt.timestep
        c = c0 + (c1 - c0) * 0.5 * (1 - math.cos(2 * math.pi * hz * t))
        d.ctrl[:] = stance_ctrl(m, c)
        mujoco.mj_step(m, d)
        peak = np.maximum(peak, np.abs(d.actuator_force))
        if d.qpos[2] < 0.05:
            upright = False
    return peak, upright


def case_drop(m, d, h=0.020):
    c = -2 * P.STANCE["hip_pitch"]
    settle(m, d, c)
    d.qpos[2] += h
    d.qvel[:] = 0
    peak = np.zeros(m.nu)
    for _ in range(int(0.6 / m.opt.timestep)):
        mujoco.mj_step(m, d)
        peak = np.maximum(peak, np.abs(d.actuator_force))
    return peak, d.qpos[2] > 0.05


# ----------------------------------------------------------------------------- main
def write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--servo-mass", type=float, default=P.SERVO["mass"])
    ap.add_argument("--tag", default="baseline")
    ap.add_argument("--override", default="{}", help='JSON, e.g. {"knee": 0.055}')
    ap.add_argument("--set", default="{}", help='JSON param overrides, e.g. {"LEG.thigh": 0.05}')
    a = ap.parse_args()
    out = OUT / a.tag
    out.mkdir(parents=True, exist_ok=True)

    for k, v in json.loads(a.set).items():
        grp, key = k.split(".")
        getattr(P, grp)[key] = tuple(v) if isinstance(v, list) else v
    overrides = json.loads(a.override)
    m, d, xml = load(a.servo_mass, overrides)
    (out / "duccky_sizing.xml").write_text(xml)
    mass = float(m.body_subtreemass[1])

    s1 = case_single_support(m, d)
    s2 = case_hip_hinge(m, d)
    s3 = case_head(m, d)
    write_csv(out / "S1_single_support.csv", s1)
    write_csv(out / "S2_hip_hinge.csv", s2)
    write_csv(out / "S3_head.csv", s3)

    dyn = {}
    for name, fn in {"D1_squat_0.5Hz": lambda: case_squat(m, d, 0.5),
                     "D1_squat_1.5Hz": lambda: case_squat(m, d, 1.5),
                     "D2_drop_20mm": lambda: case_drop(m, d)}.items():
        pk, ok = fn()
        dyn[name] = {"upright": bool(ok), **{j: round(float(v), 4) for j, v in zip(JOINTS, pk)}}
    (out / "D_dynamic.json").write_text(json.dumps(dyn, indent=2))

    # ---- demand table per joint group
    nominal = min(s1, key=lambda r: abs(r["crouch_rad"] - (-2 * P.STANCE["hip_pitch"])))
    deep = [r for r in s1 if r["crouch_rad"] <= 1.81]
    table = {}
    for jn in LEG_J:
        static_peak = max(r[f"edge_{jn}"] for r in deep)
        hinge = max(r.get(jn, 0) for r in s2) if jn in ("hip_pitch", "knee", "ankle") else 0.0
        dyn_peak = max(max(v[f"left_{jn}"], v[f"right_{jn}"]) for v in dyn.values())
        walk = nominal[f"core_{jn}"] * DYNAMIC_FACTOR
        table[jn] = {"walk_peak": walk, "peak": max(static_peak, hinge, dyn_peak, walk),
                     "static_single_support_max": static_peak, "hip_hinge_max": hinge,
                     "dynamic_max": dyn_peak}
    # swing knee: spring torque at the deepest fold plus the foot and shank weight
    swing = P.LEG["knee_spring_k"] * P.LEG["knee_swing_max"] + (P.LEG["m_shank"] + P.LEG["m_foot"]
             + overrides.get("ankle", a.servo_mass)) * G * P.LEG["shank"]
    table["knee"]["swing_spring_check"] = swing
    table["knee"]["peak"] = max(table["knee"]["peak"], swing)
    # hip yaw: gravity gives ~0; worst case is an in-place pivot under full load
    pivot = 0.9 * mass * G * P.LEG["foot"][0] / 3
    table["hip_yaw"]["pivot_friction_worst"] = pivot
    table["hip_yaw"]["peak"] = max(table["hip_yaw"]["peak"], pivot)
    table["hip_yaw"]["walk_peak"] = pivot  # conservative: turning in place under full load
    for jn in HEAD_J:
        sp = max(r[jn] for r in s3)
        dp = max(v[jn] for v in dyn.values())
        table[jn] = {"walk_peak": sp, "peak": max(sp, dp), "static_max": sp, "dynamic_max": dp}
    for jn in table:
        amp = GAIT["amp"][jn]
        table[jn]["speed_rad_s"] = 2 * math.pi * GAIT["step_hz"] * amp / 2  # stride period = 2 steps
        table[jn] = {k: round(v, 4) for k, v in table[jn].items()}

    summary = {"tag": a.tag, "servo_mass_kg": a.servo_mass, "servo_mass_overrides": overrides,
               "param_overrides": json.loads(a.set), "robot_mass_kg": round(mass, 4),
               "nominal_crouch_rad": nominal["crouch_rad"], "gait": GAIT,
               "dynamic_factor": DYNAMIC_FACTOR, "rules": {"peak": RULE_PEAK, "walk": RULE_WALK},
               "dynamic_upright": {k: v["upright"] for k, v in dyn.items()},
               "demand": table}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"mass": summary["robot_mass_kg"], "upright": summary["dynamic_upright"]}, indent=1))
    for jn, t in table.items():
        print(f"{jn:11s} walk {t['walk_peak']:.3f}  peak {t['peak']:.3f} N m   speed {t['speed_rad_s']:.2f} rad/s")


if __name__ == "__main__":
    main()
