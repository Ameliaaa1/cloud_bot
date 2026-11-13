"""Cloud Bot V7 — mm input, native Fusion sketches/features. Run inside Fusion.
Layout prototype only: selected purchased parts and wet sealing are not validated.
"""
import adsk.core, adsk.fusion, math, os, json, traceback

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'v7-cad'))
P = adsk.core.Point3D.create
V = adsk.core.ValueInput.createByString
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

def pt(x,y,z=0): return P(x/10,y/10,z/10)
def plane(c,z):
    i=c.constructionPlanes.createInput(); i.setByOffset(c.xYConstructionPlane,V(f'{z} mm'))
    p=c.constructionPlanes.add(i); p.isLightBulbOn=False
    return p
def sketch(c,z,name):
    s=c.sketches.add(plane(c,z)); s.name=name; return s
def extrude(c,s,h,name,op=NEW):
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles: profiles.add(p)
    i=c.features.extrudeFeatures.createInput(profiles,op)
    i.setDistanceExtent(False,V(f'{h} mm'))
    f=c.features.extrudeFeatures.add(i); f.name=name; s.isVisible=False
    return f
def rect(c,x,y,z,w,d,h,name,op=NEW):
    s=sketch(c,z,name+' sketch'); s.sketchCurves.sketchLines.addTwoPointRectangle(pt(x,y),pt(x+w,y+d))
    return extrude(c,s,h,name,op)
def circle(c,x,y,z,r,h,name,op=NEW):
    s=sketch(c,z,name+' sketch'); s.sketchCurves.sketchCircles.addByCenterRadius(pt(x,y),r/10)
    return extrude(c,s,h,name,op)
def ring(c,x,y,z,r,ri,h,name):
    s=sketch(c,z,name+' sketch')
    for rr in [r,ri]: s.sketchCurves.sketchCircles.addByCenterRadius(pt(x,y),rr/10)
    # Only annular profile.
    p=next(p for p in s.profiles if p.profileLoops.count==2)
    i=c.features.extrudeFeatures.createInput(p,NEW); i.setDistanceExtent(False,V(f'{h} mm'))
    f=c.features.extrudeFeatures.add(i); f.name=name;s.isVisible=False;return f
def ellipse_ring(c,z,a,b,wall,h,name):
    s=sketch(c,z,name+' sketch')
    for aa,bb in [(a,b),(a-wall,b-wall)]:
        s.sketchCurves.sketchEllipses.add(pt(0,0),pt(aa,0),pt(0,bb))
    p=next(p for p in s.profiles if p.profileLoops.count==2)
    i=c.features.extrudeFeatures.createInput(p,NEW);i.setDistanceExtent(False,V(f'{h} mm'))
    f=c.features.extrudeFeatures.add(i);f.name=name;s.isVisible=False;return f
def join_all(c):
    if c.bRepBodies.count<2:return
    bodies=list(c.bRepBodies); ts=adsk.core.ObjectCollection.create()
    for b in bodies[1:]:ts.add(b)
    i=c.features.combineFeatures.createInput(bodies[0],ts);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    c.features.combineFeatures.add(i)
def tube_path(c,coords,r,name):
    s=c.sketches.add(c.xYConstructionPlane);s.name=name+' path'
    pts=adsk.core.ObjectCollection.create()
    for x,y,z in coords:pts.add(pt(x,y,z))
    curve=s.sketchCurves.sketchFittedSplines.add(pts)
    path=c.features.createPath(curve)
    pi=c.constructionPlanes.createInput();pi.setByDistanceOnPath(curve,adsk.core.ValueInput.createByReal(0))
    pp=c.constructionPlanes.add(pi);pp.isLightBulbOn=False
    profile=c.sketches.add(pp)
    center=profile.modelToSketchSpace(pt(*coords[0]))
    profile.sketchCurves.sketchCircles.addByCenterRadius(center,r/10)
    i=c.features.sweepFeatures.createInput(profile.profiles.item(0),path,NEW)
    f=c.features.sweepFeatures.add(i);f.name=name
    profile.isVisible=False;s.isVisible=False;return f
def temp_body(c,temp,name):
    bf=c.features.baseFeatures.add();bf.name=name;bf.startEdit()
    b=c.bRepBodies.add(temp,bf);b.name=name;bf.finishEdit();return b

def build(context):
    app=adsk.core.Application.get();ui=app.userInterface
    os.makedirs(OUT,exist_ok=True)
    log=[]
    try:
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name='Cloud Bot V7 - soil stake prototype'
        design=adsk.fusion.Design.cast(app.activeProduct)
        design.designType=adsk.fusion.DesignTypes.ParametricDesignType
        design.unitsManager.distanceDisplayUnits=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root=design.rootComponent
        parts=[]
        def comp(name,note=''):
            o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=o.component;c.name=name
            c.description=note;parts.append((o,c));log.append(name)
            with open(os.path.join(OUT,'build-progress.txt'),'w',encoding='utf8') as f:f.write('\n'.join(log))
            return c
        for name,val,comment in [('rod_diameter','3 mm','Nominal stainless rod; sockets 3.4 mm'),('soil_depth','55 mm','Reference insertion depth, test wet-soil stability'),('cloud_width','140 mm','Visual envelope target'),('tank_working_volume','10','mL target, with headspace')]:
            design.userParameters.add(name,V(val),'' if name=='tank_working_volume' else 'mm',comment)

        # Fixed lightweight chassis: two joined cross rails, tank seat, rear electronics shelf.
        c=comp('01 Chassis - dry wet divider','Prototype polymer carrier; all liquid must remain inside sealed cartridge.')
        rect(c,-48,-4,90,96,8,2.4,'Main load rail')
        rect(c,-22,-33,90,44,69,2.4,'Equipment deck')
        # Drain/mist clearance through deck; tank floor above remains separate.
        circle(c,0,-17,90,8,2.4,'Mist clearance',CUT)
        for x in [-26,26]:
            ring(c,x,0,78,4.5,1.7,14.4,'Blind rod socket')
        rect(c,-23,5,92.4,46,1.8,17,'Wet dry splash divider')
        for x in [-45,45]:
            for y in [-8,8]:
                rect(c,x-4,y-4,90,8,8,2.4,'Cover fastening lug')
        join_all(c)
        for x in [-45,45]:
            for y in [-8,8]:circle(c,x,y,90,1.2,2.4,'M2 clearance',CUT)

        c=comp('02 Removable cloud cage','Diffuser support; dress with removable translucent cover, keep underside mist port clear.')
        ellipse_ring(c,93,65,43,2,2.4,'Cloud perimeter')
        rect(c,-65,-2,93,130,4,2.4,'Cage cross rail')
        # Arch ribs rise from ring to support a cloud-like soft shell.
        for x,top in [(-43,121),(0,142),(43,125)]:
            yy=43*math.sqrt(1-(x/65)**2)
            tube_path(c,[(x,-yy,94),(x,-yy*.75,top-8),(x,0,top),(x,yy*.75,top-8),(x,yy,94)],1.3,'Diffuser arch')
        tube_path(c,[(-64,0,94),(-43,0,121),(0,0,142),(43,0,125),(64,0,94)],1.3,'Longitudinal rib')
        for x in [-45,45]:
            for y in [-8,8]:rect(c,x-4,y-4,93,8,8,2.4,'Cover screw tab')
        # connect tabs to central rail
        for x in [-45,45]:rect(c,x-2,-8,93,4,16,2.4,'Tab bridge')
        join_all(c)
        for x in [-45,45]:
            for y in [-8,8]:circle(c,x,y,93,1.2,2.4,'M2 cover hole',CUT)

        c=comp('03 LED saddle left','12 mm wide LED carrier; verify actual strip width and cut-group length.')
        rect(c,-57,-25,97,14,50,1.6,'LED carrier')
        rect(c,-57,-1,95.4,14,2,1.6,'Central mounting foot')
        join_all(c)
        for y in [-18,16]:rect(c,-55,y,97,10,2,1.6,'Cable tie slot',CUT)
        c=comp('04 LED saddle right','Two 50 mm mounting zones. Final LED cut groups pending measurement.')
        rect(c,43,-25,97,14,50,1.6,'LED carrier')
        rect(c,43,-1,95.4,14,2,1.6,'Central mounting foot')
        join_all(c)
        for y in [-18,16]:rect(c,45,y,97,10,2,1.6,'Cable tie slot',CUT)

        c=comp('05 Reservoir cartridge - 10 mL target','36 x 22 x 22 mm, cavity 33 x 19 x 19 mm = 11.91 mL gross. NOT a validated sealed tank.')
        rect(c,-18,-29,92.8,36,22,22,'Tank outer')
        rect(c,-16.5,-27.5,94.3,33,19,20.5,'Water cavity',CUT)
        circle(c,0,-17,92.8,3,1.5,'Outlet placeholder',CUT)
        c=comp('06 Tank lid with refill neck','Removable gasketed lid concept, gasket compression and fasteners to finalize after atomizer selection.')
        rect(c,-18,-29,115.1,36,22,1.5,'Lid')
        circle(c,11,-18,115.1,3,1.5,'Fill hole',CUT)
        ring(c,11,-18,116.6,4.5,3,4,'Fill neck')
        join_all(c)
        c=comp('07 Refill plug - silicone concept','Friction plug; real sealing fit requires material testing.')
        circle(c,11,-18,117,2.9,3.6,'Plug stem')
        circle(c,11,-18,120.6,5.5,1.8,'Grip flange');join_all(c)
        c=comp('08 Lid gasket - placeholder','0.3 mm clearance shown. Specify actual seal before wet use.')
        s=sketch(c,114.8,'Gasket outline')
        for x,y,w,d in [(-18,-29,36,22),(-16.5,-27.5,33,19)]:s.sketchCurves.sketchLines.addTwoPointRectangle(pt(x,y),pt(x+w,y+d))
        p=next(p for p in s.profiles if p.profileLoops.count==2)
        i=c.features.extrudeFeatures.createInput(p,NEW);i.setDistanceExtent(False,V('0.3 mm'));c.features.extrudeFeatures.add(i);s.isVisible=False
        c=comp('09 Mist head mount - placeholder','Assumed 16 mm disc envelope; replace with selected matched atomizer and driver.')
        ring(c,0,-17,86,11,8.2,4,'Atomizer seat')
        ring(c,0,-17,83,9,6,3,'Downward outlet lip')
        join_all(c)
        c=comp('10 Atomizer envelope - NOT selected','Dummy 16 x 2 mm envelope, no claim of actual compatibility.')
        circle(c,0,-17,87,8,2,'Atomizer placeholder')
        c=comp('11 ESP32 CAM envelope - measure first','40 x 27 x 10 mm simplified envelope. Connector/pin clearance not validated.')
        rect(c,-20,8,96,40,27,10,'Board envelope')
        circle(c,0,21,106,4,4,'Lens envelope')
        c=comp('12 Electronics removable tray','Camera must face user through a clear opening in soft cover; pose/driver enclosure to finalize.')
        rect(c,-22,7,92.8,44,30,1.6,'PCB tray')
        for x in [-22,20]:rect(c,x,7,94.4,2,30,2,'Side guide')
        join_all(c)
        for x in [-16,16]:rect(c,x-1,11,92.8,2,22,1.6,'Board strap slot',CUT)

        for x,side in [(-26,'left'),(26,'right')]:
            c=comp('13 Soil stake '+side+' - stainless 3 mm','145 mm straight structural rod; lower 55 mm in soil. No strength or pull-out validation.')
            circle(c,x,0,-55,1.5,145,'Structural stake')
        c=comp('14 Silver decorative branches','Shapeable wire ornament; structural loads carried by two straight rods. Bend templates only.')
        for side in [-1,1]:
            for endx,endy,h in [(52,-12,96),(38,20,95),(12,-28,94)]:
                tube_path(c,[(side*26,0,20),(side*23,3,44),(side*(endx*.65),endy*.45,67),(side*endx,endy,h)],.8,'Shaped silver branch')
        c=comp('15 Rear power cable route - reference','Route low-voltage supply externally along rear stake. Supply and driver not designed here.')
        tube_path(c,[(28,4,-35),(29,4,15),(29,4,70),(32,18,93),(20,30,95)],1,'Cable route')

        tm=adsk.fusion.TemporaryBRepManager.get()
        c=comp('90 Cloud soft cover ENVELOPE - hide for internals','Spheres indicate removable diffuser volume only, not a solid printable shell.')
        envelope=parts[-1][0]
        for x,y,z,r in [(-47,0,112,23),(-25,-6,121,27),(3,0,127,29),(34,1,121,26),(51,0,110,19),(-17,22,112,22),(20,22,113,23),(-15,-24,111,23),(24,-23,112,23)]:
            temp_body(c,tm.createSphere(pt(x,y,z),r/10),'Soft cover lobe')
        c.opacity=.20
        c=comp('91 Flowerpot reference - 120 mm OD','Reference only; user has no selected pot. Rim z=10, soil z=0, base z=-100.')
        pot=parts[-1][0]
        outer=tm.createCylinderOrCone(pt(0,0,-100),4.3,pt(0,0,10),6)
        inner=tm.createCylinderOrCone(pt(0,0,-97),4.05,pt(0,0,11),5.75)
        tm.booleanOperation(outer,inner,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        temp_body(c,outer,'Pot wall');c.opacity=.30

        # Set meaningful simple appearance colors via available generic appearance.
        colors=[(225,230,235),(232,235,240),(240,200,100),(240,200,100),(125,190,220),(125,190,220),(205,210,220),(80,90,100),(125,190,220),(160,170,175),(40,65,55),(215,220,225),(175,180,190),(175,180,190),(190,195,205),(65,70,80),(245,245,250),(210,195,175)]
        for idx,(o,c) in enumerate(parts):
            try:
                base=app.materialLibraries.item(0).appearances.item(0)
                a=design.appearances.addByCopy(base,'V7 '+str(idx))
                prop=adsk.core.ColorProperty.cast(a.appearanceProperties.itemById('generic_diffuse'))
                if prop:prop.value=adsk.core.Color.create(*colors[idx%len(colors)],255)
                for b in c.bRepBodies:b.appearance=a
            except:pass
        for o,c in parts:
            c.isConstructionFolderLightBulbOn=False;c.isSketchFolderLightBulbOn=False
        cam=app.activeViewport.camera
        cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
        cam.eye=pt(280,-390,245);cam.target=pt(0,0,30);cam.upVector=adsk.core.Vector3D.create(0,0,1)
        cam.isFitView=True;app.activeViewport.camera=cam;app.activeViewport.fit();adsk.doEvents()
        app.activeViewport.saveAsImageFile(os.path.join(OUT,'v7-assembly.png'),1600,1200)
        envelope.isLightBulbOn=False;pot.isLightBulbOn=False
        app.activeViewport.fit();adsk.doEvents()
        app.activeViewport.saveAsImageFile(os.path.join(OUT,'v7-internals.png'),1600,1200)
        errors=[]
        for n in range(design.timeline.count):
            obj=design.timeline.item(n).entity
            if hasattr(obj,'healthState') and obj.healthState==adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
                errors.append(obj.name+': '+obj.errorOrWarningMessage)
        data={'parts':[{'name':c.name,'bodies':c.bRepBodies.count,'description':c.description} for o,c in parts],'timeline_count':design.timeline.count,'feature_errors':errors,'units':'mm','reservoir_gross_ml':11.913,'working_volume_target_ml':10}
        with open(os.path.join(OUT,'validation.json'),'w',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
        ex=design.exportManager
        ex.execute(ex.createFusionArchiveExportOptions(os.path.join(OUT,'CloudBot-V7.f3d')))
        ex.execute(ex.createSTEPExportOptions(os.path.join(OUT,'CloudBot-V7.step')))
        # Keep reference bodies hidden and internals visible for review.
        with open(os.path.join(OUT,'SUCCESS.txt'),'w',encoding='utf8') as f:f.write('Built and exported. '+str(len(parts))+' components; '+str(design.timeline.count)+' timeline entries. Errors: '+str(errors))
        ui.messageBox('V7 prototype built: '+str(len(parts))+' components.\nEditable archive and STEP exported to design/v7-cad.\nWaterproofing, purchased-part fits, and wet-soil stability require testing.','Cloud Bot V7')
    except:
        err=traceback.format_exc()
        with open(os.path.join(OUT,'ERROR.txt'),'w',encoding='utf8') as f:f.write(err)
        ui.messageBox(err,'V7 build error')

def polish(context):
    app=adsk.core.Application.get();ui=app.userInterface
    try:
        d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
        occ=list(root.occurrences)
        camera=next(o for o in occ if o.component.name.startswith('11 '))
        t=adsk.core.Matrix3D.create();t.setToRotation(math.pi/2,adsk.core.Vector3D.create(1,0,0),pt(0,21.5,101))
        tr=t.translation;tr.y+=.85;tr.z+=1.8;t.translation=tr
        camera.transform2=t
        d.snapshots.add()
        c=next(o.component for o in occ if o.component.name.startswith('12 '))
        rect(c,-22,35.4,94.4,44,1.6,39,'Upright camera back')
        rect(c,-22,24.5,103.9,44,12.5,1.6,'Camera bottom ledge')
        join_all(c)
        c.description='Upright camera cradle. Lens faces toward negative Y; soft-cover viewing aperture and connector fit require hardware measurement.'
        for x in [-15,15]:
            o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=o.component
            c.name='16 Tank retaining bridge '+('L' if x<0 else 'R')
            c.description='Removable concept hold-down. Fit and compression need prototype testing; not a verified watertight closure.'
            for y in [-32,-6.8]:rect(c,x-1.5,y,92.4,3,2.5,24.2,'Retention upright')
            rect(c,x-1.5,-32,116.6,3,27.7,1.5,'Lid hold-down')
            join_all(c)
        # Use a known generic appearance from the live document, or log libraries for review.
        apps=[]
        for lib in app.materialLibraries:
            apps.append({'library':lib.name,'examples':[lib.appearances.item(j).name for j in range(min(5,lib.appearances.count))]})
        with open(os.path.join(OUT,'appearance-libraries.json'),'w',encoding='utf8') as f:json.dump(apps,f,ensure_ascii=False,indent=2)
        envelope=next(o for o in occ if o.component.name.startswith('90 '));pot=next(o for o in occ if o.component.name.startswith('91 '))
        # Native interference check; ornamental wires and cover envelopes excluded.
        entities=adsk.core.ObjectCollection.create()
        for o in root.occurrences:
            if int(o.component.name[:2])<14:entities.add(o)
        collisions=[]
        try:
            results=d.analyzeInterference(d.createInterferenceInput(entities))
            if results:
                for r in results:
                    collisions.append({'one':r.entityOne.name,'two':r.entityTwo.name,'volume_cm3':r.interferenceBody.volume if r.interferenceBody else None})
        except Exception as e:collisions=[{'check_error':str(e)}]
        with open(os.path.join(OUT,'interference.json'),'w',encoding='utf8') as f:json.dump(collisions,f,ensure_ascii=False,indent=2)
        errors=[]
        for n in range(d.timeline.count):
            obj=d.timeline.item(n).entity
            if hasattr(obj,'healthState') and obj.healthState==adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:errors.append(obj.name)
        occ=list(root.occurrences)
        data={'parts':[{'name':o.component.name,'bodies':o.component.bRepBodies.count,'description':o.component.description} for o in occ],'timeline_count':d.timeline.count,'feature_errors':errors,'units':'mm','reservoir_gross_ml':11.913,'working_volume_target_ml':10}
        with open(os.path.join(OUT,'validation.json'),'w',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
        envelope.isLightBulbOn=False;pot.isLightBulbOn=False
        app.activeViewport.fit();adsk.doEvents();app.activeViewport.saveAsImageFile(os.path.join(OUT,'v7-internals.png'),1600,1200)
        envelope.isLightBulbOn=True;pot.isLightBulbOn=True
        app.activeViewport.fit();adsk.doEvents();app.activeViewport.saveAsImageFile(os.path.join(OUT,'v7-assembly.png'),1600,1200)
        envelope.isLightBulbOn=False
        app.activeViewport.fit();adsk.doEvents()
        ex=d.exportManager
        ex.execute(ex.createFusionArchiveExportOptions(os.path.join(OUT,'CloudBot-V7.f3d')))
        ex.execute(ex.createSTEPExportOptions(os.path.join(OUT,'CloudBot-V7.step')))
        with open(os.path.join(OUT,'SUCCESS.txt'),'w',encoding='utf8') as f:f.write('Built and exported. '+str(len(occ))+' components; '+str(d.timeline.count)+' timeline entries. Errors: '+str(errors))
        ui.messageBox('V7 updated: camera faces forward, retaining bridges added, CAD exported.','Cloud Bot V7')
    except:
        err=traceback.format_exc()
        with open(os.path.join(OUT,'polish-error.txt'),'w',encoding='utf8') as f:f.write(err)
        ui.messageBox(err,'V7 finish error')

def run(context):
    app=adsk.core.Application.get()
    d=adsk.fusion.Design.cast(app.activeProduct)
    if d and any(o.component.name.startswith('16 Tank') for o in d.rootComponent.occurrences):
        cage=next(o.component for o in d.rootComponent.occurrences if o.component.name.startswith('02 '))
        if not any(f.name=='Camera service clearance' for f in cage.features.extrudeFeatures):
            rect(cage,-23,7,103,46,32,33,'Camera service clearance',CUT)
        bridge=next(o for o in d.rootComponent.occurrences if o.component.name=='16 Tank retaining bridge R')
        if abs(bridge.transform2.translation.x)<.01:
            t=bridge.transform2;v=t.translation;v.x=-1.1;t.translation=v;bridge.transform2=t;d.snapshots.add()
        entities=adsk.core.ObjectCollection.create()
        for o in d.rootComponent.occurrences:
            if int(o.component.name[:2])<14 or o.component.name.startswith('16 '):entities.add(o)
        res=d.analyzeInterference(d.createInterferenceInput(entities))
        rows=[]
        if res:
            for r in res:
                rows.append({'one':r.entityOne.parentComponent.name,'two':r.entityTwo.parentComponent.name,'volume_cm3':r.interferenceBody.volume})
        with open(os.path.join(OUT,'interference-details.json'),'w',encoding='utf8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
        env=next(o for o in d.rootComponent.occurrences if o.component.name.startswith('90 '))
        pot=next(o for o in d.rootComponent.occurrences if o.component.name.startswith('91 '))
        env.isLightBulbOn=False;pot.isLightBulbOn=False
        app.activeViewport.fit();adsk.doEvents();app.activeViewport.saveAsImageFile(os.path.join(OUT,'v7-internals.png'),1600,1200)
        env.isLightBulbOn=True;pot.isLightBulbOn=True
        app.activeViewport.fit();adsk.doEvents();app.activeViewport.saveAsImageFile(os.path.join(OUT,'v7-assembly.png'),1600,1200)
        env.isLightBulbOn=False;app.activeViewport.fit()
        ex=d.exportManager;ex.execute(ex.createFusionArchiveExportOptions(os.path.join(OUT,'CloudBot-V7.f3d')));ex.execute(ex.createSTEPExportOptions(os.path.join(OUT,'CloudBot-V7.step')))
        with open(os.path.join(OUT,'validation.json'),encoding='utf8') as f:data=json.load(f)
        data['timeline_count']=d.timeline.count;data['checked_interferences']=rows
        data['interference_scope']='Structural parts, camera and atomizer envelopes, retaining bridges; excludes decorative branches, power cable and reference cover/pot.'
        with open(os.path.join(OUT,'validation.json'),'w',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
        app.userInterface.messageBox('V7 exported. Checked interferences: '+str(len(rows)),'V7 fit check')
    elif d and any(o.component.name.startswith('91 Flowerpot') for o in d.rootComponent.occurrences):
        polish(context)
    else:
        build(context)
