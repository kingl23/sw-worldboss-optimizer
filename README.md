# Summoners War – World Boss Rune Analyzer

## Overview
This project provides a Streamlit web app and a CLI tool that analyze Summoners War JSON exports to optimize World Boss rune builds and rank units by current strength. The SRP-focused structure separates domain logic, services, data access, and UI rendering while preserving existing behavior.

## Features
- Rune optimization for selected units (World Boss focused).
- Unit ranking using base stats, runes, set bonuses, artifacts, and skill-ups.
- Web UI for non-developers with JSON upload and on-screen results.
- Siege and artifact analysis tools gated by access keys.

## Installation
```bash
pip install -r requirements.txt
```

## Run
### Streamlit (Web UI)
```bash
streamlit run app.py
```
Upload your Summoners War JSON export in the World Boss or Artifact tabs to start analysis.

### CLI
```bash
python main.py
```
- Adjust `RUN_MODE` in `main.py` to `"opt"`, `"rank"`, or `"both"`.
- Update the keyword passed to `load_latest_json(...)` to match your JSON filename in the repo root or `attached_assets/`.

## Configuration
- **Core settings:** `config/settings.py` (e.g., `K_PER_SLOT`, `SKILLUP_COEF`, `TARGET_MASTER_IDS`).
- **Monster name mapping:** `resources/mapping.txt`.
- **Streamlit secrets:** supply `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `ACCESS_POLICY` for siege/artifact features.

## Folder Structure
```
.
├── app.py
├── main.py
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py
├── resources/
│   └── mapping.txt
├── data/
│   ├── __init__.py
│   ├── defense_data.py
│   ├── io.py
│   ├── siege_data.py
│   └── siege_trend.py
├── domain/
│   ├── scores.py
│   └── unit_repo.py
├── services/
│   ├── artifact_analysis.py
│   ├── optimizer.py
│   ├── ranking.py
│   └── wb_service.py
└── ui/
    ├── __init__.py
    ├── artifact_render.py
    ├── auth.py
    ├── siege_defense.py
    ├── siege_logs.py
    ├── siege_trend_chart.py
    ├── text_render.py
    ├── wb_tab.py
    └── worst_offense.py
```

## Troubleshooting
- **ModuleNotFoundError / missing dependencies:** run `pip install -r requirements.txt`.
- **Supabase errors in siege tools:** confirm `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set in Streamlit secrets.
- **Missing mapping file:** ensure `resources/mapping.txt` exists in the repository.
- **CLI JSON not found:** place the JSON in the repo root or `attached_assets/` and update the keyword in `main.py`.
