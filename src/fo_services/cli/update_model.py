import click
from ..services.updater import UpdaterService
from ..client.api_clients import TrainingApiClient
from flask import current_app
import wasabi


@click.command("update-model")
def update_model():
    msg = wasabi.Printer()
    client = TrainingApiClient(current_app.config["TRAINING_API_URL"])
    updater = UpdaterService(client)
    result = updater.reload_data()
    msg.info(f"Time elapsed: {result['elapsed']}")
    msg.info(f"Cluster assignments written: {result['cluster_assignments_written']}")
    msg.info(f"Reco assignments written: {result['reco_assignments_written']}")
    if result["cluster_assignments_written"] != result["cluster_assignments_to_write"]:
        msg.warn(
            "Not all cluster assignments were written (should be {result['cluster_assignments_to_write']})"
        )
    if result["reco_assignments_written"] != result["reco_assignments_to_write"]:
        msg.warn(
            "Not all reco assignments were written (should be {result['reco_assignments_to_write']})"
        )

    msg.good(f"Done updating model. {msg.counts['warn']} warnings.")
