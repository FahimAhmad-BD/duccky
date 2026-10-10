"""Build the carrier PCB from the netlist: outline, stackup, placement, net classes, zones.

Run with KiCad's Python:  <kicad>/bin/python.exe pcb.py place
Then route:               python route.py   (Freerouting, see route.py)

Board origin is the top left corner, x right, y down (KiCad convention), in mm.
The Radxa ZERO 3W sits above the board on the 2 x 20 socket; its four holes use the
Raspberry Pi Zero pattern (58 x 23 mm), which the ZERO 3W shares (65 x 30 mm board).
"""
import json
import math
import os
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexpr import find, find_all, parse  # noqa: E402

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent / "carrier"
FP_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "share" / "kicad" / "footprints"
PROJECT_LIB = HERE.parent / "lib" / "duccky.pretty"

BOARD_W, BOARD_H = 76.0, 62.0
SBC = (5.5, 1.0)                      # SBC board top left corner on the carrier
SBC_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)]

# Net classes: (track width, clearance, via diameter, via drill) in mm
CLASSES = {
    "Default": (0.20, 0.15, 0.6, 0.3),
    "Power": (0.30, 0.15, 0.6, 0.3),
    "HighCurrent": (0.40, 0.15, 0.8, 0.4),
}
NET_CLASS = {
    "HighCurrent": ["VBAT", "VSYS", "SW_SERVO", "V5_SERVO"],
    "Power": ["V5_SYS", "3V3", "VBUS", "SW_SYS", "CHG_PMID", "CHG_SW", "CHG_SNS", "IMON",
              "BAT_MID", "CHG_CBSET", "SPK_P", "SPK_N"],
}

# B.Cu power pours (x0, y0, x1, y1): battery entry to eFuse, eFuse output to both bucks
POWER_POURS = {"VBAT": (0.5, 31.0, 18.2, 49.0), "VSYS": (19.0, 31.0, 47.0, 49.0)}

# Fixed placements: ref -> (x, y, rotation deg). Connectors on the edges, ICs in their zones.
FIXED = {
    # Mounting holes on the SBC pattern (also the trunk standoffs)
    **{f"H{i + 1}": (SBC[0] + hx, SBC[1] + hy, 0) for i, (hx, hy) in enumerate(SBC_HOLES)},
    "J5": None,                                   # SBC socket: placed by place_socket()
    # Left edge: battery, cell sense, main switch, debug
    "J1": (3.2, 41.5, 270), "J2": (3.5, 51.5, 270), "J3": (3.5, 19.5, 270), "J6": (3.5, 12.0, 270),
    # Right edge: USB-C charge, head board, speaker
    "J4": (72.5, 46.0, 90), "J14": (72.0, 16.5, 90), "J13": (72.0, 35.0, 90),
    # Bottom edge: six servo ports, two per chain
    "J7": (8.0, 58.5, 0), "J8": (19.5, 58.5, 0), "J9": (31.0, 58.5, 0),
    "J10": (42.5, 58.5, 0), "J11": (54.0, 58.5, 0), "J12": (65.5, 58.5, 0),
    # Power chain left to right from the battery entry (XT30 body reaches x = 17)
    "U1": (21.5, 39.0, 0), "U2": (32.0, 44.5, 0), "L1": (32.0, 35.5, 0),
    "U3": (44.0, 41.0, 0), "L2": (50.5, 38.5, 0), "U4": (50.0, 46.0, 0),
    # Charger near the USB-C port
    "U5": (60.0, 40.0, 0), "L3": (60.0, 34.0, 0),
    # Bus buffers above their ports, IMU near the board centre, ADC and amplifier under the SBC
    "U7": (14.0, 53.0, 0), "U8": (37.0, 53.0, 0), "U9": (60.0, 53.0, 0),
    "U11": (38.0, 21.0, 0), "U6": (17.0, 25.5, 0), "U10": (58.0, 21.0, 0),
}


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = PROJECT_LIB if lib == "duccky" else FP_DIR / f"{lib}.pretty"
    fp = pcbnew.FootprintLoad(str(path), name)
    if fp is None:
        raise RuntimeError(f"footprint {fpid} not found")
    return fp


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def read_netlist(path):
    net = parse(Path(path).read_text(encoding="utf-8"))
    comps = {}
    for c in find_all(find(net, "components"), "comp"):
        ref = str(find(c, "ref")[1])
        fpn = find(c, "footprint")
        val = str(find(c, "value")[1])
        ts = find(c, "tstamps")
        props = {str(find(x, "name")[1]): (str(find(x, "value")[1]) if find(x, "value") else "") for x in find_all(c, "property")}
        comps[ref] = {"fp": str(fpn[1]) if fpn else "", "value": val, "pins": {},
                      "ts": str(ts[1]) if ts else "", "props": props}
    for n in find_all(find(net, "nets"), "net"):
        name = str(find(n, "name")[1])
        for node in find_all(n, "node"):
            r, p = str(find(node, "ref")[1]), str(find(node, "pin")[1])
            if r in comps:
                comps[r]["pins"][p] = name
    return comps


def bbox(fp, margin=0.2):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()) - margin, pcbnew.ToMM(bb.GetTop()) - margin,
            pcbnew.ToMM(bb.GetRight()) + margin, pcbnew.ToMM(bb.GetBottom()) + margin)


def overlaps(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def inside_board(b, edge=0.5):
    return b[0] >= edge and b[1] >= edge and b[2] <= BOARD_W - edge and b[3] <= BOARD_H - edge


def set_netclasses(board):
    ns = board.GetDesignSettings().m_NetSettings
    for name, (w, clr, vd, vdr) in CLASSES.items():
        nc = ns.GetDefaultNetclass() if name == "Default" else pcbnew.NETCLASS(name)
        nc.SetTrackWidth(mm(w))
        nc.SetClearance(mm(clr))
        nc.SetViaDiameter(mm(vd))
        nc.SetViaDrill(mm(vdr))
        if name != "Default":
            ns.SetNetclass(name, nc)
    for cls, nets in NET_CLASS.items():
        for n in nets:
            ns.SetNetclassPatternAssignment(N(n), cls)


def write_project_netclasses():
    """Persist net classes in carrier.kicad_pro so kicad-cli DRC sees them."""
    pro_path = PROJ / "carrier.kicad_pro"
    pro = json.loads(pro_path.read_text(encoding="utf-8"))
    classes = []
    for name, (w, clr, vd, vdr) in CLASSES.items():
        classes.append({"name": name, "track_width": w, "clearance": clr, "via_diameter": vd,
                        "via_drill": vdr, "priority": 0 if name == "HighCurrent" else (1 if name == "Power" else 2147483647)})
    pro["net_settings"] = {
        "classes": classes, "meta": {"version": 4},
        "netclass_patterns": [{"netclass": c, "pattern": N(n)} for c, nets in NET_CLASS.items() for n in nets],
    }
    pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {}).update(
        {"min_clearance": 0.15, "min_track_width": 0.10, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2,
         "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.15})
    pro_path.write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8")


def add_outline(board):
    pts = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(vec(*pts[i]))
        seg.SetEnd(vec(*pts[(i + 1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        board.Add(seg)


def N(name):
    """Schematic local labels become nets named with the sheet path, "/NAME"."""
    return "/" + name


def add_zone(board, netname, layer, inset=0.3, rect=None, priority=0):
    net = board.FindNet(N(netname))
    if net is None:
        raise KeyError(f"net {netname} not on board")
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    poly = z.Outline()
    poly.NewOutline()
    x0, y0, x1, y1 = rect or (inset, inset, BOARD_W - inset, BOARD_H - inset)
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        poly.Append(mm(x), mm(y))
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
    return z


def place_socket(fp):
    """Rotate the 2 x 20 socket so its rows run along x, centred on the SBC header position
    (Pi Zero pattern: header centre 32.5 mm along and 3.5 mm in from the SBC's long edge)."""
    fp.SetOrientationDegrees(90)
    pads = [p.GetPosition() for p in fp.Pads()]
    cx = sum(pcbnew.ToMM(p.x) for p in pads) / len(pads)
    cy = sum(pcbnew.ToMM(p.y) for p in pads) / len(pads)
    tx, ty = SBC[0] + 32.5, SBC[1] + 3.5
    pos = fp.GetPosition()
    fp.SetPosition(vec(pcbnew.ToMM(pos.x) + tx - cx, pcbnew.ToMM(pos.y) + ty - cy))


def place(comps):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    add_outline(board)
    nets = {}
    for c in comps.values():
        for n in c["pins"].values():
            if n not in nets:
                ni = pcbnew.NETINFO_ITEM(board, n)
                board.Add(ni)
                nets[n] = ni
    set_netclasses(board)

    fps = {}
    for ref, c in sorted(comps.items()):
        if not c["fp"]:
            continue
        fp = load_fp(c["fp"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetFPIDAsString(c["fp"])
        if c["ts"]:
            fp.SetPath(pcbnew.KIID_PATH("/" + c["ts"]))
        for key in ("MPN", "Note"):
            if key in c["props"]:
                fp.SetField(key, c["props"][key])
                f = fp.GetField(key)
                f.SetVisible(False)
                f.SetLayer(pcbnew.F_Fab)
        if c["fp"].endswith("Texas_RNN0018A"):
            # KiCad ships no RNN body; the TI RGR body has the same 3.5 x 3.5 mm outline (visual and clearance use only)
            for m in list(fp.Models()):
                m.m_Filename = "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_VQFN-RGR-20-1EP_3.5x3.5mm_Pitch0.5mm.step"
        fp.Reference().SetLayer(pcbnew.F_Fab)
        if "dnp" in c["props"]:
            fp.SetDNP(True)
        if "exclude_from_bom" in c["props"]:
            fp.SetExcludedFromBOM(True)          # dense board: designators on the assembly drawing
        for pad in fp.Pads():
            n = c["pins"].get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
        board.Add(fp)
        fps[ref] = fp

    placed = []
    for ref, spec in FIXED.items():
        fp = fps[ref]
        if ref == "J5":
            place_socket(fp)
        else:
            x, y, rot = spec
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(vec(x, y))
        placed.append((ref, bbox(fp, 0.1)))

    # Greedy placement of everything else next to the pad of its most specific net
    # (the net with the fewest pads), which is the IC pin the part serves.
    net_pads = {}
    for r, f in fps.items():
        for p in f.Pads():
            if p.GetNetname():
                net_pads.setdefault(p.GetNetname(), []).append((r, p))

    def specificity(ref):
        sizes = [len(net_pads[p.GetNetname()]) for p in fps[ref].Pads()
                 if p.GetNetname() and p.GetNetname() != "/GND"]
        return min(sizes) if sizes else 999

    def target(ref):
        cands = []
        for pad in fps[ref].Pads():
            n = pad.GetNetname()
            if not n or n == "/GND":
                continue
            others = [(r, p) for r, p in net_pads[n] if r != ref and r in placed_refs]
            if others:
                cands.append((len(net_pads[n]), others))
        if not cands:
            return BOARD_W / 2, BOARD_H / 2
        cands.sort(key=lambda c: c[0])
        pts = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for _, p in cands[0][1]]
        return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)

    placed_refs = set(FIXED)
    rest = [r for r in fps if r not in placed_refs]
    while rest:
        # Most specific first, and only once its anchor is on the board
        rest.sort(key=lambda r: (specificity(r), r))
        ready = [r for r in rest if any(rr in placed_refs for p in fps[r].Pads()
                 if p.GetNetname() and p.GetNetname() != "/GND" for rr, _ in net_pads[p.GetNetname()] if rr != r)]
        ref = (ready or rest)[0]
        rest.remove(ref)
        fp = fps[ref]
        tx, ty = target(ref)
        best = None
        for radius in [i * 0.5 for i in range(0, 80)]:
            steps = max(1, int(2 * math.pi * radius / 0.5))
            for k in range(steps):
                ang = 2 * math.pi * k / steps
                x, y = tx + radius * math.cos(ang), ty + radius * math.sin(ang)
                x, y = round(x * 4) / 4, round(y * 4) / 4
                for rot in (0, 90):
                    fp.SetOrientationDegrees(rot)
                    fp.SetPosition(vec(x, y))
                    bb = bbox(fp, 0.4)
                    if inside_board(bb) and not any(overlaps(bb, o) for _, o in placed):
                        best = (x, y, rot, bb)
                        break
                if best:
                    break
            if best:
                break
        if not best:
            raise RuntimeError(f"no room for {ref}")
        x, y, rot, bb = best
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(vec(x, y))
        placed.append((ref, bb))
        placed_refs.add(ref)

    # Planes: In1 GND, In2 servo rail. Outer GND pours are added after routing (route.py).
    add_zone(board, "GND", pcbnew.In1_Cu)
    # Servo rail plane only below the computer, leaving In2 free for signals under it
    add_zone(board, "V5_SERVO", pcbnew.In2_Cu, rect=(0.3, 30.0, BOARD_W - 0.3, BOARD_H - 0.3))
    # Battery input and eFuse output pours on B.Cu across the power section (they carry
    # up to 12.4 A; traces only escape into them)
    for net, rect in POWER_POURS.items():
        add_zone(board, net, pcbnew.B_Cu, rect=rect, priority=10)
    return board


def main(cmd):
    comps = read_netlist(PROJ / "carrier.net")
    if cmd == "place":
        board = place(comps)
        out = PROJ / "carrier.kicad_pcb"
        pcbnew.SaveBoard(str(out), board)
        write_project_netclasses()
        print("placed", len(comps), "parts ->", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "place")
