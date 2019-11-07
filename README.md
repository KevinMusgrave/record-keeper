# record_keeper

## Installation
```
pip install record_keeper
```

Easily add loggable information when you write a new function. First, create a list that contains the names of the attributes you want to record ("self.record_these" in the example below).
```
class YourNewLossFunction:
  def __init__(self, **kwargs):
    self.avg_embedding_norm = 0
    self.some_other_useful_stat = 0
    self.record_these = ["avg_embedding_norm", "some_other_useful_stat"]
    super().__init__(**kwargs)
    
  def compute_loss(self, embeddings, labels):
    self.avg_embedding_norm = torch.mean(torch.norm(embeddings, p=2, dim=1))
    self.some_other_useful_stat = some_cool_function(embeddings)
```

Then tell RecordKeeper the name of the list to read. RecordKeeper will then log and save all the attributes described in the list.
```
from torch.utils.tensorboard import SummaryWriter
import record_keeper as record_keeper_package

pickler_and_csver = record_keeper_package.PicklerAndCSVer(your_folder_for_logs)
tensorboard_writer = SummaryWriter(log_dir=your_tensorboard_folder)
record_keeper = record_keeper_package.RecordKeeper(tensorboard_writer, pickler_and_csver, ["record_these"])

# Then during training:
recorder.update_records(your_dict_of_objects, current_iteration)

```


