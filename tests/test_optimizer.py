from domain.optimizer import optimize_unit_best_runes_by_unit_id


def test_optimizer_ignores_invalid_or_out_of_range_slot_numbers():
    data = {
        "unit_list": [
            {
                "unit_id": 1,
                "unit_master_id": 10101,
                "con": 100,
                "atk": 100,
                "def": 100,
                "spd": 100,
                "critical_rate": 15,
                "critical_damage": 50,
                "resist": 15,
                "accuracy": 0,
                "runes": [
                    {"rune_id": 1, "slot_no": 1, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
                    {"rune_id": 2, "slot_no": 2, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
                    {"rune_id": 3, "slot_no": 3, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
                    {"rune_id": 4, "slot_no": 4, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
                    {"rune_id": 5, "slot_no": 5, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
                    {"rune_id": 6, "slot_no": 6, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
                ],
            }
        ],
        "runes": [
            {"rune_id": 100, "slot_no": None, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
            {"rune_id": 101, "slot_no": "invalid", "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
            {"rune_id": 102, "slot_no": 7, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
            {"rune_id": 103, "slot_no": 0, "set_id": 1, "upgrade_curr": 15, "pri_eff": [8, 20], "prefix_eff": [0, 0], "sec_eff": []},
        ],
    }

    unit, _, runes, picks, _ = optimize_unit_best_runes_by_unit_id(data, target_unit_id=1, k=1)

    assert unit is not None
    assert len(runes) == 10
    assert len(picks) == 6
