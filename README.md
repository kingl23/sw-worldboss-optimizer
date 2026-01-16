# Summoners War Analyzer

A Streamlit-based analyzer for Summoners War JSON exports. It brings **World Boss rune analysis**, **artifact stats**, and **Guild Siege analytics** into one dashboard.

## ✅ Key Features

- **World Boss Analysis**
  - Rank all units by score
  - Recommend and apply best rune builds for a unit
  - Manual optimizer for specific monster IDs
- **Artifact Analysis**
  - Attribute/Archetype top-option matrices
- **Guild Siege Tools**
  - **Search Offense Deck**: offense win-rate lookup for a defense
  - **Best Defense**: defense deck stats (overall / by opponent guild)
  - **Worst Offense**: loss-focused offense analysis
- **Personal Data**
  - Personal summary and data lookup

## Usage

This project is available as a web application powered by Streamlit.

👉 **Live Demo**: https://sw-apper-caaasrmldj9rxdpq4dfbjd.streamlit.app/

Open the link in your browser to explore the features without local setup.


## 🔗 Links

- Streamlit Docs: https://docs.streamlit.io
- Streamlit Community Cloud: https://streamlit.io/cloud
- Supabase: https://supabase.com

## 📁 Data Input

- Upload a **JSON export** from Summoners War.
- Uploaded files are **not persisted** and are used only in-session.

## 🧰 Local Development

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure Streamlit secrets

The Siege/Personal tabs require Supabase access. Create a local secrets file:

```toml
# .streamlit/secrets.toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_ANON_KEY"

# Access key policy (unlock specific gated features)
# Use "all" to allow everything for a key.
[ACCESS_POLICY]
"my-secret-key" = ["all"]
```

### 4) Run the app

```bash
streamlit run app.py
```

Open the local URL printed in the terminal.

## 🗂️ Project Structure

```
.
├── app.py              # Streamlit entry
├── config/             # global config & constants
├── data/               # data loaders/aggregations
├── domain/             # scoring/optimization/ranking logic
├── services/           # external integrations (Supabase, etc.)
├── ui/                 # Streamlit UI components
├── utils/              # shared utilities
├── requirements.txt    # Python dependencies
```

## 🔐 Access Key Policy

Some tabs require an access key.

- Input location: **left sidebar**
- Policy definition: `st.secrets.get("ACCESS_POLICY", {})`
- Example: `"my-secret-key" = ["world_boss", "siege_battle"]`

## ⚠️ Disclaimer

- This is an **analysis/utility tool**, not for game automation.
- Not affiliated with Com2uS.
