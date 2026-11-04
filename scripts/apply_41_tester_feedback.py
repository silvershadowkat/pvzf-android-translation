"""Apply the source-guarded first 4.1 feedback review to the published r4 APK.

Keep native recognition/music untouched. Restore stat-parser templates before
packaging and translate only their final display labels through the existing
runtime dictionary. All other serialized objects must remain identical.
"""
import argparse, gc, hashlib, json, re, shutil, zipfile
from pathlib import Path
import UnityPy
from build_metadata_translation import parse_metadata, load_pc_translations, is_usable_pc_translation
from build_unity_ui_translation import read_tmp_text, replace_tmp_text, hierarchy_for_component
from compact_metadata_tail import compact_metadata_tail
from protected_metadata import restore_metadata, verify_metadata, PLANT_STAT_METADATA_TEMPLATES
from prepare_41_payload import reviewed_format_rule, clean
from migrate_version_text import same_arguments
from overlay_text_assets import normalize_android_almanac_text_asset

META='assets/bin/Data/Managed/Metadata/global-metadata.dat'
BUNDLE='assets/bin/Data/data.unity3d'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('released-apk','official','source-texts','pc-source-texts','pc','review','work','identity','music-report'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);review=read(a.review)
    assert file_sha(a.released_apk)==review['base_apk_sha256']
    assert file_sha(a.official)==review['official_sha256']
    with zipfile.ZipFile(a.released_apk) as z:
        base=z.read(BUNDLE);metadata=z.read(META)
        dictionary=json.loads(z.read('assets/english/translations.json'))
        previous_keys=set(dictionary['exact'])
        old_manifest=json.loads(z.read('assets/english/manifest.json'))
        refresh=a.work/'almanac-refresh';refresh.mkdir(exist_ok=True)
        for name in ('LawnStrings','ZombieStrings','DetailStrings'):
            (refresh/(name+'.json')).write_bytes(z.read('assets/english-almanac/'+name+'.json'))
    with zipfile.ZipFile(a.official) as z:official_metadata=z.read(META)
    restored,changes=restore_metadata(official_metadata,metadata)
    restored=compact_metadata_tail(restored)
    before=[v.text for v in parse_metadata(metadata)[1]]
    after=[v.text for v in parse_metadata(restored)[1]]
    assert all(after[i] in PLANT_STAT_METADATA_TEMPLATES for i in range(len(before)) if before[i]!=after[i])
    (a.work/'metadata.dat').write_bytes(restored)
    protection=verify_metadata(official_metadata,restored)
    official=read(a.source_texts/'LawnStrings.json')['plants']
    actual_pc=read(a.pc_source_texts/'LawnStrings.json')['plants']
    pc=read(a.pc/'Localization/English/Almanac/LawnStringsTranslate.json')['plants']
    byid=lambda rows:{r['seedType']:r for r in rows}
    official,actual_pc,pc=map(byid,(official,actual_pc,pc))
    pc_exact,_,_,_=load_pc_translations(a.pc/'Localization/English/Strings',False)
    identity=read(a.identity);assert identity['sha256']==sha(base)
    e=UnityPy.load(base);del base
    objects={(o.assets_file.name,o.path_id):o for o in e.objects}
    hashes={k:sha(o.get_raw_data()) for k,o in objects.items()}
    fields=[];allowed=set();new_lawn=None
    for k,o in objects.items():
        if o.type.name!='TextAsset':continue
        data=o.read()
        if data.m_Name!='LawnStrings':continue
        rows=json.loads(data.m_Script)
        for row in rows['plants']:
            ident=row['seedType'];claims=review['plants'].get(str(ident))
            if not claims:continue
            assert official[ident]==actual_pc[ident],('Actual PC/Android source differs',ident)
            # Do not create names, including mechanically plausible compound names.
            assert row['name']==official[ident]['name']
            for field,claim in claims.items():
                assert field in ('info','introduce')
                source=official[ident][field];previous=row[field]
                assert sha(source.encode())==claim['source_sha256']
                assert sha(previous.encode())==claim['previous_sha256']
                target=claim['english'];origin=claim['origin']
                pc_value=pc[ident].get(field,'')
                if is_usable_pc_translation(pc_value) and not re.search('[\u3400-\u9fff]',pc_value):
                    target=clean(pc_value);origin='Blooms'
                assert same_arguments(source,target)
                row[field]=target
                dictionary['exact'][source]=target
                if previous!=source:dictionary['exact'][previous]=target
                fields.append(dict(id=ident,field=field,origin=origin,source_sha256=claim['source_sha256'],english=target))
        data.m_Script=json.dumps(rows,ensure_ascii=False,separators=(',',':'))
        data.save();allowed.add(k);new_lawn=data.m_Script
    assert len(fields)==sum(len(v) for v in review['plants'].values())
    assert new_lawn is not None
    assert not normalize_android_almanac_text_asset('LawnStrings',new_lawn)[1]
    (refresh/'LawnStrings.json').write_text(new_lawn,encoding='utf-8')
    for row in review['serialized']:
        k=(row['file'],row['id']);o=objects[k]
        raw=o.get_raw_data();assert read_tmp_text(raw)[0]==row['source']
        ancestry=hierarchy_for_component(objects,k)
        assert ancestry[-1]=='MaLiangMenu' and not any('input' in n.lower() for n in ancestry)
        o.set_raw_data(replace_tmp_text(raw,row['english']));allowed.add(k)
    output=a.work/'feedback.unity3d';output.write_bytes(e.file.save(packer='lz4'))
    del objects,e;gc.collect()
    e=UnityPy.load(str(output));changed=set();count=0
    for o in e.objects:
        k=(o.assets_file.name,o.path_id);count+=1
        if sha(o.get_raw_data())!=hashes[k]:changed.add(k)
    assert count==len(hashes) and changed==allowed,(changed,allowed)
    del e;gc.collect()
    rules=dict(dictionary['regex']);applied=[]
    for source,target in review['runtime_exact'].items():
        if source in pc_exact and is_usable_pc_translation(pc_exact[source]):target=clean(pc_exact[source])
        dictionary['exact'][source]=target;applied.append(dict(source=source,english=target))
        if '{' in source:
            assert same_arguments(source,target)
            rule=reviewed_format_rule(source,target)
            if rule:rules[rule[0]]=rule[1]
    rules.update(review['rendered_rules']);dictionary['regex']=list(map(list,rules.items()))
    english=a.work/'english';english.mkdir(exist_ok=True)
    write(english/'translations.json',dictionary)
    assert previous_keys.issubset(dictionary['exact'])
    report=dict(status='Local feedback candidate; not device-tested or published',pc_commit=old_manifest['pc_commit'],pc_checked_commit=review['pc_checked_commit'],previous_keys_retained=True,plant_fields=fields,static_fields=review['serialized'],runtime_display=applied,metadata_restored=changes,protected_metadata=protection,objects_compared=count,changed_objects=sorted(changed),only_reviewed_objects_changed=True,base_apk_sha256=review['base_apk_sha256'],bundle_sha256=file_sha(output))
    write(a.work/'translation-report.json',report)
    identity.update(sha256=report['bundle_sha256'],post_tester_feedback_review=report)
    write(a.work/'identity-report.json',identity)
    shutil.copyfile(a.music_report,a.work/'music-profile-build.json')
    print(json.dumps({k:report[k] for k in ('status','objects_compared','changed_objects','protected_metadata')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
