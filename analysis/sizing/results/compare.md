| Configuration | Mass (g) | Result | Joints failing |
|---|---|---|---|
| A_all_XL330 | 798 | FAIL | hip_pitch 67% / 70%, knee 76% / 99%, ankle 64% / 65% |
| B_all_STS3032 | 828 | FAIL | hip_yaw 41% / 41%, hip_pitch 82% / 85%, knee 93% / 121%, ankle 78% / 80%, neck_pitch 46% / 76% |
| C_STS3215_legs_XL330_rest | 1020 | FAIL | hip_yaw 43% / 43% |
| D_all_STS3215 | 1353 | PASS | none |
| E_XC330_legs_XL330_rest | 828 | FAIL | knee 44% / 57% |
| F_all_XC330 | 873 | FAIL | hip_pitch 41% / 42%, knee 46% / 61% |
| G_E_plus_knee_spring | 828 | PASS | none |

Selected configuration G_E_plus_knee_spring, per joint:

| Joint | Servo | Walk (N m) | Peak (N m) | Stall (N m) | Walk % | Peak % | Avail. at half gait speed (N m) | Speed (rad/s) |
|---|---|---|---|---|---|---|---|---|
| hip_yaw | XL330-M288-T | 0.183 | 0.183 | 0.52 | 35 | 35 | 0.492 | 1.18 |
| hip_roll | XL330-M288-T | 0.132 | 0.146 | 0.52 | 25 | 28 | 0.497 | 0.94 |
| hip_pitch | XC330-M288-T | 0.362 | 0.374 | 0.93 | 39 | 40 | 0.779 | 2.75 |
| knee | XC330-M288-T | 0.290 | 0.533 | 0.93 | 31 | 57 | 0.715 | 3.93 |
| ankle | XC330-M288-T | 0.346 | 0.352 | 0.93 | 37 | 38 | 0.801 | 2.36 |
| neck_pitch | XL330-M288-T | 0.196 | 0.325 | 0.52 | 38 | 62 | 0.482 | 1.57 |
| head_pitch | XL330-M288-T | 0.120 | 0.120 | 0.52 | 23 | 23 | 0.463 | 2.36 |
| head_yaw | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.331 | 7.85 |
| head_roll | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.482 | 1.57 |
| beak | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.435 | 3.53 |
