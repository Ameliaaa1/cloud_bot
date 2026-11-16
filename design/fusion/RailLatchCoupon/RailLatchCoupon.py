"""Build an assembled CloudBot fit coupon and an STL of both parts flat on one plate."""
import json
import math
from pathlib import Path
import struct
import traceback

import adsk.core
import adsk.fusion


OUTPUT = Path(__file__).resolve().parents[2] / "rail-latch-coupon"
REVISION = "R2"
LATCH_ARM_OUTER_Y = 19.6
LATCH_SIDE_CLEARANCE = 0.25
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation


def point_mm(x, y, z=0):
    return adsk.core.Point3D.create(x / 10, y / 10, z / 10)


def mm(value):
    return adsk.core.ValueInput.createByString(f"{value} mm")


def profile_extrude(component, points, distance, name, operation=NEW, yz=False):
    plane = component.yZConstructionPlane if yz else component.xYConstructionPlane
    sketch = component.sketches.add(plane)
    sketch.name = name + " profile"
    model_points = [point_mm(0, a, b) if yz else point_mm(a, b)
                    for a, b in points]
    sketch_points = [sketch.modelToSketchSpace(p) for p in model_points]
    lines = sketch.sketchCurves.sketchLines
    line = lines.addByTwoPoints(sketch_points[0], sketch_points[1])
    first = line.startSketchPoint
    end = line.endSketchPoint
    for p in sketch_points[2:]:
        end = lines.addByTwoPoints(end, p).endSketchPoint
    lines.addByTwoPoints(end, first)
    feature_input = component.features.extrudeFeatures.createInput(
        sketch.profiles.item(0), operation
    )
    feature_input.setDistanceExtent(False, mm(distance))
    feature = component.features.extrudeFeatures.add(feature_input)
    feature.name = name
    sketch.isVisible = False
    return feature


def raised_rectangle(component, x0, x1, y0, y1, height, name):
    return profile_extrude(component, [(x0,y0),(x1,y0),(x1,y1),(x0,y1)],
                           height, name, JOIN)


def offset(component, start_x):
    plane_input = component.constructionPlanes.createInput()
    plane_input.setByOffset(component.yZConstructionPlane, mm(start_x))
    plane = component.constructionPlanes.add(plane_input)
    plane.isLightBulbOn = False
    return plane


def make_slider(component):
    # The sliding tongue starts behind the receiver when in the installed pose.
    plane = offset(component, -10)
    sketch = component.sketches.add(plane)
    sketch.name = "Sliding tongue profile"
    points = [(-10,0),(10,0),(7.4,2.6),(-7.4,2.6)]
    mapped = [sketch.modelToSketchSpace(point_mm(-10, y, z)) for y,z in points]
    lines = sketch.sketchCurves.sketchLines
    for i,p in enumerate(mapped):
        lines.addByTwoPoints(p, mapped[(i+1) % len(mapped)])
    entry = component.features.extrudeFeatures.createInput(sketch.profiles.item(0), NEW)
    entry.setDistanceExtent(False, mm(43.6))
    component.features.extrudeFeatures.add(entry).name = "Sliding tongue"
    sketch.isVisible = False
    raised_rectangle(component, -15, -9, -8, LATCH_ARM_OUTER_Y, 2.6, "Pull handle")
    profile_extrude(component, [
        (-10, 16), (-6.8, 18), (10.6, 18), (10.6, LATCH_ARM_OUTER_Y),
        (6.25, 21.2), (6.25, LATCH_ARM_OUTER_Y), (-10, LATCH_ARM_OUTER_Y)
    ], 2.6, "Spring arm, insertion ramp and lock shoulder", JOIN)


def print_triangles(body, plate_x, plate_y):
    calculator = body.meshManager.createMeshCalculator()
    calculator.surfaceTolerance = 0.001
    mesh = calculator.calculate()
    coords = mesh.nodeCoordinatesAsFloat
    vertices = [[10 * coords[i+j] for j in range(3)]
                for i in range(0, len(coords), 3)]
    low = [min(v[k] for v in vertices) for k in range(3)]
    target = (plate_x, plate_y, 0)
    for vertex in vertices:
        for axis in range(3):
            vertex[axis] += target[axis] - low[axis]
    indices = mesh.nodeIndices
    triangles = []
    for i in range(0, len(indices), 3):
        a, b, c = [vertices[indices[i+j]] for j in range(3)]
        u, v = [[p[k] - a[k] for k in range(3)] for p in (b, c)]
        normal = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        length = math.sqrt(sum(n*n for n in normal))
        if length <= 1e-10:
            raise ValueError("Degenerate STL triangle")
        triangles.append([n/length for n in normal] + a + b + c)
    return triangles


def run(_context):
    app = adsk.core.Application.get()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    try:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        document.name = f"CloudBot Rail and Latch Coupon {REVISION}"
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.unitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent
        base_occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        base = base_occurrence.component
        base.name = "Rail base - entry at open end"
        profile_extrude(base, [(0,-23),(37,-23),(37,23),(0,23)], 2.4, "Flat base")
        for side, name in ((-1,"left"), (1,"right")):
            profile_extrude(base, [(side*y,z) for y,z in
                [(10.65,2.2),(14,2.2),(14,4.55),(8.65,4.55),(10.65,2.55)]],
                34, "45 degree " + name + " rail", JOIN, yz=True)
        raised_rectangle(base, 34, 37, -14, 14, 5.4, "End stop")
        raised_rectangle(base, 0, 6, LATCH_ARM_OUTER_Y + LATCH_SIDE_CLEARANCE,
                         23, 5.4, "Latch catch")

        shift = adsk.core.Matrix3D.create()
        shift.translation = adsk.core.Vector3D.create(0, 0, 0.28)
        slider_occurrence = root.occurrences.addNewComponent(shift)
        slider = slider_occurrence.component
        slider.name = "Slider - press outside tooth inward to release"
        make_slider(slider)
        if base.bRepBodies.count != 1 or slider.bRepBodies.count != 1:
            raise ValueError("Expected one solid per component")
        entities = adsk.core.ObjectCollection.create()
        entities.add(base_occurrence)
        entities.add(slider_occurrence)
        interference = design.analyzeInterference(design.createInterferenceInput(entities))
        if interference and interference.count:
            raise ValueError(f"Seated fit has {interference.count} overlapping solids")

        records = print_triangles(base.bRepBodies.item(0), 0, 0)
        records += print_triangles(slider.bRepBodies.item(0), 45, 0)
        camera = app.activeViewport.camera
        camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
        camera.eye = point_mm(-95, 120, 130)
        camera.target = point_mm(7, 1, 1)
        camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
        camera.isFitView = True
        app.activeViewport.camera = camera
        app.activeViewport.fit()
        export = design.exportManager
        if not export.execute(export.createFusionArchiveExportOptions(
                str(OUTPUT / f"CloudBot-Rail-Latch-Coupon-{REVISION}.f3d"))):
            raise ValueError("Fusion archive export did not complete")
        with (OUTPUT / f"CloudBot-Rail-Latch-Print-{REVISION}.stl").open("wb") as output:
            output.write(b"CloudBot rail-latch coupon; 2 parts; millimeters".ljust(80, b" "))
            output.write(struct.pack("<I", len(records)))
            for record in records:
                output.write(struct.pack("<12fH", *record, 0))
        (OUTPUT / f"fusion-check-{REVISION}.json").write_text(json.dumps({
            "solids": 2, "seated_interferences": 0, "stl_triangles": len(records),
            "latch_side_clearance_mm": LATCH_SIDE_CLEARANCE
        }), encoding="utf-8")
    except Exception:
        (OUTPUT / f"fusion-error-{REVISION}.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
