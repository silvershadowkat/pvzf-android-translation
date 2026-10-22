import sys,json
from pathlib import Path
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);args=ap.parse_args()
W=args.work.resolve();U=W.parent/'upgrade405'
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import UnityPy
from polish_android_ui import make_generator
out={}
for label,path in [('original',U/'android405/data.unity3d'),('packaged',W/'identity-base.unity3d')]:
 env=UnityPy.load(str(path));env.typetree_generator=make_generator('2022.3.62f1',U/'types/DummyDll')
 objects={o.path_id:o for o in env.objects if o.assets_file.name=='resources.assets'}
 def tree(i):return objects[i].read_typetree(check_read=False)
 menu=tree(189693);go=tree(menu['m_GameObject']['m_PathID'])
 transform=next(c['component']['m_PathID'] for c in go['m_Component'] if objects[c['component']['m_PathID']].type.name in ('RectTransform','Transform'))
 rows=[];visited=set()
 def walk(tid,path):
  if tid in visited:return
  visited.add(tid);t=tree(tid);g=tree(t['m_GameObject']['m_PathID']);path=path+'/'+g['m_Name']
  for c in g['m_Component']:
   i=c['component']['m_PathID'];o=objects[i]
   if o.type.name=='MonoBehaviour':
    d=tree(i)
    for key in ['m_text','m_Text']:
     if key in d:rows.append({'path':path,'id':i,'text':d[key]})
  for child in t.get('m_Children',[]):walk(child['m_PathID'],path)
 walk(transform,'')
 out[label]={'gameobjects':len(visited),'texts':rows}
(W/'mode-audit/prefab-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for label,data in out.items():
 print(label,'objects',data['gameobjects'],'texts',len(data['texts']))
 for row in data['texts']:print(row['id'],repr(row['text']))
