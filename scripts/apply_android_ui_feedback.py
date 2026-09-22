"""Source-gated changelog, generic UI, and contextual navigation corrections."""
import argparse
import collections
import gc
import hashlib
import json
import re
from pathlib import Path
import UnityPy
from audit_remaining_cjk import walk_strings
from build_metadata_translation import parse_metadata, build_metadata, load_pc_translations, translate_complete_pc_literal
from build_unity_text_translation import ALMANAC_SCHEMAS
from migrate_version_text import quarantine_duplicate_pc_ids, same_arguments, set_field
from polish_android_ui import make_generator, object_map
from reconcile_pc_english import balance_pc_rich_text


def navigation_label(value, hierarchy, rules):
    for rule in rules:
        if hierarchy == rule['hierarchy'] and value in (rule['source'], rule['current']):
            return rule['target']
    return value


def resolve_names(localization):
    names, provenance = {}, []
    dumps = localization.parents[1] / 'Dumps'
    for kind, asset in (('plant', 'LawnStrings'), ('zombie', 'ZombieStrings')):
        ls, ident = ALMANAC_SCHEMAS[asset]
        source = json.loads((dumps / (asset + '.json')).read_text(encoding='utf-8-sig'))
        english, duplicates = quarantine_duplicate_pc_ids(json.loads(
            (localization / 'Almanac' / (asset + 'Translate.json')).read_text(encoding='utf-8-sig')), ls, ident)
        translations = {x[ident]: x for x in english[ls]}
        for row in source[ls]:
            name = translations.get(row[ident], {}).get('name') or row['name']
            names[(kind, str(row[ident]))] = re.sub('<[^>]+>', '', name)
            provenance.append({'kind': kind, 'id': row[ident], 'source': row['name'], 'target': names[(kind, str(row[ident]))], 'pc_conflict': row[ident] in duplicates})
    return names, provenance


def render_changelog(source, config, names):
    assert hashlib.sha256(source.encode()).hexdigest() == config['source_sha256'], 'Changelog source changed'
    def substitute(m):
        key = m.group(1), m.group(2)
        assert key in names, key
        return names[key]
    output = []
    for line in source.splitlines(keepends=True):
        plain = line.rstrip('\r\n')
        newline = line[len(plain):]
        target = config['lines'].get(plain, plain)
        output.append(re.sub(r'@(plant|zombie):(\d+)@', substitute, target) + newline)
    result = ''.join(output)
    assert same_arguments(source, result)
    assert not re.search(r'@(plant|zombie):', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('source', 'metadata', 'inventory', 'rules', 'localization', 'dlls', 'output', 'output-metadata', 'report'):
        p.add_argument('--' + field, type=Path, required=True)
    a = p.parse_args()
    rules = json.loads(a.rules.read_text(encoding='utf8'))
    exact, _, regex, _ = load_pc_translations(a.localization / 'Strings', include_android_fallbacks=False)
    names, provenance = resolve_names(a.localization)
    changes = []

    def generic(value):
        if value not in rules['generic']:
            return value
        pc, method = translate_complete_pc_literal(value, exact, regex)
        target = pc if method else rules['generic'][value]
        assert same_arguments(value, target), value
        assert re.findall(r'\[\[[^\]]+\]\]', value) == re.findall(r'\[\[[^\]]+\]\]', target)
        # Keep deliberate runtime rich-text fragments open as in the source.
        if balance_pc_rich_text(value) == value:
            target = balance_pc_rich_text(target)
        return target

    raw = a.metadata.read_bytes()
    layout, literals = parse_metadata(raw)
    translated = []
    for i, literal in enumerate(literals):
        target = generic(literal.text)
        translated.append(target.encode())
        if target != literal.text:
            changes.append({'kind': 'metadata', 'index': i, 'source': literal.text, 'target': target})
    result = build_metadata(raw, layout, translated)
    assert [x.raw for x in parse_metadata(result)[1]] == translated
    a.output_metadata.write_bytes(result)
    inv = json.loads(a.inventory.read_text())['fields']
    rows = {(r['file'], r['id']): r for r in inv if r['kind'] == 'MonoBehaviour' and r['field'] == ['m_text']}
    env = UnityPy.load(str(a.source))
    env.typetree_generator = make_generator('2022.3.62f1c1', a.dlls)
    objects = object_map(env)
    expected = {k: hashlib.sha256(o.get_raw_data()).hexdigest() for k, o in objects.items()}
    trees = {}
    changelog_count = 0
    for key, obj in objects.items():
        if key in rows:
            row = rows[key]
            # Inspect only reviewed source/hierarchy candidates.
            h = row['hierarchy']
            is_notice = h == rules['changelog']['hierarchy']
            if row['text'] not in rules['generic'] and not is_notice and not any(h == r['hierarchy'] for r in rules['buttons']):
                continue
            tree = obj.read_typetree(check_read=True)
            before = tree['m_text']
            after = navigation_label(before, h, rules['buttons'])
            if is_notice:
                after = render_changelog(before, rules['changelog'], names)
                changelog_count += 1
            elif after == before:
                after = generic(before)
            if after == before:
                continue
            assert obj.save_typetree(tree) == obj.get_raw_data(), key
            tree['m_text'] = after
            obj.save_typetree(tree)
            trees[key] = tree
            changes.append({'kind': 'MonoBehaviour', 'object': key, 'hierarchy': h, 'source': before, 'target': after})
        elif obj.type.name == 'TextAsset':
            data = obj.read()
            if data.m_Name != 'ShootingAlmanacIndex':
                continue
            payload = json.loads(data.m_Script)
            changed = False
            for path, before in list(walk_strings(payload)):
                if path[-1] not in ('name', 'description', 'title'):
                    continue
                after = generic(before)
                if after == before:
                    continue
                set_field(payload, path, after)
                changed = True
                changes.append({'kind': 'TextAsset', 'asset': data.m_Name, 'field': list(path), 'source': before, 'target': after})
            if not changed:
                continue
            data.m_Script = json.dumps(payload, ensure_ascii=False, indent=4)
            data.save()
        else:
            continue
        expected[key] = hashlib.sha256(obj.data).hexdigest()
    assert changelog_count == 1
    a.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    check_env = UnityPy.load(str(a.output))
    check_env.typetree_generator = make_generator('2022.3.62f1c1', a.dlls)
    check = object_map(check_env)
    assert check.keys() == expected.keys()
    for key, obj in check.items():
        assert hashlib.sha256(obj.get_raw_data()).hexdigest() == expected[key], key
        if key in trees:
            assert obj.read_typetree(check_read=True) == trees[key], key
    report = {'verified_objects': len(check), 'counts': dict(collections.Counter(x['kind'] for x in changes)), 'changes': changes,
              'name_provenance': [x for x in provenance if f"@{x['kind']}:{x['id']}@" in str(rules['changelog']['lines'])]}
    a.report.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
