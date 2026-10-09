"""
Generate the Duccky v1.0 primitive sizing model (MJCF) from params.py.

Bodies are boxes, capsules and ellipsoids with budgeted masses. Every actuated
joint carries a servo mass placed at its housing location in the parent link.
Actuators are stiff position servos with no torque limit, so simulated runs
report the torque the mechanism *demands*, not what a servo could deliver.

Usage:
    python build_model.py [--servo-mass 0.018] [--out duccky_sizing.xml]
"""
import argparse
from pathlib import Path

import params as P


def f(*v):
    return " ".join(f"{x:.5g}" for x in v)


def servo_geom(name, pos, mass):
    sx, sy, sz = P.SERVO["box"]
    return (f'<geom name="{name}" type="box" size="{f(sx/2, sy/2, sz/2)}" pos="{f(*pos)}" '
            f'mass="{mass:.5g}" class="servo"/>')


def leg(side, sign, ms):
    L = P.LEG
    hx, hy, hz = L["foot"]
    thigh, shank = L["thigh"], L["shank"]
    s = side
    return f"""
    <body name="{s}_hip_yaw_link" pos="{f(0, sign*L['hip_y'], 0)}">
      <joint name="{s}_hip_yaw" axis="0 0 1" range="{f(*L['lim_hip_yaw'])}"/>
      <geom type="box" size="0.012 0.012 0.008" pos="0 0 -0.008" mass="{L['m_hip_bracket']}" class="struct"/>
      {servo_geom(s+'_servo_hip_roll', (0, 0, -L['yaw_to_roll']), ms('hip_roll'))}
      <body name="{s}_hip_roll_link" pos="{f(0, 0, -L['yaw_to_roll'])}">
        <joint name="{s}_hip_roll" axis="1 0 0" range="{f(*L['lim_hip_roll'])}"/>
        <geom type="box" size="0.012 0.014 0.006" pos="0 0 -0.006" mass="{L['m_hip_bracket']}" class="struct"/>
        {servo_geom(s+'_servo_hip_pitch', (0, 0, -L['roll_to_pitch']), ms('hip_pitch'))}
        <body name="{s}_thigh" pos="{f(0, 0, -L['roll_to_pitch'])}">
          <joint name="{s}_hip_pitch" axis="0 1 0" range="{f(*L['lim_hip_pitch'])}"/>
          <geom type="capsule" fromto="0 0 0 0 0 {-thigh:.5g}" size="0.012" mass="{L['m_thigh']}" class="struct"/>
          {servo_geom(s+'_servo_knee', (0, 0, -thigh), ms('knee'))}
          <site name="{s}_knee_site" pos="0 0 {-thigh:.5g}"/>
          <body name="{s}_shank" pos="0 0 {-thigh:.5g}">
            <joint name="{s}_knee" axis="0 1 0" range="{f(*L['lim_knee'])}" stiffness="{L['knee_spring_k']:.5g}" springref="0"/>
            <geom type="capsule" fromto="0 0 0 0 0 {-shank:.5g}" size="0.011" mass="{L['m_shank']}" class="struct"/>
            {servo_geom(s+'_servo_ankle', (0, 0, -shank), ms('ankle'))}
            <body name="{s}_foot" pos="0 0 {-shank:.5g}">
              <joint name="{s}_ankle" axis="0 1 0" range="{f(*L['lim_ankle'])}"/>
              <geom name="{s}_sole" type="box" size="{f(hx/2, hy/2, hz/2)}"
                    pos="{f(-L['foot_ankle_x'], 0, -L['ankle_to_sole'] - hz/2)}"
                    mass="{L['m_foot']}" class="foot"/>
              <site name="{s}_sole_site" pos="{f(-L['foot_ankle_x'], 0, -L['ankle_to_sole'] - hz)}"/>
            </body>
          </body>
        </body>
      </body>
    </body>"""


def head(ms):
    H = P.HEAD
    hx, hy, hz = H["head_size"]
    return f"""
    <body name="neck" pos="{f(*H['neck_base'])}">
      <joint name="neck_pitch" axis="0 1 0" range="{f(*H['lim_neck_pitch'])}"/>
      <geom type="capsule" fromto="0 0 0 0 0 {H['neck_len']:.5g}" size="0.010" mass="{H['m_neck']}" class="struct"/>
      {servo_geom('servo_head_pitch', (0, 0, H['neck_len']), ms('head_pitch'))}
      <body name="head_pitch_link" pos="0 0 {H['neck_len']:.5g}">
        <joint name="head_pitch" axis="0 1 0" range="{f(*H['lim_head_pitch'])}"/>
        {servo_geom('servo_head_yaw', (0, 0, H['pitch_to_yaw']*0.5), ms('head_yaw'))}
        <body name="head_yaw_link" pos="0 0 {H['pitch_to_yaw']:.5g}">
          <joint name="head_yaw" axis="0 0 1" range="{f(*H['lim_head_yaw'])}"/>
          {servo_geom('servo_head_roll', (0, 0, H['yaw_to_roll']*0.5), ms('head_roll'))}
          <body name="head" pos="0 0 {H['yaw_to_roll']:.5g}">
            <joint name="head_roll" axis="1 0 0" range="{f(*H['lim_head_roll'])}"/>
            <geom name="head_shell" type="ellipsoid" size="{f(hx/2, hy/2, hz/2)}" pos="0.008 0 {hz/2:.5g}"
                  mass="{H['m_head_struct'] + H['m_head_payload']:.5g}" class="body"/>
            {servo_geom('servo_beak', (0.020, 0, 0.012), ms('beak'))}
            <site name="camera" pos="{hx/2:.5g} 0 {hz*0.65:.5g}"/>
            <body name="beak" pos="{hx/2:.5g} 0 0.014">
              <joint name="beak" axis="0 1 0" range="{f(*H['lim_beak'])}"/>
              <geom type="box" size="{H['beak_len']/2:.5g} 0.016 0.004" pos="{H['beak_len']/2:.5g} 0 -0.004"
                    mass="{H['m_beak']}" class="body"/>
            </body>
          </body>
        </body>
      </body>
    </body>"""


JOINTS = [
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
    "neck_pitch", "head_pitch", "head_yaw", "head_roll", "beak",
]


def stance_hip_height():
    """Trunk origin height that puts both soles on the floor in the STANCE pose."""
    import math
    L, S = P.LEG, P.STANCE
    th = L["thigh"] * math.cos(S["hip_pitch"]) + L["shank"] * math.cos(S["hip_pitch"] + S["knee"])
    return L["yaw_to_roll"] + L["roll_to_pitch"] + th + L["ankle_to_sole"] + L["foot"][2]


def build(servo_mass=P.SERVO["mass"], kp=40.0, overrides=None):
    """servo_mass: default kg per servo. overrides: {joint_suffix: kg}, e.g. {"knee": 0.055}."""
    overrides = overrides or {}

    def ms(j):
        return overrides.get(j, servo_mass)

    T = P.TRUNK
    tx, ty, tz = T["size"]
    hip_height = stance_hip_height()
    payload = T["payload"]
    # Trunk servos: two hip yaw + neck pitch
    trunk_servos = "\n    ".join([
        servo_geom("left_servo_hip_yaw", (0, P.LEG["hip_y"], 0.010), ms("hip_yaw")),
        servo_geom("right_servo_hip_yaw", (0, -P.LEG["hip_y"], 0.010), ms("hip_yaw")),
        servo_geom("servo_neck_pitch", (P.HEAD["neck_base"][0], 0, P.HEAD["neck_base"][2] - 0.012), ms("neck_pitch")),
    ])
    # Payload lumped as boxes at their intended locations
    bat = payload["battery_npf550"]
    rest = sum(v for k, v in payload.items() if k != "battery_npf550")
    acts = "\n    ".join(
        f'<position name="{j}" joint="{j}" kp="{kp}" kv="0.4" inheritrange="1"/>' for j in JOINTS)
    sensors = "\n    ".join(
        [f'<actuatorfrc name="tau_{j}" actuator="{j}"/>' for j in JOINTS] +
        [f'<jointvel name="vel_{j}" joint="{j}"/>' for j in JOINTS] +
        ['<framequat name="trunk_quat" objtype="body" objname="trunk"/>',
         '<subtreecom name="com" body="trunk"/>'])

    xml = f"""<mujoco model="duccky_v1_sizing">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="0.002" integrator="implicitfast"/>
  <default>
    <joint damping="0.05" armature="0.005" frictionloss="0.01"/>
    <geom contype="0" conaffinity="0" rgba="0.85 0.82 0.72 1"/>
    <default class="struct"><geom rgba="0.35 0.35 0.38 1"/></default>
    <default class="servo"><geom rgba="0.12 0.12 0.12 1"/></default>
    <default class="body"><geom rgba="0.96 0.86 0.45 1" contype="1" conaffinity="1"/></default>
    <default class="foot"><geom rgba="0.95 0.55 0.15 1" contype="1" conaffinity="1" friction="0.9 0.02 0.001"/></default>
  </default>
  <visual><global offwidth="1280" offheight="960"/></visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1=".9 .9 .9" rgb2=".8 .8 .8" width="256" height="256"/>
    <material name="grid" texture="grid" texrepeat="16 16"/>
  </asset>
  <worldbody>
    <light pos="0.3 -0.3 1" dir="-0.3 0.3 -1"/>
    <geom name="floor" type="plane" size="2 2 0.05" material="grid" contype="1" conaffinity="1"/>
    <body name="trunk" pos="0 0 {hip_height:.5g}">
      <freejoint name="root"/>
      <site name="imu" pos="0 0 0.020"/>
      <geom name="trunk_shell" type="box" size="{f(tx/2, ty/2, tz/2)}" pos="{f(*T['com_offset'])}"
            mass="{rest:.5g}" class="body"/>
      <geom name="battery" type="box" size="0.035 0.019 0.010" pos="-0.004 0 0.012" mass="{bat:.5g}"
            rgba="0.2 0.4 0.8 1"/>
    {trunk_servos}
    {leg('left', 1, ms)}
    {leg('right', -1, ms)}
    {head(ms)}
    </body>
  </worldbody>
  <actuator>
    {acts}
  </actuator>
  <sensor>
    <accelerometer name="accel" site="imu"/>
    <gyro name="gyro" site="imu"/>
    {sensors}
  </sensor>
</mujoco>
"""
    return xml


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--servo-mass", type=float, default=P.SERVO["mass"])
    ap.add_argument("--out", default=str(Path(__file__).with_name("duccky_sizing.xml")))
    a = ap.parse_args()
    Path(a.out).write_text(build(a.servo_mass))
    print("wrote", a.out)
