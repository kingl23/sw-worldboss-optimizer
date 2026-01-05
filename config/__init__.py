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
    "HP": 0.08 + 0.0067,
    "ATK": 1.2 + 0.10,
    "DEF": 1.2 + 0.10,
    "SPD": 8.0 + 0.6667, # 7.99 + 0.67
    "CR": 8.0 + 0.6667, # 8.67 + 0.6667
    "CD": 6.33 + 0.5286,
    "RES": 8.0 + 0.6667, # 7.85 + 0.65
    "ACC": 8.0 + 0.6667, # 7.85 + 0.65
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

# ---------- Set effects (matches core_scores.set_effect 1:1) ----------
# Convention:
# - "stat" values:
#     * 0 < x < 1 => percent of base stat (ch[stat_key] * x)
#     * x >= 1    => flat value (e.g., CR +12, CD +40, ACC +20, RES +20)
# - "fixed" is the fixed score bonus for the set (your fixedB)

SET_EFFECTS = {
    1: {   # Energy
        "need": 2,
        "stat": {"HP": 0.15},
        "fixed": 0,
    },
    2: {   # Guard
        "need": 2,
        "stat": {"DEF": 0.15},
        "fixed": 0,
    },
    3: {   # Swift
        "need": 4,
        "stat": {"SPD": 0.25},
        "fixed": 0,
    },
    4: {   # Blade
        "need": 2,
        "stat": {"CR": 12},
        "fixed": 0,
    },
    5: {   # Rage
        "need": 4,
        "stat": {"CD": 40},
        "fixed": 0,
    },
    6: {   # Focus
        "need": 2,
        "stat": {"ACC": 20},
        "fixed": 0,
    },
    7: {   # Endure
        "need": 2,
        "stat": {"RES": 20},
        "fixed": 0,
    },
    8: {   # Fatal
        "need": 4,
        "stat": {"ATK": 0.35},
        "fixed": 0,
    },

    10: {  # Despair
        "need": 4,
        "stat": {},
        "fixed": 299 + 10.10,
    },
    11: {  # Vampire
        "need": 4,
        "stat": {},
        "fixed": 291 + 24.00,
    },
    13: {  # Violent
        "need": 4,
        "stat": {},
        "fixed": 296 + 26.60,
    },

    14: {  # Nemesis
        "need": 2,
        "stat": {},
        "fixed": 124 + 10.50,
    },
    15: {  # Will
        "need": 2,
        "stat": {},
        "fixed": 123 + 10.00,
    },
    16: {  # Shield
        "need": 2,
        "stat": {},
        "fixed": 124 + 10.10,
    },
    17: {  # Revenge
        "need": 2,
        "stat": {},
        "fixed": 123 + 10.00,
    },
    18: {  # Destroy
        "need": 2,
        "stat": {},
        "fixed": 125 + 10.50,
    },

    19: {  # Fight
        "need": 2,
        "stat": {"ATK": 0.175},
        "fixed": 0,
    },
    20: {  # Determination
        "need": 2,
        "stat": {"DEF": 0.15},
        "fixed": 0,
    },
    21: {  # Enhance
        "need": 2,
        "stat": {"HP": 0.15},
        "fixed": 0,
    },

    22: {  # Accuracy (Immemorial set score in your code)
        "need": 2,
        "stat": {},
        "fixed": 160 + 13.10,
    },
    23: {  # Tolerance
        "need": 2,
        "stat": {},
        "fixed": 160 + 13.50,
    },
    24: {  # Seal
        "need": 2,
        "stat": {},
        "fixed": 160 + 13.50,
    },
}
