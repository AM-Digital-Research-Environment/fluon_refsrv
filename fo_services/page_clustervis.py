import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Response,
)

import logging
logger = logging.getLogger(__name__)

from joblib import load
from pathlib import Path
import io
import random

bp = Blueprint("clustervis", __name__, url_prefix="/clustervis")

@bp.route('/inspect', methods=["GET"])
def inspect():
    if g.user is None:
        return redirect(url_for("auth.login"))
    if 'has_cluster_data' not in session:
        load_cluster_data()
    if session['has_cluster_data']:
        title = "Inspect Clustering"
    else:
        title = "I need data!"
    return render_template('clustervis/inspect.html', title=title, stats=session['stats'])


@bp.route('/cluster_vis.png')
def plot_cluster_vis():
    if session['has_cluster_data']:
        with open('/data/plots/cluster_vis_reachability.png', "rb") as fh:
            output = io.BytesIO(fh.read())
    else:
        fig = create_random_plot()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@bp.route('/cluster_silhouette.png')
def plot_cluster_silhouette():
    if session['has_cluster_data']:
        with open('/data/plots/cluster_vis_silhouette.png', "rb") as fh:
            output = io.BytesIO(fh.read())
    else:
        fig = create_random_plot()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_random_plot():
    fig = Figure()
    logger.debug("making a figure up")
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)
    return fig


def load_cluster_data():
    logger.debug("reloading actual data")
    session['stats'] = load('/data/cluster_stats.joblib')
    session['has_cluster_data'] = True
    flash("Reloading data successful", "success")


def require_auth(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view
