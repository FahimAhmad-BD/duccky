# List material libraries and materials whose names mention PLA, PETG, ABS or nylon.
for i in range(app.materialLibraries.count):
    lib = app.materialLibraries.item(i)
    hits = []
    for j in range(lib.materials.count):
        m = lib.materials.item(j)
        if any(k in m.name.upper() for k in ("PLA", "PETG", "ABS", "NYLON", "PA12")):
            hits.append(m.name)
    print(lib.name, "->", hits[:20])
