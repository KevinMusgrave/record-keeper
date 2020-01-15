# record-keeper

## Installation
```
pip install record-keeper
```

## The Problem:
When running machine-learning experiments, having more logged data is usually better than less. But adding new series of data to log can often require changes to your training code. When you want to log dozens of different series of data, your code starts to look awful.

## The Solution:

Use RecordKeeper, and easily add loggable information when you write a new class. The example below is taken from the [pytorch-metric-learning](https://github.com/KevinMusgrave/pytorch-metric-learning/blob/master/pytorch_metric_learning/losses/contrastive_loss.py) library. 

First, create a list that contains the names of the attributes you want to record (```self.record_these``` in the example below).
```python
class ContrastiveLoss(GenericPairLoss):
    def __init__(self, pos_margin=0, neg_margin=1, use_similarity=False, power=1, avg_non_zero_only=True, **kwargs):
        ...
        self.num_non_zero_pos_pairs = 0
        self.num_non_zero_neg_pairs = 0
        self.record_these = ["num_non_zero_pos_pairs", "num_non_zero_neg_pairs"]
        ...
    ...
```

Then tell RecordKeeper the name of the list to read. RecordKeeper will log and save all the attributes described in the list.
```python
from torch.utils.tensorboard import SummaryWriter
import record_keeper as record_keeper_package
from pytorch_metric_learning import losses

pickler_and_csver = record_keeper_package.PicklerAndCSVer(your_folder_for_logs)
tensorboard_writer = SummaryWriter(log_dir=your_tensorboard_folder)
record_keeper = record_keeper_package.RecordKeeper(tensorboard_writer, pickler_and_csver, ["record_these"])

your_loss_dictionary = {"metric_loss": losses.ContrastiveLoss()}

# Then at each iteration of training:
record_keeper.update_records(your_loss_dictionary, current_iteration)
```

Now the attributes described in ```record_these```, (specifically, ```num_non_zero_pos_pairs``` and ```num_non_zero_neg_pairs```) can be viewed on Tensorboard.

![nonzero_pairs_example](https://github.com/KevinMusgrave/powerful-benchmarker/blob/master/readme_imgs/nonzero_pairs_example.png)

These data series are also saved in pickle and CSV format. If you only want to use Tensorboard, then pass in only a SummaryWriter, and vice versa.

The dictionary that you pass into ```record_keeper.update_records``` can contain any number of objects, and for each one, RecordKeeper will check if the object has a "record_these" attribute. As long as you're making your dictionaries programmatically, it's possible to add large amounts of loggable data without clogging up your training code. See [pytorch-metric-learning](https://github.com/KevinMusgrave/pytorch-metric-learning/) and [powerful-benchmarker](https://github.com/KevinMusgrave/powerful-benchmarker/) to see RecordKeeper in action.  
