"""Source-aligned major-version text migration, preserving the new Unity schema.

No old object IDs, gameplay fields, pointers, layout, fonts or textures are copied.
Every modified MonoBehaviour must round-trip byte-for-byte before editing.
"""
import argparse
import collections
import copy
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy
from build_metadata_translation import load_pc_translations, translate_complete_pc_literal, CSHARP_FORMAT_FIELD_RE
from build_unity_text_translation import read_text_records, merge_android_almanac, ALMANAC_SCHEMAS, ALMANAC_FILES, is_usable_pc_translation
from polish_android_ui import make_generator, object_map, hierarchy_for_component
from reconcile_pc_english import balance_pc_rich_text
from audit_remaining_cjk import walk_strings

DISPLAY_FIELDS = {('m_text',), ('m_Text',), ('data', 'name'), ('data', 'description'), ('group', 'title')}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def set_field(tree, path, value):
    for key in path[:-1]:
        tree = tree[key]
    tree[path[-1]] = value


def normalized(text, almanac=False):
    if almanac:
        text = re.sub(r'</?size(?:=[^>]*)?>', '', text, flags=re.I)
    return balance_pc_rich_text(text.replace('\u2014', '-'))


def same_arguments(a, b):
    # The shared regex captures only the argument ID. Compare the full match
    # so numeric precision/alignment specifiers cannot be silently discarded.
    return sorted(m.group(0) for m in CSHARP_FORMAT_FIELD_RE.finditer(a)) == sorted(
        m.group(0) for m in CSHARP_FORMAT_FIELD_RE.finditer(b))


def quarantine_duplicate_pc_ids(payload, list_key, id_key):
    counts = collections.Counter(row[id_key] for row in payload[list_key])
    duplicate_ids = {key for key, count in counts.items() if count > 1}
    result = copy.deepcopy(payload)
    result[list_key] = [row for row in result[list_key] if row[id_key] not in duplicate_ids]
    return result, sorted(duplicate_ids)


def text_records(path):
    rows = read_text_records(path)
    result = {}
    for row in rows.values():
        if row.name in result:
            raise ValueError(f'Ambiguous TextAsset name: {row.name}')
        try:
            result[row.name] = json.loads(row.script.lstrip('\ufeff'))
        except (ValueError, AttributeError):
            result[row.name] = row.script
    del rows
    gc.collect()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'previous-source', 'previous-english', 'previous-inventory',
                 'previous-english-inventory', 'current-inventory', 'localization', 'dlls', 'output', 'report'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    exact, _, regex, _ = load_pc_translations(args.localization / 'Strings', include_android_fallbacks=False)
    old_text = text_records(args.previous_source)
    english_text = text_records(args.previous_english)
    old_inv = read_json(args.previous_inventory)['fields']
    old_eng_inv = read_json(args.previous_english_inventory)['fields']
    # Release 9's only serialized changes from Release 8 are these placeholders.
    for row in old_eng_inv:
        if row['file'] == 'resources.assets' and row['id'] in (190545, 191192) and row['field'] == ['m_text']:
            row['text'] = 'Modifiers'
    key = lambda row: (row['file'], row['id'], tuple(row['field']))
    old_eng_by_key = {key(row): row for row in old_eng_inv}
    roles = collections.defaultdict(set)
    for row in old_inv:
        translated = old_eng_by_key.get(key(row))
        field = tuple(row['field'])
        if row['kind'] == 'MonoBehaviour' and field in DISPLAY_FIELDS and translated and row['text'] != translated['text']:
            roles[(tuple(row.get('hierarchy', [])), field, row['text'])].add(translated['text'])
    current_inv = read_json(args.current_inventory)
    by_object = collections.defaultdict(list)
    for row in current_inv['fields']:
        if row['kind'] == 'MonoBehaviour' and tuple(row['field']) in DISPLAY_FIELDS:
            by_object[(row['file'], row['id'])].append(row)
    dumps = args.localization.parents[1] / 'Dumps'
    tips = {}
    for name in ('tips_fs.json', 'tips_iz.json'):
        source = read_json(dumps / name)
        target = read_json(args.localization / 'Strings' / name)
        tips.update({(key, value): target[key] for key, value in source.items()
                     if key in target and isinstance(value, str) and is_usable_pc_translation(target[key])})
    pc_details_source = read_json(dumps / 'DetailStrings.json')
    pc_details = read_json(args.localization / 'Almanac' / 'DetailStringsTranslate.json')
    changes, pending, blocked = [], [], []
    counts = collections.Counter()

    def choose(source, previous=None, english=None, almanac=False):
        target, method = translate_complete_pc_literal(source, exact, regex)
        if not method and source == previous and isinstance(english, str) and english != source:
            target, method = english, 'unchanged_39_source'
        if not method:
            return source, None
        target = normalized(target, almanac)
        if not same_arguments(source, target):
            blocked.append({'source': source, 'candidate': target, 'reason': 'format_arguments'})
            return source, None
        return target, method

    def leaves(source, old, eng, asset, path=()):
        if isinstance(source, dict):
            return {k: leaves(v, old.get(k) if isinstance(old, dict) else None,
                             eng.get(k) if isinstance(eng, dict) else None, asset, path + (k,)) for k, v in source.items()}
        if isinstance(source, list):
            return [leaves(v, old[i] if isinstance(old, list) and i < len(old) else None,
                           eng[i] if isinstance(eng, list) and i < len(eng) else None, asset, path + (i,)) for i, v in enumerate(source)]
        if not isinstance(source, str):
            return source
        # Never translate serialized names/keys used to locate a level or asset.
        if path and path[-1] not in ('tips', 'name', 'description', 'title', 'text', 'type', 'introduce', 'info', 'cost'):
            return source
        target, method = choose(source, old, eng)
        tip = tips.get((asset, source)) if path == ('tips',) else None
        if tip is not None and same_arguments(source, tip):
            target, method = normalized(tip), 'pc_source_aligned_tip'
        if target != source:
            changes.append({'kind': 'TextAsset', 'asset': asset, 'field': list(path), 'source': source, 'target': target, 'method': method})
            counts[method] += 1
        elif re.search(r'[\u3400-\u9fff]', source):
            pending.append({'kind': 'TextAsset', 'asset': asset, 'field': list(path), 'source': source,
                            'changed_from_39': old is not None and source != old})
        return target

    env = UnityPy.load(str(args.source))
    version = next(iter(env.objects)).assets_file.unity_version
    env.typetree_generator = make_generator(version, args.dlls)
    objects = object_map(env)
    expected_trees = {}
    expected = {key: hashlib.sha256(bytes(obj.get_raw_data())).hexdigest() for key, obj in objects.items()}
    for obj_key, obj in objects.items():
        raw = bytes(obj.get_raw_data())
        if obj.type.name == 'TextAsset':
            data = obj.read()
            name = data.m_Name
            try:
                source = json.loads(data.m_Script.lstrip('\ufeff'))
            except (ValueError, AttributeError):
                source = data.m_Script
            previous, eng = old_text.get(name), english_text.get(name)
            if name in ALMANAC_SCHEMAS:
                list_key, id_key = ALMANAC_SCHEMAS[name]
                pc_payload, duplicates = quarantine_duplicate_pc_ids(
                    read_json(args.localization / 'Almanac' / ALMANAC_FILES[name]), list_key, id_key)
                for duplicate in duplicates:
                    blocked.append({'asset': name, 'id': duplicate, 'reason': 'conflicting_duplicate_pc_id_quarantined'})
                merged, stats = merge_android_almanac(name, data.m_Script,
                    (dumps / f'{name}.json').read_text(encoding='utf-8-sig'),
                    json.dumps(pc_payload, ensure_ascii=False), {})
                target = json.loads(merged)
                list_key, id_key = ALMANAC_SCHEMAS[name]
                old_by_id = {row[id_key]: row for row in (previous or {}).get(list_key, [])}
                eng_by_id = {row[id_key]: row for row in (eng or {}).get(list_key, [])}
                for row, dest in zip(source[list_key], target[list_key]):
                    record_id = row[id_key]
                    for field, value in row.items():
                        if not isinstance(value, str):
                            continue
                        method = 'pc_source_aligned_almanac'
                        if dest[field] == value:
                            # Almanac prose only uses the same ID/field/source or
                            # a complete PC match, never a neighboring old record.
                            dest[field], method = choose(value, old_by_id.get(record_id, {}).get(field),
                                                        eng_by_id.get(record_id, {}).get(field), True)
                        else:
                            dest[field] = normalized(dest[field], True)
                            if not same_arguments(value, dest[field]):
                                blocked.append({'asset': name, 'id': record_id, 'field': field, 'reason': 'format_arguments'})
                                dest[field] = value
                        if dest[field] != value:
                            counts[method] += 1
                            changes.append({'kind': 'TextAsset', 'asset': name, 'id': record_id, 'field': field,
                                            'source': value, 'target': dest[field], 'method': method})
                        elif re.search(r'[\u3400-\u9fff]', value):
                            pending.append({'kind': 'TextAsset', 'asset': name, 'id': record_id, 'field': field,
                                            'source': value, 'changed_from_39': old_by_id.get(record_id, {}).get(field) not in (None, value)})
            elif name == 'DetailStrings':
                target = copy.deepcopy(source)
                old_by_title = {x['title']: x for x in (previous or {}).get('details', [])}
                eng_by_title = {a['title']: b for a, b in zip((previous or {}).get('details', []), (eng or {}).get('details', []))}
                for row, dest in zip(source['details'], target['details']):
                    title = row['title']
                    for field in ('title', 'text', 'type'):
                        value = row.get(field)
                        if not isinstance(value, str):
                            continue
                        candidate, method = choose(value, old_by_title.get(title, {}).get(field), eng_by_title.get(title, {}).get(field), True)
                        if field == 'text' and pc_details_source.get(title) == value and is_usable_pc_translation(pc_details.get(title)):
                            candidate, method = normalized(pc_details[title], True), 'pc_source_aligned_mechanics'
                        if not same_arguments(value, candidate):
                            candidate = value
                        dest[field] = candidate
                        if candidate != value:
                            counts[method] += 1
                            changes.append({'kind': 'TextAsset', 'asset': name, 'id': title, 'field': field,
                                            'source': value, 'target': candidate, 'method': method})
                        elif re.search(r'[\u3400-\u9fff]', value):
                            pending.append({'kind': 'TextAsset', 'asset': name, 'id': title, 'field': field, 'source': value})
            else:
                target = leaves(source, previous, eng, name)
            if target != source:
                data.m_Script = target if isinstance(target, str) else json.dumps(target, ensure_ascii=False, indent=4)
                data.save()
        elif obj_key in by_object:
            edits = []
            for row in by_object[obj_key]:
                source = row['text']
                field = tuple(row['field'])
                alternatives = roles.get((tuple(row.get('hierarchy', [])), field, source), set())
                old = next(iter(alternatives)) if len(alternatives) == 1 else None
                target, method = choose(source, source if old is not None else None, old)
                if target != source:
                    edits.append((row, target, method))
                elif re.search(r'[\u3400-\u9fff]', source):
                    pending.append({'kind': 'MonoBehaviour', 'hierarchy': row.get('hierarchy'), 'field': list(field), 'source': source})
            if edits:
                tree = obj.read_typetree(check_read=True)
                roundtrip = obj.save_typetree(tree)
                if roundtrip != raw:
                    obj.set_raw_data(raw)
                    blocked.append({'object': obj_key, 'reason': 'typetree_roundtrip_not_identical'})
                    continue
                for row, target, method in edits:
                    set_field(tree, row['field'], target)
                    changes.append({'kind': 'MonoBehaviour', 'object': obj_key, 'hierarchy': row.get('hierarchy'),
                                    'field': row['field'], 'source': row['text'], 'target': target, 'method': method})
                    counts[method] += 1
                obj.save_typetree(tree)
                expected_trees[obj_key] = tree
        expected[obj_key] = hashlib.sha256(obj.data if obj.data is not None else raw).hexdigest()
    args.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    check = UnityPy.load(str(args.output))
    check.typetree_generator = make_generator(version, args.dlls)
    check_objects = object_map(check)
    assert set(check_objects) == set(expected)
    for key, obj in check_objects.items():
        assert hashlib.sha256(bytes(obj.get_raw_data())).hexdigest() == expected[key], key
        if key in expected_trees:
            assert obj.read_typetree(check_read=True) == expected_trees[key], key
    report = {'verified_objects': len(expected), 'counts': dict(counts), 'changes': changes, 'pending': pending,
              'blocked': blocked, 'source_inventory_failures': current_inv['failures'],
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    # Preserve unusual source escape sequences in the audit without attempting
    # to encode surrogate code points as UTF-8. This does not alter game text.
    args.report.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf-8')
    print(json.dumps({'verified_objects': len(expected), 'counts': dict(counts), 'pending': len(pending), 'blocked': len(blocked)}))


if __name__ == '__main__':
    main()
