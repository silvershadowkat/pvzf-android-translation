"""Apply source-guarded display edits while preserving resource and gameplay keys."""
import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from build_metadata_translation import parse_metadata, build_metadata
from migrate_version_text import is_display_asset_field, same_arguments, set_field, text_records
from polish_android_ui import make_generator, object_map
from protected_metadata import PROTECTED_METADATA_STRINGS, verify_metadata
from repair_android40_catalog import validate_catalog


def value_at(tree, path):
    for key in path:
        tree = tree[key]
    return tree


def guarded_text(source, before, rule):
    if source != rule['source'] or before != rule['before']:
        raise ValueError('Source or previous translation changed; review required')
    target = rule['target']
    if not isinstance(target, str) or not target.strip():
        raise ValueError('Display text cannot be empty')
    if not same_arguments(source, target):
        raise ValueError('Format arguments changed')
    import re
    if sorted(re.findall(r'\[\[[^\]]+\]\]', source)) != sorted(re.findall(r'\[\[[^\]]+\]\]', target)):
        raise ValueError('Plant or game tokens changed')
    if '\u2014' in target:
        raise ValueError('Em dash is not allowed in reviewed output')
    return target


def metadata_target(source, before, rule):
    if source in PROTECTED_METADATA_STRINGS:
        raise ValueError('Protected runtime metadata cannot be a display patch target')
    return guarded_text(source, before, rule)


def patch_asset(source, current, asset, rule):
    path = rule['path']
    if not is_display_asset_field(asset, path):
        raise ValueError('Field is not approved display prose')
    target = guarded_text(value_at(source, path), value_at(current, path), rule)
    set_field(current, path, target)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('official', 'source', 'official-metadata', 'metadata', 'rules',
                'dlls', 'dump', 'output', 'output-metadata', 'report'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    rules = json.loads(a.rules.read_text(encoding='utf8'))
    original_bytes = a.official_metadata.read_bytes()
    source_literals = parse_metadata(original_bytes)[1]
    raw = a.metadata.read_bytes()
    layout, literals = parse_metadata(raw)
    verify_metadata(original_bytes, raw)
    output = [s.raw for s in literals]
    seen = set()
    for rule in rules['metadata']:
        i = rule['index']
        assert i not in seen, 'Duplicate metadata target'
        seen.add(i)
        output[i] = metadata_target(source_literals[i].text, literals[i].text, rule).encode('utf8')
    meta = build_metadata(raw, layout, output)
    verify_metadata(original_bytes, meta)
    assert [s.raw for s in parse_metadata(meta)[1]] == output
    original_assets = text_records(a.official)
    original_env = UnityPy.load(str(a.official))
    original_env.typetree_generator = make_generator('2022.3.62f1c1', a.dlls)
    source_objects = object_map(original_env)
    env = UnityPy.load(str(a.source))
    env.typetree_generator = original_env.typetree_generator
    objects = object_map(env)
    expected = {k: hashlib.sha256(o.get_raw_data()).hexdigest() for k, o in objects.items()}
    applied = []
    by_asset = {}
    for rule in rules['assets']:
        by_asset.setdefault(rule['asset'], []).append(rule)
    asset_seen = set()
    for key, obj in objects.items():
        if obj.type.name != 'TextAsset':
            continue
        asset = obj.read()
        if asset.m_Name not in by_asset:
            continue
        name = asset.m_Name
        assert name not in asset_seen, 'Ambiguous asset name'
        asset_seen.add(name)
        current = json.loads(asset.m_Script)
        seen = set()
        for rule in by_asset[name]:
            path = tuple(rule['path'])
            assert path not in seen, 'Duplicate asset target'
            seen.add(path)
            patch_asset(original_assets[name], current, name, rule)
            applied.append({'asset': name, 'path': list(path)})
        if name == 'ShootingAlmanacIndex':
            validate_catalog(original_assets[name], current, a.dump.read_text(encoding='utf8'))
        asset.m_Script = json.dumps(current, ensure_ascii=False, indent=4)
        asset.save()
        expected[key] = hashlib.sha256(obj.data).hexdigest()
    assert asset_seen == by_asset.keys(), 'Asset target missing'
    seen = set()
    for rule in rules['ui']:
        key = rule['file'], rule['id']
        path = rule['field']
        assert path in (['m_text'], ['m_Text']), 'Only serialized display text can change'
        assert key not in seen, 'Duplicate UI target'
        seen.add(key)
        obj = objects[key]
        assert obj.type.name == 'MonoBehaviour'
        tree = obj.read_typetree(check_read=True)
        assert obj.save_typetree(tree) == obj.get_raw_data(), 'Lossy UI roundtrip'
        source = value_at(source_objects[key].read_typetree(check_read=True), path)
        set_field(tree, path, guarded_text(source, value_at(tree, path), rule))
        obj.save_typetree(tree)
        expected[key] = hashlib.sha256(obj.data).hexdigest()
        applied.append({'file': key[0], 'id': key[1], 'field': path})
    a.output_metadata.write_bytes(meta)
    a.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, source_objects, original_env, env
    gc.collect()
    check = object_map(UnityPy.load(str(a.output)))
    assert check.keys() == expected.keys()
    for key, obj in check.items():
        assert hashlib.sha256(obj.get_raw_data()).hexdigest() == expected[key], key
    report = {'metadata_edits': len(rules['metadata']), 'asset_edits': len(rules['assets']),
              'ui_edits': len(rules['ui']), 'verified_objects': len(check),
              'protected_metadata': verify_metadata(original_bytes, meta), 'applied': applied}
    a.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k != 'applied'}))


if __name__ == '__main__':
    main()
