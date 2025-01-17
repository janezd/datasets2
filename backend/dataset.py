import Orange
import yaml
from database import Database


class Dataset:
    def __init__(self, **kwargs):
        self.calculated = {
            'instances': kwargs.get('instances'),
            'variables': kwargs.get('variables'),
            'missing': kwargs.get('missing'),
            'target': kwargs.get('target'),
            'size': kwargs.get('size'),
        }
        self.file = kwargs.get('file')
        self.dataset = {
            'name': kwargs.get('name'),
            'title': kwargs.get('title'),
            'description': kwargs.get('description'),
            'collection': kwargs.get('collection'),
            'references': kwargs.get('references'),
            'tags': kwargs.get('tags', []),
            'version': kwargs.get('version'),
            'year': kwargs.get('year'),
            'source': kwargs.get('source'),
            'language': kwargs.get('language'),
            'domain': kwargs.get('domain'),
            'custom': kwargs.get('custom'),
            'url': kwargs.get('url'),
            'location': kwargs.get('location'),
        }

    def add(self):
        if self.check_exists():
            return

        table = None

        if self.file is None:
            table = Orange.data.Table(self.dataset['url'])
        else:
            pass  # Implement file handling if needed

        target = table.domain.class_var and ("categorical" if table.domain.class_var.is_discrete else "numeric")

        if not any(self.calculated.values()):
            self.calculated.update({
                'instances': len(table),
                'variables': len(table.domain),
                'missing': table.has_missing(),
                'target': target,
                'size': None  # Implement size calculation if needed
            })

        database = Database(dataset={**self.dataset, **self.calculated})
        database.add()

    def edit(self, **kwargs):
        old = Database(dataset={'name': self.dataset['name']})
        if kwargs.get('version') is not None:
            kwargs['version'] = self.change_version(kwargs['version'])
        old.edit(kwargs)

    def get_value(self):
        return Database(dataset={'name': self.dataset['name']}).get_value()

    @staticmethod
    def get_all():
        return Database(dataset={}).get_all()

    def check_exists(self):
        return Database({'name': self.dataset['name']}).check_exists()

    @staticmethod
    def change_version(version: str):
        primary, secondary = version.split('.')
        secondary = int(secondary) + 1
        return f'{primary}.{secondary}'

    @staticmethod
    def get_table(column_name, table_name):
        return Database(dataset={}).get_tables(column_name=column_name, table_name=table_name)
