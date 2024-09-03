from ..client.api_clients import TrainingApiClient
from ..kgstuff import KGHandler
from ..db import UpdateModelResult


class UpdaterService(object):
    def __init__(self, api_client: TrainingApiClient):
        self.api_client = api_client

    def reload_data(self) -> UpdateModelResult:
        cluster_data = self.api_client.get_cluster()
        reco_data = self.api_client.get_recommendations()
        return KGHandler().reload_data(cluster_data, reco_data)
