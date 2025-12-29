# main.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sw_helper.config import TARGET_MASTER_IDS, K_PER_SLOT
from sw_helper.shared.io_utils import load_latest_json
from sw_helper.worldboss.optimizer import optimize_unit_best_runes
from sw_helper.worldboss.ranking import rank_all_units
from sw_helper.worldboss.visualize import (
    print_unit_optimizer_result,
    print_top_units,
)

# ============================
# Select run mode
# ============================
RUN_MODE = "both"  # "opt", "rank", "both"
# ============================


def main():
    data = load_latest_json("치즈라면-1124059")

    # ---------- Optimizer ----------
    if RUN_MODE in ("opt", "both"):
        for mid in TARGET_MASTER_IDS:
            u, ch, runes, picked, base_score = optimize_unit_best_runes(data, mid, K_PER_SLOT)
            print_unit_optimizer_result(u, ch, runes, picked, base_score)

    # ---------- Ranking ----------
    if RUN_MODE in ("rank", "both"):
        results = rank_all_units(data, top_n=60)
        print_top_units(results, top_n=60)


if __name__ == "__main__":
    main()
