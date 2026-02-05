from config.atb_simulator_presets import ATB_MONSTER_LIBRARY, build_full_preset
from domain.speed_optimizer_detail import (
    RequiredOrder,
    _build_enemy_mirror,
    _build_detail_preset,
    _resolve_enemy_baseline_rune_speed,
    _build_section1_overrides,
    _find_minimum_rune_speed,
    _matches_required_order,
    _resolve_required_order,
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
    assert overrides[a1_key]["rune_speed"] == 40
    assert a2_key not in overrides


def test_preset_mapping_rules_for_offsets():
    preset = build_full_preset("Preset C")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset C",
        allies,
        enemies,
        input_1=100,
        input_2=0,
        input_3=0,
        allow_enemy_fallback=False,
    )
    assert overrides[allies[1]["key"]]["rune_speed"] == 100

    preset = build_full_preset("Preset D")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset D",
        allies,
        enemies,
        input_1=100,
        input_2=0,
        input_3=0,
        allow_enemy_fallback=False,
    )
    assert overrides[allies[1]["key"]]["rune_speed"] == 99

    preset = build_full_preset("Preset E")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset E",
        allies,
        enemies,
        input_1=100,
        input_2=0,
        input_3=0,
        allow_enemy_fallback=False,
    )
    assert overrides[allies[1]["key"]]["rune_speed"] == 101

    preset = build_full_preset("Preset F")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset F",
        allies,
        enemies,
        input_1=100,
        input_2=0,
        input_3=0,
        allow_enemy_fallback=False,
    )
    assert overrides[allies[0]["key"]]["rune_speed"] == 98

    preset = build_full_preset("Preset G")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset G",
        allies,
        enemies,
        input_1=100,
        input_2=0,
        input_3=0,
        allow_enemy_fallback=False,
    )
    assert overrides[allies[0]["key"]]["rune_speed"] == 98


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
    assert source == "input_1"
    assert effective == 10
    enemy = _build_enemy_mirror("Preset B", allies, overrides, enemy_baseline_rune_speed=effective)
    assert enemy["rune_speed"] == 10


def test_enemy_baseline_resolution_default_and_override():
    source_default, speed_default = _resolve_enemy_baseline_rune_speed("Preset A", input_1=120, input_3=None)
    assert source_default == "input_1"
    assert speed_default == 120

    source_override, speed_override = _resolve_enemy_baseline_rune_speed("Preset A", input_1=120, input_3=95)
    assert source_override == "input_3"
    assert speed_override == 95


def test_enemy_baseline_direct_assignment_not_additive():
    preset = build_full_preset("Preset B")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")

    overrides, source, effective = _build_section1_overrides(
        "Preset B",
        allies,
        enemies,
        input_1=120,
        input_2=20,
        input_3=80,
        allow_enemy_fallback=False,
    )
    assert source == "input_3"
    assert effective == 80

    enemy = _build_enemy_mirror("Preset B", allies, overrides, enemy_baseline_rune_speed=effective)
    assert enemy["rune_speed"] == 80


def test_input_3_lower_than_input_1_does_not_force_no_valid():
    result_default = build_section1_detail_cached("Preset C", 120, 20, None, None, False)
    result_lower_enemy = build_section1_detail_cached("Preset C", 120, 20, 80, None, False)

    assert result_default.status == result_lower_enemy.status
    assert result_lower_enemy.enemy_rune_speed_source == "input_3"
    assert result_lower_enemy.enemy_rune_speed_effective == 80


def test_input_3_higher_than_input_1_uses_override_baseline():
    result_higher_enemy = build_section1_detail_cached("Preset C", 120, 20, 170, None, False)
    assert result_higher_enemy.enemy_rune_speed_source == "input_3"
    assert result_higher_enemy.enemy_rune_speed_effective == 170


def test_preset_e_uses_dark_harg():
    preset = build_full_preset("Preset E")
    assert preset["allies"][1]["key"] == "dark_harg"


def test_preset_library_rune_speed_adjustments():
    assert ATB_MONSTER_LIBRARY["water_dancer"]["rune_speed"] == 220
    assert ATB_MONSTER_LIBRARY["water_ciri"]["rune_speed"] == 220
    assert ATB_MONSTER_LIBRARY["fire_centa"]["rune_speed"] == 220


def test_preset_a_objective_uses_unit_labels():
    result = build_section1_detail_cached("Preset A", 10, 20, None, None, False)
    assert "water_pumpkin" in result.objective
    assert "dark_archer" in result.objective
    assert "Enemy (Mirrored" in result.objective


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
        assert len(table) == 15
        assert [row["tick"] for row in table] == list(range(1, 16))
        assert {"tick", "A1", "A2", "A3", "E", "act"}.issubset(table[0].keys())
        assert "act_speed" not in table[0]
        assert result.tick_headers is not None
        assert len(result.tick_headers) == 4


def test_tick_table_headers_include_base_rune():
    result = build_section1_detail_cached("Preset A", 10, 20, None, None, False)
    if result.status != "OK":
        return
    table = result.tick_atb_table
    assert table is not None
    assert result.tick_headers is not None
    assert all("(" in header and "+" in header for header in result.tick_headers)


def test_preset_a_min_cut_respects_order():
    preset = build_full_preset("Preset A")
    allies, _ = prefix_monsters(preset["allies"], prefix="A")
    enemies, _ = prefix_monsters(preset["enemies"], prefix="E")
    overrides, _, _ = _build_section1_overrides(
        "Preset A",
        allies,
        enemies,
        input_1=10,
        input_2=20,
        input_3=None,
        allow_enemy_fallback=True,
    )
    enemy_mirror = _build_enemy_mirror("Preset A", allies, overrides, enemy_baseline_rune_speed=10)
    detail_preset, detail_keys = _build_detail_preset(preset, allies, enemy_mirror)
    required_order = _resolve_required_order("Preset A", detail_keys)
    assert required_order is not None
    min_speed = _find_minimum_rune_speed(
        detail_preset,
        required_order,
        overrides,
        detail_keys["a3"],
        effect=0,
        start_speed=150,
        deadline=None,
        debug=None,
    )
    if min_speed is None:
        result = build_section1_detail_cached("Preset A", 10, 20, None, None, False)
        assert result.status == "NO VALID SOLUTION"
        return
    overrides[detail_keys["a3"]] = {"rune_speed": min_speed, "speedIncreasingEffect": 0}
    matched, _, _ = _matches_required_order(detail_preset, overrides, required_order)
    assert matched is True
