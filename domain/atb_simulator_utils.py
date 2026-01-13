import copy
from typing import Any, Dict, List, Tuple


def prefix_monsters(
    monsters: List[Dict[str, Any]],
    prefix: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    key_map: Dict[str, str] = {}
    for monster in monsters:
        original_key = monster.get("key")
        if original_key:
            key_map[original_key] = f"{prefix}|{original_key}"

    prefixed = []
    for monster in monsters:
        original_key = monster.get("key")
        prefixed_monster = copy.deepcopy(monster)
        if original_key and original_key in key_map:
            prefixed_monster["base_key"] = original_key
            prefixed_monster["key"] = key_map[original_key]
        prefixed_monster["skills"] = prefix_skill_targets(
            prefixed_monster.get("skills", []),
            key_map,
        )
        prefixed.append(prefixed_monster)

    return prefixed, key_map


def prefix_skill_targets(
    skills: List[Dict[str, Any]],
    key_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    updated = []
    for skill in skills:
        new_skill = copy.deepcopy(skill)
        target = new_skill.get("target")
        if target in key_map:
            new_skill["target"] = key_map[target]
        updated.append(new_skill)
    return updated
