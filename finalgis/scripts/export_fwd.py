#!/usr/bin/env python3
"""Map native GIS receipts to Core-owned FWD; never mutate simulation state."""
import argparse, hashlib, json, pathlib, subprocess, uuid

NS=uuid.UUID('8969c9e1-7b29-416e-9f7d-1f0b18479387')
def uid(text):return str(uuid.uuid5(NS,text))
def export(directory, validator, source):
    directory=pathlib.Path(directory).resolve()
    p=directory/'workflow.json';r=json.loads(p.read_text())
    fictional=r['mode']=='fictional'
    world='7a1e0c55-6b0f-4d39-9a44-3f2a8e1c9b01' if fictional else '8699ab0c-8242-458e-b3db-4e39249b3c56'
    frame=dict(r['frame']);frame.pop('model_to_frame',None);frame.pop('geodetic_anchor',None)
    if 'origin_projected' in frame:frame['origin']=frame.pop('origin_projected')
    sources=[]
    if fictional:
        data=p.read_bytes()
        # Pin the algorithm+seed specification, not variable timings in the receipt.
        data=json.dumps({'generator':r['generator'],'version':r['version'],'seed':r['seed']},sort_keys=True).encode()
        sources=[{'id':'fiction-spec','uri':'urn:finalverse:finalgis:fictional-heightfield:0.1','license':'CC0-1.0','sha256':hashlib.sha256(data).hexdigest(),'version':'0.1.0','classification':'fictional','attribution':'FinalGIS procedural demonstration; no Earth measurements'}]
    else:
        source=pathlib.Path(source)
        for filename,source_id in [('buildings.geojson','montreal-roofs'),('roads.geojson','montreal-roads'),('dtm.tif','nrcan-dtm')]:
            original=next(x for x in r['provenance'] if x['source_id']==source_id)
            sources.append({'id':source_id,'uri':original['url'],'license':original['license'],'sha256':hashlib.sha256((source/filename).read_bytes()).hexdigest(),'version':original['release']+'; bounded subset 2026-10-24','classification':'derived','attribution':original['attribution']})
    a=r['asset'];asset_id=uid(world+':finalgis-geography:'+str(r['seed']))
    fwd={'schema':'finalverse.world-definition/0.1','definition_id':uid(world+':finalgis-definition'),'version':1,'world':{'id':world,'name':'Aetheria' if fictional else 'Earth'},'frames':[frame],'sources':sources,'assets':[{'id':asset_id,'sha256':a['sha256'],'bytes':a['bytes'],'media_type':'model/gltf-binary','frame_id':frame['id'],'kind':'mesh','classification':'fictional' if fictional else 'derived','source_ids':[s['id'] for s in sources],'transform':{'translation':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}}],'generation':{'generator':r['generator'],'version':r['version'],'seed':r['seed'],'operations':['fictional-heightfield-and-decorative-lake'] if fictional else ['verify-content-pinned-source','GDAL-PROJ-project-and-clip-260m','GEOS-buffer-road-centerlines-2.5m','GEOS-constrained-triangulation','resample-NRCan-DEM-33x33','procedural-constant-12m-roof-outline-extrusion']},'semantics':[{'asset_id':asset_id,'category':'fictional_geography' if fictional else 'source_derived_terrain_roofs_with_estimated_massing','classification':'fictional' if fictional else 'derived'}]}
    target=directory/'world.fwd.json'
    with target.open('x') as f:json.dump(fwd,f,indent=2);f.write('\n')
    result=subprocess.run([str(validator),'validate',str(target),str(directory/'objects')],check=True,capture_output=True,text=True,timeout=30)
    receipt={'schema':'finalgis.fwd-export/1','definition_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'validation':json.loads(result.stdout),'world_mutated':False,'publication':'offline_export_only'}
    with (directory/'fwd-export.json').open('x') as f:json.dump(receipt,f,indent=2)
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--validator',required=True);p.add_argument('--source');a=p.parse_args()
    print(json.dumps(export(a.directory,a.validator,a.source)))
