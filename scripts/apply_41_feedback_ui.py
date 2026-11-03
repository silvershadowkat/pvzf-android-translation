"""Apply source-guarded static display fixes from the S26 4.1 review."""
import argparse,gc,hashlib,json
from pathlib import Path
import UnityPy
from build_unity_ui_translation import read_tmp_text,replace_tmp_text
from migrate_version_text import same_arguments

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('official-bundle','base','review','output','report'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    rules=json.loads(a.review.read_text(encoding='utf8'))['serialized']
    expected={(x['file'],x['id']):x for x in rules}
    assert len(expected)==len(rules)
    source=UnityPy.load(str(a.official_bundle));found=set()
    for o in source.objects:
        key=(o.assets_file.name,o.path_id)
        if key in expected:
            rule=expected[key]
            assert o.type.name=='MonoBehaviour' and read_tmp_text(o.get_raw_data())[0]==rule['source']
            assert same_arguments(rule['source'],rule['english'])
            found.add(key)
    assert found==set(expected)
    del source;gc.collect()
    env=UnityPy.load(str(a.base))
    before={(o.assets_file.name,o.path_id):sha(o.get_raw_data()) for o in env.objects}
    for o in env.objects:
        key=(o.assets_file.name,o.path_id)
        if key in expected:
            raw=o.get_raw_data();rule=expected[key]
            assert read_tmp_text(raw)[0]==rule['before'],key
            o.set_raw_data(replace_tmp_text(raw,rule['english']))
    a.output.write_bytes(env.file.save(packer='lz4'))
    del env;gc.collect()
    check=UnityPy.load(str(a.output));changed=set()
    for o in check.objects:
        key=(o.assets_file.name,o.path_id)
        if sha(o.get_raw_data())!=before[key]:
            changed.add(key)
            assert read_tmp_text(o.get_raw_data())[0]==expected[key]['english']
    assert changed==set(expected)
    report={'rules':rules,'only_reviewed_TMP_text_changed':True,'objects_compared':len(before),'base_sha256':sha(a.base.read_bytes()),'output_sha256':sha(a.output.read_bytes())}
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    identity_path=a.output.parent/'identity-report.json'
    identity=json.loads(identity_path.read_text(encoding='utf8'))
    assert report['base_sha256'] in (identity['sha256'],identity.get('post_identity_review',{}).get('base_sha256'))
    identity.update(sha256=report['output_sha256'],post_identity_review=report)
    identity_path.write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Verified',len(changed),'static UI corrections; other objects unchanged',flush=True)

if __name__=='__main__':main()
