# Summoners War Analyzer

## Overview
A web-based analyzer for Summoners War that optimizes World Boss rune builds and ranks units based on current strength.
The app focuses on practical, in-game decision support rather than theorycrafting.

👉 **Web App:**  [Open](https://sw-worldboss-optimizer-8revvqtpkhldxhho8zwhnf.streamlit.app/)

---

## What You Can Do
- Optimize rune builds for World Boss units
- Rank units by effective power (stats, runes, sets, artifacts, skill-ups)
- Analyze siege defense data and trends (access-controlled)
- Review artifact distributions and performance

---

## How to Use (Web App)

### 1. Open the Web App
Go to the URL above using a desktop browser.

### 2. Upload Your Summoners War JSON
- Export your game data as JSON (e.g., via SWEX).
- Upload the file in:
  - **World Boss** tab (rune optimization / ranking)
  - **Artifact** tab (artifact analysis)

### 3. Review Results
- Optimized rune recommendations
- Unit rankings with score breakdowns
- Tables and charts rendered directly in the browser

No local installation is required.

---

## Siege & Advanced Features
Some features (Siege defense statistics, trend analysis, worst offense review) require access authorization.

If enabled for your account:
- Enter the access key when prompted
- Data is loaded automatically from the backend

---

## Notes & Limitations
- This tool does **not** modify your game account.
- Results depend on the accuracy of the uploaded JSON.
- Large accounts may take a few seconds to process.

---

## For Developers (Optional)

This repository also includes:
- A Streamlit frontend (`app.py`)
- A CLI entry point (`main.py`)
- SRP-based separation of domain logic, services, data access, and UI

Configuration and internal structure are documented in the source code.
Secrets such as Supabase credentials are managed via Streamlit Cloud.

---

## Troubleshooting
- **App fails to load:** refresh the page and try again.
- **Siege features unavailable:** access may not be enabled for your account.
- **Unexpected results:** re-export your JSON and upload again.
