import pytest
from unittest.mock import patch, Mock
import requests

from app.services.clinical_trials import ClinicalTrialsService
from app.models.trial import SearchParams, Trial


class TestClinicalTrialsService:
    """Tests for ClinicalTrialsService."""

    def test_fetch_all_builds_correct_params_compound_only(self):
        """Test that compound parameter is correctly mapped."""
        service = ClinicalTrialsService()
        params = SearchParams(compound="pembrolizumab")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['query.intr'] == 'pembrolizumab'

    def test_fetch_all_builds_correct_params_condition_only(self):
        """Test that condition parameter is correctly mapped."""
        service = ClinicalTrialsService()
        params = SearchParams(condition="Lung Cancer")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['query.cond'] == 'Lung Cancer'

    def test_fetch_all_builds_correct_params_single_phase(self):
        """Test that single phase parameter is correctly formatted."""
        service = ClinicalTrialsService()
        params = SearchParams(phases=["PHASE3"])

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['query.term'] == 'AREA[Phase]PHASE3'

    def test_fetch_all_builds_correct_params_multiple_phases(self):
        """Test that multiple phases use OR logic."""
        service = ClinicalTrialsService()
        params = SearchParams(phases=["PHASE2", "PHASE3"])

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['query.term'] == 'AREA[Phase](PHASE2 OR PHASE3)'

    def test_fetch_all_builds_correct_params_single_status(self):
        """Test that single status parameter is correctly mapped."""
        service = ClinicalTrialsService()
        params = SearchParams(statuses=["RECRUITING"])

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['filter.overallStatus'] == 'RECRUITING'

    def test_fetch_all_builds_correct_params_multiple_statuses(self):
        """Test that multiple statuses are comma-separated."""
        service = ClinicalTrialsService()
        params = SearchParams(statuses=["RECRUITING", "COMPLETED"])

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['filter.overallStatus'] == 'RECRUITING,COMPLETED'

    def test_fetch_all_builds_correct_params_all_filters(self):
        """Test that all parameters are correctly combined."""
        service = ClinicalTrialsService()
        params = SearchParams(
            compound="pembrolizumab",
            condition="Lung Cancer",
            phases=["PHASE2", "PHASE3"],
            statuses=["RECRUITING", "ACTIVE_NOT_RECRUITING"]
        )

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['query.intr'] == 'pembrolizumab'
            assert query_params['query.cond'] == 'Lung Cancer'
            assert query_params['query.term'] == 'AREA[Phase](PHASE2 OR PHASE3)'
            assert query_params['filter.overallStatus'] == 'RECRUITING,ACTIVE_NOT_RECRUITING'

    def test_fetch_all_handles_empty_results(self, empty_api_response):
        """Test handling of empty API response."""
        service = ClinicalTrialsService()
        params = SearchParams(compound="nonexistent")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = empty_api_response
            mock_get.return_value.raise_for_status = Mock()

            result = service.fetch_all(params)

            assert result.trials == []
            assert result.total_count == 0
            assert result.truncated is False

    def test_fetch_all_paginates_through_multiple_pages(
        self, sample_api_response_page1, sample_api_response_page2
    ):
        """Test that service paginates through all pages."""
        service = ClinicalTrialsService()
        params = SearchParams(condition="Cancer")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.raise_for_status = Mock()
            mock_get.return_value.json.side_effect = [
                sample_api_response_page1,
                sample_api_response_page2
            ]

            result = service.fetch_all(params)

            assert mock_get.call_count == 2
            assert len(result.trials) == 150
            assert result.total_count == 150

    def test_fetch_all_stops_at_max_results(self):
        """Test that fetch stops when MAX_RESULTS is reached."""
        service = ClinicalTrialsService()
        params = SearchParams(condition="Cancer")

        # Create response that would have more pages
        large_response = {
            "totalCount": 1000,
            "nextPageToken": "next",
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": f"NCT{i:08d}", "briefTitle": f"Trial {i}"},
                        "designModule": {"phases": ["PHASE2"]},
                        "statusModule": {"overallStatus": "RECRUITING"},
                        "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor"}},
                        "conditionsModule": {"conditions": ["Cancer"]},
                        "armsInterventionsModule": {"interventions": []}
                    }
                }
                for i in range(100)
            ]
        }

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            with patch('app.services.clinical_trials.MAX_RESULTS', 250):
                mock_get.return_value.raise_for_status = Mock()
                mock_get.return_value.json.return_value = large_response

                result = service.fetch_all(params)

                # Should stop after 3 pages (300 results, capped at 250)
                assert len(result.trials) == 250
                assert result.truncated is True

    def test_fetch_all_sets_truncated_flag(self):
        """Test that truncated flag is set correctly."""
        service = ClinicalTrialsService()
        params = SearchParams(condition="Cancer")

        response = {
            "totalCount": 1000,
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": f"NCT{i:08d}", "briefTitle": f"Trial {i}"},
                        "designModule": {"phases": []},
                        "statusModule": {"overallStatus": "RECRUITING"},
                        "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor"}},
                        "conditionsModule": {"conditions": []},
                        "armsInterventionsModule": {"interventions": []}
                    }
                }
                for i in range(100)
            ]
        }

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.raise_for_status = Mock()
            mock_get.return_value.json.return_value = response

            result = service.fetch_all(params)

            # Only got 100 results but total is 1000
            assert result.truncated is True
            assert result.total_count == 1000

    def test_parse_study_extracts_all_fields(self, sample_api_response):
        """Test that all fields are correctly parsed from API response."""
        service = ClinicalTrialsService()
        study = sample_api_response["studies"][0]

        trial = service._parse_study(study)

        assert isinstance(trial, Trial)
        assert trial.nct_id == "NCT00000001"
        assert trial.title == "Test Trial One"
        assert trial.phase == "PHASE2, PHASE3"
        assert trial.status == "RECRUITING"
        assert trial.sponsor == "Test Sponsor Inc"
        assert trial.conditions == ["Lung Cancer", "NSCLC"]
        assert trial.interventions == ["Pembrolizumab", "Placebo"]

    def test_parse_study_handles_missing_fields(self):
        """Test parsing handles missing optional fields gracefully."""
        service = ClinicalTrialsService()
        study = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678"
                }
            }
        }

        trial = service._parse_study(study)

        assert trial.nct_id == "NCT12345678"
        assert trial.title == ""
        assert trial.phase == "N/A"
        assert trial.status == ""
        assert trial.sponsor == ""
        assert trial.conditions == []
        assert trial.interventions == []

    def test_fetch_all_propagates_api_errors(self):
        """Test that API errors are properly propagated."""
        service = ClinicalTrialsService()
        params = SearchParams(compound="test")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("API Error")

            with pytest.raises(requests.HTTPError):
                service.fetch_all(params)

    def test_fetch_all_includes_pagination_params(self):
        """Test that pageSize and countTotal are included."""
        service = ClinicalTrialsService()
        params = SearchParams(compound="test")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"totalCount": 0, "studies": []}
            mock_get.return_value.raise_for_status = Mock()

            service.fetch_all(params)

            call_args = mock_get.call_args
            query_params = call_args.kwargs['params']
            assert query_params['pageSize'] == 100
            assert query_params['countTotal'] == 'true'

    def test_fetch_all_passes_page_token_on_subsequent_requests(
        self, sample_api_response_page1, sample_api_response_page2
    ):
        """Test that pageToken is passed for pagination."""
        service = ClinicalTrialsService()
        params = SearchParams(condition="Cancer")

        with patch('app.services.clinical_trials.requests.get') as mock_get:
            mock_get.return_value.raise_for_status = Mock()
            mock_get.return_value.json.side_effect = [
                sample_api_response_page1,
                sample_api_response_page2
            ]

            service.fetch_all(params)

            # First call should not have pageToken
            first_call_params = mock_get.call_args_list[0].kwargs['params']
            assert 'pageToken' not in first_call_params

            # Second call should have pageToken
            second_call_params = mock_get.call_args_list[1].kwargs['params']
            assert second_call_params['pageToken'] == 'token123'
