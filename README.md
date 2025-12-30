diff --git a/README.md b/README.md
index 33c6a0603fc10186352a552d3c5aa7bf9a7be706..aa712a77f4f8891f66ac1075acc7c68e7e4e11fd 100644
--- a/README.md
+++ b/README.md
@@ -1,43 +1,41 @@
 # Summoners War – World Boss Rune Analyzer
 
 This project is a **Streamlit-based web tool** that analyzes Summoners War JSON data to:
 
 - Optimize rune sets for specific units (World Boss–focused)
 - Rank all units by their current overall strength
 - Allow **non-developers** to upload a JSON file and view results easily in a browser
 
 The app is deployed on **Streamlit Cloud** and requires **no local setup** for users.
 
 ---
 
 ## 🔗 Live App
 
 👉 **Access the app here:**
 
-
-
 [https://sw-worldboss-optimizer-fnyzujw3snm2om6bqh5vk9.streamlit.app/](https://sw-worldboss-optimizer-fnyzujw3snm2om6bqh5vk9.streamlit.app/)
 
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
@@ -67,50 +65,62 @@ Anyone with this link can use the tool directly.
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
+
+### Local Development
+1. Create and activate a virtual environment.
+2. Install dependencies:
+   ```bash
+   pip install -r requirements.txt
+   ```
+3. Run the app:
+   ```bash
+   streamlit run app.py
+   ```
+4. Open the URL shown in the terminal to use the app locally.
 ## Project Structure
 
 ```
 .
 ├── app.py              # Streamlit entry point
 ├── config/             # Global configuration
 ├── data/               # Data loaders/aggregations
 ├── domain/             # Core scoring/optimizer/ranking logic
 ├── services/           # External integrations
 ├── ui/                 # Streamlit tabs/components
 ├── utils/              # Shared utilities
 ├── requirements.txt    # Python dependencies
 ```
 
 
 ## 🔄 Updating the App
 
 The app is **automatically redeployed** when code changes are pushed to GitHub.
 
 ### To update:
 1. Edit files directly on GitHub (or push via git)
 2. Commit changes
 3. Streamlit Cloud redeploys automatically
 4. Refresh the app URL
 
@@ -119,26 +129,25 @@ No additional deployment steps required.
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
 - The scoring model is customizable in `domain/core_scores.py`.
 
 ---
 
 ## 📜 License
 
 This project is provided for personal and analytical use.  
 No affiliation with Com2uS.
-
