import pytest
from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key'
    })
    yield app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_api_response():
    """Sample API response matching ClinicalTrials.gov v2 format."""
    return {
        "totalCount": 2,
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT00000001",
                        "briefTitle": "Test Trial One"
                    },
                    "designModule": {
                        "phases": ["PHASE2", "PHASE3"]
                    },
                    "statusModule": {
                        "overallStatus": "RECRUITING"
                    },
                    "sponsorCollaboratorsModule": {
                        "leadSponsor": {
                            "name": "Test Sponsor Inc"
                        }
                    },
                    "conditionsModule": {
                        "conditions": ["Lung Cancer", "NSCLC"]
                    },
                    "armsInterventionsModule": {
                        "interventions": [
                            {"name": "Pembrolizumab"},
                            {"name": "Placebo"}
                        ]
                    }
                }
            },
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT00000002",
                        "briefTitle": "Test Trial Two"
                    },
                    "designModule": {
                        "phases": ["PHASE1"]
                    },
                    "statusModule": {
                        "overallStatus": "COMPLETED"
                    },
                    "sponsorCollaboratorsModule": {
                        "leadSponsor": {
                            "name": "Another Sponsor"
                        }
                    },
                    "conditionsModule": {
                        "conditions": ["Breast Cancer"]
                    },
                    "armsInterventionsModule": {
                        "interventions": [
                            {"name": "Drug A"}
                        ]
                    }
                }
            }
        ]
    }


@pytest.fixture
def sample_api_response_page1():
    """First page of paginated response."""
    return {
        "totalCount": 150,
        "nextPageToken": "token123",
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": f"NCT0000000{i}",
                        "briefTitle": f"Trial {i}"
                    },
                    "designModule": {"phases": ["PHASE2"]},
                    "statusModule": {"overallStatus": "RECRUITING"},
                    "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor"}},
                    "conditionsModule": {"conditions": ["Cancer"]},
                    "armsInterventionsModule": {"interventions": [{"name": "Drug"}]}
                }
            }
            for i in range(1, 101)
        ]
    }


@pytest.fixture
def sample_api_response_page2():
    """Second page of paginated response (final page)."""
    return {
        "totalCount": 150,
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": f"NCT000000{i}",
                        "briefTitle": f"Trial {i}"
                    },
                    "designModule": {"phases": ["PHASE2"]},
                    "statusModule": {"overallStatus": "RECRUITING"},
                    "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor"}},
                    "conditionsModule": {"conditions": ["Cancer"]},
                    "armsInterventionsModule": {"interventions": [{"name": "Drug"}]}
                }
            }
            for i in range(101, 151)
        ]
    }


@pytest.fixture
def empty_api_response():
    """Empty API response."""
    return {
        "totalCount": 0,
        "studies": []
    }
