"""Carry reviewed Android text layout only when hierarchy and source values match."""
import argparse
import collections
import copy
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from polish_android_ui import make_generator, object_map
from refine_almanac_layout import hierarchy_for_component

TMP_FIELDS = {'m_fontSize', 'm_fontSizeBase', 'm_fontSizeMin', 'm_fontSizeMax',
              'm_enableAutoSizing', 'm_enableWordWrapping', 'm_overflowMode',
              'm_margin', 'm_HorizontalAlignment', 'm_VerticalAlignment',
              'm_textAlignment', 'm_fontAsset', 'm_sharedMaterial', 'm_fontStyle',
              'm_isRichText', 'm_lineSpacing', 'm_wordSpacing', 'm_characterSpacing',
              'm_paragraphSpacing', 'm_enableKerning', 'm_enableExtraPadding'}
RECT_FIELDS = {'m_AnchorMin', 'm_AnchorMax', 'm_AnchoredPosition', 'm_SizeDelta', 'm_Pivot'}


def named(obj):
    if obj is None:
        return None
    if obj.type.name == 'MonoBehaviour':
        raw = obj.get_raw_data()
        size = int.from_bytes(raw[28:32], 'little', signed=True)
        return raw[32:32+size].decode('utf8') if 0 < size < 256 else None
    try:
        return obj.read().m_Name
    except (AttributeError, ValueError):
        return None


def semantic_pointer(objects, file, value):
    if not isinstance(value, dict) or set(value) != {'m_FileID', 'm_PathID'}:
        return value
    if value['m_PathID'] == 0:
        return value
    if value['m_FileID'] != 0:
        raise ValueError('External pointer cannot migrate by local name')
    obj = objects[(file, value['m_PathID'])]
    name = named(obj)
    if not name:
        raise ValueError('Unnamed pointer cannot migrate')
    return {'reference_type': obj.type.name, 'reference_name': name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'previous-source', 'previous-english', 'previous-dlls', 'dlls', 'output', 'report'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    # Hash the old official objects first, then release that bundle before
    # loading the translated donor. Only presentation trees are retained.
    old = UnityPy.load(str(args.previous_source))
    old.typetree_generator = make_generator('2022.3.62f1', args.previous_dlls)
    old_objects = object_map(old)
    baseline = {}
    for key, obj in old_objects.items():
        if obj.type.name not in ('MonoBehaviour', 'RectTransform'):
            continue
        try:
            tree = obj.read_typetree(check_read=True)
        except Exception:
            continue
        fields = RECT_FIELDS if obj.type.name == 'RectTransform' else TMP_FIELDS if 'm_text' in tree else set()
        if not fields:
            continue
        values = {field: semantic_pointer(old_objects, key[0], tree[field]) for field in fields if field in tree}
        baseline[key] = {'type': obj.type.name, 'hierarchy': hierarchy_for_component(old_objects, key), 'values': values}
    del obj, old_objects, old
    gc.collect()
    eng = UnityPy.load(str(args.previous_english))
    eng.typetree_generator = make_generator('2022.3.62f1', args.previous_dlls)
    eng_objects = object_map(eng)
    deltas, skipped = [], []
    for key, source in baseline.items():
        obj = eng_objects[key]
        tree = obj.read_typetree(check_read=True)
        target = {field: semantic_pointer(eng_objects, key[0], tree[field]) for field in source['values']}
        changes = {field: value for field, value in target.items() if value != source['values'][field]}
        if changes:
            deltas.append({**source, 'changes': changes})
    del obj, eng_objects, eng, baseline
    gc.collect()
    current = UnityPy.load(str(args.source))
    current.typetree_generator = make_generator('2022.3.62f1c1', args.dlls)
    objects = object_map(current)
    expected = {key: hashlib.sha256(obj.get_raw_data()).hexdigest() for key, obj in objects.items()}
    by_role = collections.defaultdict(list)
    by_name = collections.defaultdict(list)
    for key, obj in objects.items():
        if obj.type.name in ('MonoBehaviour', 'Material', 'Font'):
            name = named(obj)
            if name:
                by_name[(obj.type.name, name)].append(key)
        if obj.type.name in ('MonoBehaviour', 'RectTransform'):
            by_role[(obj.type.name, hierarchy_for_component(objects, key))].append(key)
    applied, trees = [], {}
    for delta in deltas:
        choices = by_role[(delta['type'], delta['hierarchy'])]
        # A GameObject often has multiple behaviours; filter to TMP by field.
        filtered = []
        for key in choices:
            try:
                if delta['type'] == 'RectTransform' or 'm_text' in objects[key].read_typetree(check_read=True):
                    filtered.append(key)
            except Exception:
                continue
        choices = filtered
        if len(choices) != 1:
            skipped.append({**delta, 'reason': 'missing_or_ambiguous_hierarchy'})
            continue
        key = choices[0]
        obj = objects[key]
        raw = obj.get_raw_data()
        tree = obj.read_typetree(check_read=True)
        values = {field: semantic_pointer(objects, key[0], tree[field]) for field in delta['values'] if field in tree}
        # Treat geometry as a unit: do not mix an old rectangle with a newly
        # redesigned 4.0 screen. TMP attributes also require unchanged sources.
        if values != delta['values']:
            skipped.append({**delta, 'reason': 'presentation_source_changed_in_40'})
            continue
        edits = copy.deepcopy(delta['changes'])
        for field, value in edits.items():
            if isinstance(value, dict) and 'reference_name' in value:
                refs = by_name[(value['reference_type'], value['reference_name'])]
                if len(refs) != 1 or refs[0][0] != key[0]:
                    raise ValueError(f'Ambiguous local presentation reference: {value}')
                edits[field] = {'m_FileID': 0, 'm_PathID': refs[0][1]}
        if obj.save_typetree(tree) != raw:
            raise ValueError(f'Presentation object does not roundtrip: {key}')
        tree.update(edits)
        serialized = obj.save_typetree(tree)
        expected[key] = hashlib.sha256(serialized).hexdigest()
        trees[key] = tree
        applied.append({'object': key, **delta})
    args.output.write_bytes(current.file.save(packer='lz4'))
    del obj, objects, current
    gc.collect()
    check = UnityPy.load(str(args.output))
    check.typetree_generator = make_generator('2022.3.62f1c1', args.dlls)
    check_objects = object_map(check)
    assert set(expected) == set(check_objects)
    for key, obj in check_objects.items():
        assert hashlib.sha256(obj.get_raw_data()).hexdigest() == expected[key], key
        if key in trees:
            assert obj.read_typetree(check_read=True) == trees[key], key
    report = {'verified_objects': len(expected), 'applied': applied, 'skipped': skipped}
    args.report.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps({'verified_objects': len(expected), 'applied': len(applied), 'skipped': len(skipped)}))


if __name__ == '__main__':
    main()
