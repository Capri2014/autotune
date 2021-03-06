from typing import Callable

from .hyper_param_opt import AbstractHyperParameterOptimizer
from autotune.param_space import Param


class GridSearchOptimizer(AbstractHyperParameterOptimizer):
    name = "GridSearch"

    def __init__(self, hyper_param_list: list, eval_fn: Callable, callback_fn: Callable = None, n_iterations=None,
                 verbose: int = 0, random_seed=None, name="GridSearch"):
        super().__init__(hyper_param_list=hyper_param_list, eval_fn=eval_fn, callback_fn=callback_fn,
                         n_iterations=n_iterations, verbose=verbose, random_seed=random_seed, name=name)

    def _get_all_param_combinations(self, dicts: list=None, tmp_dict: dict=None, i: int=0):
        """
        Recursively creates a list of dicts holding all possible combinations of parameters from cfg.parameter_space
        :param dicts: list of multiple dict instances
        :param tmp_dict: instance of current parameter dictionary
        :param i: parameter index
        :return: list of parameter dictionaries
        """
        if i == 0:
            tmp_dict = {}
            dicts = []
        if i == len(self.hyper_param_list):
            dicts.extend([tmp_dict])
        else:
            param = list(self.hyper_param_list)[i]
            generator = param.create_generator()
            for j in generator():
                tmp_dict[param.name] = j
                self._get_all_param_combinations(dicts, tmp_dict.copy(), i + 1)
        return dicts

    def _create_hyperparam_set_generator(self):
        hyperparam_combinations = self._get_all_param_combinations()
        if self.verbose >= 2:
            print("All hyperparameter combinations: {0}".format(hyperparam_combinations))

        def generator() -> Param:
            for x in hyperparam_combinations:
                yield x

        return generator