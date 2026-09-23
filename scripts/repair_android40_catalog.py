"""Restore protected catalog strings and apply reviewed, source-gated facts."""
import argparse
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy
from build_unity_text_translation import ALMANAC_SCHEMAS
from migrate_version_text import is_display_asset_field, same_arguments, text_records
from polish_android_ui import object_map


def restore_protected(source, current, asset, path=(), changes=None):
    changes = changes if changes is not None else []
    assert type(source) is type(current), (asset, path)
    if isinstance(source, dict):
        assert source.keys() == current.keys(), (asset, path)
        return {k: restore_protected(v, current[k], asset, path + (k,), changes)
                for k, v in source.items()}
    if isinstance(source, list):
        assert len(source) == len(current), (asset, path)
        return [restore_protected(v, current[i], asset, path + (i,), changes)
                for i, v in enumerate(source)]
    if not isinstance(source, str):
        assert source == current, (asset, path)
    elif source != current and not is_display_asset_field(asset, path):
        changes.append({'asset': asset, 'field': list(path), 'source': source, 'previous': current})
        return source
    return current


def apply_fact(source, current, rule):
    digest = hashlib.sha256(source.encode()).hexdigest()
    if digest != rule['source_sha256']:
        return current, 'source_changed_review_required'
    if current == rule['after']:
        return current, 'already_corrected'
    if current != rule['before']:
        return current, 'english_changed_review_required'
    assert same_arguments(source, rule['after'])
    return rule['after'], 'corrected'


def catalog_types(catalog):
    for plant in catalog['plants']:
        yield plant['configType']
        for buff in plant['buffs']:
            yield buff['type']


def known_types(dump):
    namespace = ''
    records = []
    for line in dump.splitlines():
        if line.startswith('// Namespace: '):
            namespace = line[len('// Namespace: '):].strip()
        match = re.search(r'\bclass ([\w.<>]+)', line)
        if match:
            records.append((namespace, match[1]))
    result = set()
    for index, (namespace, name) in enumerate(records):
        if not namespace and '.' in name:
            # Il2CppDumper emits an empty namespace for nested types and
            # lists them before their enclosing type, which owns the namespace.
            owner = name.split('.', 1)[0]
            enclosing = next((ns for ns, cls in records[index + 1:] if cls == owner), None)
            if enclosing is not None:
                namespace = enclosing
        result.add((namespace + '.' if namespace else '') + name.replace('.', '+'))
    return result


def validate_catalog(source, current, dump):
    changes = []
    restored = restore_protected(source, current, 'ShootingAlmanacIndex', changes=changes)
    assert not changes and restored == current, 'Catalog contains changed runtime strings'
    references = list(catalog_types(current))
    missing = sorted(set(references) - known_types(dump))
    assert not missing, missing
    return {'reflection_references': len(references), 'unique_reflection_types': len(set(references)),
            'roots': len(current['roots']), 'plants': len(current['plants']),
            'entries': len(current['entries']), 'all_runtime_fields_preserved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('official', 'source', 'rules', 'dump', 'output', 'report'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    original = text_records(args.official)
    rules = json.loads(args.rules.read_text(encoding='utf8'))['corrections']
    env = UnityPy.load(str(args.source))
    objects = object_map(env)
    expected = {key: hashlib.sha256(obj.get_raw_data()).hexdigest() for key, obj in objects.items()}
    restorations, corrections, changed_assets = [], [], []
    catalog_report = None
    for key, obj in objects.items():
        if obj.type.name != 'TextAsset':
            continue
        data = obj.read()
        name = data.m_Name
        before = data.m_Script
        try:
            current = json.loads(before.lstrip('\ufeff'))
        except ValueError:
            current = before
        source = original[name]
        # Almanac prose and DetailStrings have their own ID/field-based import.
        # Every other asset must obey the protected-string schema.
        if name not in ALMANAC_SCHEMAS and name != 'DetailStrings':
            current = restore_protected(source, current, name, changes=restorations)
        for rule in rules:
            if rule['asset'] != name:
                continue
            list_key, id_key = ALMANAC_SCHEMAS[name]
            source_rows = [x for x in source[list_key] if x[id_key] == rule['id']]
            target_rows = [x for x in current[list_key] if x[id_key] == rule['id']]
            assert len(source_rows) == len(target_rows) == 1
            row = target_rows[0]
            target, status = apply_fact(source_rows[0][rule['field']], row[rule['field']], rule)
            row[rule['field']] = target
            corrections.append({'id': rule['id'], 'name': rule['name'], 'field': rule['field'], 'status': status})
        if name == 'ShootingAlmanacIndex':
            catalog_report = validate_catalog(source, current, args.dump.read_text(encoding='utf8'))
        original_current = json.loads(before.lstrip('\ufeff')) if not isinstance(current, str) else before
        if current != original_current:
            data.m_Script = current if isinstance(current, str) else json.dumps(current, ensure_ascii=False, indent=4)
            data.save()
            expected[key] = hashlib.sha256(obj.data).hexdigest()
            changed_assets.append(name)
    assert catalog_report is not None
    assert len(corrections) == len(rules)
    args.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    check = object_map(UnityPy.load(str(args.output)))
    assert check.keys() == expected.keys()
    for key, obj in check.items():
        assert hashlib.sha256(obj.get_raw_data()).hexdigest() == expected[key], key
    report = {'verified_objects': len(check), 'changed_assets': changed_assets,
              'protected_strings_restored': restorations, 'corrections': corrections,
              'catalog': catalog_report}
    args.report.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps({'changed_assets': changed_assets, 'restored_strings': len(restorations),
                      'corrections': len(corrections), 'catalog': catalog_report}))


if __name__ == '__main__':
    main()
