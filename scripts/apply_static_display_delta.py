"""Apply an audited text-component delta, guarded by Chinese and prior English.

Plan rows: key (asset:path-id), field (m_text/m_Text), source, old, new.
Only the listed display fields may change. Saves a hash report beside the plan.
"""
import argparse,json,gc,hashlib
from pathlib import Path
import UnityPy
from polish_android_ui import make_generator

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('original','candidate','plan','dlls'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();rows=json.loads(a.plan.read_text('utf8'))['hits'];keys={r['key'] for r in rows}
    for row in rows:assert row['field'] in ('m_text','m_Text') and row['old'] and row['new']
    before=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    for tag,path in [('original',a.original),('candidate',a.candidate)]:
        env=UnityPy.load(str(path));env.typetree_generator=make_generator('2022.3.62f1c1',a.dlls);found=set()
        for obj in env.objects:
            key=f'{obj.assets_file.name}:{obj.path_id}'
            if key not in keys:continue
            assert obj.type.name=='MonoBehaviour';tree=obj.read_typetree(check_read=False)
            for row in rows:
                if row['key']!=key:continue
                assert tree[row['field']]==row['source' if tag=='original' else 'old'],key+' guard failed'
                if tag=='candidate':tree[row['field']]=row['new']
            if tag=='candidate':obj.save_typetree(tree)
            found.add(key)
        assert found==keys
        if tag=='candidate':a.candidate.write_bytes(env.file.save(packer='lz4'))
        del env;gc.collect()
    report={'before':before,'after':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'changes':rows}
    a.plan.with_suffix('.applied.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(str(len(rows))+' guarded static display changes')
if __name__=='__main__':main()
