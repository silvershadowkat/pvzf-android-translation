"""Regression coverage for stale English, source alignment, and partial regexes."""
import re
import json
import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_metadata_translation import translate_complete_pc_literal, translate_literal, load_reviewed_pc_records
from build_metadata_translation import load_pc_translations, is_usable_modifier_description
from build_metadata_translation import is_usable_pc_translation as usable_metadata_text
from build_unity_text_translation import repeated_narrative_is_placeholder, is_usable_pc_translation
from reconcile_pc_english import prefer_pc_tree, ui_exception, balance_pc_color_tags, balance_pc_rich_text


def rule(pattern, target):
    return (pattern, target, re.compile(pattern, re.DOTALL), "")


class PcAuthorityTests(unittest.TestCase):
    def test_all_release9_fallbacks_yield_to_future_exact_pc_translations(self):
        from audit_release9_fallbacks import release9_entries, audit
        entries = release9_entries()
        self.assertEqual(len(entries), 117)
        future_pc = {source: 'PC reviewed: ' + target for source, target in entries.items()}
        with tempfile.TemporaryDirectory() as folder:
            strings = Path(folder)
            (strings / 'translation_strings.json').write_text(
                json.dumps(future_pc), encoding='utf-8')
            exact, sources, _, _ = load_pc_translations(strings)
            for source, target in future_pc.items():
                with self.subTest(source=source):
                    self.assertIn(source, sources)
                    self.assertEqual(exact[source], target)
            rows = audit(strings)
            self.assertEqual(len(rows), 117)
            self.assertTrue(all(row['status'] == 'pc_candidate_available' for row in rows))

    def test_firewall_runtime_name_suffix_requires_complete_reviewed_pc_field(self):
        key = '火焰狙击射手的火墙密度+3\n需要重新手动建立火墙'
        suffix = '的火墙密度+3\n需要重新手动建立火墙'
        pc = 'Blazer Snipea: Gains +3 Firewall links.\nThe Firewall will have to be manually rebuilt after picking this modifier.'
        with tempfile.TemporaryDirectory() as folder:
            strings = Path(folder)
            for target in (pc, pc + ' Another effect.', ''):
                (strings / 'translation_strings.json').write_text(
                    json.dumps({key: target}), encoding='utf-8')
                exact, sources, _, _ = load_pc_translations(strings, False)
                if target == pc:
                    self.assertEqual('Blazer Snipea' + exact[suffix], pc)
                    self.assertIn(suffix, sources)
                else:
                    self.assertNotIn(suffix, exact)

    def test_generic_release9_text_preserves_format_arguments_and_line_breaks(self):
        from reviewed_release9_text import GENERIC_RELEASE9
        from build_metadata_translation import CSHARP_FORMAT_FIELD_RE
        for source, target in GENERIC_RELEASE9.items():
            with self.subTest(source=source):
                self.assertEqual(sorted(CSHARP_FORMAT_FIELD_RE.findall(source)),
                                 sorted(CSHARP_FORMAT_FIELD_RE.findall(target)))
                self.assertEqual(source.count('\n'), target.count('\n'))
        self.assertEqual(GENERIC_RELEASE9['◀️ 回到上一小拍: {0}.{1}'],
                         '◀️ Back to the previous subdivision: {0}.{1}')

    def test_syntax_repair_rejects_unreviewed_upstream_bytes(self):
        from prepare_reviewed_pc_strings import repair_september15_json, SEPT15_COMMIT
        raw = b'{"key": "value"}'
        with self.assertRaises(ValueError):
            repair_september15_json(raw, 'translation_strings.json', SEPT15_COMMIT)
        self.assertEqual(repair_september15_json(raw, 'translation_strings.json', 'other'), (raw, 0))

    def test_generic_effect_translation_requires_reviewed_pc_name(self):
        with tempfile.TemporaryDirectory() as folder:
            strings = Path(folder)
            pc = strings / 'travel_buffs.json'
            source = '护盾保护：持有护盾的植物每秒回复0.1%护盾量的生命值'
            for name in ('Enchanted Shield', 'New PC Name', ''):
                pc.write_text(json.dumps({'advancedBuffs': {'13001': {
                    'name': name, 'desc': '持有护盾的植物每秒回复0.1%护盾量的生命值'
                }}}), encoding='utf-8')
                exact, _, _, _ = load_pc_translations(strings)
                if name == 'Enchanted Shield':
                    self.assertEqual(exact['护盾保护'], name)
                    self.assertTrue(exact[source].startswith(name + '：'))
                else:
                    self.assertNotIn(source, exact)
                    self.assertNotIn('护盾保护', exact)
                strict, _, _, _ = load_pc_translations(strings, include_android_fallbacks=False)
                self.assertNotIn(source, strict)

    def test_reviewed_luck_variant_preserves_dynamic_cap_and_precision(self):
        source = '幸运提高{0:F0}，幸运可以提高好词条出现概率\n当前幸运值：{1}/{2:F0}'
        pattern = r'幸运提高(\d+)，幸运可以提高好词条出现概率' '\n' r'当前幸运值：(\d+)/250'
        pc = 'Increases your luck by {0}. Luck increases the probability of rarer modifiers appearing.\nCurrent Luck: {1}/250'
        result, method = translate_complete_pc_literal(source, {}, [rule(pattern, pc)])
        self.assertEqual(result, 'Increases your luck by {0:F0}. Luck increases the probability of rarer modifiers appearing.\nCurrent Luck: {1}/{2:F0}')
        self.assertEqual(method, 'pc_reviewed_android_template')
        self.assertEqual(translate_complete_pc_literal(source, {}, []), (source, None))
        self.assertEqual(translate_complete_pc_literal(source, {}, [rule(pattern, pc + ' Extra effect.')]), (source, None))

    def test_reviewed_respawn_variant_keeps_standard_label(self):
        source = '复活时间降低{0:F0}%\n当前标准复活时长：{1:F1}秒'
        pattern = r'复活时间降低(\d+)%' '\n' r'当前复活时长：([\s\S]+)秒'
        pc = 'Reduce plant respawn time by {0}%.\nCurrent respawn time: {1}s'
        result, method = translate_complete_pc_literal(source, {}, [rule(pattern, pc)])
        self.assertEqual(result, 'Reduce plant respawn time by {0:F0}%.\nCurrent standard respawn time: {1:F1}s')
        self.assertEqual(method, 'pc_reviewed_android_template')
        # The reviewed adapter must not consume extra Android gameplay prose.
        extra = source + '\n并立即恢复生命值'
        self.assertEqual(translate_complete_pc_literal(extra, {}, [rule(pattern, pc)]), (extra, None))

    def test_crossed_pc_styles_and_orphan_sizes_are_repaired(self):
        source = '<color=red><size=15></color>Tip</size>'
        expected = '<color=red><size=15></size></color><size=15>Tip</size>'
        self.assertEqual(balance_pc_rich_text(source), expected)
        self.assertEqual(balance_pc_rich_text(expected), expected)
        self.assertEqual(balance_pc_rich_text('One.</size>\nTwo.</size>'), 'One.\nTwo.')
        changes = []
        self.assertEqual(prefer_pc_tree('说明', 'One.</size>', {'说明': 'One.</size>'}, [], changes, repair_existing_markup=True), 'One.')
        self.assertEqual(changes[0]['method'], 'pc_markup_cleanup')

    def test_pc_color_cleanup_preserves_visible_recipe(self):
        source = 'Conversion: <color=red>Shovel <-> Blover</color></color>'
        expected = 'Conversion: <color=red>Shovel <-> Blover</color>'
        self.assertEqual(balance_pc_color_tags(source), expected)
        self.assertEqual(balance_pc_color_tags(expected), expected)
        self.assertEqual(balance_pc_color_tags('<color=red>A<color=blue>B</color>C'),
                         '<color=red>A<color=blue>B</color>C</color>')
        self.assertEqual(re.sub(r'</?color(?:=[^>]+)?>', '', source),
                         re.sub(r'</?color(?:=[^>]+)?>', '', expected))

    def test_short_effect_is_valid_but_subject_only_is_not(self):
        self.assertTrue(is_usable_modifier_description("Plants take 1.5x damage"))
        self.assertTrue(is_usable_modifier_description("Lose 75 points of Luck"))
        for text in ("", "TODO", "未翻译", "Buckshot Commando Zombie: ",
                     "<color=red>Buckshot Commando Zombie</color>：", None):
            self.assertFalse(is_usable_modifier_description(text))

    def test_structured_modifier_validation_cannot_be_bypassed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strings = root / "Localization/English/Strings"
            dumps = root / "Dumps"
            strings.mkdir(parents=True)
            dumps.mkdir()
            source = {"debuffs": {
                "1": {"name": "", "desc": "完整：效果"},
                "2": {"name": "", "desc": "未完：效果"},
                "3": {"name": "", "desc": "无名：效果"},
            }, "unlocks": {"1": {"name": "", "desc": "解锁植物"}}}
            target = {"debuffs": {
                "1": {"name": "Brittle Branches", "desc": "Plants take 1.5x damage"},
                "2": {"name": "Undead March", "desc": "Buckshot Commando Zombie: "},
                "3": {"name": "", "desc": "Plants take 1.5x damage"},
            }, "unlocks": {"1": {"name": "", "desc": "Unlock Plant"}}}
            for path, payload in ((dumps / "travel_buffs.json", source),
                                  (strings / "travel_buffs.json", target)):
                path.write_text(json.dumps(payload), encoding="utf-8")
            exact, _, _, _ = load_pc_translations(strings, include_android_fallbacks=False)
            self.assertEqual(exact, {"完整：效果": "Brittle Branches：\nPlants take 1.5x damage",
                                     "解锁植物": "Unlock Plant"})

    def test_unreviewed_bug_note_and_placeholders_still_rejected(self):
        for text in ("currently bugged", "TODO", "Attack range doubles (currently bugged and does nothing)"):
            self.assertFalse(is_usable_pc_translation(text))
        for text in ("Attack damage 未翻译", "English instructions\nSpecial Thanks: 作者", "TODO\nSpecial Thanks: 作者"):
            self.assertFalse(is_usable_pc_translation(text))
            self.assertFalse(usable_metadata_text(text))

    def test_reviewed_pc_import_rejects_incomplete_or_changed_placeholders(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.json"
            payload = {"format_version": 1, "pc_commit": "a" * 40, "records": [
                {"section": "unlocks", "id": "14", "source": "数量{0:F2}", "translation": "Count {0:F2}"}
            ]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_reviewed_pc_records(path), {"数量{0:F2}": "Count {0:F2}"})
            for invalid in ("TODO", "Count {0}", "Count {1:F2}"):
                payload["records"][0]["translation"] = invalid
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_reviewed_pc_records(path)

    def test_pc_regex_beats_old_android_name(self):
        source = "\u7532 challenge"
        target, method = translate_literal(
            source, {"\u7532": "Current PC Name"}, {"\u7532"},
            {source: ("Old Android Name Challenge", "old")},
            [rule(r"^(.+) challenge$", "{0} Challenge")],
        )
        self.assertEqual((target, method), ("Current PC Name Challenge", "pc_regex"))

    def test_partial_damage_rule_cannot_erase_description(self):
        source = "Zombie name\nDamage: High\nSpecial: armored"
        self.assertEqual(
            translate_complete_pc_literal(source, {}, [rule(r"Damage: (\w+)", "Attack: {0}")]),
            (source, None),
        )

    def test_csharp_argument_order_comes_from_pc(self):
        source = "Price {0}; item {1}"
        self.assertEqual(
            translate_complete_pc_literal(source, {}, [rule(r"^Price (\d+); item (\d+)$", "Buy {1} for {0}")]),
            ("Buy {1} for {0}", "pc_regex_csharp_template"),
        )

    def test_stat_bonus_is_not_a_fusion_recipe(self):
        source = "Damage+200%"
        self.assertEqual(
            translate_complete_pc_literal(source, {}, [rule(r"^(.+)[+](.+)$", "You haven't discovered this plant yet! {0} + {1}")]),
            (source, None),
        )
        source = "\u7532+200%"
        self.assertEqual(
            translate_literal(source, {"\u7532": "Damage"}, {"\u7532"}, {},
                              [rule(r"^(.+)[+](.+)$", "You haven't discovered this plant yet! {0} + {1}")]),
            (source, None),
        )

    def test_existing_english_does_not_hide_original_pc_key(self):
        changes = []
        self.assertEqual(
            prefer_pc_tree({"name": "source key"}, {"name": "Old English"}, {"source key": "PC English"}, [], changes),
            {"name": "PC English"},
        )
        self.assertEqual(len(changes), 1)

    def test_missing_pc_translation_does_not_revert_existing_english(self):
        self.assertEqual(
            prefer_pc_tree({"name": "source"}, {"name": "Historical English"}, {}, [], []),
            {"name": "Historical English"},
        )

    def test_translation_cannot_unhide_a_shipped_label(self):
        deferred = []
        self.assertEqual(
            prefer_pc_tree("source", "<size=0>Hidden text", {"source": "PC text"}, [], [], deferred=deferred),
            "<size=0>Hidden text",
        )
        self.assertEqual(len(deferred), 1)

    def test_variant_recipe_suffix_is_not_a_copied_placeholder(self):
        self.assertFalse(repeated_narrative_is_placeholder({"Shared body.", "Shared body.\nRecipe: A + B"}))
        self.assertTrue(repeated_narrative_is_placeholder({"First unrelated body.", "Second unrelated body."}))

    def test_close_button_context_is_preserved(self):
        self.assertIsNotNone(ui_exception("Close", ["text", "Goback", "Menu"], "Disabled"))
        self.assertIsNone(ui_exception("Old Plant Name", ["Name", "Challenge"], "Current PC Name"))


if __name__ == "__main__":
    unittest.main()
