# config/__init__.py

# Optimizer targets
TARGET_MASTER_IDS = []

# Optimizer pruning
K_PER_SLOT = 10

# Rune / stat names
SET_NAME = {
    1: "Energy",
    2: "Guard",
    3: "Swift",
    4: "Blade",
    5: "Rage",
    6: "Focus",
    7: "Endure",
    8: "Fatal",
    10: "Despair",
    11: "Vampire",
    13: "Violent",
    14: "Nemesis",
    15: "Will",
    16: "Shield",
    17: "Revenge",
    18: "Destroy",
    19: "Fight",
    20: "Determination",
    21: "Enhance",
    22: "Accuracy",
    23: "Tolerance",
    24: "Seal",
    25: "Intangible",
    99: "Immemorial",
}

EFF_NAME = {
    1: "HP",
    2: "HP%",
    3: "ATK",
    4: "ATK%",
    5: "DEF",
    6: "DEF%",
    8: "SPD",
    9: "CR",
    10: "CD",
    11: "RES",
    12: "ACC"
}


# ---------- Scoring coefficients (single source of truth) ----------

# Skill-up coefficient
SKILLUP_COEF = 53.93

STAT_KEYS = ("HP", "ATK", "DEF", "SPD", "CR", "CD", "RES", "ACC")

STAT_COEF = {
    "HP": 0.08 + 0.01,
    "ATK": 1.2 + 0.10,
    "DEF": 1.2 + 0.10,
    "SPD": 7.99 + 0.68,
    "CR": 8.67 + 0.67,
    "CD": 6.32 + 0.53,
    "RES": 7.85 + 0.65,
    "ACC": 7.85 + 0.65,
}

# Rune effect type -> (stat_key, is_percent)
TYP_TO_STAT_KEY = {
    1: ("HP", False),
    2: ("HP", True),
    3: ("ATK", False),
    4: ("ATK", True),
    5: ("DEF", False),
    6: ("DEF", True),
    8: ("SPD", False),
    9: ("CR", False),
    10: ("CD", False),
    11: ("RES", False),
    12: ("ACC", False),
}

