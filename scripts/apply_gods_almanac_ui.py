"""Apply reviewed Gods Almanac display fallbacks without touching runtime keys."""
import argparse
import copy
import gc
import hashlib
import json
import re
from pathlib import Path

import UnityPy
from build_metadata_translation import parse_metadata, build_metadata, load_pc_translations
from migrate_version_text import same_arguments, text_records
from polish_android_ui import make_generator, object_map
from repair_android40_catalog import validate_catalog
from protected_metadata import PROTECTED_METADATA_STRINGS


def valid_text(source, target):
    assert same_arguments(source, target), 'Composite format arguments changed'
    assert re.findall(r'\[\[[^\]]+\]\]', source) == re.findall(r'\[\[[^\]]+\]\]', target), 'Plant tokens changed'
    assert re.findall(r'<[^>]+>', source) == re.findall(r'<[^>]+>', target), 'Rich-text fragments changed'
    return target


def choose(source, current, rule, exact):
    if source != rule['source']:
        raise ValueError('Reviewed source changed; review before applying')
    if current not in (rule['before'], rule['target']):
        return current, 'preserved_changed_english'
    pc = exact.get(source)
    if pc and not re.search(r'[\u3400-\u9fff]', pc):
        try:
            return valid_text(source, pc), 'pc_exact'
        except AssertionError:
            # A PC result with different formatting is not a safe replacement.
            pass
    return valid_text(source, rule['target']), 'context_aware_fallback'


def patch_catalog(original, current, rules, exact):
    result = copy.deepcopy(current)
    changes = []
    for rule in rules:
        # Only individually reviewed entry prose. Never category/group/type/ID.
        field = rule['field']
        assert field in ('condition', 'description'), 'Only reviewed entry prose is authorized'
        i = rule['index']
        assert original['entries'][i]['id'] == current['entries'][i]['id'] == rule['id'], 'Entry changed'
        before = current['entries'][i][field]
        after, method = choose(original['entries'][i][field], before, rule, exact)
        result['entries'][i][field] = after
        changes.append({'kind': 'catalog', 'index': i, 'id': rule['id'], 'field': field,
                        'source': rule['source'], 'before': before, 'target': after,
                        'method': method, 'changed': before != after})
    return result, changes


def currency_ui(before, rule):
    assert hashlib.sha256(before.encode()).hexdigest() == rule['before_sha256'], 'UI text changed; review required'
    assert before.count('诸神币') == rule['occurrences']
    target = re.sub(r'(?<=[0-9}])God Coins', ' God Coins', before.replace('诸神币', 'God Coins'))
    target = target.replace('God Coins：', 'God Coins: ')
    return valid_text(before, target)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'official', 'metadata', 'official-metadata', 'rules', 'strings', 'dump',
                 'output', 'output-metadata', 'report'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--dlls', type=Path)
    p.add_argument('--inventory', type=Path)
    a = p.parse_args()
    rules = json.loads(a.rules.read_text(encoding='utf8'))
    exact, _, _, _ = load_pc_translations(a.strings, include_android_fallbacks=False)
    raw = a.metadata.read_bytes()
    layout, literals = parse_metadata(raw)
    _, original_literals = parse_metadata(a.official_metadata.read_bytes())
    assert len(literals) == len(original_literals)
    output = [s.raw for s in literals]
    changes = []
    seen = set()
    for rule in rules['metadata']:
        i = rule['index']
        assert i not in seen, 'Duplicate metadata slot'
        seen.add(i)
        target, method = choose(original_literals[i].text, literals[i].text, rule, exact)
        if original_literals[i].text in PROTECTED_METADATA_STRINGS:
            target, method = original_literals[i].text, 'protected_runtime_metadata'
        output[i] = target.encode('utf8')
        changes.append({'kind': 'metadata', 'index': i, 'source': rule['source'],
                        'before': literals[i].text, 'target': target, 'method': method,
                        'changed': target != literals[i].text})
    result = build_metadata(raw, layout, output)
    assert [s.raw for s in parse_metadata(result)[1]] == output
    a.output_metadata.write_bytes(result)

    original = text_records(a.official)['ShootingAlmanacIndex']
    dump = a.dump.read_text(encoding='utf8')
    env = UnityPy.load(str(a.source))
    serialized = {}
    if rules.get('serialized_currency'):
        assert a.dlls and a.inventory
        env.typetree_generator = make_generator('2022.3.62f1c1', a.dlls)
        inventory = {(r['file'], r['id']): r for r in json.loads(a.inventory.read_text(encoding='utf8'))['fields']
                     if r['kind'] == 'MonoBehaviour' and r['field'] == ['m_text']}
        for rule in rules['serialized_currency']:
            assert rule['field'] == 'm_text'
            key = rule['file'], rule['id']
            assert key not in serialized
            source = inventory[key]
            assert source['hierarchy'] == rule['hierarchy']
            assert hashlib.sha256(source['text'].encode()).hexdigest() == rule['source_sha256']
            serialized[key] = rule
    objects = object_map(env)
    expected = {k: hashlib.sha256(o.get_raw_data()).hexdigest() for k, o in objects.items()}
    count = 0
    for key, obj in objects.items():
        if key in serialized:
            assert obj.type.name == 'MonoBehaviour'
            tree = obj.read_typetree(check_read=True)
            assert obj.save_typetree(tree) == obj.get_raw_data(), 'UI roundtrip changed bytes'
            before = tree['m_text']
            tree['m_text'] = currency_ui(before, serialized[key])
            obj.save_typetree(tree)
            expected[key] = hashlib.sha256(obj.data).hexdigest()
            changes.append({'kind': 'serialized_currency', 'object': key, 'before': before,
                            'target': tree['m_text'], 'changed': before != tree['m_text']})
            continue
        if obj.type.name != 'TextAsset':
            continue
        asset = obj.read()
        if asset.m_Name != 'ShootingAlmanacIndex':
            continue
        count += 1
        current = json.loads(asset.m_Script)
        validate_catalog(original, current, dump)
        target, edits = patch_catalog(original, current, rules['catalog'], exact)
        catalog_check = validate_catalog(original, target, dump)
        asset.m_Script = json.dumps(target, ensure_ascii=False, indent=4)
        asset.save()
        expected[key] = hashlib.sha256(obj.data).hexdigest()
        changes.extend(edits)
    assert count == 1
    a.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    check = object_map(UnityPy.load(str(a.output)))
    assert check.keys() == expected.keys()
    for key, obj in check.items():
        assert hashlib.sha256(obj.get_raw_data()).hexdigest() == expected[key], key
    report = {'metadata_rules': len(rules['metadata']), 'catalog_rules': len(rules['catalog']),
              'serialized_currency_rules': len(serialized),
              'changed_fields': sum(c['changed'] for c in changes), 'verified_objects': len(check),
              'catalog_validation': catalog_check, 'changes': changes}
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k != 'changes'}))


if __name__ == '__main__':
    main()
