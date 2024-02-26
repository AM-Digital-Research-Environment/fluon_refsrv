import torch
import numpy as np

import logging
logger = logging.getLogger(__name__)

from ..db import get_wisski_id_for_rec_id, get_recomm_id_for_wisski_user, fill_recomm_entity

import os
import sys
sys.path.insert(0,'/app/fo_services/kgstuff/kgat_pytorch')


from data_loader.loader_kgat import DataLoaderKGAT
from model.KGAT import KGAT
from utils.model_helper import *


class KGHandler():
  
  def load_entities_if_necessary(self, entity_file):
    mtime_file = f'/app/{os.path.basename(entity_file)}.mtime'
    if not os.path.exists(mtime_file):
      last_check = 0.0
    else:
      with open(mtime_file, 'r') as _mtime:
        last_check = float(_mtime.readline().strip())
    
    timestamp = os.path.getmtime(entity_file)
    if last_check < timestamp:
      logger.debug(f"entites seem to have changed. reloading entities from {entity_file}")
      with open(mtime_file, 'w') as _mtime:
        print(timestamp, file=_mtime)
      fill_recomm_entity(entity_file) 
  
  
  def __init__(self):
    # we want to mimic the self.args-Object here without calling parse_self.args...
    # https://stackoverflow.com/a/2827734
    self.args = lambda:None
    self.args.seed = 2024
    self.args.data_dir = '/'
    self.args.data_name = 'data'
    self.args.use_pretrain = 2
    self.args.pretrain_model_path = f'{self.args.data_dir}/{self.args.data_name}/model.pth'
    self.args.pretrain_embedding_dir = f'{self.args.data_dir}/{self.args.data_name}/'
    self.args.cf_batch_size = 1024 
    self.args.kg_batch_size = 2048 
    self.args.test_batch_size = 10000 
    self.args.embed_dim = 64 
    self.args.relation_dim = 64 
    self.args.laplacian_type = 'random-walk'
    self.args.aggregation_type = 'bi-interaction'
    self.args.conv_dim_list = '[64, 32, 16]'
    self.args.mess_dropout = '[0.1,0.1,0.1]'
    self.args.kg_l2loss_lambda = 1e-5
    self.args.cf_l2loss_lambda = 1e-5
    self.args.lr = 0.0001
    self.args.n_epoch = 10 
    self.args.stopping_steps = 50 
    self.args.cf_print_every = 1
    self.args.kg_print_every = 1
    self.args.evaluate_every = 10
    self.args.Ks = '[10]'
  
  def load_shit(self): 
    # import recommendable items to database
    self.load_entities_if_necessary(f'{self.args.data_dir}/{self.args.data_name}/items_id.txt') 
     
    torch.manual_seed(self.args.seed)# GPU / CPU
    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # load data
    self.data = DataLoaderKGAT(self.args, logging)
    
    # load model
    self.model = KGAT(self.args, self.data.n_users, self.data.n_entities, self.data.n_relations)
    self.model = load_model(self.model, self.args.pretrain_model_path)
    self.model.to(self.device)
    self.evaluate(self.data.n_items, self.data.test_batch_size, self.data.test_user_dict)
  
  def evaluate(self,  n_items, test_batch_size, test_user_dict):
    self.model.eval()

    user_ids = list(test_user_dict.keys())
    user_ids_batches = [user_ids[i: i + test_batch_size] for i in range(0, len(user_ids), test_batch_size)]
    user_ids_batches = [torch.LongTensor(d) for d in user_ids_batches]

    item_ids = torch.arange(n_items, dtype=torch.long).to(self.device)

    for batch_user_ids in user_ids_batches:
        batch_user_ids = batch_user_ids.to(self.device)
        
        with torch.no_grad():
            batch_scores = self.model(batch_user_ids, item_ids, mode='predict')       # (n_batch_users, n_items)

        batch_scores = batch_scores.cpu()
        print("batch_scores.shape:",batch_scores.shape)
        
        try:
            _, rank_indices = torch.sort(batch_scores.cuda(), descending=True)    # try to speed up the sorting process
        except:
            _, rank_indices = torch.sort(batch_scores, descending=True)
        self.rank_indices = rank_indices.cpu()
        print("rank_indices.shape:", self.rank_indices.shape)
        

  def recommend_me_something(self,user_id):
    u = int(user_id)
    r_id = get_recomm_id_for_wisski_user(u)
    logger.debug(f"recommending something for wisski user {user_id} ({r_id})")
    if r_id < self.rank_indices.shape[0]:
      return [get_wisski_id_for_rec_id(i) for i in self.rank_indices[u,:].tolist()]
    return "1,2,3,4,5,6,10"
