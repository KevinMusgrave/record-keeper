import sqlite3
import json
import datetime

def adapt_list_to_JSON(lst):
    return json.dumps(lst).encode('utf8')

def convert_JSON_to_list(data):
    return json.loads(data.decode('utf8'))

sqlite3.register_adapter(list, adapt_list_to_JSON)
sqlite3.register_converter("json", convert_JSON_to_list)

class DBManager:
    def __init__(self, db_path, is_global=False):
        self.db_path = db_path
        self.is_global = is_global
        if self.is_global:
            self.create_experiment_ids_table()


    def create_experiment_ids_table(self):
        self.execute("CREATE TABLE IF NOT EXISTS experiment_ids (id integer primary key autoincrement, experiment_name text unique, has_records integer)")


    def new_experiment(self, experiment_name):
        if not self.experiment_name_has_records(experiment_name):
            self.delete_experiment(experiment_name)
        self.execute("INSERT INTO experiment_ids (experiment_name, has_records) values (?, ?)", (experiment_name, int(False)))


    def delete_experiment(self, experiment_name):
        self.execute("DELETE FROM experiment_ids WHERE experiment_name=?", (experiment_name,))


    def experiment_name_has_records(self, experiment_name):
        has_records = self.execute("SELECT has_records FROM experiment_ids WHERE experiment_name=?", (experiment_name, ), fetch=True)
        if len(has_records) > 0:
            return bool(has_records[0]["has_records"])
        return False


    def get_experiment_id(self, experiment_name):
        output = self.execute("SELECT id FROM experiment_ids WHERE experiment_name=?", (experiment_name,), fetch=True)
        return output[0]["id"]


    def write(self, table_name, dict_of_lists, experiment_name=None):
        column_names_list = list(dict_of_lists.keys())
        column_values, column_types_list = [], []

        for i, x in enumerate(column_names_list):
            curr_value = dict_of_lists[x]
            if isinstance(curr_value[0], list):
                curr_type = "%s json"%x
                column_names_list[i] += "_list"
            elif isinstance(curr_value[0], datetime.datetime):
                curr_type = "%s timestamp"%x
            elif isinstance(curr_value[0], str):
                curr_type = "%s text"%x
            else:
                curr_type = "%s real"%x
            column_values.append(curr_value)
            column_types_list.append(curr_type)

        column_types = ", ".join(column_types_list)
        column_tuple = column_names_list

        if self.is_global:
            assert experiment_name is not None
            column_tuple = ["experiment_id"]+column_tuple
            column_types = "experiment_id integer, %s, FOREIGN KEY(experiment_id) REFERENCES experiment_ids(id) ON UPDATE CASCADE ON DELETE CASCADE"%column_types
            experiment_id = (self.get_experiment_id(experiment_name),)*len(column_values[0])
            column_values = [experiment_id]+column_values

        column_tuple = str(tuple(column_tuple)) if len(column_tuple) > 1 else "(%s)"%column_tuple[0]
        prepared_statement_filler = "(%s)"%(("?, "*len(column_values))[:-2])
        column_values = [x for x in zip(*column_values)]

        self.execute("CREATE TABLE IF NOT EXISTS %s (id integer primary key autoincrement, %s)"%(table_name, column_types))

        try:
            self.execute("INSERT INTO %s %s VALUES %s"%(table_name, column_tuple, prepared_statement_filler), column_values, many=True)
        except sqlite3.OperationalError:
            existing_column_names_list = [x['name'] for x in self.execute("PRAGMA table_info(%s)"%table_name, fetch=True)]
            for i, x in enumerate(column_names_list):
                if x not in existing_column_names_list:
                    self.execute("ALTER TABLE %s ADD COLUMN %s %s"%(table_name, x, column_types_list[i]))
            self.execute("INSERT INTO %s %s VALUES %s"%(table_name, column_tuple, prepared_statement_filler), column_values, many=True)

        if self.is_global:
            self.execute("UPDATE experiment_ids SET has_records=? WHERE experiment_name=?", (int(True), experiment_name))


    def query(self, query, values=()):
        return self.execute(query, values, fetch=True)


    def table_exists(self, table_name):
        matches = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"%table_name, fetch=True)
        return len(matches) == 1


    def execute(self, query, values=(), many=False, fetch=False):
        self.open()
        self.cursor.executemany(query, values) if many else self.cursor.execute(query, values)
        self.conn.commit()
        output = self.cursor.fetchall() if fetch else None
        self.conn.close()
        return output


    def open(self):
        self.conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=60)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        