import sqlite3

class DBManager:
	def __init__(self, db_path):
		self.conn = sqlite3.connect(db_path)
		self.cursor = self.conn.cursor()
		self.cursor.execute("CREATE TABLE IF NOT EXISTS experiment_ids (id integer primary key autoincrement, experiment_name text unique)")
		self.conn.commit()

	def new_experiment(self, experiment_name):
		self.cursor.execute("INSERT INTO experiment_ids (experiment_name) values (?)", (experiment_name,))

	def write(self, experiment_name, table_name, dict_of_lists):
		column_names = sorted(list(dict_of_lists.keys()))
		column_types = " real, ".join(column_names)
		column_tuple = str(tuple(["experiment_id"]+column_names))
		column_values = [dict_of_lists[x] for x in column_names]
		self.cursor.execute("CREATE TABLE IF NOT EXISTS %s (id integer primary key autoincrement, experiment_id integer, %s)"%(table_name, column_types))

		self.cursor.execute("SELECT id FROM experiment_ids WHERE experiment_name=?", (experiment_name,))
		experiment_id = self.cursor.fetchone()*len(column_values[0])

		column_values = [experiment_id]+column_values
		prepared_statement_filler = "(%s)"%(("?, "*len(column_values))[:-2])
		column_values = [x for x in zip(*column_values)]		

		self.cursor.executemany("INSERT INTO %s %s VALUES %s"%(table_name, column_tuple, prepared_statement_filler), column_values)
		self.conn.commit()
		