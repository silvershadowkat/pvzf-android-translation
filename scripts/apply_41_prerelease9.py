"""Apply reviewed display-only corrections to immutable 4.1 pre8 payloads."""
import argparse, collections, gc, json, zipfile
from pathlib import Path
import UnityPy
from apply_41_prerelease4 import BUNDLE, META, sha, file_sha, write
from build_metadata_translation import parse_metadata, build_metadata
from compact_metadata_tail import compact_metadata_tail
from protected_metadata import verify_metadata
from migrate_version_text import same_arguments, is_display_asset_field


def replace_guarded(source, previous, row):
    assert source == row['source'] and sha(source.encode()) == row['source_sha256'], 'Official source changed'
    assert previous == row['previous'], 'Translated source changed'
    assert same_arguments(source, row['english']), 'Format arguments changed'
    return row['english']


def at(root, path):
    for key in path:
        root = root[key]
    return root


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('base', 'official', 'review', 'work'):
        p.add_argument('--' + n, type=Path, required=True)
    p.add_argument('--variant', choices=('en', 'ai'), required=True)
    a = p.parse_args(); a.work.mkdir(parents=True, exist_ok=True)
    review = json.loads(a.review.read_text('utf8'))
    assert file_sha(a.base) == review['base_' + a.variant + '_sha256']
    assert file_sha(a.official) == review['official_sha256']
    with zipfile.ZipFile(a.base) as z:
        rawmeta = z.read(META); bundle = z.read(BUNDLE)
        dictionary = json.loads(z.read('assets/english/translations.json'))
        almanacs = {n: json.loads(z.read('assets/english-almanac/' + n + '.json')) for n in ('LawnStrings', 'ZombieStrings', 'DetailStrings')}
    with zipfile.ZipFile(a.official) as z:
        original_meta = z.read(META); original_bundle = z.read(BUNDLE)
    original_literals = parse_metadata(original_meta)[1]
    layout, literals = parse_metadata(rawmeta); data = [s.raw for s in literals]
    for row in review['metadata']:
        i = row['index']
        data[i] = replace_guarded(original_literals[i].text, literals[i].text, row).encode()
    metadata = compact_metadata_tail(build_metadata(rawmeta, layout, data))
    assert metadata == rawmeta, 'This revision must not change metadata'
    protection = verify_metadata(original_meta, metadata)
    changed = [i for i, (old, new) in enumerate(zip(literals, parse_metadata(metadata)[1])) if old.raw != new.raw]
    assert sorted(changed) == sorted(r['index'] for r in review['metadata'])
    (a.work / 'metadata.dat').write_bytes(metadata)
    requests = collections.defaultdict(list)
    for row in review['fields']:
        group, key = ('plants', 'seedType') if row['asset'] == 'LawnStrings' else ('zombies', 'theZombieType')
        matches = [i for i, r in enumerate(almanacs[row['asset']][group]) if r[key] == row['id']]
        assert len(matches) == 1
        requests[row['asset']].append({**row, 'path': [group, matches[0], row['field']]})
    for row in review['text_assets']:
        requests[row['asset']].append(row)
    original = UnityPy.load(original_bundle); source_assets = {}
    for obj in original.objects:
        if obj.type.name == 'TextAsset':
            t = obj.read()
            if t.m_Name in requests:
                assert t.m_Name not in source_assets
                source_assets[t.m_Name] = json.loads(t.m_Script)
    del original, original_bundle; gc.collect()
    env = UnityPy.load(bundle); del bundle
    before = {(o.assets_file.name, o.path_id): sha(o.get_raw_data()) for o in env.objects}
    allowed = []; found = set()
    for obj in env.objects:
        if obj.type.name != 'TextAsset': continue
        t = obj.read()
        if t.m_Name not in requests: continue
        assert t.m_Name not in found; found.add(t.m_Name)
        root = json.loads(t.m_Script)
        if t.m_Name in almanacs: assert root == almanacs[t.m_Name], 'Managed and embedded almanacs diverged'
        for row in requests[t.m_Name]:
            path = row['path']; assert is_display_asset_field(t.m_Name, path)
            if 'entry_id' in row:
                assert root['entries'][path[1]]['id'] == row['entry_id']
                assert source_assets[t.m_Name]['entries'][path[1]]['id'] == row['entry_id']
            value = replace_guarded(at(source_assets[t.m_Name], path), at(root, path), row)
            at(root, path[:-1])[path[-1]] = value
        if t.m_Name in almanacs: almanacs[t.m_Name] = root
        t.m_Script = json.dumps(root, ensure_ascii=False, indent=2) + '\n'; t.save()
        allowed.append((obj.assets_file.name, obj.path_id))
    assert found == set(requests)
    target = a.work / 'data.unity3d'; target.write_bytes(env.file.save(packer='lz4'))
    del env; gc.collect()
    env = UnityPy.load(str(target))
    after = {(o.assets_file.name, o.path_id): sha(o.get_raw_data()) for o in env.objects}
    assert before.keys() == after.keys()
    delta = [k for k in before if before[k] != after[k]]
    assert sorted(delta) == sorted(allowed), 'Unexpected Unity object mutation'
    del env; gc.collect()
    old_keys = set(dictionary['exact']); dictionary['exact'].update(review['runtime_exact'])
    assert old_keys <= dictionary['exact'].keys()
    # Reviewed, anchored currency/speed labels only; old rules and aliases remain.
    patterns={row[0] for row in dictionary['regex']}
    new_rules=[]
    for pattern,replacement in review['runtime_regex']:
        assert pattern.startswith('^') and pattern.endswith('$')
        import re
        assert re.compile(pattern).groups == len(re.findall(r'\{\d+\}',replacement))
        if pattern not in patterns: new_rules.append([pattern,replacement]); patterns.add(pattern)
    dictionary['regex']=new_rules+dictionary['regex']
    dictionary.update(pc_commit=review['blooms']['commit'], pc_overlay_commit=review['blooms']['commit'])
    write(a.work / 'translations.json', dictionary)
    for name, root in almanacs.items(): write(a.work / (name + '.json'), root)
    write(a.work / 'translation-report.json', dict(base_sha256=file_sha(a.base), variant=a.variant, counts=review['counts'], blooms_commit=review['blooms']['commit'],
          protected_metadata=protection, metadata_slots=changed, objects_compared=len(before), changed_objects=delta,
          bundle_sha256=file_sha(target), metadata_sha256=sha(metadata), all_other_unity_objects_identical=True,
          gameplay_data_unchanged=True, prior_dictionary_keys_retained=True))
    print('Payload verified:', len(review['fields']), 'almanac fields;', len(changed), 'literals;', len(before), 'Unity objects compared', flush=True)


if __name__ == '__main__': main()
