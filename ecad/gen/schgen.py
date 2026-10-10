"""Write a KiCad schematic from a part list.

Every connected pin gets a local net label at its end, so the drawing reads like a
netlist: no wires to route, and each net name appears wherever it is used. Pins
listed as NC get a no-connect flag. Parts are laid out block by block on a grid.
"""
import uuid
from pathlib import Path

from kicadlib import load_symbol, symbol_pins, symbol_units
from sexpr import Q, dump

GRID = 2.54
NC = "NC"


def _uid(*parts):
    return Q(str(uuid.uuid5(uuid.NAMESPACE_URL, "duccky/" + "/".join(map(str, parts)))))


def _snap(v):
    return round(v / GRID) * GRID


def _font(size=1.27, justify=None, hide=False):
    e = ["effects", ["font", ["size", size, size]]]
    if justify:
        e.append(["justify"] + justify)
    if hide:
        e.append(["hide", "yes"])
    return e


class Part:
    def __init__(self, ref, sym, value, footprint, nets, dnp=False, fields=None):
        self.ref = ref
        self.sym = sym
        self.value = value
        self.footprint = footprint
        self.nets = {str(k): v for k, v in nets.items()}
        self.dnp = dnp
        self.fields = fields or {}
        self.pins = symbol_pins(sym)
        self.units = symbol_units(sym)
        missing = set(self.nets) - set(self.pins)
        if missing:
            raise ValueError(f"{ref}: pins {sorted(missing)} not in symbol {sym[1]}")

    def extent(self):
        xs = [p[1] for v in self.pins.values() for p in v] or [-2.54, 2.54]
        ys = [p[2] for v in self.pins.values() for p in v] or [-2.54, 2.54]
        return min(xs), max(xs), min(ys), max(ys)


class Schematic:
    def __init__(self, project, title, rev, paper="A1"):
        self.project = project
        self.title = title
        self.rev = rev
        self.paper = paper
        self.root = _uid(project, "root")
        self.lib_symbols = {}
        self.items = []
        self.parts = []
        self.texts = []

    def add_text(self, text, x, y, size=2.5):
        self.texts.append(["text", Q(text), ["exclude_from_sim", "no"], ["at", x, y, "0"],
                           _font(size, ["left", "bottom"]), ["uuid", _uid(self.project, "text", text)]])

    def place(self, part, x, y):
        """Place every unit of part with its first unit's origin at (x, y)."""
        lib_id = str(part.sym[1])
        self.lib_symbols[lib_id] = part.sym
        self.parts.append(part)
        xmin, xmax, ymin, ymax = part.extent()
        unit_step = _snap(ymax - ymin + 10.16)
        used = set()
        for k, unit in enumerate(part.units):
            ux, uy = _snap(x), _snap(y + k * unit_step)
            inst = ["symbol", ["lib_id", Q(lib_id)], ["at", ux, uy, "0"], ["unit", unit],
                    ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
                    ["dnp", "yes" if part.dnp else "no"], ["uuid", _uid(self.project, part.ref, unit)],
                    # Reference above the topmost pin, value below the lowest
                    ["property", Q("Reference"), Q(part.ref), ["at", ux, uy - ymax - 2.54, "0"], _font()],
                    ["property", Q("Value"), Q(part.value), ["at", ux, uy - ymin + 2.54, "0"], _font()],
                    ["property", Q("Footprint"), Q(part.footprint), ["at", ux, uy, "0"], _font(hide=True)],
                    ["property", Q("Datasheet"), Q(part.fields.get("Datasheet", "")), ["at", ux, uy, "0"], _font(hide=True)]]
            if xmax - xmin < 1.0:
                # Two pin vertical part: text beside the body, clear of the pin labels
                inst[9][3] = ["at", ux + 2.54, uy - 1.27, "0"]
                inst[9][4] = _font(1.27, ["left"])
                inst[10][3] = ["at", ux + 2.54, uy + 1.27, "0"]
                inst[10][4] = _font(1.27, ["left"])
            for key, val in part.fields.items():
                if key != "Datasheet":
                    inst.append(["property", Q(key), Q(val), ["at", ux, uy, "0"], _font(hide=True)])
            for num, locs in part.pins.items():
                for (pu, px, py, rot, etype) in locs:
                    if pu not in (0, unit):
                        continue
                    inst.append(["pin", Q(num), ["uuid", _uid(self.project, part.ref, unit, num, px, py)]])
                    if pu == 0 and (num, px, py) in used:
                        continue
                    used.add((num, px, py))
                    sx, sy = ux + px, uy - py
                    self._connect(part, num, sx, sy, rot, etype)
            inst.append(["instances", ["project", Q(self.project),
                                       ["path", Q("/" + self.root), ["reference", Q(part.ref)], ["unit", unit]]]])
            self.items.append(inst)

    def _connect(self, part, num, sx, sy, rot, etype):
        net = part.nets.get(num)
        if net is None:
            if etype in ("no_connect",):
                return
            raise ValueError(f"{part.ref} pin {num} has no net (use NC)")
        if net == NC:
            self.items.append(["no_connect", ["at", sx, sy], ["uuid", _uid(self.project, part.ref, num, "nc", sx, sy)]])
            return
        angle = {0: 180, 180: 0, 90: 270, 270: 90}[rot]
        just = ["right", "bottom"] if angle in (180, 270) else ["left", "bottom"]
        self.items.append(["label", Q(net), ["at", sx, sy, angle], _font(1.27, just),
                           ["uuid", _uid(self.project, part.ref, num, sx, sy)]])

    def write(self, path):
        doc = ["kicad_sch", ["version", "20250114"], ["generator", Q("duccky_schgen")],
               ["generator_version", Q("9.0")], ["uuid", self.root], ["paper", Q(self.paper)],
               ["title_block", ["title", Q(self.title)], ["rev", Q(self.rev)],
                ["company", Q("Duccky v1.0")], ["comment", "1", Q("Generated by ecad/gen; edit the generator, not this file")]],
               ["lib_symbols"] + list(self.lib_symbols.values())]
        doc += self.texts + self.items
        doc += [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]
        Path(path).write_text(dump(doc) + "\n", encoding="utf-8")


class Block:
    """Lays parts out left to right in rows inside a titled region."""

    def __init__(self, sch, title, x, y, width):
        self.sch, self.x0, self.y0, self.width = sch, x, y, width
        self.cx, self.cy, self.row_h = x, y + 12.7, 0.0
        sch.add_text(title, x, y + 5.08, 3.0)

    def add(self, part):
        xmin, xmax, ymin, ymax = part.extent()
        w = (xmax - xmin) + 30.48          # room for labels on both sides
        nunits = len(part.units)
        h = (ymax - ymin) * nunits + 10.16 * nunits + 12.7
        if self.cx + w > self.x0 + self.width and self.cx > self.x0:
            self.cx = self.x0
            self.cy += self.row_h
            self.row_h = 0.0
        self.sch.place(part, self.cx - xmin + 15.24, self.cy + ymax + 5.08)
        self.cx += w
        self.row_h = max(self.row_h, h)
        return part

    def bottom(self):
        return self.cy + self.row_h
