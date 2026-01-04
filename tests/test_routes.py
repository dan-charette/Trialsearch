import pytest
from unittest.mock import patch, Mock

from app.models.trial import Trial, SearchResult, VALID_PHASES, VALID_STATUSES


class TestSearchRoutes:
    """Tests for search routes."""

    def test_index_renders_search_form(self, client):
        """Test that index page renders the search form."""
        response = client.get('/')

        assert response.status_code == 200
        assert b'Search Clinical Trials' in response.data
        assert b'Compound' in response.data
        assert b'Condition' in response.data
        assert b'Phase' in response.data
        assert b'Status' in response.data

    def test_index_includes_phase_options(self, client):
        """Test that phase dropdown includes all valid phases."""
        response = client.get('/')

        for value, label in VALID_PHASES:
            assert label.encode() in response.data

    def test_index_includes_status_options(self, client):
        """Test that status dropdown includes all valid statuses."""
        response = client.get('/')

        for value, label in VALID_STATUSES:
            assert label.encode() in response.data

    def test_search_requires_at_least_one_criterion(self, client):
        """Test that search requires at least one search criterion."""
        response = client.get('/search')

        assert response.status_code == 200
        assert b'Please enter at least one search criterion' in response.data

    def test_search_returns_results_table(self, client):
        """Test that search returns results in a table."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id="NCT00000001",
                    title="Test Trial",
                    phase="PHASE2",
                    status="RECRUITING",
                    sponsor="Test Sponsor",
                    conditions=["Cancer"],
                    interventions=["Drug A"]
                )
            ],
            total_count=1,
            truncated=False
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/search?compound=test')

            assert response.status_code == 200
            assert b'NCT00000001' in response.data
            assert b'Test Trial' in response.data
            assert b'Test Sponsor' in response.data

    def test_search_displays_result_count(self, client):
        """Test that search displays result count."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id=f"NCT0000000{i}",
                    title=f"Trial {i}",
                    phase="PHASE2",
                    status="RECRUITING",
                    sponsor="Sponsor",
                    conditions=[],
                    interventions=[]
                )
                for i in range(5)
            ],
            total_count=5,
            truncated=False
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/search?condition=cancer')

            assert response.status_code == 200
            assert b'Showing 5 of 5 trials' in response.data

    def test_search_shows_truncated_warning(self, client):
        """Test that truncated results show warning."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id=f"NCT{i:08d}",
                    title=f"Trial {i}",
                    phase="PHASE2",
                    status="RECRUITING",
                    sponsor="Sponsor",
                    conditions=[],
                    interventions=[]
                )
                for i in range(500)
            ],
            total_count=1000,
            truncated=True
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/search?condition=cancer')

            assert response.status_code == 200
            assert b'results truncated' in response.data
            assert b'Results are limited to 500 trials' in response.data

    def test_search_handles_api_error(self, client):
        """Test that API errors are handled gracefully."""
        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.side_effect = Exception("API connection failed")

            response = client.get('/search?compound=test')

            assert response.status_code == 200
            assert b'Error fetching results' in response.data

    def test_search_links_nct_ids(self, client):
        """Test that NCT IDs are linked to ClinicalTrials.gov."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id="NCT12345678",
                    title="Test",
                    phase="PHASE1",
                    status="RECRUITING",
                    sponsor="Sponsor",
                    conditions=[],
                    interventions=[]
                )
            ],
            total_count=1,
            truncated=False
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/search?compound=test')

            assert b'href="https://clinicaltrials.gov/study/NCT12345678"' in response.data

    def test_search_passes_all_params_to_service(self, client):
        """Test that all search params are passed to service."""
        mock_result = SearchResult(trials=[], total_count=0, truncated=False)

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            client.get('/search?compound=drug&condition=cancer&phases=PHASE2&statuses=RECRUITING')

            mock_fetch.assert_called_once()
            params = mock_fetch.call_args[0][0]
            assert params.compound == 'drug'
            assert params.condition == 'cancer'
            assert params.phases == ['PHASE2']
            assert params.statuses == ['RECRUITING']

    def test_search_passes_multiple_phases_to_service(self, client):
        """Test that multiple phases are passed as a list."""
        mock_result = SearchResult(trials=[], total_count=0, truncated=False)

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            client.get('/search?phases=PHASE2&phases=PHASE3')

            mock_fetch.assert_called_once()
            params = mock_fetch.call_args[0][0]
            assert params.phases == ['PHASE2', 'PHASE3']

    def test_search_passes_multiple_statuses_to_service(self, client):
        """Test that multiple statuses are passed as a list."""
        mock_result = SearchResult(trials=[], total_count=0, truncated=False)

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            client.get('/search?statuses=RECRUITING&statuses=COMPLETED')

            mock_fetch.assert_called_once()
            params = mock_fetch.call_args[0][0]
            assert params.statuses == ['RECRUITING', 'COMPLETED']

    def test_export_returns_csv_file(self, client):
        """Test that export returns a CSV file."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id="NCT00000001",
                    title="Test Trial",
                    phase="PHASE2",
                    status="RECRUITING",
                    sponsor="Test Sponsor",
                    conditions=["Cancer", "Tumor"],
                    interventions=["Drug A", "Drug B"]
                )
            ],
            total_count=1,
            truncated=False
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/export?compound=test')

            assert response.status_code == 200
            assert response.mimetype == 'text/csv'
            assert 'attachment' in response.headers['Content-Disposition']
            assert 'clinical_trials.csv' in response.headers['Content-Disposition']

    def test_export_csv_contains_headers(self, client):
        """Test that CSV contains proper headers."""
        mock_result = SearchResult(trials=[], total_count=0, truncated=False)

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/export?compound=test')

            csv_content = response.data.decode('utf-8')
            assert 'NCT ID' in csv_content
            assert 'Title' in csv_content
            assert 'Phase' in csv_content
            assert 'Status' in csv_content
            assert 'Sponsor' in csv_content
            assert 'Conditions' in csv_content
            assert 'Interventions' in csv_content

    def test_export_csv_contains_data(self, client):
        """Test that CSV contains trial data."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id="NCT00000001",
                    title="Test Trial",
                    phase="PHASE2",
                    status="RECRUITING",
                    sponsor="Test Sponsor",
                    conditions=["Cancer", "Tumor"],
                    interventions=["Drug A", "Drug B"]
                )
            ],
            total_count=1,
            truncated=False
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/export?compound=test')

            csv_content = response.data.decode('utf-8')
            assert 'NCT00000001' in csv_content
            assert 'Test Trial' in csv_content
            assert 'Test Sponsor' in csv_content
            assert 'Cancer; Tumor' in csv_content
            assert 'Drug A; Drug B' in csv_content

    def test_search_displays_no_results_message(self, client):
        """Test that empty results show appropriate message."""
        mock_result = SearchResult(trials=[], total_count=0, truncated=False)

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/search?compound=nonexistent')

            assert response.status_code == 200
            assert b'No trials found matching your search criteria' in response.data

    def test_search_includes_export_link(self, client):
        """Test that results page includes export link with params."""
        mock_result = SearchResult(
            trials=[
                Trial(
                    nct_id="NCT00000001",
                    title="Test",
                    phase="PHASE1",
                    status="RECRUITING",
                    sponsor="Sponsor",
                    conditions=[],
                    interventions=[]
                )
            ],
            total_count=1,
            truncated=False
        )

        with patch('app.routes.search.service.fetch_all') as mock_fetch:
            mock_fetch.return_value = mock_result

            response = client.get('/search?compound=test')

            assert b'Export CSV' in response.data
            assert b'/export' in response.data
