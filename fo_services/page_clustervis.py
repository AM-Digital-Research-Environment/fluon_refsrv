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

import numpy as np
from sklearn.cluster import OPTICS, cluster_optics_dbscan
from sklearn import metrics
from sklearn.metrics import silhouette_score

from pathlib import Path
import io
import os
import random
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


bp = Blueprint("clustervis", __name__, url_prefix="/clustervis")

clust_p = Path('/data/clustering.joblib')
X_p = Path('/data/clustering_data.npy')

@bp.route('/inspect', methods=["GET"])
def inspect():
    if g.user is None:
        return redirect(url_for("auth.login"))
    if 'has_cluster_data' not in session:
        session['stats'] = {}
        session['stats']["n_items"] = 'NA'
        session['stats']["n_outliers"] = 'NA'
        session['stats']["n_clusters"] = 'NA'
        session['has_cluster_data'] = False
        
    try:
        clust_p_mtime = Path('/app/', clust_p.name + '.mtime')
        X_p_mtime = Path('/app/', X_p.name + '.mtime')
        rel_clust = check_reload_required(clust_p, clust_p_mtime)
        rel_X = check_reload_required(X_p, X_p_mtime)
        if rel_clust or rel_X:
            load_cluster_data(dummy = False)
    except FileNotFoundError:
        load_cluster_data(dummy = True)
    if session['has_cluster_data']:
        title = "Inspect Clustering"
    else:
        title = "I need data!"
    return render_template('clustervis/inspect.html', title=title, stats=session['stats'])


@bp.route('/cluster_vis.png')
def plot_cluster_vis():
    if session['has_cluster_data']:
        with open('/app/cluster_vis_reachability.png', "rb") as fh:
            output = io.BytesIO(fh.read())
    else:
        fig = create_random_plot()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@bp.route('/cluster_silhouette.png')
def plot_cluster_silhouette():
    if session['has_cluster_data']:
        with open('/app/cluster_vis_silhouette.png', "rb") as fh:
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

def render_silhouette_plot(clust, X):
    sil = []
    #ran = np.arange(0.01,1.0,0.1)
    ran = np.linspace(0.01, 1.0, num=30, endpoint=True)
    for e in ran:
        labels = cluster_optics_dbscan(
          reachability=clust.reachability_,
          core_distances=clust.core_distances_,
          ordering=clust.ordering_,
          eps=e,
        )
        if len(np.unique(labels)) > 1:
            sil.append(silhouette_score(X, labels))
        else:
            sil.append(0)
    plt.figure(0)
    ax = plt.gca()
    ax.set_ylim([-1.0, 1.0])
    ax.set_ylabel("Silhouette coefficient")
    ax.set_xlabel("DBSCAN epsilon cut")

    plt.plot(ran, sil)
    plt.savefig('/app/cluster_vis_silhouette.png')

def render_reachability_plot(clust, X):
    labels_050 = cluster_optics_dbscan(
      reachability=clust.reachability_,
      core_distances=clust.core_distances_,
      ordering=clust.ordering_,
      eps=0.5,
    )
    labels_200 = cluster_optics_dbscan(
      reachability=clust.reachability_,
      core_distances=clust.core_distances_,
      ordering=clust.ordering_,
      eps=2,
    )

    space = np.arange(len(X))
    reachability = clust.reachability_[clust.ordering_]
    labels = clust.labels_[clust.ordering_]

    plt.figure(figsize=(10, 7))
    G = gridspec.GridSpec(2, 3)
    ax1 = plt.subplot(G[0, :])
    ax2 = plt.subplot(G[1, 0])
    ax3 = plt.subplot(G[1, 1])
    ax4 = plt.subplot(G[1, 2])

    # Reachability plot
    colors = ["g.", "r.", "b.", "y.", "c."]
    for klass, color in zip(range(0, 5), colors):
      Xk = space[labels == klass]
      Rk = reachability[labels == klass]
      ax1.plot(Xk, Rk, color, alpha=0.3)
    ax1.plot(space[labels == -1], reachability[labels == -1], "k.", alpha=0.3)
    ax1.plot(space, np.full_like(space, 2.0, dtype=float), "k-", alpha=0.5)
    ax1.plot(space, np.full_like(space, 0.5, dtype=float), "k-.", alpha=0.5)
    ax1.set_ylabel("Reachability (epsilon distance)")
    ax1.set_title("Reachability Plot")

    # OPTICS
    colors = ["g.", "r.", "b.", "y.", "c."]
    for klass, color in zip(range(0, 5), colors):
      Xk = X[clust.labels_ == klass]
      ax2.plot(Xk[:, 0], Xk[:, 1], color, alpha=0.3)
    ax2.plot(X[clust.labels_ == -1, 0], X[clust.labels_ == -1, 1], "k+", alpha=0.1)
    ax2.set_title("Automatic Clustering\nOPTICS")

    # DBSCAN at 0.5
    colors = ["g.", "r.", "b.", "c."]
    for klass, color in zip(range(0, 4), colors):
      Xk = X[labels_050 == klass]
      ax3.plot(Xk[:, 0], Xk[:, 1], color, alpha=0.3)
    ax3.plot(X[labels_050 == -1, 0], X[labels_050 == -1, 1], "k+", alpha=0.1)
    ax3.set_title("Clustering at 0.5 epsilon cut\nDBSCAN")

    # DBSCAN at 2.
    colors = ["g.", "m.", "y.", "c."]
    for klass, color in zip(range(0, 4), colors):
      Xk = X[labels_200 == klass]
      ax4.plot(Xk[:, 0], Xk[:, 1], color, alpha=0.3)
    ax4.plot(X[labels_200 == -1, 0], X[labels_200 == -1, 1], "k+", alpha=0.1)
    ax4.set_title("Clustering at 2.0 epsilon cut\nDBSCAN")

    plt.tight_layout()
    plt.savefig('/app/cluster_vis_reachability.png')

def load_cluster_data(dummy = False):
    session['stats'] = {}
    if not dummy:
        logger.debug("reloading actual data")
        clust = load(str(clust_p))
        X = np.load(str(X_p))
        
        render_reachability_plot(clust, X)
        render_silhouette_plot(clust, X)
        
        session['stats']["n_items"] = len(clust.labels_)
        session['stats']["n_outliers"] = np.sum(clust.labels_==-1).item()
        session['stats']["n_clusters"] = len(np.unique(clust.labels_[clust.labels_>-1]))
        session['has_cluster_data'] = True
        flash("Reloading data successful", "success")
    else:
        session['has_cluster_data'] = False
        
        # ~ xs = range(100)
        # ~ ys = [random.randint(1, 50) for x in xs]
        # ~ plt.plot(xs, ys)
        # ~ plt.savefig('/app/cluster_vis_reachability.png')
        # ~ plt.savefig('/app/cluster_vis_silhouette.png')
        
        session['stats']["n_items"] = 'NA'
        session['stats']["n_outliers"] = 'NA'
        session['stats']["n_clusters"] = 'NA'

def check_reload_required(actual_file, mtime_file):
    actual_file = Path(actual_file)
    if not actual_file.exists():
        logger.debug(f"could not find {actual_file.resolve()}")
        raise FileNotFoundError()
    
    mtime_file = Path(mtime_file)
    if not mtime_file.exists():
      last_check = 0.0
    else:
      with open(str(mtime_file), 'r') as _mtime:
        last_check = float(_mtime.readline().strip())
    
    timestamp = os.path.getmtime(str(actual_file))
    if last_check < timestamp:
      logger.debug(f"data seem to have changed. reloading from {actual_file}")
      with open(str(mtime_file), 'w') as _mtime:
        print(timestamp, file=_mtime)
      return True
    return False

# ~ @bp.before_app_request
# ~ def init_g_for_cluster_vis():
    # ~ clust_p_mtime = Path('/app/', clust_p.name + '.mtime')
    # ~ X_p_mtime = Path('/app/', X_p.name + '.mtime')
    
    # ~ try:
        # ~ rel_clust = check_reload_required(clust_p, clust_p_mtime)
        # ~ rel_X = check_reload_required(X_p, X_p_mtime)
        # ~ if rel_clust or rel_X:
            # ~ load_cluster_data(dummy = False)
    # ~ except FileNotFoundError:
        # ~ load_cluster_data(dummy = True)


def require_auth(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view
