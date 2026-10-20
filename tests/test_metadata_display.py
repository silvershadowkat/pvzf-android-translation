import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_metadata_display import normalize_display


class MetadataDisplayTests(unittest.TestCase):
    def test_closes_pc_styles_on_complete_display_string(self):
        self.assertEqual(normalize_display("速度 {0:F2}", "<size=75%>Speed {0:F2}"),
                         "<size=75%>Speed {0:F2}</size>")

    def test_preserves_runtime_fragments_and_internal_keys(self):
        self.assertEqual(normalize_display("<color=red>攻击", "<color=red>Attack"),
                         "<color=red>Attack")
        self.assertEqual(normalize_display("升级", "Upgrade"), "升级")

    def test_rejects_changed_numeric_format(self):
        with self.assertRaises(ValueError):
            normalize_display("速度 {0:F2}", "Speed {0}")
