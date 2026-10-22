"""Apply approved 4.0.5 diary/credits art after r19; verify only two textures change."""
import argparse,gc,hashlib,json,shutil
from pathlib import Path
import UnityPy
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='dddee2076345c6d0d7e16c3ea22df26bfed1da231f6deb79e284585b8551d4c3'
SPECS={432:('剧情文本',(2048,2048),'storybook-4.0.5-english.png'),2307:('thanks',(1400,600),'credits-parchment-4.0.5-english.png')}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def raw_inventory(env):return {(o.assets_file.name,o.path_id):hashlib.sha256(o.get_raw_data()).hexdigest() for o in env.objects}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True,type=Path);w=ap.parse_args().work
    area=w/'art-r20';area.mkdir(exist_ok=True);target=w/'candidate.unity3d';report=area/'apply-report.json'
    if report.exists():
        r=json.loads(report.read_text());assert sha(target)==r['output_sha256']
        assert all(sha(ROOT/'assets'/n)==h for n,h in r['artwork_sha256'].items())
        print('Existing parchment patch verified.');return
    assert sha(target)==BASE,'Apply only after the reviewed r19 bundle'
    baseline=area/'baseline.unity3d'
    if baseline.exists():assert sha(baseline)==BASE
    else:shutil.copyfile(target,baseline)
    print('Loading baseline and recording object hashes',flush=True)
    env=UnityPy.load(str(baseline));before=raw_inventory(env);facts=[]
    for o in env.objects:
        if o.assets_file.name!='resources.assets' or o.path_id not in SPECS:continue
        assert o.type.name=='Texture2D';name,size,asset=SPECS[o.path_id];d=o.read()
        assert d.m_Name==name and (d.m_Width,d.m_Height)==size
        im=Image.open(ROOT/'assets'/asset).convert('RGBA');assert im.size==size
        old_format=d.m_TextureFormat;mips=d.m_MipCount or 1
        print('Encoding texture '+str(o.path_id),flush=True)
        d.set_image(im,target_format=old_format,mipmap_count=mips);o.save_typetree(d)
        assert d.m_TextureFormat==old_format and not d.m_StreamData.path
        facts.append({'path_id':o.path_id,'name':name,'dimensions':size,'format':old_format,'mips':d.m_MipCount})
    assert len(facts)==2
    print('Saving and reopening bundle',flush=True)
    candidate=area/'candidate.unity3d';candidate.write_bytes(env.file.save(packer='lz4'))
    del env;gc.collect();env=UnityPy.load(str(candidate));after=raw_inventory(env)
    assert before.keys()==after.keys()
    changed=sorted(k for k in before if before[k]!=after[k]);assert changed==[('resources.assets',432),('resources.assets',2307)],changed
    for o in env.objects:
        if (o.assets_file.name,o.path_id) not in changed:continue
        name,size,asset=SPECS[o.path_id];d=o.read();assert d.m_Name==name and (d.m_Width,d.m_Height)==size
        assert not d.m_StreamData.path and d.image.size==size
        d.image.save(area/('reopened-'+asset))
    del env;gc.collect();shutil.copyfile(candidate,target)
    r={'input_sha256':BASE,'output_sha256':sha(target),'artwork_sha256':{s[2]:sha(ROOT/'assets'/s[2]) for s in SPECS.values()},'serialized_objects_checked':len(before),'changed_objects':changed,'textures':facts,'unchanged':['all Sprite UV rectangles and meshes','all other serialized objects','external resource stream contents','metadata','save refresh policy']}
    report.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf8');print(json.dumps({'objects_checked':len(before),'changed_objects':changed}))
if __name__=='__main__':main()
