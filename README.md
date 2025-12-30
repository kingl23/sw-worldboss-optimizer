# Summoners War Analyzer

A Streamlit web app for analyzing Summoners War data. It combines local JSON analysis
(World Boss + artifacts) with Supabase-backed siege analytics and personal stats.

## ✨ Features

### World Boss
- Upload a Summoners War JSON export.
- Rank units by score.
- Optimize runes per unit and optionally apply the recommended build to the working data.
- Manual optimizer for specific Unit Master IDs.

### Artifact Analysis
- Upload a Summoners War JSON export.
- Build attribute and archetype matrices to surface best artifact combinations.

### Siege Analytics
- **Search Offense Deck**: look up offense matchups against a selected defense deck.
- **Best Defense**: ranked defense decks overall or by opponent guild.
- **Worst Offense**: identify defenses that most often beat offense decks.

### Personal Data
- Per-wizard record summary.
- Top offense/defense decks and hour-of-day distributions.

## 📁 Data Sources

### Local JSON Uploads
Used by **World Boss** and **Artifact Analysis** tabs.
- Expected to include `unit_list`, `runes`, and (optionally) `artifacts`.
- JSON is processed in-memory only.

### Supabase Tables
Used by **Siege Analytics** and **Personal Data** tabs.
- Requires Supabase credentials in Streamlit secrets.

## 🔐 Access Control

The sidebar accepts an **Access Key**. Keys are validated via `ACCESS_POLICY` in
Streamlit secrets. Each key maps to a list of enabled features.

Example `ACCESS_POLICY` structure:

```toml
ACCESS_POLICY = { "example-key" = ["world_boss", "artifact", "siege_battle", "siege_defense", "worst_offense", "personal_data"] }
```

## 🛠 Local Development

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.streamlit/secrets.toml` with the following values:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_ANON_KEY = "your-anon-key"
   ACCESS_POLICY = { "example-key" = ["world_boss", "artifact", "siege_battle", "siege_defense", "worst_offense", "personal_data"] }
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## 🧭 Project Structure

```
.
├── app.py              # Streamlit entry point
├── config/             # Global configuration
├── data/               # Data loaders/aggregations
├── domain/             # Core scoring/optimizer logic
├── services/           # Supabase and service helpers
├── ui/                 # Streamlit tabs/components
├── utils/              # Shared utilities
├── mapping.txt         # Monster name mapping
├── requirements.txt    # Python dependencies
```

## 📜 License

This project is provided for personal and analytical use.
No affiliation with Com2uS.
