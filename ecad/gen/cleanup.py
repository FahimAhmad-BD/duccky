"""Remove vias and track stubs that KiCad's DRC reports as dangling, then refill zones.

Removing a dangling via can leave the stub that led to it dangling, so the check repeats
until DRC reports neither. Run with KiCad's Python after route.py:
    <kicad>/bin/python.exe cleanup.py
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import pcb  # noqa: E402

KICAD_CLI = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "bin" / "kicad-cli.exe"


def dangling(pcb_path):
    out = pcb.PROJ / "drc_cleanup.json"
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--severity-all", "--format", "json", "-o", str(out), str(pcb_path)],
                   check=True, capture_output=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    out.unlink()
    pts = {"via_dangling": [], "track_dangling": []}
    for v in data.get("violations", []):
        if v.get("type") in pts:
            for item in v.get("items", []):
                pos = item.get("pos", {})
                pts[v["type"]].append((pos.get("x"), pos.get("y")))
    return pts


def _on_segment(px, py, t):
    ax, ay = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
    bx, by = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + u * dx), py - (ay + u * dy)) < 0.01


def main():
    pcb_path = pcb.PROJ / "carrier.kicad_pcb"
    total = 0
    board = pcbnew.LoadBoard(str(pcb_path))   # load once: a second LoadBoard in one process fails
    for _ in range(5):
        pts = dangling(pcb_path)
        if not pts["via_dangling"] and not pts["track_dangling"]:
            break
        for t in list(board.GetTracks()):
            if t.Type() == pcbnew.PCB_VIA_T:
                p = t.GetPosition()
                x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
                if any(abs(x - px) < 0.01 and abs(y - py) < 0.01 for px, py in pts["via_dangling"]):
                    board.Remove(t)
                    total += 1
            elif any(_on_segment(px, py, t) for px, py in pts["track_dangling"]):
                board.Remove(t)
                total += 1
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(str(pcb_path), board)
    print(f"dangling vias and stubs removed: {total}")


if __name__ == "__main__":
    main()
