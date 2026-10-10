# Build one XC330 reference in a scratch document, report mass properties, screenshot, close.
import importlib
import sys
from pathlib import Path

LIB = r"F:\Drive\OneDrive\Personal Projects\Duccky\Duccky v1.0\cad\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import dk
import servo
importlib.reload(dk)
importlib.reload(servo)

doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    root = dk.design().rootComponent
    occ = servo.build(root, "XC330-M288-T", "servo test")
    print("physical", dk.physical(occ))
    print("expected volume mm3", round(servo.volume_mm3(), 1), "(before holes)")
    app.activeViewport.goHome()
    snapshot("xc330")
finally:
    doc.close(False)
