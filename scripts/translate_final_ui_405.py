"""Apply the reviewed 4.0.5 final UI audit only to the runtime display dictionary.

No serialized objects, metadata literals, saves, node IDs or lookup keys change.
Serialized source text is verified directly against the guarded bundle.
"""
import argparse, hashlib, json
from pathlib import Path
import UnityPy
from build_metadata_translation import parse_metadata

ROOT=Path(__file__).resolve().parents[1]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(p.read_text('utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True)
    w=ap.parse_args().work;area=w/'final-audit-r20'
    area.mkdir(parents=True,exist_ok=True)
    spec=read(ROOT/'assets/final-ui-audit-4.0.5.json')
    path=w/'english/translations.json';raw=path.read_bytes();data=json.loads(raw)
    report_path=area/'apply-report.json'
    if report_path.exists():
        report=read(report_path)
        assert sha(raw)==report['output_sha256']
        assert sha((ROOT/'assets/final-ui-audit-4.0.5.json').read_bytes())==report['manifest_sha256']
        assert all(data['exact'].get(x['source'])==x['english'] for x in spec['entries'] if x['kind']=='exact')
        assert all([x['pattern'],x['replacement']] in data['regex'] for x in spec['entries'] if x['kind']=='formatted')
        print('Verified final UI audit layer.');return
    previous=read(w/'level-intros-r19/apply-report.json')
    assert sha(raw)==previous['output_sha256']
    for name,expected in spec['input_sha256'].items():
        assert sha((w/name).read_bytes())==expected,name
    env=UnityPy.load(str(w/'candidate.unity3d'))
    serialized={o.path_id:o for o in env.objects if o.assets_file.name=='resources.assets'}
    text_assets={}
    for o in env.objects:
        if o.type.name=='TextAsset':
            d=o.read();text_assets[d.m_Name]=d.m_Script
    _,literals=parse_metadata((w/'metadata.dat').read_bytes())
    rules=[];exact=0
    for x in spec['entries']:
        if x['where'].startswith('metadata:'):
            assert literals[int(x['where'].split(':')[1])].text==x['source']
        elif x['where'].startswith('UI:'):
            obj=serialized[int(x['where'].split(':')[1])]
            assert x['source'].encode('utf8') in obj.get_raw_data()
        else:
            route=x['where'].removeprefix('TextAsset:').split('/')
            value=json.loads(text_assets[route[0]])
            for key in route[1:]:value=value[int(key)] if isinstance(value,list) else value[key]
            assert value==x['source']
        assert '\u2014' not in x['english']
        if x['kind']=='exact':
            assert x['source'] not in data['exact'],x['where']
            data['exact'][x['source']]=x['english'];exact+=1
        else:
            assert x['pattern'].startswith('^') and x['pattern'].endswith('$')
            assert not any(v[0]==x['pattern'] for v in data['regex'])
            rules.append([x['pattern'],x['replacement']])
    data['regex']=rules+data['regex']
    data['final_ui_audit_revision']=spec['revision']
    output=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    (area/'baseline-translations.json').write_bytes(raw)
    path.write_bytes(output)
    report={'input_sha256':sha(raw),'output_sha256':sha(output),'manifest_sha256':sha((ROOT/'assets/final-ui-audit-4.0.5.json').read_bytes()),'exact_entries':exact,'anchored_formatted_rules':len(rules),'unchanged':['bundle','metadata','save-refresh policy','internal keys and serialized graph data'],'scope':spec['method']}
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f'Added {exact} exact display mappings and {len(rules)} anchored formatted rules.')
if __name__=='__main__':main()
