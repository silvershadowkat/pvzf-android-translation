"""Port the complete PC skin-challenge title to Android's line-wrapped UI key."""
import argparse
import gc
import hashlib
import json
from pathlib import Path

from build_metadata_translation import load_pc_translations, translate_complete_pc_literal
from build_unity_ui_translation import load_objects, read_tmp_text, replace_tmp_text, hierarchy_for_component

CARD = ('resources.assets', 191808)
HIERARCHY = ['Name', 'Window', 'Level', 'Page2', 'PageNormalTravel', 'Levels', 'TravelChallengeMenu']
SOURCE = '究极黑曜石高坚果\n皮肤挑战'
PC_SOURCE = '究极黑曜石高坚果皮肤挑战'
REVIEWED_PC = 'Obsidian Tall-nut Skin Challenge'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--strings-dir', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise ValueError('Use a separate output file')
    exact, _, regexes, _ = load_pc_translations(args.strings_dir, include_android_fallbacks=False)
    pc, method = translate_complete_pc_literal(PC_SOURCE, exact, regexes)
    if method is None or pc != REVIEWED_PC:
        raise ValueError('Complete reviewed PC title is unavailable or changed; review before importing')
    caption = pc.replace(' Skin Challenge', '\nSkin Challenge')
    assert caption.replace('\n', ' ') == pc
    env, objects = load_objects(args.input)
    obj = objects[CARD]
    before = bytes(obj.get_raw_data())
    assert hierarchy_for_component(objects, CARD) == HIERARCHY
    old_text, old_end = read_tmp_text(before)
    assert old_text in (SOURCE, caption), old_text
    after = replace_tmp_text(before, caption)
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
    assert read_tmp_text(bytes(objects[CARD].get_raw_data()))[0] == caption
    report = {'objects_verified': len(objects), 'only_caption_changed': True,
              'key': CARD, 'hierarchy': HIERARCHY, 'before': old_text, 'after': caption,
              'pc_source': PC_SOURCE, 'pc_translation': pc, 'pc_method': method,
              'all_other_component_bytes_unchanged': True, 'device_tested': False,
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
