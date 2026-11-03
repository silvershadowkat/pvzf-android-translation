"""Restore Android almanac typography and reviewed static 4.1 mode labels.

Every static field is source-guarded. All other serialized objects must retain
their original hash. This is deliberately separate from old-version layouts.
"""
import argparse, gc, hashlib, json, re
from pathlib import Path
import UnityPy
from build_unity_ui_translation import read_tmp_text, replace_tmp_text, hierarchy_for_component
from overlay_text_assets import normalize_android_almanac_text_asset
from migrate_version_text import same_arguments

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','review','output','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); rules=json.loads(a.review.read_text(encoding='utf8'))['serialized_followup']
    expected={(x['file'],x['id']):x for x in rules}; assert len(expected)==len(rules)
    e=UnityPy.load(str(a.base)); objects={(o.assets_file.name,o.path_id):o for o in e.objects}
    before={k:sha(o.get_raw_data()) for k,o in objects.items()}; almanacs=[]
    for k,row in expected.items():
        o=objects[k]; raw=o.get_raw_data(); assert read_tmp_text(raw)[0]==row['source'], k
        ancestry=hierarchy_for_component(objects,k)
        assert not any('input' in n.lower() or 'textarea' in n.lower() for n in ancestry), (k,ancestry)
        assert same_arguments(row['source'],row['english']),k
        assert re.findall(r'\{[A-Za-z]\w*\}',row['source'])==re.findall(r'\{[A-Za-z]\w*\}',row['english'])
        o.set_raw_data(replace_tmp_text(raw,row['english']))
        row['hierarchy']=ancestry
    for k,o in objects.items():
        if o.type.name!='TextAsset':continue
        d=o.read()
        if d.m_Name not in ('LawnStrings','ZombieStrings'):continue
        normalized,count=normalize_android_almanac_text_asset(d.m_Name,d.m_Script)
        if count:
            d.m_Script=normalized;d.save();almanacs.append({'key':list(k),'name':d.m_Name,'removed_size_tags':count})
    assert len(almanacs)==2,'Expected the two PC-sized entity almanacs'
    allowed=set(expected)|{tuple(x['key']) for x in almanacs}
    a.output.write_bytes(e.file.save(packer='lz4'));del objects,e;gc.collect()
    e=UnityPy.load(str(a.output));changed=set()
    for o in e.objects:
        k=(o.assets_file.name,o.path_id)
        if sha(o.get_raw_data())!=before[k]:
            changed.add(k)
            if k in expected:assert read_tmp_text(o.get_raw_data())[0]==expected[k]['english']
            else:
                d=o.read();assert not normalize_android_almanac_text_asset(d.m_Name,d.m_Script)[1]
    assert changed==allowed
    report={'static_fields':rules,'almanacs':almanacs,'objects_compared':len(before),'only_reviewed_objects_changed':True,
            'base_sha256':sha(a.base.read_bytes()),'output_sha256':sha(a.output.read_bytes())}
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    path=a.output.parent/'identity-report.json'; identity=json.loads(path.read_text(encoding='utf8'))
    assert report['base_sha256'] in (identity['sha256'],identity.get('post_identity_typography_review',{}).get('base_sha256'))
    identity.update(sha256=report['output_sha256'],post_identity_typography_review=report)
    path.write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Verified',len(expected),'static UI fields and',sum(x['removed_size_tags'] for x in almanacs),'PC font-size tags; other objects unchanged')

if __name__=='__main__':main()
