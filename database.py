import sqlite3
from copy import deepcopy


class Database:
    def __init__(self, dataset: dict, instances: int = None, variables: int = None, missing: bool = None,
                 target: str = None):
        self.extended_datasets = {
                                     'instances': instances,
                                     'variables': variables,
                                     'missing': missing,
                                     'target': target,
                                 } | dataset
        self.connection = sqlite3.connect('datasets.sqlite')
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def exist_add(self, table: str, column: str, value):
        """
        Checks if a table exists else add it do db
        :param value: value to check
        :param column: column of the table
        :param table: name of the table
        :return: None
        """
        # if domain doesn't exist add one
        try:
            self.cursor.execute(f"SELECT 1 FROM {table} WHERE {column} = ?", (value,))
            if not self.cursor.fetchone():
                self.cursor.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))

            self.connection.commit()
        except sqlite3.IntegrityError:
            self.cursor.close()
            self.connection.close()
            print(f"error {value} exists in table {table}")
            pass

    def exists_update(self, table: str, column: str, value):
        """
        Checks if a record exists in a table, if not inserts it, if exists updates it.
        :param value: value to check
        :param column: column of the table
        :param table: name of the table
        :return: None
        """
        try:
            # Check if record exists
            self.cursor.execute(f"SELECT 1 FROM {table} WHERE {column} = ?", (value,))
            existing_record = self.cursor.fetchone()

            if existing_record:
                # Update the existing record
                self.cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (value, value))
            else:
                # Insert new record
                self.cursor.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))

            self.connection.commit()
        except sqlite3.IntegrityError:
            self.cursor.close()
            self.connection.close()
            print(f"Error: {value} already exists in table {table}")
            pass

    @staticmethod
    def _converted_names(values) -> list[str]:
        # removes db_
        return ['db_' + name for name in values.keys() if name != 'tags']

    def add(self):
        try:
            for tag in self.extended_datasets['tags']:
                self.exist_add('tags', 'tag', tag)
            self.exist_add('domains', 'domain', self.extended_datasets['domain'])
            self.exist_add('languages', 'language', self.extended_datasets['language'])

            # convert list to string: delimiter is \n
            if self.extended_datasets['references'] is not None:
                self.extended_datasets['references'] = '\n'.join(self.extended_datasets['references'])

            columns = ', '.join(self._converted_names(self.extended_datasets))
            placeholders = ', '.join(['?'] * (len(self.extended_datasets) - 1))
            sql = f'INSERT INTO datasets ({columns}) VALUES ({placeholders})'

            # create a copy of dataset and remove 'tags'
            insert_values = deepcopy(self.extended_datasets)
            del insert_values['tags']

            self.cursor.execute(sql, tuple(insert_values.values()))

            for tag in self.extended_datasets['tags']:
                self.cursor.execute("""
                    INSERT INTO datasets_tags(db_name, tag_id) 
                    VALUES (?, ?)
                """, (self.extended_datasets['name'], tag))

            self.connection.commit()
        except sqlite3.IntegrityError as e:
            self.cursor.close()
            self.connection.close()
            return e, 400

    def edit(self, changes: dict):
        set_values = str([f'{i} = ?' for i in changes.values()[1:-1]])
        sql = f'UPDATE datasets SET {set_values} WHERE db_name = ?'

        self.cursor.execute(sql, (*changes.values(), self.extended_datasets['name']))

        if 'languages' in changes.keys():
            self.exists_update('languages', 'language', changes['language'])
        if 'domain' in changes.keys():
            self.exists_update('domains', 'domain', changes['domain'])
        if 'tags' in changes.keys():
            for tag in changes['tags']:
                self.exists_update('tags', 'tag', tag)
                self.cursor.execute('UPDATE datasets_tags SET tag_id = ? WHERE db_name = ? AND tag_id = ?',
                                    (
                                        changes['tag'],
                                        self.extended_datasets['name'],
                                        self.extended_datasets['tag'])
                                    )
        self.connection.commit()
        self.cursor.execute('UPDATE datasets_tags SET db_name = ? WHERE db_name = ?',
                            (
                                changes['name'],
                                self.extended_datasets['name'])
                            )

    def get_value(self):
        values = self.cursor.execute("""
            SELECT * FROM datasets
            JOIN main.datasets_tags ON datasets_tags.db_name = datasets.db_name
            WHERE datasets.db_name = ?
        """, (self.extended_datasets['name'],)).fetchone()
        self.extended_datasets.update(values)
        return values

