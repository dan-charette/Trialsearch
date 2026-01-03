# ClinicalTrials.gov Search Web Application - Implementation Plan

## Overview
Build a Flask web application for searching the ClinicalTrials.gov v2 API with filtering by compound, disease, phase, and status. Results displayed in a sortable table with CSV export.

**Sorting Strategy:** Fetch all results from API (up to 500 limit), load into DOM, let DataTables handle sorting AND pagination client-side. This enables true cross-dataset sorting.

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend** | Flask 3.0 | Simple, aligns with existing sync `requests` usage |
| **Frontend** | Jinja2 + Bootstrap 5 | Server-rendered, no build step |
| **Table** | DataTables.js (CDN) | Built-in sorting, mature library |
| **HTTP** | requests (existing) | Already in use |
| **Testing** | pytest (existing) | Already configured |

---

## Project Structure

```
clin_trial_api_practice/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Settings (page sizes, API URL)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── search.py            # Search, results, export routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── clinical_trials.py   # API service layer
│   ├── models/
│   │   ├── __init__.py
│   │   └── trial.py             # Trial, SearchParams dataclasses
│   ├── templates/
│   │   ├── base.html            # Layout with Bootstrap/DataTables CDN
│   │   ├── search.html          # Search form
│   │   └── results.html         # Results table
│   └── static/
│       └── css/
│           └── styles.css       # Custom styles (minimal)
├── tests/
│   ├── test_clinical_trials_service.py  # Service unit tests
│   ├── test_routes.py                   # Route integration tests
│   └── conftest.py                      # Shared fixtures
├── run.py                       # Entry point
└── requirements.txt             # Updated dependencies
```

---

## Implementation Steps

### Step 1: Update Dependencies
**File:** `requirements.txt`

Add:
```
Flask==3.0.0
python-dotenv==1.0.0
```

### Step 2: Create Data Models
**File:** `app/models/trial.py`

```python
from dataclasses import dataclass
from typing import List, Optional

VALID_STATUSES = [
    ("RECRUITING", "Recruiting"),
    ("NOT_YET_RECRUITING", "Not Yet Recruiting"),
    ("ACTIVE_NOT_RECRUITING", "Active, Not Recruiting"),
    ("COMPLETED", "Completed"),
    ("ENROLLING_BY_INVITATION", "Enrolling by Invitation"),
    ("SUSPENDED", "Suspended"),
    ("TERMINATED", "Terminated"),
    ("WITHDRAWN", "Withdrawn"),
]

VALID_PHASES = [
    ("EARLY_PHASE1", "Early Phase 1"),
    ("PHASE1", "Phase 1"),
    ("PHASE2", "Phase 2"),
    ("PHASE3", "Phase 3"),
    ("PHASE4", "Phase 4"),
]

@dataclass
class Trial:
    nct_id: str
    title: str
    phase: str
    status: str
    sponsor: str
    conditions: List[str]
    interventions: List[str]

@dataclass
class SearchParams:
    compound: Optional[str] = None
    condition: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None

@dataclass
class SearchResult:
    trials: List[Trial]
    total_count: int
    truncated: bool  # True if results exceeded MAX_RESULTS limit
```

### Step 3: Create API Service Layer
**File:** `app/services/clinical_trials.py`

Key methods:
- `fetch_all(params: SearchParams) -> SearchResult` - Fetch all results (paginates through API, stops at MAX_RESULTS)
- `_fetch_page(params, page_token) -> tuple[list, next_token]` - Fetch single page from API
- `_build_params(params)` - Build API query params
- `_parse_study(study)` - Parse API response into Trial dataclass

**Pagination logic for fetch_all:**
```python
def fetch_all(self, params: SearchParams) -> SearchResult:
    all_trials = []
    page_token = None

    while len(all_trials) < MAX_RESULTS:
        studies, next_token, total = self._fetch_page(params, page_token)
        all_trials.extend([self._parse_study(s) for s in studies])

        if not next_token:
            break
        page_token = next_token

    truncated = len(all_trials) >= MAX_RESULTS
    return SearchResult(
        trials=all_trials[:MAX_RESULTS],
        total_count=total,
        truncated=truncated
    )
```

Follow existing pattern from `search_by_compound.py:6-22`:
```python
response = requests.get(base_url, params=params)
response.raise_for_status()
data = response.json()
studies = data.get("studies", [])
```

### Step 4: Create Flask App Factory
**File:** `app/__init__.py`

```python
from flask import Flask

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object('app.config')
    if config:
        app.config.update(config)

    from app.routes.search import search_bp
    app.register_blueprint(search_bp)

    return app
```

**File:** `app/config.py`
```python
SECRET_KEY = 'dev-key-change-in-production'
MAX_RESULTS = 500  # Limit to prevent performance issues
DATATABLES_PAGE_SIZE = 25  # Default rows per page in DataTables
```

### Step 5: Create Search Routes
**File:** `app/routes/search.py`

Routes:
- `GET /` - Render search form
- `GET /search` - Execute search, render results table
- `GET /export` - Stream CSV download

### Step 6: Create Templates

**File:** `app/templates/base.html`
- Bootstrap 5 CDN
- DataTables.js CDN
- Navigation bar
- Flash message display

**File:** `app/templates/search.html`
- Form inputs: compound, condition (text fields)
- Dropdowns: phase, status (from VALID_PHASES, VALID_STATUSES)
- Submit button

**File:** `app/templates/results.html`
- Results count display (e.g., "Showing 350 of 350 trials" or "Showing 500 of 1,234 trials (truncated)")
- Warning banner if results truncated
- Export CSV button
- HTML table with columns: NCT ID (linked), Title, Phase, Status, Sponsor, Conditions, Interventions
- DataTables initialization for **both sorting AND pagination** (client-side)

```javascript
$('#trials-table').DataTable({
    paging: true,           // DataTables handles pagination
    pageLength: 25,         // Default rows per page
    lengthMenu: [10, 25, 50, 100],
    ordering: true,         // Enable column sorting
    order: [[0, 'asc']],    // Default sort by NCT ID
    searching: true         // Enable search/filter box
});
```

### Step 7: Create Entry Point
**File:** `run.py`

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Step 8: Write Tests

**File:** `tests/conftest.py`
- Shared `SAMPLE_API_RESPONSE` fixture (expand existing pattern)
- Flask test client fixture

**File:** `tests/test_clinical_trials_service.py`
Follow pattern from `tests/test_search_by_compound.py`:
- `test_fetch_all_builds_correct_params`
- `test_fetch_all_handles_empty_results`
- `test_fetch_all_paginates_through_multiple_pages`
- `test_fetch_all_stops_at_max_results`
- `test_fetch_all_sets_truncated_flag`
- `test_parse_study_extracts_all_fields`
- `test_fetch_all_propagates_api_errors`

**File:** `tests/test_routes.py`
- `test_index_renders_search_form`
- `test_search_returns_results_table`
- `test_search_requires_at_least_one_criterion`
- `test_export_returns_csv_file`

---

## API Parameters Reference

| UI Field | API Parameter | Example |
|----------|---------------|---------|
| Compound | `query.intr` | `query.intr=pembrolizumab` |
| Condition | `query.cond` | `query.cond=Lung Cancer` |
| Phase | `query.term` | `query.term=AREA[Phase]PHASE3` |
| Status | `filter.overallStatus` | `filter.overallStatus=RECRUITING` |

**Internal pagination params** (used by fetch_all to collect results):
- `pageSize=100` (max per request for efficiency)
- `pageToken` (for subsequent pages)
- `countTotal=true` (to get total count)

---

## Table Columns

| Column | API Field Path | Sortable |
|--------|----------------|----------|
| NCT ID | `protocolSection.identificationModule.nctId` | Yes |
| Title | `protocolSection.identificationModule.briefTitle` | Yes |
| Phase | `protocolSection.designModule.phases` | Yes |
| Status | `protocolSection.statusModule.overallStatus` | Yes |
| Sponsor | `protocolSection.sponsorCollaboratorsModule.leadSponsor.name` | Yes |
| Conditions | `protocolSection.conditionsModule.conditions` | Yes |
| Interventions | `protocolSection.armsInterventionsModule.interventions[].name` | Yes |

---

## Testing Strategy

1. **Unit Tests (Service Layer)**
   - Mock `requests.get` using `@patch` decorator
   - Test parameter building for all filter combinations
   - Test response parsing with sample API data
   - Test error propagation

2. **Integration Tests (Routes)**
   - Use Flask test client
   - Mock service layer
   - Test form rendering, results display, CSV export

3. **Run tests:** `pytest tests/ -v`

---

## Files to Create/Modify

### New Files
- `app/__init__.py`
- `app/config.py`
- `app/models/__init__.py`
- `app/models/trial.py`
- `app/services/__init__.py`
- `app/services/clinical_trials.py`
- `app/routes/__init__.py`
- `app/routes/search.py`
- `app/templates/base.html`
- `app/templates/search.html`
- `app/templates/results.html`
- `app/static/css/styles.css`
- `tests/conftest.py`
- `tests/test_clinical_trials_service.py`
- `tests/test_routes.py`
- `run.py`

### Modified Files
- `requirements.txt` - Add Flask, python-dotenv

### Reference Files (existing patterns)
- `search_by_compound.py` - API request pattern
- `tests/test_search_by_compound.py` - Test mocking pattern

---

## Launch Command

```bash
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open: http://localhost:5000
