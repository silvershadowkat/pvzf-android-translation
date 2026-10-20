import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_metadata_translation import find_pc_exact_remnants


class MetadataRemnantTests(unittest.TestCase):
    def test_runtime_keys_do_not_trigger_display_translation_requirement(self):
        exact = {"升级": "Upgrade", "护盾保护": "Enchanted Shield",
                 "爆炸保护": "Blast Protection", "返回": "Back"}
        literals = [SimpleNamespace(text=text) for text in exact]
        self.assertEqual(find_pc_exact_remnants(literals, exact, set(exact), set()),
                         [{"index": 3, "source": "返回", "expected": "Back"}])

    def test_only_explicitly_preserved_display_slots_are_exempt(self):
        literals = [SimpleNamespace(text="返回"), SimpleNamespace(text="返回")]
        self.assertEqual(find_pc_exact_remnants(literals, {"返回": "Back"}, {"返回"}, {0}),
                         [{"index": 1, "source": "返回", "expected": "Back"}])
