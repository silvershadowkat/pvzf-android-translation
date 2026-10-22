"""Translate only the game's initial template-name literal, never saved names."""
import argparse
import hashlib
import json
from pathlib import Path
from build_metadata_translation import parse_metadata, build_metadata

INDEX = 17475
SOURCE = '我的规则'
ENGLISH = 'My Rule'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', type=Path, required=True)
    a = ap.parse_args()
    area = a.work / 'editor-r19'
    area.mkdir(exist_ok=True)
    path = a.work / 'metadata.dat'
    raw = path.read_bytes()
    report_path = area / 'default-name-report.json'
    if report_path.exists():
        report = json.loads(report_path.read_text())
        assert hashlib.sha256(raw).hexdigest() == report['output_sha256']
        print('Verified existing My Rule default patch.')
        return
    port = json.loads((a.work / 'coverage-r12/port-report.json').read_text('utf-8'))
    before_hash = hashlib.sha256(raw).hexdigest()
    assert before_hash == port['outputs']['metadata.dat']
    layout, literals = parse_metadata(raw)
    assert literals[INDEX].text == SOURCE
    values = [x.raw for x in literals]
    values[INDEX] = ENGLISH.encode()
    result = build_metadata(raw, layout, values)
    _, checked = parse_metadata(result)
    assert [x.raw for x in checked] == values
    changed = [i for i, (x,y) in enumerate(zip(literals, checked)) if x.raw != y.raw]
    assert changed == [INDEX]
    (area / 'baseline-metadata.dat').write_bytes(raw)
    path.write_bytes(result)
    report = {'input_sha256': before_hash, 'output_sha256': hashlib.sha256(result).hexdigest(),
              'index': INDEX, 'source': SOURCE, 'english': ENGLISH,
              'scope': 'Initial suggested name only. User templates and input contents are not rewritten.',
              'native_evidence': 'ShowTemplatePage ARM64 RVA 0x246ff34 calls MakeInput with literal 17475. GOT 0x4a41978 relocates to 0x4babbc8, initialized to 0xa0008887, whose literal index is 17475.'}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Verified exactly one changed literal: My Rule default.')


if __name__ == '__main__':
    main()
