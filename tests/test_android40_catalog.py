import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from repair_android40_catalog import apply_fact, restore_protected, validate_catalog, known_types


class Android40CatalogTests(unittest.TestCase):
    def test_corrupted_nested_type_restored_without_losing_display_translation(self):
        source = {'plants': [{'buffs': [{'type': 'GameLevel.A+Buff'}]}],
                  'entries': [{'title': '标题', 'quality': 'gold'}]}
        current = {'plants': [{'buffs': [{'type': 'Find this plant by fusing A + Buff'}]}],
                   'entries': [{'title': 'Title', 'quality': 'gold'}]}
        changes = []
        repaired = restore_protected(source, current, 'ShootingAlmanacIndex', changes=changes)
        self.assertEqual(repaired['plants'], source['plants'])
        self.assertEqual(repaired['entries'][0]['title'], 'Title')
        self.assertEqual(len(changes), 1)
        self.assertNotEqual(current['plants'], source['plants'])

    def test_catalog_validation_checks_reflection_target_exists(self):
        catalog = {'plants': [{'configType': 'GameLevel.A', 'buffs': [{'type': 'GameLevel.A+Buff'}]}],
                   'roots': ['A'], 'entries': []}
        dump = '// Namespace: GameLevel\npublic class A : Base\nprivate class A.Buff : Base'
        self.assertEqual(validate_catalog(catalog, catalog, dump)['reflection_references'], 2)
        with self.assertRaises(AssertionError):
            validate_catalog(catalog, catalog, '// Namespace: GameLevel\npublic class A : Base')

    def test_dumper_nested_type_inherits_following_owner_namespace(self):
        dump = '// Namespace: \nprivate class A.Buff : Base\n// Namespace: GameLevel\npublic class A : Base'
        self.assertIn('GameLevel.A+Buff', known_types(dump))

    def test_reviewed_fact_does_not_override_changed_source_or_pc_wording(self):
        source = '20/2.25秒'
        rule = {'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'before': '20/1.5s', 'after': '20/2.25s'}
        self.assertEqual(apply_fact(source, rule['before'], rule), (rule['after'], 'corrected'))
        self.assertEqual(apply_fact(source, 'New upstream wording', rule)[0], 'New upstream wording')
        self.assertEqual(apply_fact('20/3秒', rule['before'], rule)[0], rule['before'])

    def test_protected_data_changes_fail_even_if_json_shape_is_valid(self):
        with self.assertRaises(AssertionError):
            restore_protected({'schemaVersion': 4}, {'schemaVersion': 5}, 'ShootingAlmanacIndex')
        source = '\ufeff([—'
        self.assertEqual(restore_protected(source, '\ufeff([-', 'LineBreaking Leading Characters'), source)


if __name__ == '__main__':
    unittest.main()
