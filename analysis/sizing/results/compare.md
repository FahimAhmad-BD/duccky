| Configuration | Mass (g) | Result | Joints failing |
|---|---|---|---|
| A_all_XL330 | 810 | FAIL | hip_pitch 68% / 71%, knee 77% / 101%, ankle 65% / 66% |
| B_all_STS3032 | 840 | FAIL | hip_yaw 42% / 42%, hip_pitch 84% / 86%, knee 94% / 123%, ankle 80% / 81%, neck_pitch 45% / 75% |
| C_STS3215_legs_XL330_rest | 1032 | FAIL | hip_yaw 44% / 44% |
| D_all_STS3215 | 1365 | PASS | none |
| E_XC330_legs_XL330_rest | 840 | FAIL | knee 45% / 58% |
| F_all_XC330 | 885 | FAIL | hip_pitch 42% / 43%, knee 47% / 61% |
| G_E_plus_knee_spring | 840 | PASS | none |

Selected configuration G_E_plus_knee_spring, per joint:

| Joint | Servo | Walk (N m) | Peak (N m) | Stall (N m) | Walk % | Peak % | Avail. at half gait speed (N m) | Speed (rad/s) |
|---|---|---|---|---|---|---|---|---|
| hip_yaw | XL330-M288-T | 0.185 | 0.185 | 0.52 | 36 | 36 | 0.492 | 1.18 |
| hip_roll | XL330-M288-T | 0.134 | 0.148 | 0.52 | 26 | 28 | 0.497 | 0.94 |
| hip_pitch | XC330-M288-T | 0.368 | 0.380 | 0.93 | 40 | 41 | 0.779 | 2.75 |
| knee | XC330-M288-T | 0.296 | 0.530 | 0.93 | 32 | 57 | 0.715 | 3.93 |
| ankle | XC330-M288-T | 0.351 | 0.357 | 0.93 | 38 | 38 | 0.801 | 2.36 |
| neck_pitch | XL330-M288-T | 0.192 | 0.320 | 0.52 | 37 | 62 | 0.482 | 1.57 |
| head_pitch | XL330-M288-T | 0.118 | 0.118 | 0.52 | 23 | 23 | 0.463 | 2.36 |
| head_yaw | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.331 | 7.85 |
| head_roll | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.482 | 1.57 |
| beak | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.435 | 3.53 |
