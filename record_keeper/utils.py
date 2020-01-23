import collections
import pickle
import csv
import os, errno

def save_pkl(obj, filename, protocol=None):
    # https://stackoverflow.com/a/19201448
    if protocol is None:
        protocol = pickle.HIGHEST_PROTOCOL
    with open(filename, "wb") as f:
        pickle.dump(obj, f, protocol)


def load_pkl(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def write_dict_of_lists_to_csv(obj, filename):
    # https://stackoverflow.com/a/23613603
    with open(filename, "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(obj.keys())
        writer.writerows(zip(*obj.values()))


def convert_to_scalar(v):
    try:
        return v.detach().item()  # pytorch
    except:
        try:
            return v[0]  # list or numpy
        except:
            return v  # already a scalar


def convert_to_list(v):
    try:
        return v.detach().tolist()  # pytorch
    except:
        try:
            return list(v)  # list or numpy
        except:
            return [v]  # already a scalar


def try_get_len(v):
    try:
        return len(v)  # most things
    except:
        try:
            return v.nelement()  # 0-d tensor
        except:
            return 0  # not a list

def is_list_and_has_more_than_one_element(input_val):
    return isinstance(input_val, collections.Sized) and try_get_len(input_val) > 1


def try_getting_dataparallel_module(input_obj):
    try:
        return input_obj.module
    except BaseException:
        return input_obj

def makedir_if_not_there(dir_name):
    try:
        os.makedirs(dir_name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise