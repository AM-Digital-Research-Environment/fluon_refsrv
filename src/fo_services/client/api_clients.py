import requests
import logging

logger = logging.getLogger(__name__)

class ApiError(Exception):
    pass

class TrainingApiClient(object):
    def __init__(self, base_url: str):
        self.session = requests.Session()
        self.base_url = base_url

    def get_cluster(self) -> list[dict[str, str]]:
        r = self.session.get(f"{self.base_url}/api/v1/export/wisski/cluster")
        if r.status_code != 200:
            logger.error(f"[API] got response code {r.status_code} for GET /api/v1/wisski/cluster")
            raise ApiError(f"Error communicating with training API, got status {r.status_code} for {r.request.url}")

        return r.json()


    def get_recommendations(self) -> list[dict[str, str]]:
        r = self.session.get(f"{self.base_url}/api/v1/export/wisski/recommendations")
        if r.status_code != 200:
            logger.error(f"[API] got response code {r.status_code} for GET /api/v1/wisski/recommendation")
            raise ApiError(f"Error communicating with training API, got status {r.status_code} for {r.request.url}")

        return r.json()
