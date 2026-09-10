"""Apply the Android 3.9 Recommended Levels caption wrap, preserving all other bytes."""
import argparse
import gc
import hashlib
import json
from pathlib import Path

from build_unity_ui_translation import load_objects, read_tmp_text, replace_tmp_text, hierarchy_for_component

CARD = ('resources.assets', 188456)
HIERARCHY = ['Name', 'Window', 'Level_1', 'HotLevelMenu']
CAPTION = 'The Gods: Evolved\nPurgatory'
ACCEPTED = {'诸神进化：炼狱', 'The Gods: Evolved - Purgatory', CAPTION}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise ValueError('Use a separate output file')
    env, objects = load_objects(args.input)
    obj = objects[CARD]
    before = bytes(obj.get_raw_data())
    assert hierarchy_for_component(objects, CARD) == HIERARCHY
    old_text, old_end = read_tmp_text(before)
    assert old_text in ACCEPTED, old_text
    after = replace_tmp_text(before, CAPTION)
    _, new_end = read_tmp_text(after)
    assert before[:88] == after[:88] and before[old_end:] == after[new_end:]
    expected = {key: hashlib.sha256(bytes(value.get_raw_data())).hexdigest()
                for key, value in objects.items()}
    expected[CARD] = hashlib.sha256(after).hexdigest()
    obj.set_raw_data(after)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(env.file.save(packer='lz4'))
    del obj, objects, env
    gc.collect()
    verified, objects = load_objects(args.output)
    assert set(objects) == set(expected)
    for key, obj in objects.items():
        assert hashlib.sha256(bytes(obj.get_raw_data())).hexdigest() == expected[key], key
    assert read_tmp_text(bytes(objects[CARD].get_raw_data()))[0] == CAPTION
    report = {'objects_verified': len(objects), 'only_caption_changed': True,
              'key': CARD, 'hierarchy': HIERARCHY, 'before': old_text, 'after': CAPTION,
              'all_other_component_bytes_unchanged': True, 'device_tested': False,
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
