import numpy as np

import logging
logger = logging.getLogger(__name__)

from ..db import is_new_user, update_model_infos, export_user_data, export_interaction_data, get_itemlist_from_model, get_itemlist_from_cluster

import os


class KGHandler():
  
  def __init__(self):
    # we want to mimic the self.args-Object here without calling parse_self...
    # https://stackoverflow.com/a/2827734
    self.data_dir = '/'
    self.data_name = 'data'
    
    
  def fill_sample_users(self):
    # for testing purposes: fill db with random user info
    import os, random
    from ..db import db_session, Base, engine
    from ..models import InteractionHistory, RecommUser, UserRecommendationModel, ItemClusterInfo
    
    try:
        UserRecommendationModel.__table__.drop(engine)
        InteractionHistory.__table__.drop(engine)
        RecommUser.__table__.drop(engine)
        ItemClusterInfo.__table__.drop(engine)
    except:
        pass
    Base.metadata.create_all(bind=engine)
    
    N = 3
    recomm_file = f'{self.data_dir}/{self.data_name}/recommendations.csv'
    if os.path.exists(recomm_file):
        with open(recomm_file, 'rb') as f:
            try:  # catch OSError in case of a one line file 
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()
            N = int(last_line.split(' ')[0])+1
    logger.warning(f"remember: I am creating {N} dummy users right now in KGHandler.fill_sample_data!")
    
    for u in range(N):
        db_session.add(RecommUser(u))
    db_session.commit()
    return N
    
  def fill_sample_interactions(self, n_users, n_interact_min,n_interact_max):
      # for testing purposes: fill db with random user info
    import os, random
    from ..db import db_session, Base, engine
    from ..models import InteractionHistory
    items = []
    with open(f'{self.data_dir}/{self.data_name}/items_id.txt', 'r') as f:
        field = f.readline().strip().split(' ')[2]
        if field != 'wisskiid':
            raise Exception("Deep Shit Error Code")
        for line in f:
            items.append(int(line.strip().split(' ')[2]))
    
    for u in range(n_users):
        n = random.choice(range(n_interact_min,n_interact_max+1))
        interactions = random.sample(items, k=n)
        for i in interactions:
            db_session.add(InteractionHistory(u, i))
        
    db_session.commit()
  
  def load_shit(self): 
    # import recommendable items to database
    # ~ self.N = self.fill_sample_users()
    
    # ~ n_interact_min = 10
    # ~ n_interact_max = 50
    # ~ self.fill_sample_interactions(self.N,n_interact_min,n_interact_max)
    pass

  def reload_data(self):
    clu_file = f'{self.data_dir}/{self.data_name}/cluster.csv'
    rec_file = f'{self.data_dir}/{self.data_name}/recommendations.csv'
    res = update_model_infos(clu_file, rec_file)
    
    # ~ n_interact_min = 10
    # ~ n_interact_max = 50
    # ~ self.fill_sample_interactions(self.N,n_interact_min,n_interact_max)
    
    return res

  def export_user_data(self):
    usr_file = '/app/known_users.tsv'
    export_user_data(usr_file)
    return usr_file

  def export_interaction_data(self):
    intr_file = '/app/user_interactions.tsv'
    export_interaction_data(intr_file)
    return intr_file

  def recommend_me_something(self,user_id,max_n,start_at):
    u = int(user_id)
    if start_at > 0:
        max_n += start_at
    if is_new_user(u):
        recs = get_itemlist_from_cluster(10)
        logger.debug(f"new user. get itemlist from cluster: {recs}")
    else:
        recs = get_itemlist_from_model(u, max_n)
        if len(recs) == 0:
            recs = get_itemlist_from_cluster(10)
            logger.debug(f"known user. no recommendations. get itemlist from cluster: {recs}")
        else:
            logger.debug(f"known user. get itemlist from model: {recs}")
    if start_at > 0:
        recs = recs[start_at:len(recs)]
    logger.debug(f"recommending something for wisski user {user_id}")
    return ','.join(str(r[0]) for r in recs)
