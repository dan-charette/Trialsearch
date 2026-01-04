import requests
from typing import Optional, Tuple, List

from app.config import API_BASE_URL, API_PAGE_SIZE, MAX_RESULTS
from app.models.trial import Trial, SearchParams, SearchResult


class ClinicalTrialsService:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def fetch_all(self, params: SearchParams) -> SearchResult:
        """Fetch all results, paginating through API up to MAX_RESULTS."""
        all_trials = []
        page_token = None
        total_count = 0

        while len(all_trials) < MAX_RESULTS:
            studies, next_token, total = self._fetch_page(params, page_token)
            total_count = total
            all_trials.extend([self._parse_study(s) for s in studies])

            if not next_token:
                break
            page_token = next_token

        truncated = len(all_trials) >= MAX_RESULTS or len(all_trials) < total_count
        return SearchResult(
            trials=all_trials[:MAX_RESULTS],
            total_count=total_count,
            truncated=truncated and total_count > len(all_trials[:MAX_RESULTS])
        )

    def _fetch_page(
        self, params: SearchParams, page_token: Optional[str] = None
    ) -> Tuple[List[dict], Optional[str], int]:
        """Fetch a single page from the API.

        Returns: (studies, next_page_token, total_count)
        """
        query_params = self._build_params(params)
        query_params['pageSize'] = API_PAGE_SIZE
        query_params['countTotal'] = 'true'

        if page_token:
            query_params['pageToken'] = page_token

        response = requests.get(self.base_url, params=query_params)
        response.raise_for_status()
        data = response.json()

        studies = data.get('studies', [])
        next_token = data.get('nextPageToken')
        total_count = data.get('totalCount', 0)

        return studies, next_token, total_count

    def _build_params(self, params: SearchParams) -> dict:
        """Build API query parameters from SearchParams."""
        query_params = {}

        if params.compound:
            query_params['query.intr'] = params.compound

        if params.condition:
            query_params['query.cond'] = params.condition

        if params.phases:
            # Multiple phases use OR logic: AREA[Phase](PHASE2 OR PHASE3)
            if len(params.phases) == 1:
                query_params['query.term'] = f'AREA[Phase]{params.phases[0]}'
            else:
                phases_or = ' OR '.join(params.phases)
                query_params['query.term'] = f'AREA[Phase]({phases_or})'

        if params.statuses:
            # Multiple statuses are comma-separated
            query_params['filter.overallStatus'] = ','.join(params.statuses)

        return query_params

    def _parse_study(self, study: dict) -> Trial:
        """Parse API study response into Trial dataclass."""
        protocol = study.get('protocolSection', {})

        # Identification
        id_module = protocol.get('identificationModule', {})
        nct_id = id_module.get('nctId', '')
        title = id_module.get('briefTitle', '')

        # Design
        design_module = protocol.get('designModule', {})
        phases = design_module.get('phases', [])
        phase = ', '.join(phases) if phases else 'N/A'

        # Status
        status_module = protocol.get('statusModule', {})
        status = status_module.get('overallStatus', '')

        # Sponsor
        sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
        lead_sponsor = sponsor_module.get('leadSponsor', {})
        sponsor = lead_sponsor.get('name', '')

        # Conditions
        conditions_module = protocol.get('conditionsModule', {})
        conditions = conditions_module.get('conditions', [])

        # Interventions
        arms_module = protocol.get('armsInterventionsModule', {})
        interventions_list = arms_module.get('interventions', [])
        interventions = [i.get('name', '') for i in interventions_list if i.get('name')]

        return Trial(
            nct_id=nct_id,
            title=title,
            phase=phase,
            status=status,
            sponsor=sponsor,
            conditions=conditions,
            interventions=interventions
        )
