from config.atb_simulator_presets import build_full_preset
from domain.speed_optimizer_detail import (
    RequiredOrder,
    _build_enemy_mirror,
    _build_section1_overrides,
    _matches_required_order,
    build_section1_detail_cached,
)
from domain.atb_simulator_utils import prefix_monsters


def test_preset_mapping_rules_for_a2():
    preset = build_full_preset("Preset A")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset A",
        allies,
        enemies,
        input_1=10,
        input_2=20,
        input_3=30,
        allow_enemy_fallback=False,
    )
    a1_key = allies[0]["key"]
    a2_key = allies[1]["key"]
    assert a1_key not in overrides
    assert overrides[a2_key]["rune_speed"] == 59


def test_preset_mapping_rules_for_a1():
    preset = build_full_preset("Preset F")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset F",
        allies,
        enemies,
        input_1=42,
        input_2=7,
        input_3=30,
        allow_enemy_fallback=False,
    )
    a1_key = allies[0]["key"]
    a2_key = allies[1]["key"]
    assert overrides[a1_key]["rune_speed"] == 42
    assert a2_key not in overrides


def test_required_order_allows_a1_anywhere_for_preset_a():
    detail_preset = {
        "allies": [
            {
                "key": "a1",
                "name": "a1",
                "isAlly": True,
                "base_speed": 1500,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            },
            {
                "key": "a2",
                "name": "a2",
                "isAlly": True,
                "base_speed": 1400,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            },
            {
                "key": "a3",
                "name": "a3",
                "isAlly": True,
                "base_speed": 1300,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            },
        ],
        "enemies": [
            {
                "key": "e1",
                "name": "e1",
                "isAlly": False,
                "base_speed": 1200,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            }
        ],
        "allyEffects": {},
        "enemyEffects": {},
        "tickCount": 5,
    }
    required_order = RequiredOrder(mode="a2_a3_e", order=["a2", "a3", "e1"])
    matched, _, _ = _matches_required_order(detail_preset, {}, required_order)
    assert matched is True


def test_input_3_optional_and_enemy_mirror_default_speed():
    preset = build_full_preset("Preset B")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, source, effective = _build_section1_overrides(
        "Preset B",
        allies,
        enemies,
        input_1=10,
        input_2=20,
        input_3=None,
        allow_enemy_fallback=False,
    )
    assert source == "default"
    assert effective == 0
    enemy = _build_enemy_mirror("Preset B", allies, overrides, input_3=None)
    reference = allies[1]
    expected_rune_speed = overrides[reference["key"]]["rune_speed"]
    assert enemy["rune_speed"] == expected_rune_speed


def test_preset_e_uses_dark_harg():
    preset = build_full_preset("Preset E")
    assert preset["allies"][1]["key"] == "dark_harg"


def test_preset_a_objective_uses_unit_labels():
    result = build_section1_detail_cached("Preset A", 10, 20, None, None, False)
    assert "A2" in result.objective
    assert "A3" in result.objective
    assert "E" in result.objective


def test_all_presets_return_with_tick_tables():
    results = build_section1_detail_cached("Preset A", 10, 20, None, None, False)
    assert results.preset_name == "Preset A"
    all_results = [
        build_section1_detail_cached(preset_id, 10, 20, None, None, False)
        for preset_id in [
            "Preset A",
            "Preset B",
            "Preset C",
            "Preset D",
            "Preset E",
            "Preset F",
            "Preset G",
        ]
    ]
    preset_ids = {result.preset_name for result in all_results}
    assert preset_ids == {"Preset A", "Preset B", "Preset C", "Preset D", "Preset E", "Preset F", "Preset G"}
    for result in all_results:
        assert result.effect_table is not None
        ranges = result.effect_table.ranges
        assert ranges
        range_starts = []
        range_ends = []
        for entry in ranges:
            span = entry.get("Effect Range", "")
            if "~" in span:
                start, end = span.split("~")
            else:
                start = end = span
            range_starts.append(int(start))
            range_ends.append(int(end))
        assert min(range_starts) == 0
        assert max(range_ends) == 60
        if result.status != "OK":
            assert result.tick_atb_table is None
            assert result.tick_atb_table_step1 is None
            assert result.tick_atb_table_step2 is None
            continue
        assert result.tick_atb_table_step1 is None
        assert result.tick_atb_table_step2 is None
        assert result.tick_atb_table is not None
        table = result.tick_atb_table
        assert len(table) == 16
        assert [row["tick"] for row in table] == list(range(16))
        assert {"tick", "A1", "A2", "A3", "E", "act"}.issubset(table[0].keys())
        assert "act_speed" not in table[0]
