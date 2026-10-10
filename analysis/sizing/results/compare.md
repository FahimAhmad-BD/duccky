| Configuration | Mass (g) | Result | Joints failing |
|---|---|---|---|
| A_all_XL330 | 795 | FAIL | hip_pitch 66% / 69%, knee 79% / 106%, ankle 64% / 65% |
| B_all_STS3032 | 825 | FAIL | hip_yaw 41% / 41%, hip_pitch 81% / 84%, knee 96% / 126%, ankle 78% / 80% |
| C_STS3215_legs_XL330_rest | 1017 | FAIL | hip_yaw 43% / 43% |
| D_all_STS3215 | 1350 | PASS | none |
| E_XC330_legs_XL330_rest | 825 | FAIL | knee 46% / 60% |
| F_all_XC330 | 870 | FAIL | hip_pitch 41% / 42%, knee 48% / 63% |
| G_E_plus_knee_spring | 825 | PASS | none |

Selected configuration G_E_plus_knee_spring, per joint:

| Joint | Servo | Walk (N m) | Peak (N m) | Stall (N m) | Walk % | Peak % | Avail. at half gait speed (N m) | Speed (rad/s) |
|---|---|---|---|---|---|---|---|---|
| hip_yaw | XL330-M288-T | 0.182 | 0.182 | 0.52 | 35 | 35 | 0.492 | 1.18 |
| hip_roll | XL330-M288-T | 0.131 | 0.146 | 0.52 | 25 | 28 | 0.497 | 0.94 |
| hip_pitch | XC330-M288-T | 0.357 | 0.368 | 0.93 | 38 | 40 | 0.779 | 2.75 |
| knee | XC330-M288-T | 0.304 | 0.494 | 0.93 | 33 | 53 | 0.715 | 3.93 |
| ankle | XC330-M288-T | 0.344 | 0.351 | 0.93 | 37 | 38 | 0.801 | 2.36 |
| neck_pitch | XL330-M288-T | 0.096 | 0.096 | 0.52 | 18 | 18 | 0.482 | 1.57 |
| head_pitch | XL330-M288-T | 0.057 | 0.057 | 0.52 | 11 | 11 | 0.463 | 2.36 |
| head_yaw | XL330-M288-T | 0.008 | 0.008 | 0.52 | 2 | 2 | 0.331 | 7.85 |
| head_roll | XL330-M288-T | 0.008 | 0.008 | 0.52 | 2 | 2 | 0.482 | 1.57 |
| beak | XL330-M288-T | 0.012 | 0.012 | 0.52 | 2 | 2 | 0.435 | 3.53 |
