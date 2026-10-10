# Bridge check: report the Fusion version, the open document and the design state.
doc = app.activeDocument
print("Fusion", app.version)
print("Document:", doc.name if doc else None)
d = design()
if d:
    root = d.rootComponent
    print("Design type:", "parametric" if d.designType == adsk.fusion.DesignTypes.ParametricDesignType else "direct")
    print("Bodies:", root.bRepBodies.count, "Occurrences:", root.occurrences.count)
    print("User parameters:", d.userParameters.count)
    snapshot("ping")
