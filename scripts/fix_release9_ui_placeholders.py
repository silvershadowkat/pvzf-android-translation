"""Translate two Travel Store placeholder labels without modifying component layout."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
from build_unity_ui_translation import load_objects, read_tmp_text, replace_tmp_text, hierarchy_for_component

FIELDS = {
    ('resources.assets', 190545): ['InvestText', 'Content', 'Viewport', 'Scroll View', 'TravelStore'],
    ('resources.assets', 191192): ['InvestText_shadow', 'Content', 'Viewport', 'Scroll View', 'TravelStore'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'output', 'report'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise ValueError('Use a separate output file')
    env, objects = load_objects(args.input)
    expected = {k: hashlib.sha256(bytes(o.get_raw_data())).hexdigest() for k, o in objects.items()}
    changes = []
    for key, hierarchy in FIELDS.items():
        assert hierarchy_for_component(objects, key) == hierarchy
        obj = objects[key]
        before = bytes(obj.get_raw_data())
        text, old_end = read_tmp_text(before)
        assert text == '词条' * 28 or text == 'Modifiers', repr(text)
        after = replace_tmp_text(before, 'Modifiers')
        _, new_end = read_tmp_text(after)
        assert before[:88] == after[:88] and before[old_end:] == after[new_end:]
        obj.set_raw_data(after)
        expected[key] = hashlib.sha256(after).hexdigest()
        changes.append({'key': key, 'hierarchy': hierarchy, 'before': text, 'after': 'Modifiers'})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    env, objects = load_objects(args.output)
    assert set(objects) == set(expected)
    for key, obj in objects.items():
        assert hashlib.sha256(bytes(obj.get_raw_data())).hexdigest() == expected[key], key
    report = {'objects_verified': len(objects), 'changes': changes,
              'all_other_object_and_component_bytes_unchanged': True, 'device_tested': False,
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'objects_verified': len(objects), 'changed_text_fields': len(changes)}))


if __name__ == '__main__':
    main()
