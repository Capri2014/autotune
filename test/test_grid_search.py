from optimizers import grid_search

from test.test_data import sample_params, sample_eval_fn, sample_callback_fn

def test_grid_search():
    optimizer = grid_search.GridSearchOptimizer(sample_params, sample_eval_fn, callback_fn=sample_callback_fn)
    results = optimizer.maximize()
    assert(results[0][1] == 14.0)


