"""Report courtyard area of every footprint in a KiCad netlist (run with KiCad's Python).

Usage: <kicad>/bin/python.exe fparea.py ../carrier/carrier.net
"""
import os
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexpr import find, find_all, parse  # noqa: E402

FP_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "share" / "kicad" / "footprints"
PROJECT_LIB = Path(__file__).resolve().parents[1] / "lib" / "duccky.pretty"


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = PROJECT_LIB if lib == "duccky" else FP_DIR / f"{lib}.pretty"
    return pcbnew.FootprintLoad(str(path), name)


def main(net_path):
    net = parse(Path(net_path).read_text(encoding="utf-8"))
    comps = find_all(find(net, "components"), "comp")
    total, rows = 0.0, []
    for c in comps:
        ref = str(find(c, "ref")[1])
        fpn = find(c, "footprint")
        if not fpn or not str(fpn[1]):
            continue
        fp = load_fp(str(fpn[1]))
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox()
        w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
        total += w * h
        rows.append((w * h, ref, str(fpn[1]), w, h))
    for a, ref, fpid, w, h in sorted(rows, reverse=True)[:15]:
        print(f"{ref:6} {w:6.2f} x {h:6.2f} = {a:7.1f} mm2  {fpid}")
    print(f"{len(rows)} footprints, total courtyard area {total:.0f} mm2")


if __name__ == "__main__":
    main(sys.argv[1])
