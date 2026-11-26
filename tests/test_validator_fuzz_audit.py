import unittest

from app.engine.validator import audit_character_sheet, run_fuzz_audit


class TestValidatorFuzzAudit(unittest.TestCase):
    def test_synthetic_and_broken_sheet_is_flagged(self):
        broken_sheet = {
            "name": "Broken Tester",
            "level": 10,
            "ancestry": "Dwarf",
            "heritage": "Rock Dwarf",
            "background": "Scholar",
            "character_class": "Fighter",
            "attributes": {"str": 5, "dex": 3, "con": 3, "int": 1, "wis": 2, "cha": 0},
            "perception": {"rank": 4, "rank_letter": "E", "modifier": 16},
            "all_skills": [
                {"name": "Athletics", "attribute": "STR", "rank": 6, "rank_letter": "M", "modifier": 10},
                {"name": "Diplomacy", "attribute": "CHA", "rank": 0, "rank_letter": "U", "modifier": 0},
            ],
            "equipment": {
                "strikes": [
                    {
                        "name": "+1 Striking Longsword",
                        "attack_bonus": "+22",
                        "map_second": "+17",
                        "map_third": "+12",
                        "damage_dice": "2d8+5",
                        "damage_type": "Slashing",
                        "traits": ["Versatile P"],
                    },
                    {
                        "name": "Horn",
                        "attack_bonus": "+17",
                        "map_second": "+12",
                        "map_third": "+7",
                        "damage_dice": "1d6+5",
                        "damage_type": "Piercing",
                        "traits": ["Unarmed"],
                    },
                    {
                        "name": "Horns",
                        "attack_bonus": "+17",
                        "map_second": "+12",
                        "map_third": "+7",
                        "damage_dice": "1d8+5",
                        "damage_type": "Piercing",
                        "traits": ["Unarmed"],
                    },
                ]
            },
            "feats": [
                {"id": "anc-feat-dwarf-5", "name": "Dwarf Resiliency", "category": "Ancestry (Level 5)", "traits": ["dwarf"], "description": ""},
                {"id": "hobnobber", "name": "Hobnobber", "category": "Skill (Level 2)", "traits": ["skill"], "description": ""},
                {"id": "beastmaster-dedication", "name": "Beastmaster Dedication", "category": "Archetype (Beastmaster)", "traits": ["archetype", "dedication"], "description": ""},
                {"id": "sentinel-dedication", "name": "Sentinel Dedication", "category": "Archetype (Sentinel)", "traits": ["archetype", "dedication"], "description": ""},
            ],
        }
        res = audit_character_sheet(broken_sheet)
        self.assertFalse(res.passed)
        codes = {i.code for i in res.issues}
        self.assertIn("synthetic_placeholder_feat", codes)
        self.assertIn("skill_modifier_mismatch", codes)
        self.assertIn("missing_feat_granted_skill", codes)
        self.assertIn("dedication_two_feat_violation", codes)
        self.assertIn("duplicate_strike", codes)
        self.assertIn("missing_or_wrong_potency_rune", codes)

    def test_fuzz_audit_50_builds_executes_without_crashes(self):
        report = run_fuzz_audit(num_builds=50, min_level=1, max_level=15, seed=2026)
        self.assertEqual(report["total_builds"], 50)
        self.assertEqual(report["crashes"], [])


if __name__ == "__main__":
    unittest.main()
