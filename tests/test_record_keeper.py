import shutil
import unittest

import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter

from record_keeper import RecordKeeper, RecordWriter

FOLDER = "test_folder"


class TestRecordKeeper(unittest.TestCase):
    def test_record_keeper(self):
        tensorboard_writer = SummaryWriter(
            log_dir=FOLDER, max_queue=1000000, flush_secs=30
        )
        record_writer = RecordWriter(folder=FOLDER)
        record_keeper = RecordKeeper(
            tensorboard_writer=tensorboard_writer,
            record_writer=record_writer,
            attributes_to_search_for=["_record_these"],
        )

        for i in range(10):
            if i < 5:
                record = {
                    "A": i,
                    "B": 10 - np.array([i * 2]),
                    "C": torch.tensor(i * 1.25),
                    "D": "hello",
                    "F": {"goodbye": "Sunday"},
                }
            else:
                record = {"A": 500, "C": float("inf")}
            if i == 9:
                record["F"] = {"goodbye": "Monday"}
            record_keeper.update_records(record, i, parent_name="stuff")

        record_keeper.update_records({"E": "new column"}, 11, parent_name="stuff")
        record_keeper.save_records()
        record_keeper.tensorboard_writer.flush()

        result = record_keeper.query("SELECT A from stuff", return_dict=True)
        correct = list(range(5)) + [500] * 5 + [None]
        self.assertTrue(result["A"] == correct)

        result = record_keeper.query("SELECT B from stuff", return_dict=True)
        correct = list(10 - np.arange(5) * 2) + [None] * 6
        self.assertTrue(result["B"] == correct)

        result = record_keeper.query("SELECT C from stuff", return_dict=True)
        correct = list(np.arange(5) * 1.25) + [float("inf")] * 5 + [None]
        self.assertTrue(result["C"] == correct)

        result = record_keeper.query("SELECT D from stuff", return_dict=True)
        correct = ["hello"] * 5 + [None] * 6
        self.assertTrue(result["D"] == correct)

        result = record_keeper.query("SELECT E from stuff", return_dict=True)
        correct = [None] * 10 + ["new column"]
        self.assertTrue(result["E"] == correct)

        result = record_keeper.query("SELECT * from stuff_F", return_dict=True)
        correct = ["Sunday"] * 5 + ["Monday"]
        self.assertTrue(result["goodbye"] == correct)
        self.assertTrue(result["~iteration~"] == [0, 1, 2, 3, 4, 9])

        shutil.rmtree(FOLDER)

    def test_no_dict_attribute(self):
        x = torch.nn.CrossEntropyLoss()
        record_keeper = RecordKeeper(
            record_writer=RecordWriter(folder=FOLDER),
            attributes_to_search_for=["_record_these"],
        )
        record_keeper.update_records(
            {"loss_fn": x}, 0, recursive_types=[torch.nn.Module, dict]
        )
