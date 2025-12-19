def get_unit_by_unit_id(data, unit_id: int):
    for u in data.get("unit_list", []):
        if int(u.get("unit_id", -1)) == int(unit_id):
            return u
    return None


def infer_occupied_types(data):
    equipped_type = None
    for u in data.get("unit_list", []):
        for r in (u.get("runes", []) or []):
            if "occupied_type" in r:
                equipped_type = int(r.get("occupied_type"))
                break
        if equipped_type is not None:
            break

    storage_type = None
    for r in (data.get("runes", []) or []):
        if "occupied_type" in r:
            storage_type = int(r.get("occupied_type"))
            break

    return equipped_type or 1, storage_type or 2


def apply_build_to_working_data(working_data, unit_id: int, new_runes):
    u = get_unit_by_unit_id(working_data, unit_id)
    if u is None:
        return False, "Target unit not found."

    equipped_type, storage_type = infer_occupied_types(working_data)
    old_runes = list(u.get("runes", []) or [])

    def rid(r):
        return r.get("rune_id")

    old_ids = {rid(r) for r in old_runes}
    new_ids = {rid(r) for r in new_runes}

    removed_ids = old_ids - new_ids
    added_ids = new_ids - old_ids

    storage = list(working_data.get("runes", []) or [])
    storage = [r for r in storage if rid(r) not in added_ids]

    removed_runes = [r for r in old_runes if rid(r) in removed_ids]
    storage.extend(removed_runes)

    for r in new_runes:
        if "occupied_id" in r:
            r["occupied_id"] = int(unit_id)
        if "occupied_type" in r:
            r["occupied_type"] = int(equipped_type)

    for r in removed_runes:
        if "occupied_id" in r:
            r["occupied_id"] = 0
        if "occupied_type" in r:
            r["occupied_type"] = int(storage_type)

    u["runes"] = list(new_runes)
    working_data["runes"] = storage

    return True, "Applied."
