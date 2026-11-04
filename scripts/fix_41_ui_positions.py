"""Normalize only the thirteen reviewed UIConfigMenu caption sizes."""
import argparse,gc,hashlib,json
from pathlib import Path
import UnityPy
from build_unity_ui_translation import read_tmp_text,hierarchy_for_component
from refine_almanac_layout import make_generator

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','review','dummy-dll-dir','output','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();review=json.loads(a.review.read_text(encoding='utf8'))
    assert sha(a.base.read_bytes())==review['base_bundle_sha256']
    labels={(r['file'],r['id']):r for r in review['labels']};assert len(labels)==13
    env=UnityPy.load(str(a.base));env.typetree_generator=make_generator('2022.3.62f1',a.dummy_dll_dir)
    objects={(o.assets_file.name,o.path_id):o for o in env.objects}
    before={k:sha(o.get_raw_data()) for k,o in objects.items()};audits=[];expected_trees={}
    fields={'m_fontSize','m_fontSizeBase','m_enableAutoSizing'}
    for k,row in labels.items():
        o=objects[k];assert read_tmp_text(o.get_raw_data())[0]==row['text']
        hierarchy=hierarchy_for_component(objects,k);assert list(hierarchy)==row['hierarchy'] and hierarchy[-1]=='UIConfigMenu'
        tree=o.read_typetree(check_read=False)
        assert {f:tree[f] for f in fields}==row['before']
        original=dict(tree)
        tree.update(m_fontSize=review['font_size'],m_fontSizeBase=review['font_size'],m_enableAutoSizing=0)
        assert {f for f in tree if tree[f]!=original[f]}<=fields
        o.save_typetree(tree)
        expected_trees[k]=tree
        audits.append(dict(key=list(k),text=row['text'],before=row['before'],after={f:tree[f] for f in sorted(fields)}))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(env.file.save(packer='lz4'));del env,objects;gc.collect()
    check=UnityPy.load(str(a.output));check.typetree_generator=make_generator('2022.3.62f1',a.dummy_dll_dir);changed=[]
    for o in check.objects:
        k=(o.assets_file.name,o.path_id)
        if sha(o.get_raw_data())!=before[k]:
            changed.append(k);assert k in labels
            assert o.read_typetree(check_read=False)==expected_trees[k]
    assert set(changed)==set(labels) and len(check.objects)==len(before)
    del check;gc.collect()
    report=dict(objects_compared=len(before),changed_objects=sorted(changed),only_reviewed_captions_changed=True,fields=sorted(fields),font_size=review['font_size'],labels=audits,base_sha256=review['base_bundle_sha256'],output_sha256=sha(a.output.read_bytes()))
    write(a.report,report)
    identity=json.loads((a.base.parent/'identity-report.json').read_text(encoding='utf8'));assert identity['sha256']==report['base_sha256']
    identity.update(sha256=report['output_sha256'],ui_position_typography=report);write(a.output.parent/'identity-report.json',identity)
    print('Verified 13 caption objects; all other '+str(len(before)-13)+' objects unchanged',flush=True)

if __name__=='__main__':main()
