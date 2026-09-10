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
