#!/usr/bin/env python3
"""Regression tests for release-critical translation merge behavior."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_unity_text_translation import (  # noqa: E402
    merge_android_almanac,
    merge_android_detail_strings,
)
from overlay_text_assets import (  # noqa: E402
    EM_DASH,
    normalize_android_almanac_text_asset,
    normalize_overlay_text_asset,
)


class AlmanacMergeSafetyTests(unittest.TestCase):
    def merge(self, official_plants, translated_plants):
        source = json.dumps({"plants": official_plants}, ensure_ascii=False)
        translated = json.dumps({"plants": translated_plants}, ensure_ascii=False)
        merged, counts = merge_android_almanac(
            "LawnStrings", source, source, translated, {}
        )
        return json.loads(merged)["plants"], counts

    def test_repeated_cost_is_not_treated_as_placeholder(self):
        official = [
            {"seedType": 1, "name": "甲", "cost": "阳光: 125", "info": "说明甲"},
            {"seedType": 2, "name": "乙", "cost": "阳光: 125", "info": "说明乙"},
        ]
        translated = [
            {"seedType": 1, "name": "A", "cost": "Cost: 125 Sun", "info": "First description"},
            {"seedType": 2, "name": "B", "cost": "Cost: 125 Sun", "info": "Second description"},
        ]

        merged, counts = self.merge(official, translated)

        self.assertEqual([item["cost"] for item in merged], ["Cost: 125 Sun"] * 2)
        self.assertEqual(counts["pc_placeholder_fields_rejected"], 0)

    def test_copied_narrative_placeholder_is_rejected(self):
        official = [
            {"seedType": 1, "name": "甲", "cost": "阳光: 25", "info": "说明甲"},
            {"seedType": 2, "name": "乙", "cost": "阳光: 50", "info": "说明乙"},
        ]
        translated = [
            {"seedType": 1, "name": "A", "cost": "Cost: 25 Sun", "info": "Copied placeholder prose"},
            {"seedType": 2, "name": "B", "cost": "Cost: 50 Sun", "info": "Copied placeholder prose"},
        ]

        merged, counts = self.merge(official, translated)

        self.assertEqual([item["info"] for item in merged], ["说明甲", "说明乙"])
        self.assertEqual([item["cost"] for item in merged], ["Cost: 25 Sun", "Cost: 50 Sun"])
        self.assertEqual(counts["pc_placeholder_fields_rejected"], 2)


class MechanicsMergeSafetyTests(unittest.TestCase):
    def test_current_exact_key_wins_over_historical_alias(self):
        source = json.dumps(
            {
                "details": [
                    {"type": "植物机制", "title": "植物机制-护盾", "text": "旧说明"}
                ]
            },
            ensure_ascii=False,
        )

        merged, counts = merge_android_detail_strings(
            source,
            {"植物机制-护盾": "Current shield mechanics."},
            {"植物机制-护盾": "Plant Mechanics - Shield"},
        )

        item = json.loads(merged)["details"][0]
        self.assertEqual(item["text"], "Current shield mechanics.")
        self.assertEqual(counts["untranslated_android_titles"], [])


class AndroidAlmanacLayoutSafetyTests(unittest.TestCase):
    def test_entity_almanac_size_tags_are_removed(self):
        source = json.dumps(
            {"plants": [{"info": "<size=36>Large</size> and <SIZE=90%>larger</SIZE>"}]}
        )

        normalized, removed = normalize_android_almanac_text_asset("LawnStrings", source)

        self.assertEqual(removed, 4)
        self.assertEqual(json.loads(normalized)["plants"][0]["info"], "Large and larger")

    def test_unrelated_text_asset_is_unchanged(self):
        source = '{"tips":"<size=18>Keep this override"}'

        normalized, removed = normalize_android_almanac_text_asset("Tutorial", source)

        self.assertEqual((normalized, removed), (source, 0))

    def test_overlay_normalizes_em_dash_separately(self):
        source = json.dumps(
            {"plants": [{"info": f"<size=36>A{EM_DASH}B</size>"}]},
            ensure_ascii=False,
        )

        normalized, size_tags, em_dashes = normalize_overlay_text_asset("LawnStrings", source)

        self.assertEqual((size_tags, em_dashes), (2, 1))
        self.assertEqual(json.loads(normalized)["plants"][0]["info"], "A-B")


if __name__ == "__main__":
    unittest.main()
