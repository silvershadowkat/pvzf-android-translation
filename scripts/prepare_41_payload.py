"""Source-guarded 4.1 display dictionary and managed-language payload.

Starts with the released dictionary, merges changed/current PC entries and
source-aligned names, then applies the explicit generic UI/effect review. Mixed
name variants are generated at build time as complete keys, never as runtime
substring replacements. No save or gameplay identifier is rewritten.
"""
import argparse, collections, gc, hashlib, json, re, zipfile
from pathlib import Path
import UnityPy
from build_metadata_translation import load_pc_translations, parse_metadata, build_metadata, is_usable_pc_translation, normalize_modifier_translation
from compact_metadata_tail import compact_metadata_tail
from protected_metadata import verify_metadata

META = 'assets/bin/Data/Managed/Metadata/global-metadata.dat'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def clean(text):
    return re.sub(r'</?size(?:=[^>]+)?>', '', text, flags=re.I).replace('\u2014', '-')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def reviewed_format_rule(source, target):
    """Match an entire rendered reviewed template; never edit its source key."""
    slots = re.compile(r'\{(\d+)\}')
    parts, seen, end = [], {}, 0
    for m in slots.finditer(source):
        parts.append(re.escape(source[end:m.start()]))
        field = int(m[1])
        if field in seen:
            parts.append('(?:\\'+str(seen[field]+1)+')')
        else:
            seen[field] = len(seen)
            parts.append('(.*?)')
        end = m.end()
    if not seen:
        return None
    parts.append(re.escape(source[end:]))
    if any(int(m[1]) not in seen for m in slots.finditer(target)):
        raise ValueError('Reviewed replacement references an absent field')
    return ''.join(parts), slots.sub(lambda m: '{'+str(seen[int(m[1])])+'}', target)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('previous-apk', 'official', 'pc', 'previous-pc', 'source-texts', 'bundle', 'metadata', 'review', 'work'):
        ap.add_argument('--'+key, type=Path, required=True)
    ap.add_argument('--pc-commit', required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.previous_apk) as z:
        previous = json.loads(z.read('assets/english/translations.json'))
    current, _, current_rules, counts = load_pc_translations(a.pc/'Localization/English/Strings', False)
    old_pc, _, old_rules, _ = load_pc_translations(a.previous_pc/'Localization/English/Strings', False)
    exact = dict(previous['exact'])
    report = {'pc_commit': a.pc_commit, 'pc_counts': counts, 'pc_updates': [], 'retained_android': [], 'reviewed': [], 'name_pairs': [], 'aliases': []}
    for source, english in current.items():
        english = clean(english)
        prior = exact.get(source)
        # Preserve a reviewed Android fix if the PC field itself did not change.
        if prior is not None and source in old_pc and clean(old_pc[source]) == english and prior != english:
            report['retained_android'].append(source)
            continue
        if prior != english:
            exact[source] = english
            report['pc_updates'].append({'source': source, 'before': prior, 'after': english})
    with zipfile.ZipFile(a.official) as z:
        original_bytes = z.read(META)
    _, original = parse_metadata(original_bytes)
    layout, translated = parse_metadata(a.metadata.read_bytes())
    assert len(original) == len(translated)
    # Prefer the metadata builder's verified complete display output, which also
    # preserves modifier heading/body boundaries and complete recipe provenance.
    for source, target in zip(original, translated):
        if source.text != target.text and re.search(r'[\u3400-\u9fff]', source.text):
            exact[source.text] = clean(target.text)
    env = UnityPy.load(str(a.bundle))
    names = collections.defaultdict(set)
    almanacs = a.work/'almanac-refresh'
    for o in env.objects:
        if o.type.name != 'TextAsset':
            continue
        asset = o.read()
        if asset.m_Name not in ('LawnStrings', 'ZombieStrings', 'DetailStrings'):
            continue
        raw = asset.m_Script.encode('utf8') if isinstance(asset.m_Script, str) else bytes(asset.m_Script)
        content = json.loads(raw)
        almanacs.mkdir(parents=True, exist_ok=True)
        (almanacs/(asset.m_Name+'.json')).write_bytes(raw)
        if asset.m_Name == 'DetailStrings':
            continue
        source = read(a.source_texts/(asset.m_Name+'.json'))
        root, id_key = ('plants', 'seedType') if asset.m_Name == 'LawnStrings' else ('zombies', 'theZombieType')
        original_names = {r[id_key]: r['name'] for r in source[root]}
        for row in content[root]:
            cn = re.sub('<[^>]+>', '', original_names[row[id_key]]).strip()
            english = re.sub('<[^>]+>', '', row.get('name', '')).strip()
            if re.search('[\u3400-\u9fff]', cn) and is_usable_pc_translation(english):
                names[cn].add(english)
    del env
    gc.collect()
    name_pairs = {cn: next(iter(en)) for cn, en in names.items() if len(en) == 1}
    for cn, english in name_pairs.items():
        exact[cn] = english
        report['name_pairs'].append({'source': cn, 'english': english})
    review = read(a.review)
    reviewed = {**review.get('runtime_only', {}), **review['exact']}
    for source, target in reviewed.items():
        assert is_usable_pc_translation(target), 'Invalid reviewed English'
        assert any(source in literal.text for literal in original), 'Reviewed string not present in official 4.1: '+source
        # PC remains authoritative unless an explicit Android effect/source
        # correction is needed, as documented for the screenshot fragments.
        if source in current and current[source] != review.get('pc_inaccurate_values', {}).get(source):
            target = clean(current[source])
        exact[source] = target
        report['reviewed'].append({'source': source, 'english': target})
    changes = []
    payload = [v.raw for v in translated]
    for i, source in enumerate(original):
        if source.text in review['exact']:
            target = exact[source.text]
            payload[i] = target.encode('utf8')
            changes.append({'index': i, 'source': source.text, 'english': target})
    output = compact_metadata_tail(build_metadata(a.metadata.read_bytes(), layout, payload))
    protection = verify_metadata(original_bytes, output)
    (a.work/'metadata.dat').write_bytes(output)
    report['reviewed_metadata_changes'] = changes
    report['protected_metadata'] = protection
    # Metadata normalizes modifier boundaries before rendering. Preserve known
    # whole-record English for that structured source and for uniquely resolved
    # title/body spans. Otherwise tags or a separately inserted plant name can
    # hide an already-reviewed complete translation from exact lookup.
    active_sources = {v.text for v in original}
    modifier_spans = collections.defaultdict(set)
    for source, target in list(exact.items()):
        if source not in active_sources or not is_usable_pc_translation(target):
            continue
        if not any(d in source for d in ('：', ':')) or not any(d in target for d in ('：', ':')):
            continue
        try:
            structured, _ = normalize_modifier_translation(source)
            english, _ = normalize_modifier_translation(target)
        except ValueError:
            continue
        if structured != source:
            exact.setdefault(structured, english)
        cn_title, cn_body = re.sub('<[^>]+>', '', structured).split('：\n', 1)
        en_title, en_body = re.sub('<[^>]+>', '', english).split('：\n', 1)
        if len(cn_title) >= 2:
            modifier_spans[cn_title].add(en_title)
        modifier_spans[cn_body].add(en_body)
    for source, targets in modifier_spans.items():
        if source not in exact and len(targets) == 1:
            exact[source] = next(iter(targets))
    # Screenshot-backed composed passive prefix: the source prepends 被 before
    # the named plant and the numeric effect fragment. Keep it off unrelated UI.
    laser = '的激光的非boss类僵尸若血量低于10%则立即化为灰烬，多选提高斩杀线'
    for suffix in (laser, exact[laser]):
        exact['被Apocalypse Railgun'+suffix] = 'Apocalypse Railgun'+exact[laser]
    # This PC modifier key accidentally includes the almanac's discovery banner.
    # Reuse its verified effect text for the actual standalone card body too.
    firecracker = '烈焰竹龙释放的飞天爆竹数 + 1'
    pc_firecracker = [v for k,v in current.items() if k.endswith(firecracker) and k != firecracker]
    assert len(set(pc_firecracker)) == 1, 'Re-review PC Firecracker key'
    for source in (firecracker, firecracker.replace(' + ', '+')):
        exact[source] = clean(pc_firecracker[0])
    # Generate only complete-key aliases. Ambiguous results are excluded. A long
    # plant name wins over a contained shorter name in the combined-name variant.
    candidates = collections.defaultdict(set)
    canonical_names = {cn: en for cn, en in name_pairs.items() if len(cn) >= 2}
    pattern = re.compile('|'.join(re.escape(cn) for cn in sorted(canonical_names, key=len, reverse=True)))
    for source, target in list(exact.items()):
        found = {m.group(0) for m in pattern.finditer(source)}
        for cn in found:
            alias = source.replace(cn, canonical_names[cn])
            if alias != source:
                candidates[alias].add(target)
        if found:
            alias = pattern.sub(lambda m: canonical_names[m.group(0)], source)
            if alias != source:
                candidates[alias].add(target)
    for alias, targets in candidates.items():
        if len(targets) == 1 and alias not in exact and re.search('[\u3400-\u9fff]', alias):
            target = next(iter(targets))
            exact[alias] = target
            report['aliases'].append({'source': alias, 'english': target})
    rules = {row[0]: row[1] for row in previous['regex']}
    old_rules = {row[0]: clean(row[1]) for row in old_rules}
    for pattern, target, _, origin in current_rules:
        if pattern == 'BUFF_NAME_FORMAT' or '(?P' in pattern or '(?<' in pattern or re.search(r'\{\d+[:,]', target):
            continue
        if pattern in rules and pattern in old_rules and rules[pattern] != old_rules[pattern] and clean(target) == old_rules[pattern]:
            continue
        rules[pattern] = clean(target)
    rules[r'Availability:\s*(.+)'] = 'Availability: {0}'
    rules[r'(?:\[神笔马良\] 鉴定失败：|\[Magic Plantbrush\] Recognition failed: )(.*)'] = '[Magic Plantbrush] Recognition failed: {0}'
    for source in review.get('runtime_only', {}):
        rule = reviewed_format_rule(source, exact[source])
        if rule:
            rules[rule[0]] = rule[1]
    result = {**previous, 'pc_commit': a.pc_commit, 'pc_overlay_commit': a.pc_commit, 'exact': exact, 'regex': list(map(list, rules.items()))}
    online = a.pc/'Localization/English/Strings/custom_level_data.json'
    if online.exists():
        result['online_levels'] = {k: {f: clean(v[f]) for f in ('name', 'startTip')} for k, v in read(online).items()
                                  if re.fullmatch(r'level_[0-9]+_[A-Za-z0-9]+', k) and all(isinstance(v.get(f), str) and not re.search('[\u3400-\u9fff]', v[f]) for f in ('name', 'startTip'))}
    write(a.work/'english/translations.json', result)
    report.update(exact_count=len(exact), regex_count=len(rules), previous_keys_retained=set(previous['exact']).issubset(exact))
    write(a.work/'translation-report.json', report)
    print(json.dumps({k: report[k] for k in ('exact_count', 'regex_count', 'previous_keys_retained')}, indent=2))


if __name__ == '__main__':
    main()
