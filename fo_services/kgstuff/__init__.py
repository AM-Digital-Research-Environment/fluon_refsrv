import torch
import numpy as np

import logging
logger = logging.getLogger("kgstuff")

import os
# ~ from sys import path as syspathlib
# ~ syspathlib += [os.path.abspath('r/kgat_pytorch')]
import sys
sys.path.insert(0,'/app/fo_services/kgstuff/kgat_pytorch')


from data_loader.loader_kgat import DataLoaderKGAT
from model.KGAT import KGAT
from utils.log_helper import *
from utils.model_helper import *

from ..db import get_wisski_id_for_rec_id, get_recomm_id_for_wisski_user, fill_recomm_entity

class KGHandler():
  
  def load_entities_if_necessary(self, entity_file):
    if not os.path.exists(entity_file + '.mtime'):
      last_check = 0.0
    else:
      with open(entity_file + '.mtime', 'r') as _mtime:
        last_check = float(_mtime.readline().strip())
    
    timestamp = os.path.getmtime(entity_file)
    if last_check < timestamp:
      logger.debug(f"entites seem to have changed. reloading entities from {entity_file}")
      with open(entity_file + '.mtime', 'w') as _mtime:
        print(timestamp, file=_mtime)
      fill_recomm_entity(entity_file)
      
  
  def load_shit(self):
    logger.debug(f"loading models and stuff")
    # we want to mimic the args-Object here without calling parse_args...
    # https://stackoverflow.com/a/2827734
    args = lambda:None
    args.seed = 2024
    args.data_dir = '/'
    args.data_name = 'data'
    args.use_pretrain = 2
    args.pretrain_model_path = f'{args.data_dir}/{args.data_name}/model.pth'
    args.pretrain_embedding_dir = f'{args.data_dir}/{args.data_name}/'
    args.cf_batch_size = 1024 
    args.kg_batch_size = 2048 
    args.test_batch_size = 10000 
    args.embed_dim = 64 
    args.relation_dim = 64 
    args.laplacian_type = 'random-walk'
    args.aggregation_type = 'bi-interaction'
    args.conv_dim_list = '[64, 32, 16]'
    args.mess_dropout = '[0.1,0.1,0.1]'
    args.kg_l2loss_lambda = 1e-5
    args.cf_l2loss_lambda = 1e-5
    args.lr = 0.0001
    args.n_epoch = 10 
    args.stopping_steps = 50 
    args.cf_print_every = 1
    args.kg_print_every = 1
    args.evaluate_every = 10
    args.Ks = '[10]'
    
    # import recommendable items to database
    self.load_entities_if_necessary(f'{args.data_dir}/{args.data_name}/items_id.txt')
    
    torch.manual_seed(args.seed)# GPU / CPU
    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # load data
    self.data = DataLoaderKGAT(args, logging)
    
    # load model
    self.model = KGAT(args, self.data.n_users, self.data.n_entities, self.data.n_relations)
    self.model = load_model(self.model, args.pretrain_model_path)
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
