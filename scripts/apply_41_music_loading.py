"""Match stock decompressed playback for the 44 added normalized music clips.

Original clips/payloads stay unchanged. Only added profile loading flags change;
background decoding avoids doing the new songs' decode work in the render loop.
"""
import argparse,gc,hashlib,json
from pathlib import Path
import UnityPy

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','output','music-report','report'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();music=json.loads(a.music_report.read_text(encoding='utf8'))
    expected={x['path_id']:x for x in music['tracks']}
    assert len(expected)==44
    env=UnityPy.load(str(a.base));before={(o.assets_file.name,o.path_id):sha(o.get_raw_data()) for o in env.objects}
    changed=[]
    for o in env.objects:
        if o.assets_file.name!='resources.assets' or o.path_id not in expected:continue
        assert o.type.name=='AudioClip'
        t=o.read_typetree();claim=expected[o.path_id]
        assert t['m_Name']==claim['name'] and t['m_LoadType']==2
        assert t['m_Frequency']==44100 and t['m_CompressionFormat']==1
        assert t['m_Resource']['m_Offset']==claim['resource_offset'] and t['m_Resource']['m_Size']==claim['resource_bytes']
        t['m_LoadType']=0
        t['m_LoadInBackground']=True
        t['m_PreloadAudioData']=False
        o.save_typetree(t);changed.append((o.assets_file.name,o.path_id))
    assert len(changed)==44
    a.output.write_bytes(env.file.save(packer='lz4'));del env;gc.collect()
    check=UnityPy.load(str(a.output));actual=[]
    for o in check.objects:
        key=(o.assets_file.name,o.path_id)
        if sha(o.get_raw_data())!=before[key]:
            actual.append(key);t=o.read_typetree()
            assert t['m_LoadType']==0 and t['m_LoadInBackground'] and not t['m_PreloadAudioData']
    assert sorted(actual)==sorted(changed)
    report={'base_sha256':sha(a.base.read_bytes()),'output_sha256':sha(a.output.read_bytes()),
            'changed_added_profile_clips':changed,'all_other_objects_unchanged':True,
            'load_type':'DecompressOnLoad','load_in_background':True,'preload_audio_data':False,
            'original_audio_payloads_unchanged':True}
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    identity_path=a.output.parent/'identity-report.json';identity=json.loads(identity_path.read_text())
    assert identity['sha256']==report['base_sha256']
    identity.update(sha256=report['output_sha256'],post_identity_audio_review=report)
    identity_path.write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    music.update(added_music_clips=music.pop('added_streaming_clips',44),load_type='DecompressOnLoad',loading_review=report)
    a.music_report.write_text(json.dumps(music,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Verified decompressed playback on 44 added profiles; other objects and audio payloads unchanged',flush=True)

if __name__=='__main__':main()
