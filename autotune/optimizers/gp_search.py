from autotune.param_space import Real, Integer, Bool
from typing import Callable

from .hyper_param_opt import AbstractHyperParameterOptimizer
from bayes_opt import BayesianOptimization
import random
import numpy as np


class GaussianProcessOptimizer(AbstractHyperParameterOptimizer):
    name = "GP"
    def __init__(self, hyper_param_list: list, eval_fn: Callable, callback_fn: Callable=None, verbose: int = 0,
                 n_iterations=50, n_init_points=5, random_seed=None, gp_n_warmup=100000, gp_n_iter=25,
                 name="GP", **gp_params):
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.n_iterations = n_iterations
        self.n_init_points = n_init_points
        super().__init__(hyper_param_list, eval_fn, callback_fn, verbose)

        param_bounds = self._create_pbounds_from_param_space(hyper_param_list)
        print("Param bounds: ", param_bounds)
        self.bo = BayesianOptimization(f=lambda **params: eval_fn(self.transform_raw_param_samples(pop=params)),
                                  pbounds=param_bounds,
                                  verbose=0,
                                  random_state=random_seed)

        self.bo._acqkw = {'n_warmup': gp_n_warmup, 'n_iter': gp_n_iter}
        self.gp_params = gp_params if gp_params is not None else {"alpha": 1e-3, "n_restarts_optimizer": 5}

        self.name = name

    def transform_raw_param_samples(self, pop):
        param_dict = {}
        for i in range(len(self.hyper_param_list)):
            cur_hyp_param = self.hyper_param_list[i]
            param_dict[cur_hyp_param.name] = \
                cur_hyp_param.transform_raw_sample(pop[cur_hyp_param.name])
        return param_dict

    def _create_pbounds_from_param_space(self, hyper_param_list):
        param_bounds = {}
        for param in hyper_param_list:
            tmp_bound = None
            if type(param) is Real:
                tmp_bound = (param.space[0], param.space[1])
            elif type(param) is Integer:
                tmp_bound = (0, len(param.space) - 1e-5)
            elif type(param) is Bool:
                tmp_bound = (0, 2.0 - 1e-5)
            assert tmp_bound is not None
            param_bounds[param.name] = tmp_bound
        return param_bounds

    def _create_hyperparam_set_generator(self):
        def generator():
            gen = self.bo.create_maximize_generator(init_points=self.n_init_points, n_iter=self.n_iterations, acq="ei",
                                                    kappa=0.1, **self.gp_params)
            for x in gen():
                yield x
        return generator

    def maximize(self) -> dict:
        generator = self._create_hyperparam_set_generator()

        self._on_pre_hyp_opt_step()
        for next_hyperparam_set, eval_metric in generator():
            self._on_post_hyp_opt_step()
            next_hyperparam_set_dict = {}
            for i in range(len(next_hyperparam_set)):
                next_hyperparam_set_dict[self.hyper_param_list[i].name] = next_hyperparam_set[i]
            self._add_sampled_point(next_hyperparam_set_dict, eval_metric)
            self._on_optimizer_step_done(next_hyperparam_set_dict, eval_metric)
            self._on_pre_hyp_opt_step()

        self._on_optimizer_done()
        sorted_results = sorted(self.params_to_results_dict.items(), key=lambda kv: kv[1], reverse=True)
        if self.verbose == 1:
            print("======")
            print(len(sorted_results))
            for k, v in sorted_results[0:10]:
                print("{0}: {1}".format(k, v))
            print("======")
        return sorted_results
