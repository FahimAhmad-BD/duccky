"""Autoroute the carrier board with Freerouting, then pour outer GND and fill zones.

Run with KiCad's Python:  <kicad>/bin/python.exe route.py [passes] [rounds]

Freerouting (GPL, free) runs headless on the Specctra DSN that KiCad exports; the
session (.ses) is imported back. Each further round re-exports the routed board so
Freerouting only works on the connections still open. Paths to Java 25 and the
Freerouting jar come from DUCCKY_JAVA and DUCCKY_FREEROUTING, with defaults under
%USERPROFILE%/tools.
"""
import math
import os
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import pcb  # noqa: E402

PROJ = pcb.PROJ
TOOLS = Path(os.environ["USERPROFILE"]) / "tools"
JAVA = Path(os.environ.get("DUCCKY_JAVA", next((TOOLS / "jdk25").glob("*/bin/java.exe"), "java")))
JAR = Path(os.environ.get("DUCCKY_FREEROUTING", TOOLS / "freerouting" / "freerouting-2.5.0.jar"))


def unrouted(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    conn = board.GetConnectivity()
    conn.RecalculateRatsnest()
    return conn.GetUnconnectedCount(False)


def freeroute(board, passes, log):
    dsn, ses = PROJ / "carrier.dsn", PROJ / "carrier.ses"
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("DSN export failed")
    cmd = [str(JAVA), "-jar", str(JAR), "-de", str(dsn), "-do", str(ses), "-mp", str(passes)]
    subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True,
                   env={**os.environ, "FREEROUTING__GUI__ENABLED": "false"})
    if not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise SystemExit("SES import failed")


def _fill(board, net, layer):
    for z in board.Zones():
        if z.GetNetname() == pcb.N(net) and z.GetLayer() == layer:
            return z.GetFilledPolysList(layer)
    return None


def stitch(board, net, via_d=0.8, drill=0.4, step=0.5):
    """Drop stitching vias so every top layer island of a power pour reaches the
    bottom layer pour of the same net. One via per island, two for large islands."""
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    top, bot = _fill(board, net, pcbnew.F_Cu), _fill(board, net, pcbnew.B_Cu)
    if top is None or bot is None:
        return 0
    margin = pcbnew.FromMM(via_d / 2 + 0.05)
    safe_top, safe_bot = pcbnew.SHAPE_POLY_SET(top), pcbnew.SHAPE_POLY_SET(bot)
    for s in (safe_top, safe_bot):
        s.Deflate(margin, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.005))
    netinfo = board.FindNet(pcb.N(net))
    me = pcb.N(net)
    clr = 0.25
    r_via = via_d / 2
    # Obstacles of other nets on any layer: (kind, geometry, keepout radius in mm)
    segs, circles, boxes = [], [], []
    for t in board.GetTracks():
        if t.GetNetname() == me:
            if t.Type() == pcbnew.PCB_VIA_T:
                circles.append((t.GetPosition(), 1.0 + r_via))       # spacing between our own vias
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            circles.append((t.GetPosition(), pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2 + r_via + clr))
        else:
            segs.append((t.GetStart(), t.GetEnd(), pcbnew.ToMM(t.GetWidth()) / 2 + r_via + clr))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            same = pad.GetNetname() == me
            bb = pad.GetBoundingBox()
            k = (0.0 if same else clr) + r_via
            if pad.HasHole() or not same:
                boxes.append((pcbnew.ToMM(bb.GetLeft()) - k, pcbnew.ToMM(bb.GetTop()) - k,
                              pcbnew.ToMM(bb.GetRight()) + k, pcbnew.ToMM(bb.GetBottom()) + k))

    def clear(p):
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        for c, r in circles:
            if math.hypot(x - pcbnew.ToMM(c.x), y - pcbnew.ToMM(c.y)) < r:
                return False
        for a, b, r in segs:
            ax, ay, bx, by = pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            u = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
            if math.hypot(x - (ax + u * dx), y - (ay + u * dy)) < r:
                return False
        return not any(b0 <= x <= b2 and b1 <= y <= b3 for b0, b1, b2, b3 in boxes)

    added = 0
    for i in range(top.OutlineCount()):
        island = top.Outline(i)
        want = 2 if island.Area() / 1e12 > 40 else 1
        bb = island.BBox()
        x = bb.GetX()
        got = []
        while x < bb.GetRight() and len(got) < want:
            y = bb.GetY()
            while y < bb.GetBottom() and len(got) < want:
                p = pcbnew.VECTOR2I(int(x), int(y))
                if island.PointInside(p) and safe_top.Contains(p) and safe_bot.Contains(p) and clear(p) and \
                        all((p - q).EuclideanNorm() > pcbnew.FromMM(3) for q in got):
                    got.append(p)
                    circles.append((p, 1.0 + r_via))
                y += pcbnew.FromMM(step)
            x += pcbnew.FromMM(step)
        for p in got:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(p)
            v.SetWidth(pcbnew.FromMM(via_d))
            v.SetDrill(pcbnew.FromMM(drill))
            v.SetNet(netinfo)
            board.Add(v)
            added += 1
    return added


def remove_dangling_vias(board):
    """Delete vias that connect copper on fewer than two layers (router leftovers)."""
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    conn = board.GetConnectivity()
    layers = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    dead = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T
            and sum(1 for ly in layers if conn.IsConnectedOnLayer(t, ly)) < 2]
    for v in dead:
        board.Remove(v)
    return len(dead)


def main(passes, rounds):
    pcb_path = PROJ / "carrier.kicad_pcb"
    board = pcbnew.LoadBoard(str(pcb_path))
    with open(PROJ / "freerouting.log", "w", encoding="utf-8") as log:
        for r in range(rounds):
            freeroute(board, passes, log)
            left = unrouted(board)
            print(f"round {r + 1}: {left} unrouted", flush=True)
            if left == 0:
                break
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        pcb.add_zone(board, "GND", layer)
    # Top layer copies of the power pours join pins the router reached only by via
    for net, rect in pcb.POWER_POURS.items():
        pcb.add_zone(board, net, pcbnew.F_Cu, rect=rect, priority=10)
    for net in pcb.POWER_POURS:
        print(f"stitching vias {net}: {stitch(board, net)}")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(pcb_path), board)
    print("routed and saved", pcb_path)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60, int(sys.argv[2]) if len(sys.argv) > 2 else 4)
