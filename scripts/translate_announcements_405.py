"""Apply the reviewed 4.0.5 announcement after the Creator Guide patch.

Changes one TMP text field. Source, complete object inventory and layout are
checked before replacing the staged bundle. No runtime or save changes.
"""
import argparse
import collections
import gc
import hashlib
import json
import re
import shutil
from pathlib import Path

import UnityPy
from polish_android_ui import make_generator

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(path):
    env = UnityPy.load(str(path))
    result = {(o.assets_file.name, o.path_id): hashlib.sha256(o.get_raw_data()).hexdigest()
              for o in env.objects}
    del env
    gc.collect()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', type=Path, required=True)
    a = ap.parse_args()
    w = a.work
    area = w / 'announcements-r17'
    area.mkdir(exist_ok=True)
    review = json.loads((ROOT / 'assets/announcements-4.0.5-review.json').read_text('utf-8'))
    target = w / 'candidate.unity3d'
    report_path = area / 'apply-report.json'
    baseline = area / 'baseline.unity3d'
    previous = None
    if report_path.exists():
        previous = json.loads(report_path.read_text())
        assert sha(target) == previous['output_sha256'], 'Bundle changed since announcement patch'
        if hashlib.sha256(review['english'].encode()).hexdigest() == previous['english_sha256']:
            print('Verified existing announcement patch; no changes.')
            return
        assert sha(baseline) == previous['input_sha256'], 'Announcement baseline changed'
    guide = json.loads((w / 'guide-r13/apply-report.json').read_text('utf-8'))
    assert sha(baseline if previous else target) == guide['outputs']['candidate.unity3d'], 'Apply after verified guide patch'
    if baseline.exists():
        assert previous or sha(baseline) == sha(target), 'Unexpected existing baseline'
    else:
        shutil.copyfile(target, baseline)
    env = UnityPy.load(str(baseline))
    env.typetree_generator = make_generator('2022.3.62f1', w.parent / 'types/DummyDll')
    spec = review['object']
    key = (spec['file'], spec['path_id'])
    obj = next(o for o in env.objects if (o.assets_file.name, o.path_id) == key)
    before = obj.read_typetree()
    source, english = before[spec['field']], review['english']
    assert source == review['source']
    assert hashlib.sha256(source.encode()).hexdigest() == review['source_sha256']
    assert not re.search(r'[\u3400-\u9fff]', english), 'Unresolved Chinese in announcement'
    assert '\u2014' not in english
    assert collections.Counter(re.findall(r'\d+(?:\.\d+)?', source)) == collections.Counter(re.findall(r'\d+(?:\.\d+)?', english))
    assert re.findall(r'<[^>]*>', source) == re.findall(r'<[^>]*>', english)
    assert source.count('\n') == english.count('\n')
    after = dict(before)
    after[spec['field']] = english
    obj.save_typetree(after)
    candidate = area / 'candidate.unity3d'
    candidate.write_bytes(env.file.save(packer='lz4'))
    del obj, env
    gc.collect()
    old, new = inventory(baseline), inventory(candidate)
    assert old.keys() == new.keys()
    changed = [k for k in old if old[k] != new[k]]
    assert changed == [key], changed
    env = UnityPy.load(str(candidate))
    env.typetree_generator = make_generator('2022.3.62f1', w.parent / 'types/DummyDll')
    obj = next(o for o in env.objects if (o.assets_file.name, o.path_id) == key)
    assert obj.read_typetree() == after, 'Text or non-text component fields changed on reopen'
    del obj, env
    gc.collect()
    shutil.copyfile(candidate, target)
    report = {'revision': review['revision'], 'input_sha256': sha(baseline),
              'output_sha256': sha(target), 'english_sha256': hashlib.sha256(english.encode()).hexdigest(),
              'serialized_objects_checked': len(old), 'changed_objects': changed,
              'changed_field': spec['field'], 'terms': review['terms'],
              'unchanged': ['layout fields', 'font', 'metadata', 'runtime dictionaries', 'native libraries', 'save refresh policy']}
    if previous:
        archive = area / ('apply-report-' + previous['output_sha256'][:12] + '.json')
        archive.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('serialized_objects_checked', 'changed_objects', 'changed_field')}))


if __name__ == '__main__':
    main()
