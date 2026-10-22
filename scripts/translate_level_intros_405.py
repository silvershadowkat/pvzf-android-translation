"""Add source-gated complete level-title display mappings after the guide layer."""
import argparse
import hashlib
import json
from pathlib import Path
from build_metadata_translation import parse_metadata

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', type=Path, required=True)
    a = ap.parse_args()
    area = a.work / 'level-intros-r19'
    area.mkdir(exist_ok=True)
    spec = json.loads((ROOT / 'assets/level-intros-4.0.5.json').read_text('utf-8'))
    path = a.work / 'english/translations.json'
    raw = path.read_bytes()
    data = json.loads(raw)
    _, literals = parse_metadata((a.work / 'metadata.dat').read_bytes())
    report_path = area / 'apply-report.json'
    if report_path.exists():
        report = json.loads(report_path.read_text('utf-8'))
        assert hashlib.sha256(raw).hexdigest() == report['output_sha256']
        assert all(data['exact'].get(x['source']) == x['english'] for x in spec['entries'])
        print('Verified existing level title patch.')
        return
    guide = json.loads((a.work / 'guide-r13/apply-report.json').read_text('utf-8'))
    assert hashlib.sha256(raw).hexdigest() == guide['outputs']['english/translations.json']
    for row in spec['entries']:
        assert literals[row['index']].text == row['source']
        assert row['source'] not in data['exact'], 'Review existing mapping before replacing it'
        data['exact'][row['source']] = row['english']
    data['level_intro_revision'] = spec['revision']
    output = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    (area / 'baseline-translations.json').write_bytes(raw)
    path.write_bytes(output)
    report_path.write_text(json.dumps({'input_sha256': hashlib.sha256(raw).hexdigest(),
        'output_sha256': hashlib.sha256(output).hexdigest(), 'entries': spec['entries'],
        'scope': 'Rendered title text only; level IDs and source metadata unchanged.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Added three complete ZombiesTD level titles.')


if __name__ == '__main__':
    main()
