import logging
logging.basicConfig(level=logging.WARNING)
import pandas as pd

import argparse

import hpbandster.core.nameserver as hpns
import hpbandster.core.result as hpres

from hpbandster.optimizers import BOHB as BOHB
from chemception_transfer_worker import Chemception_wroker


parser = argparse.ArgumentParser(description='Example 1 - sequential and local execution.')
parser.add_argument('--min_budget',   type=float, help='Minimum budget used during the optimization.',    default=6)
parser.add_argument('--max_budget',   type=float, help='Maximum budget used during the optimization.',    default=114)
parser.add_argument('--n_iterations', type=int,   help='Number of iterations performed by the optimizer', default=4)
parser.add_argument('--n_workers', type=int,   help='Number of workers to run in parallel.', default=1)

args=parser.parse_args()


# Step 1: Start a nameserver (see example_1)
NS = hpns.NameServer(run_id='example2', host='127.0.0.1', port=None)
NS.start()

# Step 2: Start the workers
# Now we can instantiate the specified number of workers. To emphasize the effect,
# we introduce a sleep_interval of one second, which makes every function c
# take a bit of time. Note the additional id argument that helps separating the
# individual workers. This is necessary because every worker uses its processes
# ID which is the same for all threads here.
workers=[]
for i in range(args.n_workers):
    w = Chemception_wroker(sleep_interval = 0.5, nameserver='127.0.0.1', run_id='example2', id=i)
    w.run(background=True)
    workers.append(w)

# Step 3: Run an optimizer
# Now we can create an optimizer object and start the run.
# We add the min_n_workers argument to the run methods to make the optimizer wait
# for all workers to start. This is not mandatory, and workers can be added
# at any time, but if the timing of the run is essential, this can be used to
# synchronize all workers right at the start.
bohb = BOHB(  configspace = w.get_configspace(),
              run_id = 'example2',
              min_budget=args.min_budget, max_budget=args.max_budget
           )
res = bohb.run(n_iterations=args.n_iterations, min_n_workers=args.n_workers)

# Step 4: Shutdown
# After the optimizer run, we must shutdown the master and the nameserver.
bohb.shutdown(shutdown_workers=True)
NS.shutdown()

# Step 5: Analysis
# Each optimizer returns a hpbandster.core.result.Result object.
# It holds informations about the optimization run like the incumbent (=best) configuration.
# For further details about the Result object, see its documentation.
# Here we simply print out the best config and some statistics about the performed runs.
id2config = res.get_id2config_mapping()
incumbent = res.get_incumbent_id()

all_runs = res.get_all_runs()
pd.to_pickle(res, 'res.pkl')
pd.to_pickle(id2config[incumbent]['config'], 'best_config.pkl')

print('Best found configuration:', id2config[incumbent]['config'])
print('A total of %i unique configurations where sampled.' % len(id2config.keys()))
print('A total of %i runs where executed.' % len(res.get_all_runs()))
print('Total budget corresponds to %.1f full function evaluations.'%(sum([r.budget for r in all_runs])/args.max_budget))
print('Total budget corresponds to %.1f full function evaluations.'%(sum([r.budget for r in all_runs])/args.max_budget))
print('The run took  %.1f seconds to complete.'%(all_runs[-1].time_stamps['finished'] - all_runs[0].time_stamps['started']))