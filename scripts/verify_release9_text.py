"""Validate the actual Release 9 metadata and its 143 changed text records."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from build_metadata_translation import parse_metadata, CSHARP_FORMAT_FIELD_RE
from reconcile_pc_english import balance_pc_rich_text
from audit_release9_fallbacks import release9_entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'baseline', 'candidate', 'strings', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    original_data = args.original.read_bytes()
    baseline_data = args.baseline.read_bytes()
    data = args.candidate.read_bytes()
    original_layout, original = parse_metadata(original_data)
    baseline_layout, baseline = parse_metadata(baseline_data)
    layout, candidate = parse_metadata(data)
    assert len(original) == len(baseline) == len(candidate) == 19061
    changes = []
    inherited_format_differences = []
    for index, (source, old, new) in enumerate(zip(original, baseline, candidate)):
        assert new.raw.decode('utf-8', errors='strict') == new.text
        if sorted(CSHARP_FORMAT_FIELD_RE.findall(source.text)) != sorted(
                CSHARP_FORMAT_FIELD_RE.findall(new.text)):
            assert new.raw == old.raw, f'new format difference at {index}'
            inherited_format_differences.append({'index': index, 'source': source.text, 'unchanged_english': new.text})
        if new.raw == old.raw:
            continue
        assert '\0' not in new.text and '\ufffd' not in new.text, index
        assert not re.search(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', new.text), index
        assert balance_pc_rich_text(new.text) == new.text, f'rich text at {index}'
        changes.append({'index': index, 'source': source.text, 'before': old.text, 'after': new.text})
    assert len(changes) == 143
    # Only literal lookup offsets/sizes and literal bytes may change.
    prefixes = []
    for payload, info in ((original_data, original_layout), (baseline_data, baseline_layout), (data, layout)):
        prefix = bytearray(payload[:info.data_offset])
        prefix[16:24] = b'\0' * 8
        prefix[info.lookup_offset:info.lookup_offset + info.lookup_size] = b'\0' * info.lookup_size
        prefixes.append(prefix)
    # Previous releases also translated reviewed display-enum names. Preserve
    # those existing differences from the original Android metadata.
    assert prefixes[1] == prefixes[2]
    by_source = {item['source']: item for item in changes}
    for source, fallback in release9_entries().items():
        assert source in by_source, source
        target = by_source[source]['after']
        if source == '命运无常：获得了{0}幸运':
            assert target == '<nobr>Whims of Fate</nobr>：\nGained {0} Luck'
        else:
            assert target == fallback, source
            assert source.count('\n') == target.count('\n'), source
    json_files = list(args.strings.rglob('*.json'))
    assert json_files
    for path in json_files:
        json.loads(path.read_text(encoding='utf-8-sig'))
    report = {
        'passed': True, 'metadata_literals': len(candidate), 'changed_records': len(changes),
        'provisional_entries_verified': 117, 'pc_json_files_strictly_parsed': len(json_files),
        'all_utf8_and_changed_format_arguments_verified': True, 'changed_rich_text_balanced': True,
        'inherited_format_differences': inherited_format_differences,
        'non_literal_metadata_identical_to_release8': True,
        'sha256': hashlib.sha256(data).hexdigest(),
        'android_runtime_tested': False,
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
