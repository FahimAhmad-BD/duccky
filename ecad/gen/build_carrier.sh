#!/usr/bin/env bash
# Rebuild the carrier board end to end: schematic, ERC, netlist, placement, routing,
# cleanup, DRC, STEP, renders. Run from ecad/gen in Git Bash.
set -euo pipefail
KDIR="$(cygpath -u "$LOCALAPPDATA")/Programs/KiCad/10.0/bin"
KC="$KDIR/kicad-cli.exe"
KPY="$KDIR/python.exe"
PY="${DUCCKY_PY:-$USERPROFILE/.venvs/duccky/Scripts/python.exe}"
OUT=../carrier

"$PY" carrier.py
"$KC" sch erc --format report -o "$OUT/erc.rpt" "$OUT/carrier.kicad_sch"
"$KC" sch export netlist --format kicadsexpr -o "$OUT/carrier.net" "$OUT/carrier.kicad_sch"
"$KC" sch export pdf -o "$OUT/carrier_schematic.pdf" "$OUT/carrier.kicad_sch"
# Freerouting is not deterministic: retry from a fresh placement until DRC is clean
for attempt in 1 2 3; do
  "$KPY" pcb.py place
  "$KPY" -u route.py "${PASSES:-100}" "${ROUNDS:-4}"
  "$KPY" cleanup.py
  "$KC" pcb drc --schematic-parity --severity-all --format report -o "$OUT/drc.rpt" "$OUT/carrier.kicad_pcb" > "$OUT/drc.log"
  if grep -q "Found 0 unconnected" "$OUT/drc.log"; then echo "routing attempt $attempt: complete"; break; fi
  echo "routing attempt $attempt: open connections remain"
done
"$KPY" pcb.py models
"$KC" pcb export step --subst-models --include-tracks --include-zones -o "$OUT/carrier.step" "$OUT/carrier.kicad_pcb"
"$KC" pcb export step --subst-models -o "$OUT/carrier_mech.step" "$OUT/carrier.kicad_pcb"   # light model for CAD packaging
"$KC" pcb render --side top --width 1600 --height 1300 -o "$(cygpath -w "$OUT")\carrier_top.png" "$OUT/carrier.kicad_pcb"
"$KC" pcb render --side top --perspective --rotate "-45,0,30" --width 1600 --height 1200 -o "$(cygpath -w "$OUT")\carrier_iso.png" "$OUT/carrier.kicad_pcb"
grep -E "^\*\* Found|Found [0-9]+ (unconnected|schematic)" "$OUT/drc.rpt" || true
