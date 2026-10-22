import argparse,zipfile,hashlib,json,gc
from pathlib import Path
import UnityPy
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();w=a.work
with zipfile.ZipFile(a.base) as z:
 source=w/'identity-base.unity3d'
 if not source.exists():source.write_bytes(z.read('assets/bin/Data/data.unity3d'))
e=UnityPy.load(str(source));before={};changes=[]
for o in e.objects:
 key=(o.assets_file.name,o.path_id);before[key]=hashlib.sha256(o.get_raw_data()).hexdigest()
 if o.type.name=='PlayerSettings':
  t=o.read_typetree();assert t['productName']=='PlantsVsZombiesEN';t['productName']='PlantsVsZombiesENAI'
  def walk(x):
   if isinstance(x,dict):
    for k,v in x.items():
     if v=='com.LanPiaoPiao.PlantsVsZombiesEN':x[k]=v+'AI'
     else:walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(t);o.save_typetree(t);changes.append(list(key))
assert len(changes)==1
out=w/'identity-ai.unity3d';out.write_bytes(e.file.save(packer='lz4'));del e;gc.collect()
e=UnityPy.load(str(out));after={};actual=[]
for o in e.objects:
 key=(o.assets_file.name,o.path_id);after[key]=hashlib.sha256(o.get_raw_data()).hexdigest()
 if before[key]!=after[key]:actual.append(list(key));assert o.type.name=='PlayerSettings'
assert before.keys()==after.keys() and actual==changes
(w/'identity-unity-audit.json').write_text(json.dumps({'objects_compared':len(before),'changed':actual,'only_player_settings_changed':True},indent=2))
print('Verified Unity identity change across',len(before),'objects')
