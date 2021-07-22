import csv
import errno
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
                header = next(reader)
                if len(header) > 0 and header == list(obj.keys()):
                    write_header = False

    # https://stackoverflow.com/a/23613603
    with open(filename, open_as) as outfile:
        writer = csv.writer(outfile)
        if write_header:
            writer.writerow(obj.keys())
        writer.writerows(zip(*obj.values()))


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
    return isinstance(x, (int, float, str, bool, list, np.ndarray, torch.Tensor))


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
