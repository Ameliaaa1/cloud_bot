"""CloudBot V8, with native Fusion features. All geometry inputs are in mm."""
import importlib.util
import json
import math
from pathlib import Path
import struct
import traceback

import adsk.core
import adsk.fusion


HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[1] / "v8-1-cad"
V8_NAME = "CloudBot-V8.1"
FEATURE = adsk.fusion.FeatureOperations
NEW, JOIN, CUT = (FEATURE.NewBodyFeatureOperation, FEATURE.JoinFeatureOperation,
                  FEATURE.CutFeatureOperation)
OUTLET = 19


def load_helpers(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE.parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coupon = load_helpers("cloudbot_coupon", "RailLatchCoupon/RailLatchCoupon.py")
shell = load_helpers("cloudbot_v7_geometry", "CloudBotV7/CloudBotV7.py")
pt, mm = coupon.point_mm, coupon.mm
box, cylinder = shell.rect, shell.circle


def pose(x=0, y=0, z=0, angle=0):
    transform = adsk.core.Matrix3D.create()
    transform.setToRotation(angle, adsk.core.Vector3D.create(0, 0, 1), pt(0, 0))
    transform.translation = adsk.core.Vector3D.create(x / 10, y / 10, z / 10)
    return transform


def add_component(root, name, transform, description):
    occurrence = root.occurrences.addNewComponent(transform)
    occurrence.component.name = name
    occurrence.component.description = description
    return occurrence


def extrude_yz(component, origin, section, distance, name):
    plane = coupon.offset(component, origin)
    sketch = component.sketches.add(plane)
    sketch.name = name + " profile"
    points = [sketch.modelToSketchSpace(pt(origin, y, z)) for y, z in section]
    lines = sketch.sketchCurves.sketchLines
    for i, point in enumerate(points):
        lines.addByTwoPoints(point, points[(i+1) % len(points)])
    feature = component.features.extrudeFeatures.createInput(sketch.profiles.item(0), JOIN)
    feature.setDistanceExtent(False, mm(distance))
    component.features.extrudeFeatures.add(feature).name = name
    sketch.isVisible = False


def rail(component, reverse, side):
    # Map the R2 rail's YZ section onto the rear- or front-facing insertion axis.
    origin = 37 if reverse else -37
    sign = -1 if reverse else 1
    section = [(10.65, 2.2), (14, 2.2), (14, 4.55),
               (8.65, 4.55), (10.65, 2.55)]
    extrude_yz(component, origin, [(y*side*sign,z) for y,z in section],
               34*sign, ("Camera" if reverse else "Tank") + f" rail {side:+}")


def chassis(component):
    box(component, -37, -26, 0, 74, 52, 2.4, "Flat chassis")
    for reverse in (False, True):
        for side in (-1, 1):
            rail(component, reverse, side)
    box(component, -3, -14, 0, 6, 28, 5.4, "Shared hard stops", JOIN)
    gap_face = coupon.LATCH_ARM_OUTER_Y + coupon.LATCH_SIDE_CLEARANCE
    box(component, -37, gap_face, 0, 6, 23-gap_face, 5.4, "Tank latch catch", JOIN)
    box(component, 31, -23, 0, 6, 23-gap_face, 5.4, "Camera latch catch", JOIN)
    for y in (-42, 24):
        box(component, -35, y, 0, 70, 18, 2.4, "Integrated 70 mm LED shelf", JOIN)
        for x in (-26, 20):
            for inset in (1, 15):
                box(component, x, y+inset, 0, 6, 2, 2.4, "Accessible LED tie slot", CUT)
    for y in (-32, 32):
        cylinder(component, 0, y, 0, 4.8, 10, "Stake socket boss", JOIN)
        cylinder(component, 0, y, -.1, 1.75, 10.2, "3.5 mm stake opening", CUT)
        for x in (-32, 32):
            cylinder(component, x, y+(-7 if y<0 else 7), -.1, 1.15, 2.6,
                     "Removable wire frame tie hole", CUT)
    box(component, -1, -26, 2, 2, 52, 13, "Wet / dry splash divider", JOIN)
    cylinder(component, -37+OUTLET, 0, -.1, 8, 2.6, "16 mm mist clearance, through", CUT)


def tank(component):
    coupon.make_slider(component)
    extrude_yz(component, 4, [(-7,2.3),(7,2.3),(10,5.3),(10,27),
                             (-10,27),(-10,5.3)], 27, "Tank with 45-degree base")
    for side in (-1,1):
        # An external pocket leaves the tank wall intact and opens outwards.
        lip = [(9.8,10),(12.2,12.4),(12.2,27),(9.8,27)]
        extrude_yz(component, 7.6, [(side*y,z) for y,z in lip],
                   8.8, f"External latch rib {side:+}")
        box(component, 8.45, 10 if side > 0 else -13, 21.9, 7.1, 3, 2,
            f"Open-sided latch notch {side:+}", CUT)
    box(component, 5.4, -8.6, 5.5, 24.2, 17.2, 21.7, "Reservoir cavity", CUT)
    cylinder(component, OUTLET, 0, -.1, 3, 5.8, "6 mm reservoir outlet, through", CUT)


def lid(component):
    # The cap prints upside down. A locating tongue fits into the reservoir.
    box(component, 3, -11.5, 0, 29, 23, 2.4, "Cap flange")
    box(component, 5.75, -8.25, 2.2, 23.5, 16.5, 2.1, "Locating tongue", JOIN)
    box(component, 14, 10, 0, 8, 5, 2.4, "Grip tab", JOIN)
    for side in (-1,1):
        y = 11.2 if side > 0 else -13.85
        box(component, 8.8, y, 0, 6.4, 2.65, 2.4, f"Latch arm root {side:+}", JOIN)
        arm = [(12.45,2.2),(13.85,2.2),(13.85,10.2),(12.45,10.2),
               (12.45,7.15),(11.55,6.05),(12.45,6.05)]
        extrude_yz(component, 8.8, [(side*y,z) for y,z in arm],
                   6.4, f"Press-out cap latch {side:+}")


def camera_tray(component):
    coupon.make_slider(component)
    box(component, 12, -6, 2.2, 4, 12, 2, "Ledge support on sliding tongue", JOIN)
    box(component, 12, -23, 3.8, 4, 46, 3.6, "Board bottom ledge", JOIN)
    box(component, 14, -23, 6.6, 2, 46, 30, "Upright backplate", JOIN)
    for y in (-22, 19):
        for z in (11, 22):
            box(component, 13.8, y, z, 2.4, 3, 2.5, "Side strap pass-through", CUT)


def model_references(root):
    identity = pose()
    wires = add_component(root, "90 Wire cloud cage and decorative trunk", identity,
                          "Hand bend lightweight wire. Use four chassis tie points.")
    c = wires.component
    for side in (-1, 1):
        for endx, endy in ((-32, 39), (32, 39), (9, 43)):
            shell.tube_path(c, [(0,side*32,-64),(8,side*30,-42),
                             (endx*.55,side*36,-17),(endx,side*endy,2.4)],
                            .65, "Decorative wire branch")
    for x in (-32, 0, 32):
        shell.tube_path(c, [(x,-39,2.4),(x,-39,21),(x,0,54 if x==0 else 42),
                             (x,39,21),(x,39,2.4)], .65, "Hand-bent cloud rib")
    for side in (-1, 1):
        o = add_component(root, f"80 Stainless stake {side:+}", identity,
                          "3 mm diameter, 145 mm length. Soil stability to test.")
        cylinder(o.component, 0, side*32, -135.5, 1.5, 145, "Pull-out metal stake")
    tm = adsk.fusion.TemporaryBRepManager.get()
    cover = add_component(root, "91 Cloud diffuser envelope", identity,
                          "Removable translucent mesh and fiber cover. Keep tank grip, lens and outlet clear.")
    for x, y, z, r in [(-31,-23,35,27),(-26,22,39,29),(0,0,47,33),
                       (26,24,39,29),(29,-22,34,26)]:
        shell.temp_body(cover.component, tm.createSphere(pt(x,y,z), r/10), "Diffuser lobe")
    cover.component.opacity = .25
    pot = add_component(root, "92 Flowerpot reference 120 mm", identity,
                        "Reference only. Soil at Z=-80.5 mm, insertion 55 mm.")
    outer = tm.createCylinderOrCone(pt(0,0,-183),4.3,pt(0,0,-73),6)
    inner = tm.createCylinderOrCone(pt(0,0,-180),4.05,pt(0,0,-72),5.75)
    tm.booleanOperation(outer, inner, adsk.fusion.BooleanTypes.DifferenceBooleanType)
    shell.temp_body(pot.component, outer, "Reference flowerpot")
    pot.component.opacity = .42
    return wires, cover, pot


def write_stl(path, records):
    with path.open("wb") as stream:
        stream.write(b"CloudBot V8 dry prototype, millimeters".ljust(80, b" "))
        stream.write(struct.pack("<I", len(records)))
        for triangle in records:
            stream.write(struct.pack("<12fH", *triangle, 0))


def show(viewport, eye, target):
    view = viewport.camera
    view.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    view.eye, view.target = pt(*eye), pt(*target)
    view.upVector = adsk.core.Vector3D.create(0, 0, 1)
    view.isFitView = True
    viewport.camera = view
    viewport.fit()
    adsk.doEvents()


def run(_context):
    OUTPUT.mkdir(exist_ok=True)
    app = adsk.core.Application.get()
    try:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        document.name = V8_NAME
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.unitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent
        base = add_component(root, "01 Integrated chassis", pose(), "One piece: rails, LED shelves, two stake sockets, splash divider and mist opening.")
        chassis(base.component)
        jar = add_component(root, "02 Slide-out reservoir", pose(-37,0,2.8), "Pull from the wet end, press side latch inward to release.")
        tank(jar.component)
        cap = add_component(root, "03 Reservoir cap with two release latches", pose(-37,0,32.55),
                            "Press sideways to release. Nominal 0.35 mm seal allowance; dry fit first.")
        cap_pose = cap.transform2
        cap_pose.setToRotation(math.pi, adsk.core.Vector3D.create(1,0,0), pt(0,0))
        cap_pose.translation = adsk.core.Vector3D.create(-3.7,0,3.255)
        cap.transform2 = cap_pose
        design.snapshots.add()
        lid(cap.component)
        cam = add_component(root, "04 Rear slide-out camera tray", pose(37,0,2.8,math.pi),
                            "Upright seat, side belt access, releases toward the electronics end.")
        camera_tray(cam.component)

        printable = (base, jar, cap, cam)
        checks = adsk.core.ObjectCollection.create()
        for occurrence in printable:
            if occurrence.component.bRepBodies.count != 1:
                raise ValueError(f"Expected one connected solid: {occurrence.component.name}")
            checks.add(occurrence)
        results = design.analyzeInterference(design.createInterferenceInput(checks))
        clashes = []
        if results:
            for result in results:
                clashes.append([result.entityOne.name, result.entityTwo.name,
                                result.interferenceBody.volume])
        if clashes:
            raise ValueError(f"Printable components intersect at rest: {clashes}")

        cam_ref = add_component(root, "81 ESP32-CAM 40 x 27 reference", pose(37,0,2.8,math.pi),
                                "Verify actual socket, connector, camera cable and lens geometry.")
        box(cam_ref.component, 11, -20, 7.6, 3, 40, 27, "Board envelope")
        led_ref = add_component(root, "82 12V RGB strip reference", pose(),
                                "Use only confirmed manufacturing cut marks.")
        for y in (-38,28):
            box(led_ref.component, -33, y, 2.4, 66, 10, 2.5, "WS2811 strip envelope")
        mist = add_component(root, "83 Atomizer module envelope - choose hardware", pose(),
                             "Optional 16 mm envelope. Keep the opening visible in its default state.")
        cylinder(mist.component, -37+OUTLET, 0, -2.2, 8, 2, "Atomizer reference")
        mist.isLightBulbOn = False
        wires, cover, pot = model_references(root)
        show(app.activeViewport, (250,-320,185), (0,0,-21))
        app.activeViewport.saveAsImageFile(str(OUTPUT / f"{V8_NAME}-assembly.png"), 1500, 1100)
        for occurrence in (wires, cover, pot):
            occurrence.isLightBulbOn = False
        show(app.activeViewport, (-125,-165,145), (0,0,8))
        app.activeViewport.saveAsImageFile(str(OUTPUT / f"{V8_NAME}-internals.png"), 1500, 1100)

        for occurrence, name in zip(printable, ("01-chassis", "02-tank-dry", "03-tank-cap", "04-camera-tray")):
            write_stl(OUTPUT / f"{name}.stl", coupon.print_triangles(
                occurrence.component.bRepBodies.item(0), 0, 0))
        tracks = []
        for occurrence, (x,y) in zip(printable, ((0,0),(84,0),(84,115),(0,96))):
            tracks.extend(coupon.print_triangles(occurrence.component.bRepBodies.item(0),x,y))
        write_stl(OUTPUT / f"{V8_NAME}-dry-plate.stl", tracks)
        exported = design.exportManager
        if not exported.execute(exported.createFusionArchiveExportOptions(str(OUTPUT / f"{V8_NAME}.f3d"))):
            raise ValueError("Fusion archive export failed")
        (OUTPUT / "validation.json").write_text(json.dumps({
            "printable_solids": len(printable), "seated_interferences": clashes,
            "latch_side_gap_mm": coupon.LATCH_SIDE_CLEARANCE,
            "outlet_center_mm": [-37+OUTLET,0], "plate_triangles": len(tracks)
        }, indent=2), encoding="utf-8")
    except Exception:
        (OUTPUT / "fusion-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
