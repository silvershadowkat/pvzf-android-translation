"""Reviewed October 21 PC delta on top of the tested Android prerelease-3 payload.

Use a frozen input snapshot and fail if another change has occurred since this
patch last ran. Never touch device data, game identifiers, or native libraries.
"""
import argparse, collections, gc, hashlib, json, re, shutil, zipfile
from pathlib import Path
import UnityPy
from build_metadata_translation import load_pc_translations, parse_metadata, build_metadata
from prepare_runtime_payload import normalize, digest, META, OFFICIAL_SHA

PC_MAIN='c7fb5997d65e1d5248f3d7a9ca9c9e0a4b516640'
PC_BASE='94b9ec0aecc3cea494c5b2c2883a7cbf14642440'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def plain(s):return re.sub(r'\s+',' ',re.sub('<[^>]+>','',s)).strip() if isinstance(s,str) else s
def main():
 ap=argparse.ArgumentParser()
 for n in ('work','old_pc','new_pc','official'):ap.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=ap.parse_args();w=a.work;backup=w/'coverage-r12/baseline';backup.mkdir(parents=True,exist_ok=True)
 assert digest(a.official)==OFFICIAL_SHA
 report_path=w/'coverage-r12/port-report.json'
 paths=('candidate.unity3d','metadata.dat','english/translations.json')
 if report_path.exists():
  prior=read(report_path)
  assert all(digest(w/p)==h for p,h in prior['outputs'].items()),'Payload changed since last port; review before rerunning'
 for p in paths:
  dest=backup/p;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():shutil.copyfile(w/p,dest)
 inputs={p:digest(backup/p) for p in paths}
 report={'pc_base':PC_BASE,'pc_overlay':PC_MAIN,'inputs':inputs,'almanac':[],'dictionary':[],'metadata':[],'retained':[],'names':[]}
 with zipfile.ZipFile(a.official) as z: original_meta=z.read(META)
 original=UnityPy.load(str(w/'official.unity3d'));cn={}
 for o in original.objects:
  if o.type.name=='TextAsset':
   d=o.read()
   if d.m_Name in ('LawnStrings','ZombieStrings','DetailStrings'):cn[d.m_Name]=json.loads(d.m_Script)
 del original;gc.collect()
 env=UnityPy.load(str(backup/'candidate.unity3d'));assets={}
 for o in env.objects:
  if o.type.name=='TextAsset':
   d=o.read()
   if d.m_Name in cn:assets[d.m_Name]=(d,json.loads(d.m_Script))
 runtime=read(backup/'english/translations.json');exact=runtime['exact'];name_pairs=collections.defaultdict(set)
 # Align by stable numeric IDs, not array position. Require matching Chinese
 # content and the previous PC English before accepting a changed display field.
 for kind,root,idkey in [('Lawn','plants','seedType'),('Zombie','zombies','theZombieType')]:
  asset,current=assets[kind+'Strings'];android_cn={r[idkey]:r for r in cn[kind+'Strings'][root]}
  pc_cn={r[idkey]:r for r in read(a.new_pc/'Dumps'/(kind+'Strings.json'))[root]}
  pe={r[idkey]:r for r in read(a.new_pc/'Localization/English/Almanac'/(kind+'StringsTranslate.json'))[root]}
  po={r[idkey]:r for r in read(a.old_pc/'Localization/English/Almanac'/(kind+'StringsTranslate.json'))[root]}
  for row in current[root]:
   i=row[idkey]
   for field in ('name','introduce','info','cost'):
    new=pe.get(i,{}).get(field);old=po.get(i,{}).get(field)
    if new is None or new==old or plain(row.get(field))==plain(new):continue
    evidence={'asset':kind+'Strings','id':i,'field':field}
    if plain(android_cn.get(i,{}).get(field))!=plain(pc_cn.get(i,{}).get(field)) or plain(row.get(field))!=plain(old):
     report['retained'].append({**evidence,'reason':'Source or prior English differs; retained Android wording'});continue
    assert isinstance(new,str) and not re.search('[\u3400-\u9fff]',new)
    report['almanac'].append({**evidence,'before':row[field],'after':normalize(new)})
    row[field]=normalize(new)
   source=android_cn.get(i,{}).get('name','');target=re.sub('<[^>]+>','',row.get('name','')).strip()
   if re.search('[\u3400-\u9fff]',source) and target and not re.search('[\u3400-\u9fff]',target):name_pairs[source].add(target)
  asset.m_Script=json.dumps(current,ensure_ascii=False,separators=(',',':'));asset.save()
 # Detail keys stay intact; match their full original Chinese text to PC dumps.
 asset,current=assets['DetailStrings'];pc_cn=read(a.new_pc/'Dumps/DetailStrings.json')
 pe=read(a.new_pc/'Localization/English/Almanac/DetailStringsTranslate.json');po=read(a.old_pc/'Localization/English/Almanac/DetailStringsTranslate.json')
 for source,row in zip(cn['DetailStrings']['details'],current['details']):
  keys=[k for k,v in pc_cn.items() if plain(v)==plain(source['text'])]
  if len(keys)!=1:continue
  k=keys[0];new=pe.get(k);old=po.get(k)
  if new and new!=old and plain(row['text'])==plain(old):
   report['almanac'].append({'asset':'DetailStrings','key':k,'field':'text','before':row['text'],'after':normalize(new)})
   row['text']=normalize(new)
 asset.m_Script=json.dumps(current,ensure_ascii=False,separators=(',',':'));asset.save()
 (w/'candidate.unity3d').write_bytes(env.file.save(packer='lz4'));del env;gc.collect()
 oldx,_,_,_=load_pc_translations(a.old_pc/'Localization/English/Strings',False)
 newx,_,_,_=load_pc_translations(a.new_pc/'Localization/English/Strings',False)
 updates={}
 # Two already reviewed Android corrections are more complete/equivalent.
 preserve=('爆裂连珠：','硬化-坚不可摧：')
 for source,new in newx.items():
  if normalize(new)==normalize(oldx.get(source,'')):continue
  if source.startswith(preserve):
   report['retained'].append({'source':source,'reason':'Existing reviewed Android correction retained'});continue
  before=exact.get(source);target=normalize(new).replace('shrooom','shroom')
  if before and before.startswith('<nobr>') and '：\n' in target:
   heading,body=target.split('：\n',1);target='<nobr>'+heading+'</nobr>：\n'+body
  exact[source]=target;updates[source]=(before,target)
  report['dictionary'].append({'source':source,'before':before,'after':target,'provenance':'PC main delta'})
 # Small Android-specific display variants. PC has a longer Purgatory sentence
 # with a speed multiplier that is absent here, so do not import that claim.
 variants={
  '制作指南':'Creator Guide','关卡制作指南':'Level Creator Guide','返回制作指南':'Back to Creator Guide',
  '额外2次刷新机会，僵尸血量x4':'+2 Rerolls, Zombie HP x4',
  '通关获得50诸神币':'Complete to earn 50 God Coins',
  '通关获得75诸神币':'Complete to earn 75 God Coins',
  '通关获得100诸神币':'Complete to earn 100 God Coins',
 }
 for source,target in variants.items():
  exact[source]=target;report['dictionary'].append({'source':source,'after':target,'provenance':'Reviewed Android display variant; PC terminology'})
 for source,targets in name_pairs.items():
  if len(targets)==1 and source not in exact:
   target=next(iter(targets));exact[source]=target;report['names'].append({'source':source,'english':target})
 # A fixed node-operation label is composed with a plus sign in Android.
 if exact.get('整数')=='Integer':exact['+ 整数']='+ Integer'
 runtime['pc_overlay_commit']=PC_MAIN
 online=read(a.new_pc/'Localization/English/Strings/custom_level_data.json')
 runtime['online_levels']={k:{f:normalize(re.sub(r'</?size(?:=[^>]*)?>','',v[f],flags=re.I)) for f in ('name','startTip')} for k,v in online.items()
     if re.fullmatch(r'level_[0-9]+_[A-Za-z0-9]+',k) and all(isinstance(v.get(f),str) and not re.search('[\u3400-\u9fff]',v[f]) for f in ('name','startTip'))}
 report['online_level_count']=len(runtime['online_levels'])
 write(w/'english/translations.json',runtime)
 # Update already baked literal translations only where their original Chinese
 # slot is known, and the current English is exactly the tested runtime wording.
 raw=(backup/'metadata.dat').read_bytes();layout,entries=parse_metadata(raw);_,original=parse_metadata(original_meta)
 output=[e.raw for e in entries]
 for i,(source,current) in enumerate(zip(original,entries)):
  pair=updates.get(source.text)
  if pair and pair[0] is not None and current.text==pair[0]:
   output[i]=pair[1].encode('utf8');report['metadata'].append({'index':i,'source':source.text,'before':current.text,'after':pair[1]})
 (w/'metadata.dat').write_bytes(build_metadata(raw,layout,output))
 report['outputs']={p:digest(w/p) for p in paths}
 write(report_path,report)
 print(json.dumps({k:len(report[k]) for k in ('almanac','dictionary','metadata','names','retained')}))
if __name__=='__main__':main()
