"""Append normalized decompressed-playback music profiles without rewriting original clips.

Uses the installed Unity FSBTool command-line encoder directly. AudioClips retain the game's serialized
schema and use its own ResourceManager and native playback implementation.
"""
import argparse, copy, gc, hashlib, json, subprocess, wave
from pathlib import Path
import UnityPy


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('base-bundle', 'base-resource', 'normalization', 'encoder', 'output', 'output-resource', 'work', 'report'):
        ap.add_argument('--' + key, type=Path, required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    banks = a.work / 'fsb'
    banks.mkdir(exist_ok=True)
    cache = a.work / 'fsb-cache'
    cache.mkdir(exist_ok=True)
    normalization = json.loads(a.normalization.read_text(encoding='utf8'))
    tracks = normalization['tracks']
    names = set()
    facts = []
    for track in tracks:
        key = track['profile'] + '__' + track['name']
        if key in names or track['profile'] not in ('original', 'blooms'):
            raise ValueError('Duplicate or unknown profile: ' + key)
        names.add(key)
        wav = a.normalization.parent / track['output']
        assert sha(wav) == track['output_sha256'], 'Normalization input changed'
        with wave.open(str(wav), 'rb') as w:
            channels, rate, frames, width = w.getnchannels(), w.getframerate(), w.getnframes(), w.getsampwidth()
        assert (channels, rate, width) == (2, 44100, 2)
        bank = banks / (key + '.fsb')
        receipt = banks / (key + '.json')
        stamp = {'input_sha256': sha(wav), 'encoder_sha256': sha(a.encoder), 'quality': 80, 'rate': rate}
        if not (bank.exists() and receipt.exists() and json.loads(receipt.read_text()) == {**stamp, 'output_sha256': sha(bank)}):
            subprocess.run([str(a.encoder), '-i', str(wav), '-o', str(bank), '-l', str(a.encoder.parent),
                            '-h', str(cache), '-c', 'vorbis', '-C', 'fsb', '-q', '80', '-s', str(rate), '-R'],
                           check=True, timeout=180)
            assert bank.read_bytes().startswith(b'FSB5')
            receipt.write_text(json.dumps({**stamp, 'output_sha256': sha(bank)}, indent=2), encoding='utf8')
        facts.append({**track, 'bank': str(bank), 'bank_sha256': sha(bank), 'frames': frames, 'rate': rate, 'channels': channels})
        print('Encoded streaming music:', key, flush=True)
    by_key = {(r['profile'], r['name']): r for r in facts}
    stem_lengths = []
    for (profile, name), row in by_key.items():
        if name.endswith('_drum') and (profile, name[:-5]) in by_key:
            base = by_key[(profile, name[:-5])]
            # Some official and PC stems intentionally have different source
            # lengths. Record these rather than silently trimming or padding
            # their arrangements to satisfy an assumed equality.
            stem_lengths.append({'profile': profile, 'name': name,
                                 'base_frames': base['frames'], 'drum_frames': row['frames'],
                                 'delta_seconds': (row['frames']-base['frames'])/row['rate']})
    env = UnityPy.load(str(a.base_bundle))
    resources = next(o.assets_file for o in env.objects if o.assets_file.name == 'resources.assets')
    managers = [o for o in env.objects if o.type.name == 'ResourceManager']
    assert len(managers) == 1
    manager = managers[0]
    manager_tree = manager.read_typetree()
    container = manager_tree['m_Container']
    assert isinstance(container, list)
    assert not any(path.startswith('englishmusic/') for path, _ in container), 'Never patch an already-profiled bundle'
    sources = {}
    for path, ptr in container:
        if path.startswith('audio/music/'):
            obj = resources.objects.get(ptr['m_PathID'])
            if obj and obj.type.name == 'AudioClip':
                tree = obj.read_typetree()
                sources[tree['m_Name']] = (obj, tree, ptr['m_FileID'])
    before = {(o.assets_file.name, o.path_id): hashlib.sha256(o.get_raw_data()).hexdigest() for o in env.objects}
    next_id = max(resources.objects) + 1
    a.output_resource.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copyfile(a.base_resource, a.output_resource)
    with a.output_resource.open('ab') as out:
        for row in facts:
            source, original, file_id = sources[row['name']]
            tree = copy.deepcopy(original)
            data = Path(row['bank']).read_bytes()
            out.write(b'\0' * (-out.tell() % 16))
            offset = out.tell()
            out.write(data)
            tree.update(m_LoadType=0, m_PreloadAudioData=False, m_LoadInBackground=True,
                        m_Channels=row['channels'], m_Frequency=row['rate'], m_BitsPerSample=16,
                        m_Length=row['frames']/row['rate'], m_SubsoundIndex=0, m_CompressionFormat=1,
                        m_Resource={'m_Source': a.output_resource.name, 'm_Offset': offset, 'm_Size': len(data)})
            clone = copy.copy(source)
            clone.path_id = next_id
            next_id += 1
            clone.save_typetree(tree)
            resources.objects[clone.path_id] = clone
            path = 'englishmusic/' + row['profile'] + '/' + row['name'].lower()
            container.append((path, {'m_FileID': file_id, 'm_PathID': clone.path_id}))
            row.update(resource_path=path, path_id=clone.path_id, resource_offset=offset, resource_bytes=len(data))
    manager.save_typetree(manager_tree)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(env.file.save(packer='lz4'))
    del env
    gc.collect()
    env = UnityPy.load(str(a.output))
    changed, added = [], []
    expected = {r['path_id']: r for r in facts}
    for o in env.objects:
        key = (o.assets_file.name, o.path_id)
        if key not in before:
            assert o.assets_file.name == 'resources.assets' and o.path_id in expected and o.type.name == 'AudioClip'
            t = o.read_typetree()
            row = expected[o.path_id]
            assert t['m_Name'] == row['name'] and t['m_LoadType'] == 0 and t['m_LoadInBackground'] and not t['m_PreloadAudioData']
            r = t['m_Resource']
            with a.output_resource.open('rb') as f:
                f.seek(r['m_Offset'])
                assert hashlib.sha256(f.read(r['m_Size'])).hexdigest() == row['bank_sha256']
            added.append(key)
        elif hashlib.sha256(o.get_raw_data()).hexdigest() != before[key]:
            assert o.type.name == 'ResourceManager', 'Unexpected original object change: ' + str(key)
            changed.append(key)
    assert len(added) == len(facts) and len(changed) == 1
    with a.base_resource.open('rb') as old, a.output_resource.open('rb') as new:
        while block := old.read(8*1024*1024):
            assert new.read(len(block)) == block, 'Original audio payload changed'
    report = {'base_sha256': sha(a.base_bundle), 'output_sha256': sha(a.output),
              'resource_sha256': sha(a.output_resource), 'original_objects_compared': len(before),
              'changed_original_objects': changed, 'added_music_clips': len(added), 'load_type': 'DecompressOnLoad', 'tracks': facts,
              'source_stem_lengths_preserved': stem_lengths,
              'all_original_audio_objects_and_payloads_unchanged': True}
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('Verified', len(added), 'music clips; only ResourceManager changed among original objects', flush=True)


if __name__ == '__main__':
    main()
