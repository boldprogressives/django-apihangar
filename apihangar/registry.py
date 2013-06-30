
from apihangar.core import get_variables, render_sql, run

class Query(object):
    def __init__(self, sql, database, 
                 use_templates=False, 
                 return_one=False, return_list=False,
                 cache_timeout_seconds=None):
        self.sql = sql
        self.database = database
        self.use_templates = use_templates
        self.return_one = return_one
        self.return_list = return_list
        self.cache_timeout_seconds = cache_timeout_seconds

    def get_variables(self):
        return get_variables(self)

    def render_sql(self, params):
        return render_sql(self, params)
    
    def run(self, params={}):
        return run(self, return_one=self.return_one, return_list=self.return_list,
                   params=params)

class Endpoint(object):

    def __init__(self, name, description, url, queries={}, permissions=[]):
        self.name = name
        self.description = description
        self.url = url
        self.queries = queries
        self.permissions = permissions

    def run(self, params={}):
        queries = {}
        results = {}
        for key, query in self.queries.items():
            sql, result = query.run(params=params)
            results[key] = result
            queries[key] = sql
        return dict(queries=queries, results=results)

    def get_required_permissions(self):
        return self.permissions

registry = {}

def register_endpoint(url, name, description, queries, permissions=[]):
    registry[url] = Endpoint(name, description, url, queries=queries, permissions=permissions)

