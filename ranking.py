# ranking.py
from core_scores import score_unit_total


def rank_all_units(data, top_n=60):
    results = []

    for u in data.get("unit_list", []):
        r = score_unit_total(u)
        if r is not None:
            results.append(r)

    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results[:top_n]
