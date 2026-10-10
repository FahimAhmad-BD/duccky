# Fusion tools

Duccky drives Fusion through the standalone **Claude Fusion Bridge** add-in
(private repo `FahimAhmad-BD/claude-fusion-bridge`, cloned at `C:\Users\fahim\dev\claude-fusion-bridge`).
Install that add-in once in Fusion; do not install a second copy.

* `fusion_run.sh <job.py> [timeout]` sends a job to the bridge and prints the result JSON.
* `jobs/` holds Duccky's Fusion jobs (`ping.py` checks the link).
