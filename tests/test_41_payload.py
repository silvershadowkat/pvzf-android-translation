import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_41_payload import reviewed_format_rule


class ReviewedTemplateTests(unittest.TestCase):
    def test_rendered_counters_match_without_changing_source_keys(self):
        pattern, target = reviewed_format_rule('匹配到{0}项，请用完整名称或编号', 'Found {0} matches. Use the full name or ID.')
        self.assertEqual(re.fullmatch(pattern, '匹配到12项，请用完整名称或编号').groups(), ('12',))
        self.assertIsNone(re.fullmatch(pattern, '前缀匹配到12项，请用完整名称或编号'))
        self.assertEqual(target, 'Found {0} matches. Use the full name or ID.')

    def test_reordered_fields_and_repeated_values_keep_identity(self):
        pattern, target = reviewed_format_rule('剩余{1}，损失{0}，再报{1}2', 'Lost {0}; {1} remain')
        self.assertEqual(re.fullmatch(pattern, '剩余50，损失3，再报502').groups(), ('50', '3'))
        self.assertIsNone(re.fullmatch(pattern, '剩余50，损失3，再报402'))
        self.assertEqual(target, 'Lost {1}; {0} remain')

    def test_literals_are_not_treated_as_regex_operators(self):
        pattern, _ = reviewed_format_rule('[格位]+{0}.', 'Slot {0}')
        self.assertIsNotNone(re.fullmatch(pattern, '[格位]+5.'))
        self.assertIsNone(re.fullmatch(pattern, '格位555x'))

    def test_invalid_replacement_field_fails_closed(self):
        with self.assertRaises(ValueError):
            reviewed_format_rule('数量{0}', 'Count {1}')

    def test_static_labels_need_no_runtime_rule(self):
        self.assertIsNone(reviewed_format_rule('保存进度', 'Save Progress'))


if __name__ == '__main__':
    unittest.main()
