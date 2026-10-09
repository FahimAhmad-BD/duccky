"""Render the sizing model in nominal stance (front three-quarter and side views).

Usage: MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa python render.py <model.xml> <out.png>
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np

import params as P

xml, out = sys.argv[1], sys.argv[2]
m = mujoco.MjModel.from_xml_path(xml)
d = mujoco.MjData(m)
for s in ("left", "right"):
    for k, v in P.STANCE.items():
        d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{s}_{k}")]] = v
mujoco.mj_forward(m, d)

r = mujoco.Renderer(m, 720, 540)
imgs = []
for az, el in ((145, -12), (90, -5)):
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.0, 0.0, 0.14]
    cam.distance, cam.azimuth, cam.elevation = 0.62, az, el
    r.update_scene(d, cam)
    imgs.append(r.render())
fig, ax = plt.subplots(1, 2, figsize=(10, 4), dpi=140)
for a, im, t in zip(ax, imgs, ("Three-quarter", "Side")):
    a.imshow(im)
    a.set_axis_off()
    a.set_title(t, fontsize=9)
fig.suptitle(f"Duccky v1.0 sizing model, nominal stance ({m.body_subtreemass[1]*1000:.0f} g)", fontsize=10)
fig.tight_layout()
fig.savefig(out)
print("wrote", out)
