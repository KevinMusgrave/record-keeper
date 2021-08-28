import collections
import datetime
import glob
import os

from . import utils as c_f
from .db_utils import DBManager


class RecordKeeper:
    def __init__(
        self,
        tensorboard_writer=None,
        record_writer=None,
        attributes_to_search_for=None,
    ):
        self.tensorboard_writer = tensorboard_writer
        self.record_writer = record_writer
        self.attributes_to_search_for = (
            [] if attributes_to_search_for is None else attributes_to_search_for
        )
        self.hash_map = {}

    def append_data(self, group_name, series_name, value, iteration):
        if self.tensorboard_writer:
            tag_name = "%s/%s" % (group_name, series_name)
            if (value is not None) and (
                not c_f.is_list_and_has_more_than_one_element(value)
            ):
                if all(
                    not isinstance(v, (str, datetime.datetime))
                    for v in [value, iteration]
                ):
                    self.tensorboard_writer.add_scalar(
                        tag_name, c_f.convert_to_scalar(value), iteration
                    )
        if self.record_writer:
            self.record_writer.append(group_name, series_name, value, iteration)

    def append_primitive(self, group, series, value, global_iteration):
        if group == "":
            raise ValueError("group cannot be an empty string")
        new_group = c_f.hash_if_too_long(group)
        if new_group != group:
            self.hash_map[new_group] = group
        self.append_data(new_group, series, value, global_iteration)

    def update_records(
        self,
        record_these,
        global_iteration,
        custom_attr_func=None,
        parent_name="",
        recursive_types=None,
    ):
        kwargs = {
            "global_iteration": global_iteration,
            "custom_attr_func": custom_attr_func,
            "recursive_types": recursive_types,
        }

        for name_in_dict, input_obj in record_these.items():
            if c_f.is_primitive(input_obj):
                self.append_primitive(
                    parent_name,
                    name_in_dict,
                    input_obj,
                    global_iteration,
                )
            elif isinstance(input_obj, dict):
                next_parent_name = c_f.next_parent_name(parent_name, name_in_dict)
                self.update_records(input_obj, parent_name=next_parent_name, **kwargs)
            else:
                the_obj = c_f.try_getting_dataparallel_module(input_obj)
                attr_list = self.get_attr_list_for_record_keeper(the_obj)
                name = self.get_record_name(name_in_dict, the_obj)
                next_record_these = {f"{k}": getattr(the_obj, k) for k in attr_list}
                next_parent_name = c_f.next_parent_name(parent_name, name)
                self.update_records(
                    next_record_these, parent_name=next_parent_name, **kwargs
                )
                if custom_attr_func is not None:
                    self.update_records(
                        custom_attr_func(the_obj),
                        parent_name=next_parent_name,
                        **kwargs,
                    )
                if recursive_types is not None:
                    for attr_name, attr in vars(input_obj).items():
                        if any(isinstance(attr, rt) for rt in recursive_types):
                            next_record_these = {f"{name}_{attr_name}": attr}
                            self.update_records(next_record_these, **kwargs)
                        elif isinstance(attr, (list, tuple)):
                            if any(
                                all(isinstance(aaa, rt) for aaa in attr)
                                for rt in recursive_types
                            ):
                                for i, aaa in enumerate(attr):
                                    next_record_these = {f"{name}_{attr_name}{i}": aaa}
                                    self.update_records(next_record_these, **kwargs)

    def get_attr_list_for_record_keeper(self, input_obj):
        attr_list = []
        for k in self.attributes_to_search_for:
            if (hasattr(input_obj, k)) and (getattr(input_obj, k) is not None):
                attr_list += getattr(input_obj, k)
        return attr_list

    def get_record_name(self, name_in_dict, input_obj, key_name=None):
        obj_type = type(input_obj).__name__
        if obj_type in c_f.unneeded_descriptors():
            record_name = name_in_dict
        else:
            record_name = "%s_%s" % (name_in_dict, obj_type)
        if key_name:
            record_name += "_%s" % key_name
        return record_name

    def get_record(self, group_name):
        return self.record_writer.records[group_name]

    def save_records(self):
        self.record_writer.save_records()
        if len(self.hash_map) > 0:
            c_f.write_dict_to_json(
                self.hash_map, os.path.join(self.record_writer.folder, "hash_map.json")
            )

    def query(self, query, *args, **kwargs):
        return self.record_writer.query(query, *args, **kwargs)

    def table_exists(self, table_name, *args, **kwargs):
        return self.record_writer.table_exists(table_name, *args, **kwargs)


class RecordWriter:
    def __init__(
        self,
        folder,
        global_db_path=None,
        experiment_name=None,
        is_new_experiment=True,
        save_lists=False,
    ):
        self.records = self.get_empty_nested_dict()
        self.folder = folder
        self.save_lists = save_lists
        self.records_that_are_lists = set()
        c_f.makedir_if_not_there(self.folder)
        self.local_db = DBManager(os.path.join(self.folder, "logs.db"), is_global=False)
        self.global_db = None
        self.experiment_name = experiment_name
        if global_db_path:
            assert self.experiment_name is not None
            self.global_db = DBManager(global_db_path, is_global=True)
            if is_new_experiment:
                self.global_db.new_experiment(self.experiment_name)

    def get_empty_nested_dict(self):
        return collections.defaultdict(lambda: collections.OrderedDict())

    def append(self, group_name, series_name, input_val, iteration):
        curr_dict = self.records[group_name]
        if isinstance(input_val, str):
            append_this = input_val
        elif c_f.is_list_and_has_more_than_one_element(input_val):
            append_this = c_f.convert_to_list(input_val)
            self.records_that_are_lists.add((group_name, series_name))
        else:
            append_this = c_f.convert_to_scalar(input_val)
        c_f.try_add_to_dict(curr_dict, series_name, append_this, iteration)

    def save_records(self):
        for k, v in self.records.items():
            if len(v) > 0:
                v = c_f.separate_iterations_from_series(v)
                len_of_list = len(v[sorted(list(v.keys()))[0]])  # get random sub list
                assert all(
                    len(v[sub_key]) == len_of_list for sub_key in v.keys()
                )  # assert all lists are the same length
                if not self.save_lists:
                    self.remove_lists(v)
                base_filename = os.path.join(self.folder, k)
                c_f.write_dict_of_lists_to_csv(v, base_filename + ".csv", append=True)
                self.local_db.write(k, v)
                if self.global_db is not None:
                    self.global_db.write(k, v, experiment_name=self.experiment_name)
        self.records = self.get_empty_nested_dict()

    def remove_lists(self, record):
        remove_keys = []
        for k, v in record.items():
            if isinstance(v[0], list):
                remove_keys.append(k)
        for k in remove_keys:
            record.pop(k, None)

    def get_db(self, use_global_db):
        return self.global_db if use_global_db else self.local_db

    def query(self, query, values=(), use_global_db=False, return_dict=False):
        output = self.get_db(use_global_db).query(query, values)
        if return_dict:
            if len(output) > 0:
                return {k: [row[k] for row in output] for k in output[0].keys()}
            return {}
        return output

    def table_exists(self, table_name, use_global_db=False):
        return self.get_db(use_global_db).table_exists(table_name)
