"""Prepare 4.0.5 runtime dictionaries, original soundtrack, and refresh fixture."""
import argparse, collections, gc, hashlib, json, re, shutil, zipfile, struct
from pathlib import Path
import UnityPy
from build_metadata_translation import load_pc_translations, parse_metadata, build_metadata, is_usable_pc_translation
from polish_android_ui import make_generator

PIN='94b9ec0aecc3cea494c5b2c2883a7cbf14642440'
BASE_SHA='3a2318c29d6da4ed8a2f7f7a1017f6c766c16f471cd6f8c2eae7aaf66863899d'
OFFICIAL_SHA='2c200c6eef6ecfb6cfe2554125cf1f52ba74dab1f037594c8591903ee53ef9f6'
META='assets/bin/Data/Managed/Metadata/global-metadata.dat'
BUNDLE='assets/bin/Data/data.unity3d'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def normalize(s):return re.sub(r'</?size(?:=[^>]*)?>','',s).replace('—','-')

def prepare_almanac_refresh(work):
    """Extract current embedded language assets and create a seed-only name fixture."""
    candidate=work/'candidate.unity3d';report_path=work/'almanac-refresh-payload.json'
    source_hash=digest(candidate)
    if report_path.exists():
        report=json.loads(report_path.read_text('utf-8'))
        if report.get('schema')==1 and report.get('candidate_sha256')==source_hash and all((work/name).is_file() and digest(work/name)==h for name,h in report['outputs'].items()):
            return report
    output=work/'almanac-refresh';output.mkdir(exist_ok=True)
    wanted={'LawnStrings','ZombieStrings','DetailStrings'};found=[];env=UnityPy.load(str(candidate))
    for obj in env.objects:
        if obj.type.name!='TextAsset':continue
        asset=obj.read()
        if asset.m_Name not in wanted:continue
        text=asset.m_Script
        if isinstance(text,bytes):text=text.decode('utf-8')
        data=json.loads(text);(output/(asset.m_Name+'.json')).write_text(text,encoding='utf-8')
        found.append(asset.m_Name)
        if asset.m_Name=='LawnStrings':
            plants=[p for p in data['plants'] if p['seedType']==0]
            assert len(plants)==1 and plants[0]['name']=='Peashooter','Unexpected display-name fixture source'
            plants[0]['name']='STALE Pea'
            stale=json.dumps(data,ensure_ascii=False,separators=(',',':'))
            (output/'seed-LawnStrings.json').write_text(stale,encoding='utf-8')
            asset.m_Script=stale;asset.save()
    assert set(found)==wanted and len(found)==3,'Unexpected embedded almanac inventory'
    (work/'seed-candidate.unity3d').write_bytes(env.file.save(packer='lz4'));del env;gc.collect()
    outputs=[*output.glob('*.json'),work/'seed-candidate.unity3d']
    report={'schema':1,'candidate_sha256':source_hash,'outputs':{p.relative_to(work).as_posix():digest(p) for p in outputs},'seed_name':{'seedType':0,'before':'Peashooter','after':'STALE Pea'},'scope':'Only LawnStrings TextAsset name field in seed bundle; main bundle unchanged.'}
    write(report_path,report);return report

def main():
    ap=argparse.ArgumentParser()
    for n in ['base','official','pc','work','dlls']:ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--rebuild-bundle',action='store_true')
    a=ap.parse_args();a.work.mkdir(parents=True,exist_ok=True)
    assert digest(a.base)==BASE_SHA;assert digest(a.official)==OFFICIAL_SHA
    with zipfile.ZipFile(a.base) as z:
        raw=z.read(META);(a.work/'metadata.dat').write_bytes(raw)
        if not (a.work/'pre2.unity3d').exists():(a.work/'pre2.unity3d').write_bytes(z.read(BUNDLE))
    with zipfile.ZipFile(a.official) as z:
        original_meta=z.read(META)
        if not (a.work/'official.unity3d').exists():(a.work/'official.unity3d').write_bytes(z.read(BUNDLE))
        if not (a.work/'resources.resource').exists():(a.work/'resources.resource').write_bytes(z.read('assets/bin/Data/resources.resource'))
    strings=a.pc/'Localization/English/Strings'
    exact,_,regex,counts=load_pc_translations(strings,include_android_fallbacks=False)
    layout,english=parse_metadata(raw);_,original=parse_metadata(original_meta)
    # Current reviewed Android factual corrections outrank older upstream wording.
    known=collections.defaultdict(set)
    for cn,en in zip(original,english):
        if cn.text!=en.text and re.search('[\u3400-\u9fff]',cn.text) and not re.search('[\u3400-\u9fff]',en.text):known[cn.text].add(en.text)
    for cn,values in known.items():
        if len(values)==1:exact[cn]=next(iter(values))
    # Tactic group headings are runtime keys. Derive their DISPLAY names from
    # the uniquely matched first-level PC modifier rather than altering the key.
    cn=json.loads((a.pc/'Dumps/travel_buffs.json').read_text('utf-8-sig'))
    en=json.loads((strings/'travel_buffs.json').read_text('utf-8-sig'));groups={}
    for i in range(13002,13046,4):
        c=cn['advancedBuffs'][str(i)];e=en['advancedBuffs'][str(i)]
        heading=c['desc'].split('：',1)[0];group=heading.split('-')[-1]
        assert group and is_usable_pc_translation(e['name'])
        groups[group]={'english':e['name'],'pc_record':i,'source_heading':heading}
        exact[group]=e['name']
    # These Android group keys differ from the PC keys. Their first-level titles
    # were matched as complete records and verified in the pinned prerelease 2.
    groups['裂空']={'english':'G-fish Bomber','pc_record':13014,'source_heading':'支援-飞艇','android_id':'Shooting_裂空'}
    groups['全能']={'english':'Omnipotence','source':'prerelease 2 complete-record projection','android_id':'Shooting_全能'}
    exact.update({k:v['english'] for k,v in groups.items()})
    # Confirmed generic card-stage labels. These affect text only.
    exact.setdefault('进阶','Evolved')
    exact.setdefault('被动','Passive')
    exact.setdefault('特别感谢','Special Thanks')
    exact.setdefault('提示','Hint')
    normalized={k:normalize(v) for k,v in exact.items() if is_usable_pc_translation(v)}
    rules=[];rejected=[]
    for item in regex:
        pattern,target,_,source=item
        if pattern=='BUFF_NAME_FORMAT':
            rejected.append({'pattern':pattern,'source':source,'reason':'PC layout template, not a regex translation'});continue
        if '(?P' in pattern or '(?<' in pattern or re.search(r'\{\d+[:,]',target):
            rejected.append({'pattern':pattern,'source':source,'reason':'requires explicit .NET compatibility review'});continue
        rules.append([pattern,normalize(target)])
    rules.insert(0,[r'(\d+(?:-\d+)+)教程',r'{0} Tutorial'])
    rules.insert(0,[r'(\d+(?:-\d+)+)提示',r'{0} Hint'])
    for cn,group in groups.items():
        rules.append([r'([^\u3400-\u9fff]*)'+re.escape(cn)+r'([^\u3400-\u9fff]*)',r'{0}'+group['english']+r'{1}'])
    assets=a.work/'english';assets.mkdir(exist_ok=True)
    write(assets/'translations.json',{'pc_commit':PIN,'exact':normalized,'regex':rules,'display_groups':{k:v['english'] for k,v in groups.items()}})
    # Keep each original AudioClip and stream resource together. Blooms tracks
    # are external, locally loaded files selected at runtime, never gameplay SFX.
    output=a.work/'candidate.unity3d'
    audio_report=[];ui=[]
    if not output.exists() or a.rebuild_bundle:
        original_env=UnityPy.load(str(a.work/'official.unity3d'))
        audio={o.path_id:(o.read().m_Name,o.get_raw_data()) for o in original_env.objects if o.type.name=='AudioClip'}
        del original_env;gc.collect()
        env=UnityPy.load(str(a.work/'pre2.unity3d'));env.typetree_generator=make_generator('2022.3.62f1',a.dlls)
        scripts={o.path_id:o.read().m_ClassName for o in env.objects if o.type.name=='MonoScript'}
        objects={o.path_id:o for o in env.objects}
        for o in env.objects:
            if o.type.name=='AudioClip':
                name,data=audio[o.path_id];assert name==o.read().m_Name
                if o.get_raw_data()!=data:audio_report.append({'path_id':o.path_id,'name':name,'before_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'after_sha256':hashlib.sha256(data).hexdigest()});o.set_raw_data(data)
            elif o.type.name=='MonoBehaviour':
                # The fixed MonoBehaviour header has a 64-bit script path ID at
                # byte 20 in this pinned little-endian Unity build. Read the
                # complete type tree only for the three UI classes under review.
                raw_object=o.get_raw_data();script=scripts.get(struct.unpack_from('<q',raw_object,20)[0]) if len(raw_object)>=28 else None
                if script in ('OptionMenu','InGameUI','UIConfigMenu'):
                    tree=o.read_typetree()
                    ui.append({'id':o.path_id,'class':script,'fields':tree})
            elif o.type.name=='PlayerSettings':
                tree=o.read_typetree();write(a.work/'player-settings-before.json',tree)
                assert tree['productName']=='PlantsVsZombiesRH'
                tree['productName']='PlantsVsZombiesEN'
                # A guarded schema walk, limited to bundle IDs matching the original identity.
                def update(x):
                    if isinstance(x,dict):
                        for k,v in x.items():
                            if v=='com.LanPiaoPiao.PlantsVsZombiesRH':x[k]='com.LanPiaoPiao.PlantsVsZombiesEN'
                            else:update(v)
                    elif isinstance(x,list):
                        for v in x:update(v)
                update(tree);o.save_typetree(tree)
        output.write_bytes(env.file.save(packer='lz4'));del env;gc.collect()
        write(a.work/'audio-restoration.json',audio_report);write(a.work/'ui-context.json',ui)
    included=json.loads((Path(__file__).resolve().parents[1]/'assets/audio-translation-map-4.0.5.json').read_text())['included']
    for name in included:
        options=[a.pc/'[Custom Audios]'/f'{name}{ext}' for ext in ('.ogg','.mp3')]
        source=next(p for p in options if p.exists());shutil.copyfile(source,assets/source.name)
    # Seed fixture is an otherwise valid, same-version metadata file. It changes
    # one visible label so stale override removal is observable after an update.
    fixture=[v.raw for v in english];slots=[i for i,v in enumerate(english) if v.text=='God Coins: {0}'];assert slots
    for i in slots:fixture[i]=b'STALE TEST Coins: {0}'
    (a.work/'stale-test-metadata.dat').write_bytes(build_metadata(raw,layout,fixture))
    write(a.work/'translation-coverage.json',{'pc_commit':PIN,'exact_count':len(normalized),'regex_count':len(rules),'regex_exclusions':rejected,'groups':groups,'source_counts':counts,'fixture_slots':slots,'policy':'Complete display matches and explicit group tokens only. Unknown text retained. No dictionary/resource/save keys changed.'})
    print(json.dumps({'exact':len(normalized),'regex':len(rules),'excluded_regex':len(rejected),'groups':len(groups),'music_tracks':len(included),'fixture_slots':slots}))

if __name__=='__main__':main()
