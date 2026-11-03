"""Apply explicitly reviewed 4.1 fields, then scope the Unity product identity.

New PC records are accepted only when absent from the PC repository's older
source dump and identical in the actual PC/Android 4.1 source. Every contextual
field and announcement is guarded by its complete original source hash.
"""
import argparse, gc, hashlib, json, re
from pathlib import Path
import UnityPy
from build_unity_ui_translation import read_tmp_text, replace_tmp_text
from build_metadata_translation import is_usable_pc_translation

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def current_raw(obj):
    return obj.data if obj.data is not None else obj.get_raw_data()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'android-texts', 'pc-texts', 'pc', 'review', 'output', 'report'):
        ap.add_argument('--'+key, type=Path, required=True)
    a = ap.parse_args()
    review = read(a.review)
    android = {r['seedType']: r for r in read(a.android_texts/'LawnStrings.json')['plants']}
    official_pc = {r['seedType']: r for r in read(a.pc_texts/'LawnStrings.json')['plants']}
    dumps = {r['seedType']: r for r in read(a.pc/'Dumps/LawnStrings.json')['plants']}
    english = {r['seedType']: r for r in read(a.pc/'Localization/English/Almanac/LawnStringsTranslate.json')['plants']}
    env = UnityPy.load(str(a.base))
    before = {(o.assets_file.name, o.path_id): digest(o.get_raw_data()) for o in env.objects}
    changed_fields, announcement_done = [], False
    for obj in env.objects:
        if obj.type.name == 'TextAsset':
            data = obj.read()
            if data.m_Name != 'LawnStrings':
                continue
            rows = json.loads(data.m_Script)
            for row in rows['plants']:
                key = str(row['seedType'])
                if key not in review['plants']:
                    continue
                ident = row['seedType']
                assert ident not in dumps, 'Existing PC source record requires normal stale-source guards'
                source = android[ident]
                assert source == official_pc[ident], 'PC/Android new record differs'
                for field, claim in review['plants'][key].items():
                    assert digest(source[field].encode()) == claim['source_sha256']
                    if claim['origin'] == 'Blooms':
                        target = english[ident][field]
                        assert digest(target.encode()) == claim['pc_sha256'], 'PC field changed; review again'
                        assert not re.search('[\u3400-\u9fff]', target), 'Incomplete PC field'
                    else:
                        target = claim['english']
                        # A future complete PC field supersedes this contextual
                        # fallback; markup-only placeholder prose does not.
                        pc_value = english[ident].get(field, '')
                        plain = re.sub('<[^>]+>', '', pc_value)
                        if re.search('[A-Za-z]{2}', plain) and is_usable_pc_translation(pc_value):
                            target = pc_value
                    target = re.sub(r'</?size(?:=[^>]+)?>', '', target, flags=re.I)
                    row[field] = target
                    changed_fields.append({'id': ident, 'field': field, **claim})
            data.m_Script = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
            obj.save_typetree(data)
        elif (obj.assets_file.name, obj.path_id) == ('resources.assets', review['announcement']['path_id']):
            raw = obj.get_raw_data()
            source = read_tmp_text(raw)[0]
            assert digest(source.encode()) == review['announcement']['source_sha256']
            obj.set_raw_data(replace_tmp_text(raw, review['announcement']['english']))
            announcement_done = True
    assert announcement_done and len(changed_fields) == sum(map(len, review['plants'].values()))
    allowed = {('resources.assets', review['announcement']['path_id'])}
    allowed.update((o.assets_file.name, o.path_id) for o in env.objects if o.type.name == 'TextAsset' and o.read().m_Name == 'LawnStrings')
    changed = {k for o in env.objects if before[(k := (o.assets_file.name, o.path_id))] != digest(current_raw(o))}
    assert changed == allowed, changed
    pre_identity = { (o.assets_file.name, o.path_id): digest(current_raw(o)) for o in env.objects }
    settings = [o for o in env.objects if o.type.name == 'PlayerSettings']
    assert len(settings) == 1
    tree = settings[0].read_typetree()
    assert tree['productName'] == 'PlantsVsZombiesRH'
    tree['productName'] = 'PlantsVsZombiesEN'
    def rename(value):
        if isinstance(value, dict):
            return {k: rename(v) for k,v in value.items()}
        if isinstance(value, list):
            return [rename(v) for v in value]
        return 'com.LanPiaoPiao.PlantsVsZombiesEN' if value == 'com.LanPiaoPiao.PlantsVsZombiesRH' else value
    settings[0].save_typetree(rename(tree))
    identity_changes = [k for o in env.objects if pre_identity[(k := (o.assets_file.name,o.path_id))] != digest(current_raw(o))]
    assert identity_changes == [('globalgamemanagers',1)]
    a.output.write_bytes(env.file.save(packer='lz4'))
    del env
    gc.collect()
    reopened = UnityPy.load(str(a.output))
    actual = {(o.assets_file.name,o.path_id): digest(o.get_raw_data()) for o in reopened.objects}
    assert set(actual) == set(before)
    assert {k for k in actual if actual[k] != before[k]} == allowed | {('globalgamemanagers',1)}
    report = {'fields': changed_fields, 'announcement': review['announcement'], 'changed_objects': sorted(allowed), 'roundtrip_verified': True}
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    identity = {'objects_compared': len(actual), 'changed': identity_changes, 'only_player_settings_changed': True, 'sha256': digest(a.output.read_bytes())}
    (a.output.parent/'identity-report.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf8')
    print('Reviewed 4.1 fields, announcement and identity verified',flush=True)

if __name__ == '__main__':
    main()
