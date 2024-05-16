import functools
import io
import logging
from pathlib import Path
import random

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    redirect,
    render_template,
    session,
    url_for,
)
import joblib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

bp = Blueprint("clustervis", __name__, url_prefix="/clustervis")


@bp.route("/inspect", methods=["GET"])
def inspect():
    if g.user is None:
        return redirect(url_for("auth.login"))
    if "has_cluster_data" not in session:
        load_cluster_data()
    if session["has_cluster_data"]:
        title = "Inspect Clustering"
    else:
        title = "I need data!"
    return render_template(
        "clustervis/inspect.html", title=title, stats=session["stats"]
    )


@bp.route("/cluster_vis.png")
def plot_cluster_vis():
    plot_file = Path("../data/plots/cluster_vis_reachability.png")
    if plot_file.exists() and session["has_cluster_data"]:
        with open(plot_file, "rb") as fh:
            output = io.BytesIO(fh.read())
    else:
        fig = create_random_plot()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


@bp.route("/cluster_silhouette.png")
def plot_cluster_silhouette():
    plot_file = Path("../data/plots/cluster_vis_silhouette.png")
    if plot_file.exists() and session["has_cluster_data"]:
        with open(plot_file, "rb") as fh:
            output = io.BytesIO(fh.read())
    else:
        fig = create_random_plot()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


def create_random_plot():
    fig = Figure()
    logger.debug("making a figure up")
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)
    return fig


def load_cluster_data():
    cluster_data = Path("../data/cluster_stats.joblib")
    if not cluster_data.exists():
        logger.error(f"Cluster data dump at {cluster_data} not found")
        session["has_cluster_data"] = False
        session["stats"] = []
        return

    logger.debug("reloading actual data")
    session["stats"] = joblib.load(cluster_data)
    session["has_cluster_data"] = True
    flash("Reloading data successful", "success")


def require_auth(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view
