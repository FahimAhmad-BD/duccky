# Activate the open document with the most occurrences (the robot preview), fit the view,
# and close empty unsaved documents left by failed jobs.
docs = [app.documents.item(i) for i in range(app.documents.count)]
info = []
best, best_n = None, -1
for d in docs:
    des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
    n = des.rootComponent.allOccurrences.count if des else 0
    info.append((d.name, n, d.isSaved))
    if n > best_n:
        best, best_n = d, n
print("open documents (name, occurrences, saved):", info)
for d in docs:
    des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
    if d is not best and not d.isSaved and des and des.rootComponent.allOccurrences.count == 0 \
            and des.rootComponent.bRepBodies.count == 0 and app.documents.count > 1:
        d.close(False)
best.activate()
app.activeViewport.fit()
print("active:", best.name, "with", best_n, "occurrences")
