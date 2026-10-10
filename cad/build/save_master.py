# Build the whole robot from the scripts and save it to Fusion as the master document
# "Duccky v1.0" in the root folder of the Fusion project "Duccky" (free personal cloud storage).
# A later run saves a dated copy. Every run also writes local backups: a Fusion archive (.f3d)
# and a STEP into cad/export/master (committed to git) and a dated pair into
# %USERPROFILE%/Documents/Duccky_backups (outside OneDrive). The document stays open.
import importlib, os, shutil, sys, time
LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts, assembly
for mod in (dk, prim, servo, leg, legparts, robot, trunk, cartridge, head, headparts, assembly):
    importlib.reload(mod)

NAME = "Duccky v1.0"
PROJECT = "Duccky"                               # dedicated Fusion project (free personal storage)
project = None
for i in range(app.data.dataProjects.count):
    if app.data.dataProjects.item(i).name == PROJECT:
        project = app.data.dataProjects.item(i)
if project is None:
    project = app.data.dataProjects.add(PROJECT)
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
    ok = doc.saveAs(NAME + " " + time.strftime("%Y-%m-%d %H%M"), folder,
                    "Duccky v1.0 build from the duccky repo (cad/build/save_master.py)", "")
print("saved:", ok, "| document:", doc.name)

REPO_OUT = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\export\master"
BACKUP = os.path.join(os.path.expanduser("~"), "Documents", "Duccky_backups")
os.makedirs(REPO_OUT, exist_ok=True)
os.makedirs(BACKUP, exist_ok=True)
em = dk.design().exportManager
f3d = os.path.join(REPO_OUT, "duccky_master.f3d")
step = os.path.join(REPO_OUT, "duccky_master.step")
print("f3d:", em.execute(em.createFusionArchiveExportOptions(f3d)))
print("step:", em.execute(em.createSTEPExportOptions(step)))
stamp = time.strftime("%Y%m%d_%H%M")
for src in (f3d, step):
    base, ext = os.path.splitext(os.path.basename(src))
    dst = os.path.join(BACKUP, f"{base}_{stamp}{ext}")
    shutil.copy2(src, dst)
    print("backup:", dst, os.path.getsize(dst), "bytes")
app.activeViewport.fit()
snapshot("master", 1400, 1400, fit=False)
