# record-keeper

## Installation
```
pip install record-keeper
```

## The Problem:
When running machine-learning experiments, having more logged data is usually better than less. But adding new series of data to log can often require changes to your training code. When you want to log dozens of different series of data, your code starts to look awful.

## The Solution:

Use RecordKeeper, and easily add loggable information when you write a new class. The example below is modified from the [pytorch-metric-learning](https://github.com/KevinMusgrave/pytorch-metric-learning/blob/master/src/pytorch_metric_learning/miners/batch_hard_miner.py) library. 

First, create a list that contains the names of the attributes you want to record (```self._record_these``` in the example below).
```python
class BatchHardMiner(BaseTupleMiner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._record_these = ["hardest_triplet_dist", "hardest_pos_pair_dist", "hardest_neg_pair_dist"]
```

Then tell RecordKeeper the name of the list to read. RecordKeeper will log and save all the attributes described in the list. It'll search recursively too, if you have nested objects.
```python
from torch.utils.tensorboard import SummaryWriter
import record_keeper as record_keeper_package
from pytorch_metric_learning import miners

record_writer = record_keeper_package.RecordWriter(your_folder_for_logs)
tensorboard_writer = SummaryWriter(log_dir=your_tensorboard_folder)
record_keeper = record_keeper_package.RecordKeeper(tensorboard_writer, record_writer, ["_record_these"])

your_miner_dictionary = {"tuple_miner": miners.BatchHardMiner()}

# Then at each iteration of training:
record_keeper.update_records(your_miner_dictionary, current_iteration)
```

Now the attributes described in ```_record_these```, (specifically, ```hardest_triplet_dist```, ```hardest_pos_pair_dist```, and ```hardest_neg_pair_dist```) can be viewed on Tensorboard.

These data series are also saved in sqlite and CSV format. If you only want to use Tensorboard, then pass in only a SummaryWriter, and vice versa.

The dictionary that you pass into ```record_keeper.update_records``` can contain any number of objects, and for each one, RecordKeeper will check if the object has a "record_these" attribute. As long as you're making your dictionaries programmatically, it's possible to add large amounts of loggable data without clogging up your training code. See [pytorch-metric-learning](https://github.com/KevinMusgrave/pytorch-metric-learning/) and [powerful-benchmarker](https://github.com/KevinMusgrave/powerful-benchmarker/) to see RecordKeeper in action.  
