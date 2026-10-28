"""Finalize the audited Oct28 PC delta, three modifier fixes and compact metadata.

Run after port_pc_refresh_405 in a separate work directory. No native gameplay,
unlock state, saved data, music or artwork changes. Reports input/output hashes.
"""
import argparse,hashlib,json,zipfile,gc
from pathlib import Path
import UnityPy
from build_metadata_translation import parse_metadata,build_metadata
from compact_metadata_tail import compact_metadata_tail
from protected_metadata import verify_metadata
from prepare_runtime_payload import META,OFFICIAL_SHA

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--official',type=Path,required=True)
    a=ap.parse_args();w=a.work;r=Path(__file__).resolve().parents[1]
    if (w/'final-payload-report.json').exists():raise ValueError('Already finalized; use a fresh port snapshot')
    with a.official.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==OFFICIAL_SHA
    with zipfile.ZipFile(a.official) as z:official=z.read(META)
    source=(w/'metadata.dat').read_bytes();layout,current=parse_metadata(source);_,original=parse_metadata(official)
    strings=[row.raw for row in current];data=read(w/'english/translations.json');before=dict(data['exact'])
    fixtures=read(r/'runtime/tests/modifier-display-cases.json')
    for case in fixtures:
        i=case['index'];assert original[i].text==case['source'] and current[i].text==case['previous']
        strings[i]=case['english'].encode('utf8')
        for key in (case['source'],case['previous']):data['exact'][key]=case['english']
    # Complete styled description spans as well, without general substring rules.
    data['exact']['：攻击范围增加']=': Increased attack range'
    write(w/'english/translations.json',data)
    expanded=build_metadata(source,layout,strings);compact=compact_metadata_tail(expanded)
    _,verified=parse_metadata(compact);assert [row.raw for row in verified]==strings
    protected=verify_metadata(official,compact)
    (w/'metadata.dat').write_bytes(compact)
    assert set(before)<=set(data['exact']),'Lost a translation key'
    manifest=read(w/'english/manifest.json');manifest['revision']='4.0.5-pre3-performance2-oct28'
    manifest['pc_overlay_commit']=data['pc_overlay_commit']
    manifest['metadata_sha256']=sha(compact);manifest['files']['translations.json']=sha((w/'english/translations.json').read_bytes())
    assert not manifest.get('refresh_test_seed',False)
    output=w/'almanac-refresh';output.mkdir(exist_ok=True);env=UnityPy.load(str(w/'candidate.unity3d'));found=set()
    for obj in env.objects:
        if obj.type.name!='TextAsset':continue
        text=obj.read();filename=text.m_Name+'.json'
        if filename not in manifest['almanac_files']:continue
        payload=text.m_Script.encode('utf8') if isinstance(text.m_Script,str) else text.m_Script
        json.loads(payload);(output/filename).write_bytes(payload);manifest['almanac_files'][filename]=sha(payload);found.add(filename)
    assert found==set(manifest['almanac_files']);del env;gc.collect()
    write(w/'english/manifest.json',manifest)
    files={'assets/bin/Data/data.unity3d':w/'candidate.unity3d',META:w/'metadata.dat','assets/english/translations.json':w/'english/translations.json','assets/english/manifest.json':w/'english/manifest.json'}
    files.update({'assets/english-almanac/'+p.name:p for p in output.glob('*.json')})
    report={'metadata_before_bytes':len(source),'metadata_after_bytes':len(compact),'removed_bytes':len(source)-len(compact),'protected_metadata':protected,'modifier_fixes':fixtures,'all_prior_dictionary_keys_retained':True,'files':{k:{'path':str(p),'sha256':sha(p.read_bytes())} for k,p in files.items()}}
    write(w/'final-payload-report.json',report)
    print(json.dumps({'removed_metadata_bytes':report['removed_bytes'],'protected_slots':protected['verified_slots'],'modifier_fixes':len(fixtures),'payload_files':len(files)}))
if __name__=='__main__':main()
