"""Apply tracked generic UI fallbacks, preferring complete current PC English."""
import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from audit_remaining_cjk import walk_strings
from build_metadata_translation import load_pc_translations, translate_complete_pc_literal, parse_metadata, build_metadata
from migrate_version_text import same_arguments, normalized, set_field
from polish_android_ui import make_generator, object_map
from reconcile_pc_english import balance_pc_rich_text
from protected_metadata import PROTECTED_METADATA_STRINGS


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'metadata', 'official-metadata', 'translations', 'strings', 'dlls', 'inventory', 'output', 'output-metadata', 'report'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    config = json.loads(a.translations.read_text(encoding='utf8'))
    mappings = config['translations']
    exact, _, regex, _ = load_pc_translations(a.strings, include_android_fallbacks=False)
    changes = []

    def translate(value):
        if value not in mappings:
            return value
        pc, method = translate_complete_pc_literal(value, exact, regex)
        target = normalized(pc if method else mappings[value])
        assert same_arguments(value, target), value
        return target

    raw = a.metadata.read_bytes()
    layout, literals = parse_metadata(raw)
    _, originals = parse_metadata(a.official_metadata.read_bytes())
    assert len(originals) == len(literals)
    output = []
    for i, literal in enumerate(literals):
        value = translate(literal.text)
        if not same_arguments(originals[i].text, value):
            value = config.get('format_repairs', {}).get(originals[i].text, originals[i].text)
            assert same_arguments(originals[i].text, value), i
        # A source that is a complete styled string can safely have PC-added
        # tags closed. Preserve deliberately open runtime fragments verbatim.
        if value != originals[i].text and balance_pc_rich_text(originals[i].text) == originals[i].text:
            value = balance_pc_rich_text(value)
        if originals[i].text in PROTECTED_METADATA_STRINGS:
            value = originals[i].text
        output.append(value.encode('utf8'))
        if value != literal.text:
            changes.append({'kind': 'metadata', 'index': i, 'source': literal.text, 'target': value})
    result = build_metadata(raw, layout, output)
    assert [x.raw for x in parse_metadata(result)[1]] == output
    a.output_metadata.write_bytes(result)

    env = UnityPy.load(str(a.source))
    env.typetree_generator = make_generator('2022.3.62f1c1', a.dlls)
    objects = object_map(env)
    expected = {key: hashlib.sha256(obj.get_raw_data()).hexdigest() for key, obj in objects.items()}
    inv = json.loads(a.inventory.read_text(encoding='utf8'))['fields']
    ui = {(r['file'], r['id']): r for r in inv if r['kind'] == 'MonoBehaviour' and r['field'] == ['m_text'] and r['text'] in mappings}
    trees = {}
    for key, obj in objects.items():
        tree = None
        if key in ui:
            tree = obj.read_typetree(check_read=True)
            before = tree['m_text']
            after = translate(before)
            if after == before:
                continue
            assert obj.save_typetree(tree) == obj.get_raw_data(), key
            tree['m_text'] = after
            obj.save_typetree(tree)
            trees[key] = tree
            changes.append({'kind': 'MonoBehaviour', 'object': key, 'hierarchy': ui[key]['hierarchy'], 'source': before, 'target': after})
        elif obj.type.name == 'TextAsset':
            data = obj.read()
            if data.m_Name != 'ShootingAlmanacIndex':
                continue
            payload = json.loads(data.m_Script)
            edited = False
            for path, before in list(walk_strings(payload)):
                if path[-1] not in ('name', 'title', 'description'):
                    continue
                after = translate(before)
                if before != after:
                    set_field(payload, path, after)
                    edited = True
                    changes.append({'kind': 'TextAsset', 'asset': data.m_Name, 'field': list(path), 'source': before, 'target': after})
            if not edited:
                continue
            data.m_Script = json.dumps(payload, ensure_ascii=False, indent=4)
            data.save()
        else:
            continue
        expected[key] = hashlib.sha256(obj.data).hexdigest()
    a.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    check = UnityPy.load(str(a.output))
    check.typetree_generator = make_generator('2022.3.62f1c1', a.dlls)
    checked = object_map(check)
    assert set(checked) == set(expected)
    for key, obj in checked.items():
        assert hashlib.sha256(obj.get_raw_data()).hexdigest() == expected[key], key
        if key in trees:
            assert obj.read_typetree(check_read=True) == trees[key], key
    a.report.write_text(json.dumps({'verified_objects': len(expected), 'changes': changes}, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps({'verified_objects': len(expected), 'changes': len(changes)}))


if __name__ == '__main__':
    main()
