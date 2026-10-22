"""Apply reviewed English to LevelCreatorHelp display fields, never node IDs.

No device access, save-file operations, metadata rewrites or native hooks.
The baseline and report make this patch repeatable and fail closed after edits.
"""
import argparse, collections, gc, hashlib, json, re, shutil
from pathlib import Path
import UnityPy
from build_metadata_translation import parse_metadata

ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v): return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def validate(source, target, pin):
    assert canonical(source) == pin['source_canonical_sha256'], 'Unexpected Chinese guide revision'
    assert source.keys() == target.keys() == {'topics','nodes'}
    assert len(source['topics']) == len(target['topics']) == 11
    assert len(source['nodes']) == len(target['nodes']) == 241
    for old,new in zip(source['topics'],target['topics']):
        assert old.keys() == new.keys() == {'title','body'}
        assert re.findall(r'</?b>',old['body']) == re.findall(r'</?b>',new['body'])
    number_review=[]
    for index,(old,new) in enumerate(zip(source['nodes'],target['nodes'])):
        assert old.keys() == new.keys() == {'type','purpose','usage','example','warning'}
        assert old['type'] == new['type']
        for field in ('purpose','usage','example','warning'):
            assert isinstance(new[field],str) and new[field].strip()
            nums=lambda s:collections.Counter(re.findall(r'(?<![A-Za-z])\d+(?:\.\d+)?',s))
            if nums(old[field]) != nums(new[field]):
                number_review.append([index,field,list(nums(old[field]).elements()),list(nums(new[field]).elements())])
    assert number_review == pin['reviewed_numeric_text_differences'], 'Unreviewed numerical change'
    # Three exact Chinese technical terms are deliberately retained in English
    # explanations. Internal lookup text must not be replaced with display names.
    cjk=re.findall(r'[\u3400-\u9fff]+',json.dumps(target,ensure_ascii=False))
    assert sorted(cjk)==sorted(['外挂','二爷无视植物','电力相生']), cjk
    assert 'Bullet_pea' in target['nodes'][232]['example']
    assert 'walk' in target['nodes'][59]['example']
    assert 'SuperSkill' in target['nodes'][195]['warning']
    assert 'StarUp' in target['nodes'][196]['warning']
    for name in ('Day/Night','Day_6/Night_6','Pool/NightPool','Roof/NightRoof','SnowPool'):
        assert name in target['nodes'][235]['warning']
    for collection in ('topics','nodes'):
        for row in target[collection]:
            for key,value in row.items():
                if key!='type': assert '\u2014' not in value

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);a=ap.parse_args()
    w=a.work;area=w/'guide-r13';area.mkdir(exist_ok=True)
    pin=read(ROOT/'assets/creator-guide-4.0.5-review.json')
    target=read(ROOT/'assets/creator-guide-4.0.5.en.json')
    ui=read(ROOT/'assets/creator-guide-ui-4.0.5.json')
    editor=read(ROOT/'assets/creator-editor-ui-4.0.5.json')
    report_path=area/'apply-report.json';paths=['candidate.unity3d','english/translations.json'];previous=None
    if report_path.exists():
        previous=read(report_path)
        assert all(sha(w/p)==h for p,h in previous['outputs'].items()), 'Payload changed since guide patch; review before rerunning'
    backup=area/'baseline'
    for p in paths:
        b=backup/p;b.parent.mkdir(parents=True,exist_ok=True)
        if not b.exists():shutil.copyfile(w/p,b)
    env=UnityPy.load(str(backup/'candidate.unity3d'))
    matches=[]
    for obj in env.objects:
        if obj.type.name=='TextAsset':
            d=obj.read()
            if d.m_Name=='LevelCreatorHelp':matches.append((obj,d))
    assert len(matches)==1 and matches[0][0].path_id==3378
    obj,d=matches[0];source=json.loads(d.m_Script);validate(source,target,pin)
    candidate=area/'guide-candidate.unity3d'
    reuse=bool(previous and canonical(target)==previous['english_canonical_sha256']
               and candidate.exists() and sha(candidate)==previous['outputs']['candidate.unity3d']
               and all(sha(backup/p)==h for p,h in previous['inputs'].items()))
    if not reuse:
        d.m_Script=json.dumps(target,ensure_ascii=False,separators=(',',':'));d.save()
        candidate.write_bytes(env.file.save(packer='lz4'))
    del env;gc.collect()
    # Verify every serialized object against the frozen r12 payload, not only
    # the edited JSON. A bundle repack must not alter other game objects.
    def inventory(path):
        e=UnityPy.load(str(path));res={}
        for o in e.objects:
            key=(o.assets_file.name,o.path_id)
            assert key not in res
            res[key]=hashlib.sha256(o.get_raw_data()).hexdigest()
        return res
    if reuse:
        checked=previous['serialized_objects_checked'];changed=previous['changed_objects']
    else:
        before=inventory(backup/'candidate.unity3d');gc.collect()
        after=inventory(candidate);gc.collect()
        assert before.keys()==after.keys()
        checked=len(before);changed=[k for k in before if before[k]!=after[k]]
    assert len(changed)==1 and changed[0][1]==3378, changed
    runtime=read(backup/'english/translations.json');exact=runtime['exact'];entries=[]
    # Reuse translated full explanations in node-detail screens too. Only
    # unambiguous whole strings are eligible; existing reviewed PC text wins.
    pairs=collections.defaultdict(set)
    for key in ('topics','nodes'):
        for old,new in zip(source[key],target[key]):
            for field in old:
                if field!='type':pairs[old[field]].add(new[field])
    for cn,values in pairs.items():
        if len(values)==1 and cn not in exact:
            en=next(iter(values));exact[cn]=en;entries.append({'source':cn,'before':None,'after':en,'reason':'Reviewed guide display text'})
    for cn,en in ui.items():
        old=exact.get(cn)
        if old==en:continue
        if old is not None: assert cn=='僵尸进家失败', (cn,old,en)
        exact[cn]=en;entries.append({'source':cn,'before':old,'after':en,'reason':'Guide-linked UI terminology; display only'})
    # Pin each additional editor literal to the current game metadata. Translate
    # only rendered text; never change metadata, port IDs or editable values.
    _,literals=parse_metadata((w/'metadata.dat').read_bytes())
    for row in editor['entries']:
        cn,en=row['source'],row['english']
        assert literals[row['metadata_index']].text==cn, ('Editor source changed',row['metadata_index'])
        variants=[(cn,en)]
        if cn.count('\n')==en.count('\n'):
            variants.extend((x,y) for x,y in zip(cn.splitlines(),en.splitlines()) if x.strip() and y.strip())
        if cn.startswith('<b>'):
            variants.append((re.sub(r'</?b>','',cn).strip(),re.sub(r'</?b>','',en).strip()))
            variants.extend((re.sub(r'</?b>','',x),re.sub(r'</?b>','',y)) for x,y in list(variants) if x.startswith('<b>') and '\n' not in x)
        for source_text,english_text in variants:
            old=exact.get(source_text)
            if old==english_text:continue
            assert old is None, ('Editor translation conflict',source_text,old,english_text)
            exact[source_text]=english_text
            entries.append({'source':source_text,'before':old,'after':english_text,'reason':'Reviewed generated editor help; metadata literal '+str(row['metadata_index'])})
    assert all(pattern.startswith('^') and pattern.endswith('$') for pattern,_ in editor['regex'])
    runtime['regex']=editor['regex']+runtime['regex']
    runtime['creator_guide_revision']=editor['revision']
    staged=area/'translations.json';write(staged,runtime)
    shutil.copyfile(candidate,w/'candidate.unity3d');shutil.copyfile(staged,w/'english/translations.json')
    report={'source_canonical_sha256':canonical(source),'english_canonical_sha256':canonical(target),
            'inputs':{p:sha(backup/p) for p in paths},'outputs':{p:sha(w/p) for p in paths},
            'topics':11,'nodes':241,'unchanged_node_ids':241,'display_fields':11*2+241*4,
            'serialized_objects_checked':checked,'bundle_verification_reused_by_hash':reuse,'changed_objects':changed,'dictionary_changes':entries,
            'ambiguous_explanation_strings_skipped':sum(len(v)>1 for v in pairs.values()),
            'editor_regex':editor['regex'],'revision':editor['revision'],
            'numeric_text_review':pin['reviewed_numeric_text_differences'],'retained_technical_terms':['外挂','二爷无视植物','电力相生'],
            'not_changed':['game metadata','native game libraries','node types','save refresh policy','user save data']}
    write(report_path,report)
    print(json.dumps({k:v for k,v in report.items() if k in ('topics','nodes','display_fields','serialized_objects_checked','changed_objects','ambiguous_explanation_strings_skipped')}))

if __name__=='__main__':main()
