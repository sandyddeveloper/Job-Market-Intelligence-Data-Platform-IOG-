import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Retry configuration for transient failures (503, 429, timeouts)
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds


def _request_with_retry(method, url, **kwargs):
    """
    Wrapper around requests.get/post with automatic retry + exponential backoff
    for transient HTTP errors (429, 500, 502, 503, 504) and connection errors.
    """
    retryable_status_codes = {429, 500, 502, 503, 504}
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = method(url, **kwargs)
            if response.status_code in retryable_status_codes and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Adzuna API returned {response.status_code} for {url} "
                    f"(attempt {attempt}/{MAX_RETRIES}). Retrying in {wait}s..."
                )
                time.sleep(wait)
                continue
            return response
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Adzuna request to {url} failed with {type(e).__name__} "
                    f"(attempt {attempt}/{MAX_RETRIES}). Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                raise

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception


class AdzunaClient:
    """Adzuna Job Search API Client with automatic retry on transient failures."""

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
        
        if country.lower() == 'in':
            params['where'] = 'india'

        headers = {
            'Accept': 'application/json'
        }

        try:
            logger.info(f"Adzuna GET {url} - params: what='{query}', page={page}")
            response = _request_with_retry(requests.get, url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                logger.error(f"Adzuna API returned error code {response.status_code} for {url}")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch jobs from Adzuna API for {country} page {page}: {e}", exc_info=True)
            return []

    def fetch_salary_history(self, country, category=None, location=None):
        """
        Fetch historical salary data for a specific country, category and location.
        """
        if not self.app_id or not self.app_key:
            return {}

        url = f"{self.base_url}/{country}/history"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'content-type': 'application/json'
        }
        if category:
            params['category'] = category
        if location:
            params['location0'] = 'UK' if country.lower() == 'gb' else country.upper()
            params['location1'] = location

        try:
            logger.info(f"Adzuna GET {url} - params: category={category}, location={location}")
            response = _request_with_retry(requests.get, url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch salary history for {country}: {e}", exc_info=True)
            return {}

    def fetch_salary_histogram(self, country, what=None, location=None):
        """
        Fetch salary distribution histogram.
        """
        if not self.app_id or not self.app_key:
            return {}

        url = f"{self.base_url}/{country}/histogram"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'content-type': 'application/json'
        }
        if what:
            params['what'] = what
        if location:
            params['location0'] = 'UK' if country.lower() == 'gb' else country.upper()
            params['location1'] = location

        try:
            logger.info(f"Adzuna GET {url} - params: what={what}, location={location}")
            response = _request_with_retry(requests.get, url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch salary histogram for {country}: {e}", exc_info=True)
            return {}

    def fetch_top_companies(self, country, what=None):
        """
        Fetch leaderboard of top employers.
        """
        if not self.app_id or not self.app_key:
            return []

        url = f"{self.base_url}/{country}/top_companies"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'content-type': 'application/json'
        }
        if what:
            params['what'] = what

        try:
            logger.info(f"Adzuna GET {url} - params: what={what}")
            response = _request_with_retry(requests.get, url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('leaderboard', [])
            return []
        except Exception as e:
            logger.error(f"Failed to fetch top companies for {country}: {e}", exc_info=True)
            return []

    def fetch_categories(self, country):
        """
        Fetch sectors list.
        """
        if not self.app_id or not self.app_key:
            return []

        url = f"{self.base_url}/{country}/categories"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'content-type': 'application/json'
        }

        try:
            logger.info(f"Adzuna GET {url}")
            response = _request_with_retry(requests.get, url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []
        except Exception as e:
            logger.error(f"Failed to fetch categories for {country}: {e}", exc_info=True)
            return []

    def fetch_salary_prediction(self, country, title, description):
        """
        Fetch Jobsworth Salary Prediction for a job description.
        """
        if not self.app_id or not self.app_key:
            return {}

        url = f"{self.base_url}/{country}/jobsworth"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'title': title,
            'description': description,
            'content-type': 'application/json'
        }

        try:
            logger.info(f"Adzuna GET {url} - params: title={title}")
            response = _request_with_retry(requests.get, url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch salary prediction for {country}: {e}", exc_info=True)
            return {}
