"""Load KiCad library symbols and build simple custom symbols.

A loaded symbol is flattened (an `extends` child takes its parent's graphics and
pins) and renamed "Lib:Name" for embedding in a schematic's lib_symbols block.
"""
import os
import re
from pathlib import Path

from sexpr import Q, find, find_all, parse

KICAD_SHARE = Path(os.environ.get(
    "KICAD_SHARE", Path(os.environ["LOCALAPPDATA"]) / "Programs" / "KiCad" / "10.0" / "share" / "kicad"))
SYMBOL_DIR = KICAD_SHARE / "symbols"

_lib_cache = {}


def _load_lib(path):
    if path not in _lib_cache:
        _lib_cache[path] = parse(Path(path).read_text(encoding="utf-8"))
    return _lib_cache[path]


def _raw_symbol(lib_path, name):
    lib = _load_lib(lib_path)
    for s in find_all(lib, "symbol"):
        if s[1] == name:
            return s
    raise KeyError(f"{name} not in {lib_path}")


def load_symbol(lib_id, lib_path=None):
    """Return a flattened copy of library symbol lib_id ("Lib:Name")."""
    lib, name = lib_id.split(":")
    lib_path = lib_path or SYMBOL_DIR / f"{lib}.kicad_sym"
    sym = _raw_symbol(lib_path, name)
    ext = find(sym, "extends")
    if ext:
        parent = load_symbol(f"{lib}:{ext[1]}", lib_path)
        pname = ext[1]
        # Child keeps its own properties; graphics and pins come from the parent.
        props = {p[1]: p for p in find_all(sym, "property")}
        out = [x for x in parent if not (isinstance(x, list) and x[0] == "property")]
        out[1] = Q(lib_id)
        merged = [x for x in find_all(parent, "property")]
        merged = [props.pop(p[1], p) for p in merged] + list(props.values())
        body = []
        for x in out[2:]:
            if isinstance(x, list) and x[0] == "symbol":
                sub = list(x)
                sub[1] = Q(re.sub(r"^.*?(_\d+_\d+)$", name + r"\1", str(sub[1])))
                body.append(sub)
            else:
                body.append(x)
        # Properties go before sub-symbols to match KiCad's ordering
        head = [x for x in body if not (isinstance(x, list) and x[0] == "symbol")]
        subs = [x for x in body if isinstance(x, list) and x[0] == "symbol"]
        return ["symbol", Q(lib_id)] + head + merged + subs
    out = list(sym)
    out[1] = Q(lib_id)
    return out


def symbol_pins(sym):
    """Map pin number -> list of (unit, x, y, rotation, electrical type), y up."""
    pins = {}
    for sub in find_all(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", str(sub[1]))
        unit, style = int(m.group(1)), int(m.group(2))
        if style > 1:
            continue
        for p in find_all(sub, "pin"):
            at = find(p, "at")
            num = find(p, "number")[1]
            rot = int(float(at[3])) if len(at) > 3 else 0
            pins.setdefault(str(num), []).append((unit, float(at[1]), float(at[2]), rot, str(p[1])))
    return pins


def symbol_units(sym):
    units = set()
    for sub in find_all(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", str(sub[1]))
        if int(m.group(1)) > 0:
            units.add(int(m.group(1)))
    return sorted(units) or [1]


def _font():
    return ["effects", ["font", ["size", "1.27", "1.27"]]]


def _prop(key, value, x, y, hide=False):
    eff = _font()
    if hide:
        eff.append(["hide", "yes"])
    return ["property", Q(key), Q(value), ["at", x, y, "0"], eff]


def make_symbol(lib_id, ref, value, footprint, datasheet, description, left, right, width=15.24):
    """Rectangular symbol. left/right are lists of (number, name, type) top to bottom,
    None for a gap. Pins are 2.54 mm long on a 2.54 mm grid."""
    name = lib_id.split(":")[1]
    rows = max(len(left), len(right))
    h = (rows + 1) * 2.54
    top = round(h / 2 / 2.54) * 2.54
    w = width / 2
    graphics = ["symbol", Q(f"{name}_0_1"),
                ["rectangle", ["start", -w, top], ["end", w, top - h],
                 ["stroke", ["width", "0.254"], ["type", "default"]], ["fill", ["type", "background"]]]]
    pins = ["symbol", Q(f"{name}_1_1")]
    for side, lst in ((-1, left), (1, right)):
        for i, p in enumerate(lst):
            if p is None:
                continue
            num, pname, ptype = p
            y = top - 2.54 * (i + 1)
            x = side * (w + 2.54)
            angle = "0" if side < 0 else "180"
            pins.append(["pin", ptype, "line", ["at", x, y, angle], ["length", "2.54"],
                         ["name", Q(pname), _font()], ["number", Q(str(num)), _font()]])
    return ["symbol", Q(lib_id),
            ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
            _prop("Reference", ref, 0, top + 1.27),
            _prop("Value", value, 0, top - h - 1.27),
            _prop("Footprint", footprint, 0, top - h - 3.81, True),
            _prop("Datasheet", datasheet, 0, top - h - 6.35, True),
            _prop("Description", description, 0, 0, True),
            graphics, pins]
