import csv
import errno
import hashlib
import json
import os
import pickle
from collections import defaultdict
from collections.abc import Sized

import numpy as np
import torch


def save_pkl(obj, filename, protocol=None):
    # https://stackoverflow.com/a/19201448
    if protocol is None:
        protocol = pickle.DEFAULT_PROTOCOL
    with open(filename, "wb") as f:
        pickle.dump(obj, f, protocol)


def load_pkl(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def write_dict_of_lists_to_csv(obj, filename, append=False):
    write_header = True
    open_as = "w"
    if append:
        open_as = "a"
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                reader = csv.reader(f)
                all_header_rows = list(reader)
                for row in all_header_rows[::-1]:
                    if len(row) > 0 and row[0] == "~iteration~":
                        write_header = row != list(obj.keys())
                        break

    # https://stackoverflow.com/a/23613603
    with open(filename, open_as) as outfile:
        writer = csv.writer(outfile)
        if write_header:
            writer.writerow(obj.keys())
        writer.writerows(zip(*obj.values()))


# https://stackoverflow.com/a/8685873
def write_dict_to_json(obj, filename):
    with open(filename, "w") as f:
        json.dump(obj, f, indent=2)


def convert_to_scalar(v):
    try:
        return v.detach().item()  # pytorch
    except AttributeError:
        try:
            output = v[0]  # list or numpy
            if isinstance(output, (np.int32, np.int64)):
                output = int(output)
            return output
        except (TypeError, IndexError):
            return v  # already a scalar


def convert_to_list(v):
    try:
        return v.detach().tolist()  # pytorch
    except AttributeError:
        try:
            return list(v)  # list or numpy
        except TypeError:
            return [v]  # already a scalar


def try_get_len(v):
    try:
        return len(v)  # most things
    except TypeError:
        try:
            return v.nelement()  # 0-d tensor
        except AttributeError:
            return 0  # not a list


def is_list_and_has_more_than_one_element(input_val):
    return isinstance(input_val, Sized) and try_get_len(input_val) > 1


def try_getting_dataparallel_module(input_obj):
    try:
        return input_obj.module
    except AttributeError:
        return input_obj


def makedir_if_not_there(dir_name):
    try:
        os.makedirs(dir_name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def try_add_to_dict(input_dict, key, value, iteration):
    try:
        input_dict[key][iteration] = value
    except KeyError:
        input_dict[key] = {iteration: value}


def unneeded_descriptors():
    return ["ModuleDict", "ModuleList"]


def is_primitive(x):
    return isinstance(
        x, (int, float, str, bool, list, np.int32, np.int64, np.ndarray, torch.Tensor)
    )


def separate_iterations_from_series(records):
    all_iterations = set()

    for series_name, series in records.items():
        all_iterations.update(series.keys())

    all_iterations = sorted(list(all_iterations))

    output = {"~iteration~": all_iterations}
    for series_name, series in records.items():
        output[series_name] = []
        for i in all_iterations:
            output[series_name].append(series.get(i, None))

    return output


def hash_if_too_long(x):
    y = x.split("_")
    if len(y) <= 2:
        return x
    start = y.pop(0)
    end = y.pop(-1)
    new_x = "_".join(y)
    if len(new_x) <= 64:
        return x
    h = f"{hashlib.sha256(new_x.encode('utf-8')).hexdigest()}"
    return f"{start}_{h}_{end}"


def next_parent_name(parent_name, name):
    if parent_name != "":
        return f"{parent_name}_{name}"
    return name
