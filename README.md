# Clinical Trials Search

A Flask web application for searching the ClinicalTrials.gov v2 API with filtering by compound, disease, phase, and status.

## Features

- **Multi-criteria search**: Filter by compound/intervention, condition/disease, phase, and status
- **Multi-select filters**: Select multiple phases (e.g., Phase 2 AND Phase 3) or statuses (e.g., Recruiting AND Completed)
- **Sortable results**: DataTables.js provides client-side sorting, filtering, and pagination
- **CSV export**: Download search results as a CSV file
- **Direct links**: NCT IDs link directly to ClinicalTrials.gov study pages

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dan-charette/Trialsearch.git
cd Trialsearch

# Run the application (creates venv, installs deps, starts server)
./run.sh
```

Then open http://localhost:5000

## Requirements

- Python 3.8+
- Flask 3.0
- requests

## Project Structure

```
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration settings
│   ├── models/
│   │   └── trial.py             # Data models (Trial, SearchParams)
│   ├── routes/
│   │   └── search.py            # Routes (/, /search, /export)
│   ├── services/
│   │   └── clinical_trials.py   # ClinicalTrials.gov API service
│   ├── templates/               # Jinja2 templates
│   └── static/css/              # Custom styles
├── tests/                       # Test suite
├── run.py                       # Entry point
├── run.sh                       # Run script with venv
└── requirements.txt
```

## Usage

### Search Filters

| Filter | Description |
|--------|-------------|
| Compound/Intervention | Drug or treatment name (e.g., "pembrolizumab") |
| Condition/Disease | Medical condition (e.g., "Lung Cancer") |
| Phase | Clinical trial phase (Early Phase 1 through Phase 4) |
| Status | Trial status (Recruiting, Completed, etc.) |

### API Limits

- Results are limited to 500 trials to ensure performance
- A warning is displayed when results are truncated

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
