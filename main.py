import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from config.settings import TARGET_MASTER_IDS, K_PER_SLOT
from data.io import load_latest_json
from services.optimizer import optimize_unit_best_runes
from services.ranking import rank_all_units
from ui.text_render import print_unit_optimizer_result, print_top_units

RUN_MODE = "both"


def main():
    """Run the CLI optimizer and ranking tasks."""
    data = load_latest_json("치즈라면-1124059")

    if RUN_MODE in ("opt", "both"):
        for mid in TARGET_MASTER_IDS:
            u, ch, runes, picked, base_score = optimize_unit_best_runes(data, mid, K_PER_SLOT)
            print_unit_optimizer_result(u, ch, runes, picked, base_score)

    if RUN_MODE in ("rank", "both"):
        results = rank_all_units(data, top_n=60)
        print_top_units(results, top_n=60)


if __name__ == "__main__":
    main()
