from config.atb_simulator_presets import build_full_preset
from domain.speed_optimizer_detail import (
    RequiredOrder,
    _build_case_display,
    _build_enemy_mirror,
    _build_section1_overrides,
    _matches_required_order,
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


def test_case_display_uses_unit_names():
    detail_preset = {
        "allies": [
            {"key": "a1", "name": "Alpha", "isAlly": True, "base_speed": 1500, "rune_speed": 0},
            {"key": "a2", "name": "Bravo", "isAlly": True, "base_speed": 1400, "rune_speed": 0},
            {"key": "a3", "name": "Charlie", "isAlly": True, "base_speed": 1300, "rune_speed": 0},
        ],
        "enemies": [
            {"key": "e1", "name": "Echo", "isAlly": False, "base_speed": 1200, "rune_speed": 0}
        ],
        "allyEffects": {"lead": 24, "tower": 15},
        "enemyEffects": {"lead": 24, "tower": 15},
        "tickCount": 5,
    }
    detail_keys = {"a1": "a1", "a2": "a2", "a3": "a3", "e_fast": "e1"}
    required_order = RequiredOrder(mode="a2_a3_e", order=["a2", "a3", "e1"])
    case_display = _build_case_display(
        "Preset A",
        detail_preset,
        detail_keys,
        required_order,
        overrides={},
    )
    assert "Bravo" in case_display["display_title"]
    assert "Charlie" in case_display["display_title"]
    assert "Mirrored from Bravo" in case_display["display_title"]
