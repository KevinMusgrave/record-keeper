import sqlite3
import json

def adapt_list_to_JSON(lst):
    return json.dumps(lst).encode('utf8')

def convert_JSON_to_list(data):
    return json.loads(data.decode('utf8'))

sqlite3.register_adapter(list, adapt_list_to_JSON)
sqlite3.register_converter("json", convert_JSON_to_list)

class DBManager:
    def __init__(self, db_path, is_global=False):
        self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.is_global = is_global
        if self.is_global:
            self.create_experiment_ids_table()

    def create_experiment_ids_table(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS experiment_ids (id integer primary key autoincrement, experiment_name text unique)")
        self.conn.commit()

    def new_experiment(self, experiment_name):
        self.cursor.execute("INSERT INTO experiment_ids (experiment_name) values (?)", (experiment_name,))

    def get_experiment_id(self, experiment_name):
        self.cursor.execute("SELECT id FROM experiment_ids WHERE experiment_name=?", (experiment_name,))
        output = self.cursor.fetchall()
        assert len(output) == 1
        return output[0]["id"]

    def write(self, table_name, dict_of_lists, experiment_name=None):
        column_names = sorted(list(dict_of_lists.keys()))
        column_values, column_types = [], []

        for x in column_names:
            curr_value = dict_of_lists[x]
            if isinstance(curr_value[0], list):
                curr_type = "%s json"%x
            else:
                curr_type = "%s real"%x
            column_values.append(curr_value)
            column_types.append(curr_type)

        column_types = ", ".join(column_types)
        column_tuple = column_names

        if self.is_global:
            assert experiment_name is not None
            column_tuple = ["experiment_id"]+column_tuple
            column_types = "experiment_id integer, " + column_types
            experiment_id = (self.get_experiment_id(experiment_name),)*len(column_values[0])
            column_values = [experiment_id]+column_values

        column_tuple = str(tuple(column_tuple)) if len(column_tuple) > 1 else "(%s)"%column_tuple[0]
        prepared_statement_filler = "(%s)"%(("?, "*len(column_values))[:-2])
        column_values = [x for x in zip(*column_values)]

        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s (id integer primary key autoincrement, %s)"%(table_name, column_types))
        self.cursor.executemany("INSERT INTO %s %s VALUES %s"%(table_name, column_tuple, prepared_statement_filler), column_values)
        self.conn.commit()

    def query(self, query, values=()):
        self.cursor.execute(query, values)
        return self.cursor.fetchall()

    def table_exists(self, table_name):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"%table_name)
        return len(self.cursor.fetchall()) == 1

        