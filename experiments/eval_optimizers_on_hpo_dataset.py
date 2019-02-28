import pickle
import numpy as np
from optimizers import grid_search, random_search, ga_search, gp_search, tpe_search
from preprocess_hpo_dataset import create_index_param_space


optimizers = [gp_search.GaussianProcessOptimizer, random_search.RandomSearchOptimizer, ga_search.GeneticAlgorithmSearch,
             tpe_search.TPEOptimizer]#grid_search.GridSearchOptimizer ]

# Load preprocessed data dicts
with open('../hpo_dataset/preprocessed_data.pickle', 'rb') as handle:
    classifier_indexed_params = pickle.load(handle)

with open('../hpo_dataset/preprocessed_param_values.pickle', 'rb') as handle:
    classifier_param_values = pickle.load(handle)

classifier_param_spaces = {}
for k in classifier_indexed_params.keys():
    param_list = create_index_param_space(classifier_param_values[k])
    for p in param_list:
        print(p.name, p.space)
    classifier_param_spaces[k] = param_list

n_datasets = 2 # 42
n_repititions_per_optimizer = 2 # 10
optimizer_steps = 50 # 100
optimizer_results = {}

for optimizer in optimizers:
    optimizer_results[optimizer.name] = {}
    for classifier in classifier_indexed_params.keys():
        optimizer_results[optimizer.name][classifier] = []
        for dataset_idx in range(n_datasets):
            tmp_agg_results = []
            for i in range(n_repititions_per_optimizer):
                print("Parameter space for classifier {0} is :".format(classifier))
                for p in classifier_param_spaces[classifier]:
                    print(p.name, p.space)

                def eval_fn(params):
                    modified_params = dict(params)
                    if modified_params['preprocessing'] == 0:
                        del modified_params['pca:keep_variance']
                    # minimize val error
                    return -classifier_indexed_params[classifier][frozenset(modified_params.items())][dataset_idx]

                def sample_callback_fn(**params):
                    print(params)

                print(optimizer.name)
                tmp_opt = optimizer(classifier_param_spaces[classifier], eval_fn, callback_fn=sample_callback_fn,
                                    n_iterations=optimizer_steps)
                _ = tmp_opt.maximize()
                tmp_results = list(zip(tmp_opt.hyperparameter_set_per_timestep, tmp_opt.eval_fn_per_timestep))
                tmp_agg_results += [tmp_results]
                print("Len tmp results: ", len(tmp_results))
            optimizer_results[optimizer.name][classifier] += [tmp_agg_results]



with open('../experiment_results/hpo_dataset_optimizer_results.pickle', 'wb') as handle:
    pickle.dump(optimizer_results, handle, protocol=pickle.HIGHEST_PROTOCOL)
