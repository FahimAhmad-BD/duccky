"""Write the project library ecad/lib: custom symbols and footprints.

Footprint geometry is taken from the cited package drawings. Run after editing a
custom part:  python library.py
"""
from pathlib import Path

from sexpr import Q, dump

LIB = Path(__file__).resolve().parents[1] / "lib"


def _fp_text(kind, text, x, y, layer, hide=False):
    eff = ["effects", ["font", ["size", "1", "1"], ["thickness", "0.15"]]]
    node = ["property", Q(kind), Q(text), ["at", x, y, "0"], ["layer", Q(layer)]]
    if hide:
        node.append(["hide", "yes"])
    node.append(eff)
    return node


def _line_rect(x0, y0, x1, y1, layer, width):
    return ["fp_rect", ["start", x0, y0], ["end", x1, y1],
            ["stroke", ["width", width], ["type", "solid"]], ["fill", "no"], ["layer", Q(layer)]]


def _smd(num, x, y, w, h, paste=True, rratio=0.25):
    layers = ["layers", Q("F.Cu"), Q("F.Mask")] + ([Q("F.Paste")] if paste else [])
    return ["pad", Q(num), "smd", "roundrect", ["at", x, y], ["size", w, h], layers, ["roundrect_rratio", rratio]]


def _via(num, x, y):
    return ["pad", Q(num), "thru_hole", "circle", ["at", x, y], ["size", "0.45", "0.45"], ["drill", "0.2"],
            ["layers", Q("*.Cu")], ["remove_unused_layers", "no"]]


def tps25982_rge0024m():
    """TI RGE0024M (TPS25982), drawing 4223975/B: 4 x 4 mm VQFN, two exposed pads.
    Terminal pads 0.575 x 0.24 on 3.825 mm centres; pad 25 (IN) 2.7 x 1.45 at y = -0.625;
    pad 26 (GND) 2.7 x 0.85 at y = +0.925 (KiCad y down, pin 1 top left)."""
    name = "Texas_RGE0024M_TPS25982"
    c, pitch = 3.825 / 2, 0.5
    pads = []
    ys = [-1.25 + pitch * i for i in range(6)]
    for i, y in enumerate(ys):                       # 1..6 left column, top to bottom
        pads.append(_smd(str(1 + i), -c, y, 0.575, 0.24))
    for i, x in enumerate(ys):                       # 7..12 bottom row, left to right
        pads.append(_smd(str(7 + i), x, c, 0.24, 0.575))
    for i, y in enumerate(reversed(ys)):             # 13..18 right column, bottom to top
        pads.append(_smd(str(13 + i), c, y, 0.575, 0.24))
    for i, x in enumerate(reversed(ys)):             # 19..24 top row, right to left
        pads.append(_smd(str(19 + i), x, -c, 0.24, 0.575))
    pads.append(_smd("25", 0, -0.625, 2.7, 1.45, paste=False, rratio=0.05))
    pads.append(_smd("26", 0, 0.925, 2.7, 0.85, paste=False, rratio=0.05))
    # Paste windows at about 70 % area on the exposed pads
    for num, cy, h in (("25", -0.625, 1.45), ("26", 0.925, 0.85)):
        for px in (-0.68, 0.68):
            pads.append(["pad", Q(""), "smd", "roundrect", ["at", px, cy], ["size", 1.13, round(h * 0.84, 3)],
                         ["layers", Q("F.Paste")], ["roundrect_rratio", 0.1]])
    for x in (-1.1, 0, 1.1):                          # thermal vias per the example board layout
        pads += [_via("25", x, -0.9375), _via("25", x, -0.3125), _via("26", x, 0.925)]
    body = [
        _line_rect(-2, -2, 2, 2, "F.Fab", "0.1"),
        _line_rect(-2.45, -2.45, 2.45, 2.45, "F.CrtYd", "0.05"),
        ["fp_line", ["start", -2.11, -1.6], ["end", -2.11, -2.11], ["stroke", ["width", "0.12"], ["type", "solid"]], ["layer", Q("F.SilkS")]],
        ["fp_line", ["start", -2.11, -2.11], ["end", -1.6, -2.11], ["stroke", ["width", "0.12"], ["type", "solid"]], ["layer", Q("F.SilkS")]],
        ["fp_circle", ["center", -2.4, -1.25], ["end", -2.3, -1.25], ["stroke", ["width", "0.2"], ["type", "solid"]], ["fill", "yes"], ["layer", Q("F.SilkS")]],
    ]
    fp = ["footprint", Q(name), ["version", "20241229"], ["generator", Q("duccky_library")],
          ["layer", Q("F.Cu")], ["descr", Q("TI RGE0024M VQFN-24 4x4 mm with split exposed pad (TPS25982), drawing 4223975/B")],
          ["tags", Q("VQFN TPS25982 RGE0024M")],
          _fp_text("Reference", "REF**", 0, -3.3, "F.SilkS"), _fp_text("Value", name, 0, 3.3, "F.Fab"),
          ["attr", "smd"]] + body + pads + [
          ["model", Q("${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm.step"),
           ["offset", ["xyz", 0, 0, 0]], ["scale", ["xyz", 1, 1, 1]], ["rotate", ["xyz", 0, 0, 0]]]]
    return name, fp


def write_footprints():
    d = LIB / "duccky.pretty"
    d.mkdir(parents=True, exist_ok=True)
    for make in (tps25982_rge0024m,):
        name, fp = make()
        (d / f"{name}.kicad_mod").write_text(dump(fp) + "\n", encoding="utf-8")
        print("footprint", name)


def write_symbols(symbols):
    """symbols: list of make_symbol() trees named duccky:*; written without the lib prefix."""
    out = ["kicad_symbol_lib", ["version", "20241209"], ["generator", Q("duccky_library")],
           ["generator_version", Q("9.0")]]
    for s in symbols:
        s = list(s)
        s[1] = Q(str(s[1]).split(":")[1])
        out.append(s)
    LIB.mkdir(parents=True, exist_ok=True)
    (LIB / "duccky.kicad_sym").write_text(dump(out) + "\n", encoding="utf-8")
    print("symbols", len(symbols))


if __name__ == "__main__":
    write_footprints()
