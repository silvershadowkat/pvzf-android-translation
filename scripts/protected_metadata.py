"""Keep reported Gods: Evolved runtime keys out of metadata translation.

Exact metadata literals only. This must not disable separately verified display
translations in the Almanac or replace substrings inside ordinary prose.
"""

PROTECTED_METADATA_STRINGS = frozenset({
    '升级', '获得新植物', '试炼', '试炼：',
    'ShootingAlmanacIndex', 'UI/Data/ShootingAlmanacIndex',
    '木桩', '烈阳', '战锤', '裂空', '明月', '硬化', '交易', '宝藏',
    '业火', '光棱', '天罚', '护盾保护', '爆炸保护',
    '不破不立', '两极分化', '傲慢之罚', '嫉妒之惩',
    '大帝诅咒', '大帝祝福', '究樱诅咒', '究樱祝福',
    '火菜炮诅咒', '火菜炮祝福', '磁坚诅咒', '磁坚祝福',
})


def protected_changes(original, current):
    if len(original) != len(current):
        raise ValueError('Metadata literal counts differ; compare matching game versions')
    return [
        {'index': i, 'source': source, 'target': current[i]}
        for i, source in enumerate(original)
        if source in PROTECTED_METADATA_STRINGS and current[i] != source
    ]


def verify_metadata(original_bytes, candidate_bytes):
    # Local import keeps the literal translator free of an import cycle.
    from build_metadata_translation import parse_metadata
    original = [s.text for s in parse_metadata(original_bytes)[1]]
    current = [s.text for s in parse_metadata(candidate_bytes)[1]]
    changes = protected_changes(original, current)
    if changes:
        slots = ', '.join(str(row['index']) for row in changes)
        raise ValueError('Protected runtime metadata strings were translated at slots: ' + slots)
    present = set(original) & PROTECTED_METADATA_STRINGS
    return {'protected_strings': len(PROTECTED_METADATA_STRINGS),
            'present_strings': len(present),
            'verified_slots': sum(s in present for s in original),
            'absent_strings': sorted(PROTECTED_METADATA_STRINGS - present)}


def restore_metadata(original_bytes, candidate_bytes):
    from build_metadata_translation import parse_metadata, build_metadata
    original = parse_metadata(original_bytes)[1]
    layout, current = parse_metadata(candidate_bytes)
    changes = protected_changes([s.text for s in original], [s.text for s in current])
    output = [s.raw for s in current]
    for row in changes:
        output[row['index']] = original[row['index']].raw
    result = build_metadata(candidate_bytes, layout, output) if changes else candidate_bytes
    assert [s.raw for s in parse_metadata(result)[1]] == output
    verify_metadata(original_bytes, result)
    return result, changes


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--official', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, help='Restore protected slots into a new file')
    args = p.parse_args()
    original = args.official.read_bytes()
    candidate = args.candidate.read_bytes()
    changes = []
    if args.output:
        candidate, changes = restore_metadata(original, candidate)
        with args.output.open('xb') as f:
            f.write(candidate)
    report = verify_metadata(original, candidate)
    report.update(restored=changes, sha256=hashlib.sha256(candidate).hexdigest())
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'verified_slots': report['verified_slots'], 'restored_slots': len(changes)}))


if __name__ == '__main__':
    main()
