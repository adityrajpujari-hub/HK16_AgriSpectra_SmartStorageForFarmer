# HK16_AgriSpectra_SmartStorageForFarmer
A scientific rule based framework for post-harvest risk assessment
# AgriSpectra

AgriSpectra is a lightweight Flask app that estimates post-harvest storage risk using crop, region, temperature, humidity, season and storage duration. The engine is rule-based (scientific ranges) and explainable.

Prerequisites
- Python 3.8+
- Create and activate a virtual environment (recommended)
- Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally

```bash
python app.py
# open http://127.0.0.1:5000/ in your browser
```

Run on Windows (helper)

```powershell
./run.ps1
```

The `run.ps1` script will try to find `python` or `py`, create a `.venv`, install `requirements.txt`, and start the app. If Python is missing and `winget` is available it will attempt to install Python automatically.

Pages
- Home: overview and links
- Risk Calculator: main tool (interactive, API-backed)
- How It Works: algorithm and scientific notes
- Data Source: disclaimer and references
- About: project info

Notes
- This is a decision-support tool based on scientific thresholds and domain knowledge. It is not a substitute for professional agronomic consulting.

Files
- `app.py`: Flask routes and API
- `risk_engine.py`: rule-based risk engine (core logic)
- `data.py`: sample CSV loader
- `templates/`: Jinja2 templates for pages
- `static/`: CSS and JavaScript (Chart.js used via CDN)

Next steps
- Add CSV batch upload and processing
- Integrate local weather APIs to auto-fill temperature/humidity

- Add persistent dataset and ML model training pipeline (ML-ready)
