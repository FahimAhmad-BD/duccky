"""Remove vias that KiCad's DRC reports as dangling, then refill zones.

Run with KiCad's Python after route.py:  <kicad>/bin/python.exe cleanup.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import pcb  # noqa: E402

KICAD_CLI = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin" / "kicad-cli.exe"


def dangling_vias(pcb_path):
    out = pcb.PROJ / "drc_cleanup.json"
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--severity-all", "--format", "json", "-o", str(out), str(pcb_path)],
                   check=True, capture_output=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    out.unlink()
    pts = []
    for v in data.get("violations", []):
        if v.get("type") == "via_dangling":
            for item in v.get("items", []):
                pos = item.get("pos", {})
                pts.append((pos.get("x"), pos.get("y")))
    return pts


def main():
    pcb_path = pcb.PROJ / "carrier.kicad_pcb"
    pts = dangling_vias(pcb_path)
    board = pcbnew.LoadBoard(str(pcb_path))
    removed = 0
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        p = t.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if any(abs(x - px) < 0.01 and abs(y - py) < 0.01 for px, py in pts):
            board.Remove(t)
            removed += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(pcb_path), board)
    print(f"dangling vias reported {len(pts)}, removed {removed}")


if __name__ == "__main__":
    main()
