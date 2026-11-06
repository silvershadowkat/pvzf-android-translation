"""Apply the exact, reviewed follow-up to the public 4.1 pre-release 2 payload.

Two almanac fields and two display literals only. Never change Plant Info's
parser protocol, gameplay identifiers, music assets, recipes or save data.
"""
import argparse,gc,hashlib,json,zipfile
from pathlib import Path
import UnityPy
from build_metadata_translation import parse_metadata,build_metadata
from compact_metadata_tail import compact_metadata_tail
from protected_metadata import verify_metadata
from migrate_version_text import same_arguments
from prepare_41_payload import META,write
from build_unity_ui_translation import read_tmp_text,replace_tmp_text

BUNDLE='assets/bin/Data/data.unity3d'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def reviewed_payload(metadata,lawn,dictionary,review,original):
    layout,literals=parse_metadata(metadata)
    data=[s.raw for s in literals]
    changes=[]
    for slot,claim in review['metadata'].items():
        i=int(slot);s=literals[i].text
        assert s==claim['source'] and sha(s.encode())==claim['source_sha256']
        assert same_arguments(s,claim['english'])
        data[i]=claim['english'].encode('utf8');changes.append(i)
    output=compact_metadata_tail(build_metadata(metadata,layout,data))
    protection=verify_metadata(original,output)
    assert [i for i,(a,b) in enumerate(zip(literals,parse_metadata(output)[1])) if a.text!=b.text]==sorted(changes)
    rows={r['seedType']:r for r in lawn['plants']}
    for ident,claim in review['plants'].items():
        row=rows[int(ident)]
        assert row['name']==claim['name']
        assert sha(row['info'].encode())==claim['previous_sha256']
        assert sha(claim['source'].encode())==claim['source_sha256']
        assert sha(claim['blooms_info'].encode())==claim['blooms_info_sha256']
        assert same_arguments(row['info'],claim['english'])
        dictionary['exact'][row['info']]=claim['english']
        row['info']=claim['english']
    dictionary['exact'].update(review['runtime_exact'])
    return output,lawn,dictionary,protection

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('released-apk','official','review','work'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
    review=json.loads(a.review.read_text(encoding='utf8'))
    assert file_sha(a.released_apk)==review['base_apk_sha256']
    assert file_sha(a.official)==review['official_sha256']
    with zipfile.ZipFile(a.released_apk) as z:
        metadata=z.read(META);base=z.read(BUNDLE)
        dictionary=json.loads(z.read('assets/english/translations.json'));old_keys=set(dictionary['exact'])
        refresh=a.work/'almanac-refresh';refresh.mkdir(exist_ok=True)
        for n in ('LawnStrings','ZombieStrings','DetailStrings'):
            (refresh/(n+'.json')).write_bytes(z.read('assets/english-almanac/'+n+'.json'))
    with zipfile.ZipFile(a.official) as z:original=z.read(META)
    old_lawn=json.loads((refresh/'LawnStrings.json').read_text(encoding='utf8'))
    metadata,lawn,dictionary,protection=reviewed_payload(metadata,old_lawn,dictionary,review,original)
    almanacs={'LawnStrings':lawn,'ZombieStrings':json.loads((refresh/'ZombieStrings.json').read_text(encoding='utf8'))}
    for claim in review.get('extra_fields',[]):
        root,key=('plants','seedType') if claim['asset']=='LawnStrings' else ('zombies','theZombieType')
        row=next(r for r in almanacs[claim['asset']][root] if r[key]==claim['id'])
        source=row[claim['field']]
        assert sha(source.encode())==claim['previous_sha256']==claim['source_sha256']
        assert source==claim['source'] and row['name']==claim['name']
        dictionary['exact'][source]=claim['english'];row[claim['field']]=claim['english']
    assert old_keys.issubset(dictionary['exact'])
    (a.work/'metadata.dat').write_bytes(metadata)
    write(a.work/'english/translations.json',dictionary)
    texts={name:json.dumps(data,ensure_ascii=False,separators=(',',':')) for name,data in almanacs.items()}
    for name,text in texts.items():(refresh/(name+'.json')).write_text(text,encoding='utf8')
    e=UnityPy.load(base);del base
    before={(o.assets_file.name,o.path_id):sha(o.get_raw_data()) for o in e.objects}
    allowed=[]
    for o in e.objects:
        announcement=review.get('announcement')
        if announcement and (o.assets_file.name,o.path_id)==(announcement['file'],announcement['id']):
            raw=o.get_raw_data();previous=read_tmp_text(raw)[0]
            assert sha(previous.encode())==announcement['previous_sha256']
            o.set_raw_data(replace_tmp_text(raw,announcement['english']));allowed.append((o.assets_file.name,o.path_id))
        if o.type.name!='TextAsset':continue
        t=o.read()
        if t.m_Name not in texts:continue
        embedded=json.loads(t.m_Script)
        root,key=('plants','seedType') if t.m_Name=='LawnStrings' else ('zombies','theZombieType')
        old={r[key]:r for r in embedded[root]}
        new={r[key]:r for r in almanacs[t.m_Name][root]}
        assert old.keys()==new.keys()
        for i,row in old.items():
            expected=dict(row)
            if t.m_Name=='LawnStrings' and str(i) in review['plants']:expected['info']=review['plants'][str(i)]['english']
            for claim in review.get('extra_fields',[]):
                if claim['asset']==t.m_Name and claim['id']==i:expected[claim['field']]=claim['english']
            assert expected==new[i],('Unreviewed almanac field',i)
        t.m_Script=texts[t.m_Name];t.save();allowed.append((o.assets_file.name,o.path_id))
    assert len(allowed)==2+bool(review.get('announcement'))
    bundle=a.work/'feedback.unity3d';bundle.write_bytes(e.file.save(packer='lz4'))
    del e;gc.collect()
    e=UnityPy.load(str(bundle));changed=[];count=0
    for o in e.objects:
        key=(o.assets_file.name,o.path_id);count+=1
        if sha(o.get_raw_data())!=before[key]:changed.append(key)
    assert count==len(before) and sorted(changed)==sorted(allowed)
    del e;gc.collect()
    report=dict(base_apk_sha256=review['base_apk_sha256'],pc_checked_commit=review['pc_checked_commit'],previous_keys_retained=True,protected_metadata=protection,metadata_slots=sorted(map(int,review['metadata'])),plant_ids=sorted(map(int,review['plants'])),objects_compared=count,changed_objects=changed,bundle_sha256=file_sha(bundle),metadata_sha256=sha(metadata),device_tested=False,published=False)
    write(a.work/'translation-report.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
