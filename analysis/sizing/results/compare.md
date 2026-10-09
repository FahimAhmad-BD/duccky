| Configuration | Mass (g) | Result | Joints failing |
|---|---|---|---|
| A_all_XL330 | 783 | FAIL | hip_pitch 65% / 68%, knee 78% / 106%, ankle 63% / 64% |
| B_all_STS3032 | 813 | FAIL | hip_yaw 41% / 41%, hip_pitch 80% / 82%, knee 95% / 125%, ankle 77% / 78% |
| C_STS3215_legs_XL330_rest | 1005 | FAIL | hip_yaw 43% / 43% |
| D_all_STS3215 | 1338 | PASS | none |
| E_XC330_legs_XL330_rest | 813 | FAIL | knee 45% / 59% |
| F_all_XC330 | 858 | FAIL | hip_pitch 40% / 41%, knee 48% / 62% |
| G_E_plus_knee_spring | 813 | PASS | none |

Selected configuration G_E_plus_knee_spring, per joint:

| Joint | Servo | Walk (N m) | Peak (N m) | Stall (N m) | Walk % | Peak % | Avail. at half gait speed (N m) | Speed (rad/s) |
|---|---|---|---|---|---|---|---|---|
| hip_yaw | XL330-M288-T | 0.179 | 0.179 | 0.52 | 34 | 34 | 0.492 | 1.18 |
| hip_roll | XL330-M288-T | 0.129 | 0.144 | 0.52 | 25 | 28 | 0.497 | 0.94 |
| hip_pitch | XC330-M288-T | 0.352 | 0.363 | 0.93 | 38 | 39 | 0.779 | 2.75 |
| knee | XC330-M288-T | 0.297 | 0.495 | 0.93 | 32 | 53 | 0.715 | 3.93 |
| ankle | XC330-M288-T | 0.339 | 0.346 | 0.93 | 36 | 37 | 0.801 | 2.36 |
| neck_pitch | XL330-M288-T | 0.096 | 0.096 | 0.52 | 18 | 18 | 0.482 | 1.57 |
| head_pitch | XL330-M288-T | 0.057 | 0.057 | 0.52 | 11 | 11 | 0.464 | 2.36 |
| head_yaw | XL330-M288-T | 0.008 | 0.008 | 0.52 | 2 | 2 | 0.332 | 7.85 |
| head_roll | XL330-M288-T | 0.008 | 0.008 | 0.52 | 2 | 2 | 0.482 | 1.57 |
| beak | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.436 | 3.53 |
