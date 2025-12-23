# Summoners War – World Boss Rune Analyzer

This project is a **Streamlit-based web tool** that analyzes Summoners War JSON data to:

- Optimize rune sets for specific units (World Boss–focused)
- Rank all units by their current overall strength
- Allow **non-developers** to upload a JSON file and view results easily in a browser

The app is deployed on **Streamlit Cloud** and requires **no local setup** for users.

---

## 🔗 Live App

👉 **Access the app here:**

[https://sw-worldboss-optimizer-9y5rftyfwi36gvkn2bnhi4.streamlit.app/](https://sw-worldboss-optimizer-ekrcqcwreqinmzdnrdrjih.streamlit.app/)

Anyone with this link can use the tool directly.

---

## ✨ Features

### 1. Rune Optimizer
- Finds the best rune combination for selected unit(s)
- Uses:
  - Rune main/sub stat scoring
  - Set bonuses
  - Pruning with top-K candidates per slot
- Outputs:
  - Slot-by-slot rune breakdown
  - Final stat summary
  - Total score

### 2. Current Unit Ranking
- Calculates the current strength of **all units with equipped runes**
- Considers:
  - Base stats
  - Rune stats
  - Set bonuses
  - Artifacts
  - Skill-ups
- Displays **Top N units by total score**

### 3. Web-Based UI
- Upload JSON file
- Choose mode:
  - Optimizer
  - Ranking
  - Both
- View results instantly in the browser
- No coding knowledge required

---

## 📁 Input Data

### Required
- A Summoners War JSON export containing:
  - `unit_list`
  - `runes`
  - `artifacts` (optional but supported)

The file is uploaded via the web UI and **not stored** on the server.

---

## 🖥 How to Use (For Non-Developers)

1. Open the app link
2. Upload your Summoners War JSON file
3. Select a mode:
   - **Optimizer**: Rune optimization only
   - **Ranking**: Current unit ranking only
   - **Both**
4. Click **Run Analysis**
5. Review results on screen

That’s it.

---

## 🛠 For Developers

### Tech Stack
- Python
- Streamlit
- GitHub + Streamlit Cloud deployment
## Project Structure

```
.
├── app.py              # Streamlit entry point
├── requirements.txt    # Python dependencies
├── config.py           # Global configuration
├── core_scores.py      # Stat and scoring logic
├── optimizer.py        # Rune optimizer logic
├── ranking.py          # Current ranking logic
├── visualize.py        # Result rendering
```


## 🔄 Updating the App

The app is **automatically redeployed** when code changes are pushed to GitHub.

### To update:
1. Edit files directly on GitHub (or push via git)
2. Commit changes
3. Streamlit Cloud redeploys automatically
4. Refresh the app URL

No additional deployment steps required.

---

## ⚠️ Limitations (Streamlit Cloud – Free Tier)

- Shared CPU / memory (heavy optimizations may be slow)
- App sleeps when inactive (wakes up on access)
- No user authentication
- Uploaded files are not persisted

These are acceptable for analysis and sharing purposes.

---

## 📌 Notes

- This tool is intended for **analysis and optimization**, not in-game automation.
- JSON files remain in memory only during the session.
- The scoring model is customizable in `core_scores.py`.

---

## 📜 License

This project is provided for personal and analytical use.  
No affiliation with Com2uS.


