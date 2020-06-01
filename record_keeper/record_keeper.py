#! /usr/bin/env python3
from . import utils as c_f
from .db_utils import DBManager
import collections
from cycler import cycler
import numpy as np
import glob
import os
import datetime


class RecordKeeper:
    def __init__(self, tensorboard_writer=None, record_writer=None, attributes_to_search_for=None, save_figures=False):
        self.tensorboard_writer = tensorboard_writer
        self.record_writer = record_writer
        self.attributes_to_search_for = [] if attributes_to_search_for is None else attributes_to_search_for
        self.save_figures = save_figures
        if save_figures:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            self.plt_module = plt

    def append_data(self, group_name, series_name, value, iteration):
        if self.tensorboard_writer:
            tag_name = '%s/%s' % (group_name, series_name)
            if not c_f.is_list_and_has_more_than_one_element(value):
                if all(not isinstance(v, (str, datetime.datetime)) for v in [value, iteration]):
                    self.tensorboard_writer.add_scalar(tag_name, value, iteration)
        if self.record_writer:
            self.record_writer.append(group_name, series_name, value)

    def update_records(self, record_these, global_iteration, custom_attr_func=None, input_group_name_for_non_objects=None, recursive_types=None):
        for name_in_dict, input_obj in record_these.items():
            if input_group_name_for_non_objects is not None:
                group_name = input_group_name_for_non_objects
                self.append_data(group_name, name_in_dict, input_obj, global_iteration)
            else:
                the_obj = c_f.try_getting_dataparallel_module(input_obj)
                attr_list = self.get_attr_list_for_record_keeper(the_obj)
                name = self.get_record_name(name_in_dict, the_obj) 
                for k in attr_list:
                    v = getattr(the_obj, k)                    
                    self.append_data(name, k, v, global_iteration)
                if custom_attr_func is not None:
                    for k, v in custom_attr_func(the_obj).items():
                        self.append_data(name, k, v, global_iteration)
                if recursive_types is not None:
                    try:
                        for attr_name, attr in vars(input_obj).items():
                            next_record_these = None
                            if isinstance(attr, dict):
                                next_record_these = {"%s_%s"%(name, k): v for k, v in attr.items()}
                            elif any(isinstance(attr, rt) for rt in recursive_types):
                                next_record_these = {"%s_%s"%(name, attr_name): attr}
                            if next_record_these:
                                self.update_records(next_record_these, global_iteration, custom_attr_func, input_group_name_for_non_objects, recursive_types)
                    except TypeError:
                        pass


    def get_attr_list_for_record_keeper(self, input_obj):
        attr_list = []
        for k in self.attributes_to_search_for:
            if (hasattr(input_obj, k)) and (getattr(input_obj, k) is not None):
                attr_list += getattr(input_obj, k)
        return attr_list

    def get_record_name(self, name_in_dict, input_obj, key_name=None):
        record_name = "%s_%s" % (name_in_dict, type(input_obj).__name__)
        if key_name:
            record_name += '_%s' % key_name
        return record_name

    def maybe_add_multi_line_plots_to_tensorboard(self, global_iteration):
        if self.record_writer and self.tensorboard_writer and self.save_figures:
            for group_name, dict_of_lists in self.record_writer.records.items():
                for series_name, v in dict_of_lists.items():
                    if len(v) > 0 and isinstance(v[0], list):
                        tag_name = '%s/%s' % (group_name, series_name)
                        figure = self.multi_line_plot(v)
                        self.tensorboard_writer.add_figure(tag_name, figure, global_iteration)

    def multi_line_plot(self, list_of_lists):
        # Each sublist represents a snapshot at an iteration.
        # Transpose so that each row covers many iterations.
        numpified = np.transpose(np.array(list_of_lists))
        fig = self.plt_module.figure()
        for sublist in numpified:
            self.plt_module.plot(np.arange(numpified.shape[1]), sublist)
        return fig

    def add_embedding_plot(self, embeddings, labels, tag, global_iteration):
        # The pytorch tensorboard function "add_embedding" doesn't seem to work
        # So this will have to do for now
        if self.tensorboard_writer and self.save_figures:
            label_set = np.unique(labels)
            num_classes = len(label_set)
            fig = self.plt_module.figure()
            self.plt_module.gca().set_prop_cycle(cycler("color", [self.plt_module.cm.nipy_spectral(i) for i in np.linspace(0, 0.9, num_classes)]))
            for i in range(num_classes):
                idx = labels == label_set[i]
                self.plt_module.plot(embeddings[idx, 0], embeddings[idx, 1], ".", markersize=1)
            self.tensorboard_writer.add_figure(tag, fig, global_iteration)

    def get_record(self, group_name):
        return self.record_writer.records[group_name]

    def save_records(self):
        self.record_writer.save_records()

    def query(self, query, *args, **kwargs):
        return self.record_writer.query(query, *args, **kwargs)

    def table_exists(self, table_name, *args, **kwargs):
        return self.record_writer.table_exists(table_name, *args, **kwargs)


class RecordWriter:
    def __init__(self, folder, global_db_path=None, experiment_name=None, is_new_experiment=True, save_lists=False):
        self.records = self.get_empty_nested_dict()
        self.folder = folder
        self.save_lists = save_lists
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

    def append(self, group_name, series_name, input_val):
        curr_dict = self.records[group_name]
        if isinstance(input_val, str):
            append_this = input_val
        elif c_f.is_list_and_has_more_than_one_element(input_val):
        	append_this = c_f.convert_to_list(input_val)
        else:
        	append_this = c_f.convert_to_scalar(input_val)
        c_f.try_append_to_dict(curr_dict, series_name, append_this)

    def save_records(self):
        for k, v in self.records.items():
            if len(v) > 0:
                len_of_list = len(v[sorted(list(v.keys()))[0]]) # get random sub list
                assert all(len(v[sub_key])==len_of_list for sub_key in v.keys()) # assert all lists are the same length
                if not self.save_lists: self.remove_lists(v)
                base_filename = os.path.join(self.folder, k)
                c_f.write_dict_of_lists_to_csv(v, base_filename+".csv", append=True)
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
                return {k:[row[k] for row in output] for k in output[0].keys()}
            return {}
        return output

    def table_exists(self, table_name, use_global_db=False):
        return self.get_db(use_global_db).table_exists(table_name)

