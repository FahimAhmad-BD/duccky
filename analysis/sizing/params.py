"""
Duccky v1.0 sizing parameters (Phase 1).

Single source of truth for the primitive sizing model. Every length is in metres,
every mass in kilograms. Frame convention: x forward, y left, z up.

These values are the Phase 0 design targets. In Phase 3 they are replaced by
values exported from the Fusion master assembly (joint frames, masses, inertias),
and the same generator rebuilds the model.
"""

SERVO = {
    # Mass applied per actuated joint. 18 g is the XL330-M288 class; the sizing
    # script re-runs with heavier candidates to check the mass sensitivity.
    "mass": 0.018,  # default; per-joint masses come from compare.py
    "box": (0.034, 0.020, 0.026),  # envelope, used only for visual/collision
}

TRUNK = {
    # trunk origin height is derived from STANCE so the soles sit on the floor
    "size": (0.090, 0.096, 0.070),  # full box size x, y, z (width from CAD: yaw servos at +-34 mm, cad/lib/trunk.py)
    "com_offset": (-0.0018, 0.0, 0.0162),  # trunk non-servo CoM from the CAD export (analysis/mass)
    # Non-servo payload carried by the trunk (kg), from the CAD mass report (analysis/mass/mass_report.md):
    # printed parts and cells measured in Fusion, the rest kept as DCK-00 allocations
    "payload": {
        "battery_pack": 0.1232,       # 2 cells (92 g) + tray and lid (30.6 g)
        "cad_trunk_rest": 0.1964,     # trunk frame, neck mount, board, computer, sensors, harness, fasteners, shells
    },
}

LEG = {
    "hip_y": 0.034,          # lateral offset of each hip yaw axis from centreline
    "yaw_to_roll": 0.014,    # vertical drop hip yaw -> hip roll (analysis/layout/leg_layout.py)
    "roll_to_pitch": 0.0307, # vertical drop hip roll -> hip pitch (leg_layout.py: roll clearance)
    "thigh": 0.052,          # hip pitch -> knee (shortened from 56 to hold height <= 30 cm)
    "shank": 0.046,          # knee -> ankle (shortened from 50; shorter than thigh cuts the knee lever arm)
    "ankle_to_sole": 0.013,  # ankle axis -> sole (leg_layout.py: ankle servo lies in the foot)
    "foot": (0.075, 0.036, 0.008),  # sole box full size
    "foot_ankle_x": -0.006,  # ankle axis x relative to foot centre (negative: ankle 6 mm behind, foot extends forward)
    # Printed + fastener mass per link (servo mass is added separately)
    "m_hip_bracket": 0.0097,    # CAD: yaw link 6.2 g and roll link 9.2 g averaged, + 2 g idler and screws
    "m_thigh": 0.0099,          # CAD 7.9 g + 2 g idler and screws
    "m_shank": 0.0141,          # CAD 9.1 g + 2 g idler + 3 g knee spring (LTL048J 04)
    "m_foot": 0.0148,           # CAD 12.8 g + 2 g idler and screws
    # Parallel knee assist spring (N m/rad, rest angle = straight knee). It extends
    # the knee against gravity in stance; 0 disables it.
    "knee_spring_k": 0.0,
    "knee_swing_max": 1.60,  # deepest knee fold in swing, for the spring penalty check
    # Joint limits (rad)
    "lim_hip_yaw": (-0.50, 0.50),
    "lim_hip_roll": (-0.40, 0.40),
    "lim_hip_pitch": (-1.60, 1.60),
    "lim_knee": (-0.10, 2.20),
    "lim_ankle": (-1.40, 1.40),
}

HEAD = {
    "neck_base": (0.030, 0.0, 0.058),  # neck pitch axis relative to trunk origin (cad/lib/head.py)
    "neck_vec": (0.038, 0.0, 0.0),        # neck link runs forward (cad/lib/head.py)
    "pitch_to_yaw_vec": (0.0, 0.0, 0.039),     # head pitch axis -> head yaw joint (yaw axis above the head pitch axis)
    "yaw_to_roll_vec": (0.0, 0.0, 0.0155),     # head yaw joint -> head roll axis (cad/lib/head.py)
    "head_size": (0.070, 0.060, 0.050),
    "beak_len": 0.040,
    "m_neck": 0.0109,           # CAD neck plates 6.9 g + 4 g idlers
    "m_head_struct": 0.0707,    # CAD head shell 47.9 + head base 13.9 + yaw link 6.9 g + 2 g idler
    "m_head_payload": 0.012,  # camera, ToF, wiring
    "m_beak": 0.010,
    "lim_neck_pitch": (-1.50, 0.70),    # clear range from cad/build/head_skeleton.py, 0.1 rad margin
    "lim_head_pitch": (-0.80, 1.50),    # clear range from cad/build/head_skeleton.py, 0.1 rad margin
    "lim_head_yaw": (-2.90, 2.90),
    "lim_head_roll": (-0.45, 0.45),
    "lim_beak": (0.0, 0.70),
}

# Nominal stance used as the reference pose (rad): slight crouch, standard for
# small bipeds so the knee never locks straight.
#   hip_pitch < 0 swings the knee forward, knee > 0 folds the shank back,
#   ankle = -(hip_pitch + knee) keeps the sole flat.
STANCE = {"hip_pitch": -0.40, "knee": 0.80, "ankle": -0.40}
