# Bridge geometry test: build a 20 x 34 x 26 mm block (servo envelope) in a scratch
# document, report its volume, take a screenshot, then close the document unsaved.
doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
d = adsk.fusion.Design.cast(app.activeProduct)
root = d.rootComponent
sk = root.sketches.add(root.xYConstructionPlane)
sk.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(2.0, 3.4, 0))
ext = root.features.extrudeFeatures.addSimple(sk.profiles.item(0), adsk.core.ValueInput.createByString("26 mm"),
                                              adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
body = ext.bodies.item(0)
print("volume mm3:", round(body.volume * 1000, 1))
app.activeViewport.goHome()
snapshot("servo_envelope")
doc.close(False)
