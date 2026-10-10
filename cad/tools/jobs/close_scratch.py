# Close unsaved scratch documents left by failed test jobs: unsaved documents whose root
# has a "servo test" occurrence or that were created by a job. Never closes saved documents.
closed = []
for i in reversed(range(app.documents.count)):
    d = app.documents.item(i)
    if d.isSaved:
        continue
    des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
    names = [des.rootComponent.occurrences.item(k).component.name for k in range(des.rootComponent.occurrences.count)] if des else []
    if any("test" in n for n in names):
        closed.append(d.name)
        d.close(False)
print("closed", closed, "remaining", [app.documents.item(i).name for i in range(app.documents.count)])
