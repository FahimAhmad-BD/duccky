# Build the whole robot from the scripts and save it to Fusion as the master document
# "Duccky v1.0" in the root folder of the active Fusion project (free personal cloud storage).
# A later run saves a new version of the same document. The document stays open.
import importlib, sys
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts, assembly
for mod in (dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts, assembly):
    importlib.reload(mod)

NAME = "Duccky v1.0"
try:
    project = app.data.activeProject
except RuntimeError:
    project = None
if project is None:
    project = app.data.dataProjects.item(0)      # first project if none is active
folder = project.rootFolder
existing = None
for i in range(folder.dataFiles.count):
    f = folder.dataFiles.item(i)
    if f.name == NAME:
        existing = f
print("project:", project.name, "| existing master:", existing is not None)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
entries = assembly.build(dk.design().rootComponent, include_board=True)
print("built", len(entries), "parts")
if existing is None:
    ok = doc.saveAs(NAME, folder, "Duccky v1.0 master, generated from the duccky repo (cad/build/save_master.py)", "")
else:
    # Fusion saves new versions only of an opened data file; save this build as a dated copy
    import time
    ok = doc.saveAs(NAME + " " + time.strftime("%Y-%m-%d %H%M"), folder,
                    "Duccky v1.0 build from the duccky repo (cad/build/save_master.py)", "")
print("saved:", ok, "| document:", doc.name)
app.activeViewport.fit()
snapshot("master", 1400, 1400, fit=False)
