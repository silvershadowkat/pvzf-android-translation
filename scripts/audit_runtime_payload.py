"""Independent, sequential object-level audit for the pinned pre3 payload."""
import argparse, collections, gc, hashlib, json, re, subprocess, zipfile
from pathlib import Path
import UnityPy

def inventory(path):
    env=UnityPy.load(str(path)); result={}; old_ids=[]; settings=[]
    for o in env.objects:
        raw=o.get_raw_data();key=(o.assets_file.name,o.path_id)
        assert key not in result
        result[key]=(o.type.name,hashlib.sha256(raw).hexdigest())
        if b'com.LanPiaoPiao.PlantsVsZombiesRH' in raw:old_ids.append([*key,o.type.name])
        if o.type.name=='PlayerSettings':settings.append(o.read_typetree())
    del env;gc.collect();return result,old_ids,settings

def main():
    p=argparse.ArgumentParser()
    for n in ('work','base','output','aapt'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--revision',type=int,default=1)
    a=p.parse_args();before,_,old_settings=inventory(a.work/'pre2.unity3d');after,old_ids,settings=inventory(a.work/'candidate.unity3d')
    assert before.keys()==after.keys(),'Object inventory changed'
    changed=[{'asset':k[0],'path_id':k[1],'type':after[k][0],'before':before[k][1],'after':after[k][1]} for k in after if before[k]!=after[k]]
    counts=collections.Counter(x['type'] for x in changed)
    assert counts=={'AudioClip':17,'PlayerSettings':1},counts
    assert not old_ids,old_ids
    assert len(settings)==1 and settings[0]['productName']=='PlantsVsZombiesEN'
    old_settings[0]['productName']='PlantsVsZombiesEN'
    assert old_settings==settings,'Unexpected PlayerSettings change'
    suffix='' if a.revision==1 else '-r'+str(a.revision)
    final=json.loads((a.output/('build-test1'+suffix+'.json')).read_text())
    def manifest(apk):
        return subprocess.run([str(a.aapt),'dump','xmltree',str(apk),'--file','AndroidManifest.xml'],capture_output=True,text=True,check=True,timeout=30).stdout
    original=manifest(a.base);current=manifest(final['apk'])
    def permissions(text):
        return re.findall(r'E: uses-permission[^\n]*\n\s*A: [^\n]*name[^\n]*',text)
    assert permissions(original)==permissions(current),'Permissions changed'
    assert 'sharedUserId' not in current
    assert current.count('"android.intent.action.MAIN" (Raw:')==1
    assert current.count('"android.intent.category.LAUNCHER" (Raw:')==1
    # Structured edits retain original Java namespaces. Only the application ID changes.
    with zipfile.ZipFile(final['apk']) as z:
        dex=z.read('classes.dex')
        assert b'com.LanPiaoPiao.PlantsVsZombiesRH' not in dex
        assert b'com.LanPiaoPiao.PlantsVsZombiesEN' in dex
        assert z.read('assets/bin/Data/Managed/Metadata/global-metadata.dat')==(a.work/'metadata.dat').read_bytes()
        native_identity=[]
        for name in z.namelist():
            if name.startswith('lib/') and name.endswith('.so'):
                data=z.read(name)
                if b'com.LanPiaoPiao.PlantsVsZombiesRH' in data or 'com.LanPiaoPiao.PlantsVsZombiesRH'.encode('utf-16le') in data:native_identity.append(name)
        assert not native_identity,native_identity
    result={'objects_compared':len(before),'changed_object_counts':dict(counts),'changed_objects':changed,'old_package_in_bundle_objects':old_ids,'old_package_in_native_libraries':native_identity,'permissions_unchanged':True,'single_launcher':True,'main_metadata_unchanged_from_pre2':True,'device_tested':False}
    (a.output/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='changed_objects'}))

if __name__=='__main__':main()
