"""Apply a source-guarded display review to immutable public 4.1 pre3 APKs."""
import argparse,collections,gc,hashlib,json,re,zipfile
from pathlib import Path
import UnityPy
from build_metadata_translation import parse_metadata,build_metadata
from compact_metadata_tail import compact_metadata_tail
from protected_metadata import verify_metadata
from migrate_version_text import same_arguments
BUNDLE='assets/bin/Data/data.unity3d';META='assets/bin/Data/Managed/Metadata/global-metadata.dat'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('base','official','review','work'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--variant',choices=['en','ai'],required=True);a=ap.parse_args();a.work.mkdir(parents=True,exist_ok=True)
    review=json.loads(a.review.read_text('utf8'));assert file_sha(a.base)==review['base_'+a.variant+'_sha256']
    assert file_sha(a.official)=='6272551fd2573bd3e342acf1a214aa0ee6d44833260babe600e27301ef9a6390'
    with zipfile.ZipFile(a.base) as z:
        dictionary=json.loads(z.read('assets/english/translations.json'));old_exact=dict(dictionary['exact'])
        almanacs={name:json.loads(z.read('assets/english-almanac/'+name+'.json')) for name in ('LawnStrings','ZombieStrings')}
        rawmeta=z.read(META);bundle_bytes=z.read(BUNDLE)
        ai_catalog=json.loads(z.read('assets/plantbrush/catalog.json')) if a.variant=='ai' else None
        ai_manifest=json.loads(z.read('assets/plantbrush/manifest.json')) if a.variant=='ai' else None
    with zipfile.ZipFile(a.official) as z:original=z.read(META)
    orig=parse_metadata(original)[1];layout,literals=parse_metadata(rawmeta);data=[s.raw for s in literals]
    for slot,row in review['metadata'].items():
        i=int(slot);assert orig[i].text==row['source'] and literals[i].text==row['previous'];assert same_arguments(row['source'],row['english'])
        data[i]=row['english'].encode('utf8')
    metadata=compact_metadata_tail(build_metadata(rawmeta,layout,data));protection=verify_metadata(original,metadata)
    changed=[i for i,(old,new) in enumerate(zip(literals,parse_metadata(metadata)[1])) if old.text!=new.text]
    assert sorted(changed)==sorted(map(int,review['metadata']))
    rows={name:{r['seedType' if name=='LawnStrings' else 'theZombieType']:r for r in root['plants' if name=='LawnStrings' else 'zombies']} for name,root in almanacs.items()}
    for c in review['fields']:
        row=rows[c['asset']][c['id']];assert row[c['field']]==c['previous'];assert same_arguments(c['previous'],c['english'])
        row[c['field']]=c['english']
    dictionary['exact'].update(review['runtime_exact'])
    assert old_exact.keys()<=dictionary['exact'].keys()
    # Exact prior rules retain priority; five complete-match display rules add
    # only equipment wording, never a generic replacement rule.
    existing={r[0] for r in dictionary['regex']}
    dictionary['regex'] += [r for r in review['runtime_regex'] if r[0] not in existing]
    dictionary['recipe_names']=sorted(set(dictionary.get('recipe_names',[]))|{r['english'] for r in review['fields'] if r['asset']=='LawnStrings' and r['field']=='name'})
    dictionary['pc_commit']=review['blooms']['commit'];dictionary['pc_overlay_commit']=review['blooms']['commit']
    write(a.work/'translations.json',dictionary);(a.work/'metadata.dat').write_bytes(metadata)
    for name,root in almanacs.items():write(a.work/(name+'.json'),root)
    catalog_changes=0
    if ai_catalog is not None:
        translated={r['id']:re.sub('<[^>]*>','',r['english']) for r in review['fields'] if r['asset']=='LawnStrings' and r['field']=='name'}
        for row in ai_catalog:
            name=translated.get(row['plantType'])
            if name and row['displayName']!=name:row['displayName']=name;catalog_changes+=1
        write(a.work/'catalog.json',ai_catalog);ai_manifest['files']['catalog.json']=file_sha(a.work/'catalog.json');write(a.work/'plantbrush-manifest.json',ai_manifest)
    e=UnityPy.load(bundle_bytes);del bundle_bytes
    before={(o.assets_file.name,o.path_id):sha(o.get_raw_data()) for o in e.objects};allowed=[]
    for o in e.objects:
        if o.type.name!='TextAsset':continue
        t=o.read()
        if t.m_Name not in almanacs:continue
        root=json.loads(t.m_Script);key='seedType' if t.m_Name=='LawnStrings' else 'theZombieType';group='plants' if key=='seedType' else 'zombies'
        original_rows={r[key]:r for r in root[group]};new_rows=rows[t.m_Name]
        assert original_rows.keys()==new_rows.keys()
        for i,old in original_rows.items():
            expected=dict(old)
            for c in review['fields']:
                if c['asset']==t.m_Name and c['id']==i:assert expected[c['field']]==c['previous'];expected[c['field']]=c['english']
            assert expected==new_rows[i]
        t.m_Script=json.dumps(almanacs[t.m_Name],ensure_ascii=False,indent=2)+'\n';t.save();allowed.append((o.assets_file.name,o.path_id))
    assert len(allowed)==2
    bundle=a.work/'data.unity3d';bundle.write_bytes(e.file.save(packer='lz4'));del e;gc.collect()
    e=UnityPy.load(str(bundle));delta=[(o.assets_file.name,o.path_id) for o in e.objects if sha(o.get_raw_data())!=before[(o.assets_file.name,o.path_id)]]
    assert len(e.objects)==len(before) and sorted(delta)==sorted(allowed);del e;gc.collect()
    write(a.work/'translation-report.json',dict(base_sha256=file_sha(a.base),variant=a.variant,blooms_commit=review['blooms']['commit'],counts=review['counts'],protected_metadata=protection,metadata_slots=changed,objects_compared=len(before),changed_objects=delta,bundle_sha256=file_sha(bundle),metadata_sha256=sha(metadata),prior_dictionary_keys_retained=True,offline_catalog_names_updated=catalog_changes,device_tested=False,published=False))
    print(a.variant,'payload verified;',len(review['fields']),'almanac fields,',len(changed),'display literals;',len(before),'objects compared',flush=True)
if __name__=='__main__':main()
