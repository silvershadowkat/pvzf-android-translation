import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_pc_modifier_records import project_catalog_entries
from migrate_version_text import is_display_asset_field
from repair_android40_catalog import restore_protected


class PcModifierProjectionTests(unittest.TestCase):
    def setUp(self):
        self.sources = {"advancedBuffs": {
            "1": {"desc": "群攻-木桩：伤害60%"},
            "2": {"desc": "群攻-木桩：伤害100%"},
            "3": {"desc": "傲慢：伤害30%"},
        }}
        self.english = {"advancedBuffs": {
            "1": {"name": "Voodoo Dummy", "desc": "Damage 60%"},
            "2": {"name": "Voodoo Dummy - A", "desc": "Damage 100%"},
            "3": {"name": "High Grounds", "desc": "Damage 30%"},
        }}

    def project(self, entries):
        return project_catalog_entries({"entries": entries}, self.sources,
                                       self.english, lambda x: isinstance(x, str) and bool(x))

    def test_repeated_title_requires_complete_body_identity(self):
        rows = [{"title": "群攻-木桩", "description": "伤害100%", "category": "Tactics"},
                {"title": "群攻-木桩", "description": "伤害60%", "category": "Tactics"}]
        self.assertEqual([x["pc_id"] for x in self.project(rows)], ["2", "1"])
        rows[0]["description"] = "伤害50%"
        self.assertEqual([x["index"] for x in self.project(rows)], [1])

    def test_body_only_and_ambiguous_records_are_rejected(self):
        self.assertEqual(self.project([{"title": "别的技能", "description": "伤害60%"}]), [])
        self.english["advancedBuffs"]["1"]["desc"] = "Dummy Zombie:"
        self.assertEqual(self.project([{"title": "群攻-木桩", "description": "伤害60%"}]), [])
        self.english["advancedBuffs"]["1"]["desc"] = "Damage 60%"
        self.sources["advancedBuffs"]["4"] = {"desc": "群攻-木桩：伤害60%"}
        self.english["advancedBuffs"]["4"] = {"name": "Other", "desc": "Damage 60%"}
        self.assertEqual(self.project([{"title": "群攻-木桩", "description": "伤害60%"}]), [])

    def test_trial_category_prefix_is_display_only(self):
        entry = {"title": "试炼：傲慢", "description": "伤害30%", "category": "Trials",
                 "id": "Trials:傲慢", "group": "傲慢"}
        original = copy.deepcopy(entry)
        self.assertEqual(self.project([entry])[0]["title"], "High Grounds")
        self.assertEqual(entry, original)
        entry["category"] = "Tactics"
        self.assertEqual(self.project([entry]), [])

    def test_only_exact_override_path_is_display_prose(self):
        self.assertTrue(is_display_asset_field(
            "ShootingAlmanacIndex", ("plants", 0, "buffs", 0, "descriptionOverride")))
        for path in (("plants", 0, "buffs", 0, "type"),
                     ("plants", 0, "buffs", 0, "arguments", 0),
                     ("plants", 0, "descriptionOverride"),
                     ("entries", 0, "group"), ("entries", 0, "id")):
            self.assertFalse(is_display_asset_field("ShootingAlmanacIndex", path))
        source = {"plants": [{"buffs": [{"descriptionOverride": "伤害60%",
                                       "type": "GameLevel.Buff", "arguments": ["木桩"]}]}]}
        current = copy.deepcopy(source)
        current["plants"][0]["buffs"][0].update(descriptionOverride="Damage 60%", type="Bad")
        changes = []
        fixed = restore_protected(source, current, "ShootingAlmanacIndex", changes=changes)
        self.assertEqual(fixed["plants"][0]["buffs"][0]["descriptionOverride"], "Damage 60%")
        self.assertEqual(fixed["plants"][0]["buffs"][0]["type"], "GameLevel.Buff")
        self.assertEqual(len(changes), 1)
