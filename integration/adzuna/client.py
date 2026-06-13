import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AdzunaClient:
    """Adzuna Job Search API Client."""

    def __init__(self, app_id=None, app_key=None):
        self.app_id = app_id or getattr(settings, 'ADZUNA_APP_ID', None)
        self.app_key = app_key or getattr(settings, 'ADZUNA_APP_KEY', None)
        self.base_url = "https://api.adzuna.com/v1/api/jobs"

    def fetch_jobs(self, country, page, query="data engineer"):
        """
        Fetch jobs from Adzuna API for a specific country and page.
        """
        if not self.app_id or not self.app_key:
            logger.error("Adzuna API credentials (ADZUNA_APP_ID/ADZUNA_APP_KEY) are not configured.")
            return []

        url = f"{self.base_url}/{country}/search/{page}"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'what': query,
            'results_per_page': 20,
            'content-type': 'application/json'
        }
        
        # Specifying 'where' for India query as referenced in user curl search
        if country.lower() == 'in':
            params['where'] = 'india'

        headers = {
            'Accept': 'application/json'
        }

        try:
            logger.info(f"Adzuna GET {url} - params: what='{query}', page={page}")
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                logger.error(f"Adzuna API returned error code {response.status_code}: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch jobs from Adzuna API for {country} page {page}: {e}", exc_info=True)
            return []
