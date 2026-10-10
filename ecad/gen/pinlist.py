"""Print the pins of library symbols: python pinlist.py Lib:Name [Lib:Name ...]"""
import sys

from kicadlib import find, find_all, load_symbol, symbol_pins

for lib_id in sys.argv[1:]:
    sym = load_symbol(lib_id)
    fp = next((p[2] for p in find_all(sym, "property") if p[1] == "Footprint"), "")
    names = {}
    for sub in find_all(sym, "symbol"):
        for p in find_all(sub, "pin"):
            names[str(find(p, "number")[1])] = str(find(p, "name")[1])
    pins = symbol_pins(sym)
    print(f"{lib_id}  footprint={fp}")
    for num in sorted(pins, key=lambda s: (len(s), s)):
        units = ",".join(str(u[0]) for u in pins[num])
        print(f"  {num:>4} {names.get(num, ''):<14} {pins[num][0][4]:<12} unit {units}")
