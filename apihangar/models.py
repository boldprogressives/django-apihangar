from django.conf import settings
from django.core.cache import get_cache
from django.db import connections
from django.db import models
from django.template import Template, Context
from django.utils.hashcompat import md5_constructor
import djtemplateinspector as inspector
import re

from apihangar.utils import dictfetchall
from apihangar.utils import json_dumps, json_loads

class Query(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)

    sql = models.TextField()
    database = models.CharField(max_length=50, 
                                choices=settings.APIHANGAR_DATABASES)

    use_templates = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def _template_get_variables(self):
        """
        Returns an ordered list of variable names in this query's SQL,
        by monkeypatching Django template internals to maintain a list
        of all variables that it attempted to resolve in the template.
        """
        tmpl = Template(self.sql.replace("int:", "").replace("list:", ""))
        variables = inspector.get_variables(tmpl)

        restored_variables = []
        for v in variables:
            if "list:int:%s" % v in self.sql:
                restored_variables.append("list:int:%s" % v)
            elif "int:%s" % v in self.sql:
                restored_variables.append("int:%s" % v)
            elif "list:%s" % v in self.sql:
                restored_variables.append("list:%s" % v)
            else:
                restored_variables.append(v)
        return restored_variables

    _format_char_to_type = {
        's': "",
        'd': "int:",
        'l': "list:",
        'a': "list:int:",
        }

    def _string_get_variables(self):
        """
        Returns an ordered list of variable names in this query's SQL,
        by extracting %(var_name)s patterns from the raw string.
        """
        extraction = re.findall(
            r"%\((?P<var_name>[\w\d\-_]+)\)(?P<var_type>[sdla])", self.sql)
        restored_variables = []
        for var, type in extraction:
            restored_variables.append("%s%s" % (self._format_char_to_type[type], var))
        return restored_variables

    def get_variables(self):
        if self.use_templates:
            return self._template_get_variables()
        return self._string_get_variables()

    def _template_render_sql(self, params):
        ## Parameters have already been type-cast as needed,
        ## so swallow all the ad-hoc type prefixes which will
        ## otherwise trip up the Django template machinery.
        sql = self.sql.replace("int:", "").replace("list:", "")

        ## Forcibly shut off Django's template safety measures
        ## which screw up user input by escaping strings.
        from django.utils import html
        original_escape = html.escape
        html.escape = lambda x: x

        try:
            sql = Template(sql).render(Context(params))
        finally:
            html.escape = original_escape
        return sql
            
    def _string_render_sql(self, params):
        sql = self.sql.replace(")l", ")r").replace(")a", ")r")
        return sql % params

    def render_sql(self, params):
        if self.use_templates:
            return self._template_render_sql(params)
        return self._string_render_sql(params)

    def run(self, return_one=False, params={}):
        cursor = connections[self.database].cursor()

        sql = self.render_sql(params)
        sql = ' '.join(line.strip() for line in sql.splitlines() 
                       if line and line.strip())
        ## Python's tuple repr() will result in 1-tuples like ("foo",)
        ## but MySQL needs them to look like ("foo") instead.
        sql = sql.replace(",)", ")").replace(", )", " )")

        cursor.execute(sql)
        result = dictfetchall(cursor)

        if return_one:
            result = result[0]

        return (connections[self.database].queries.pop(0),
                result)

class Endpoint(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=250, unique=True)

    def __unicode__(self):
        return "'%s' at %s" % (self.name, self.get_absolute_url())

    @models.permalink
    def execute_endpoint_json_url(self):
        return ("execute_endpoint_json", [self.url])

    @models.permalink
    def execute_endpoint_html_url(self):
        return ("execute_endpoint_html", [self.url])

    @models.permalink
    def retrieve_endpoint_form_html_url(self):
        return ("retrieve_endpoint_form_html", [self.url])

    @models.permalink
    def retrieve_endpoint_form_json_url(self):
        return ("retrieve_endpoint_form_json", [self.url])

    get_absolute_url = execute_endpoint_json_url

    def run(self, params={}):
        queries = {}
        results = {}
        for endpoint_query in self.endpoint_queries.select_related("query").all():
            sql, result = endpoint_query.run(params=params)
            results[endpoint_query.key] = result
            queries[endpoint_query.key] = sql
        return dict(queries=queries, results=results)

class EndpointPermission(models.Model):
    endpoint = models.ForeignKey(Endpoint, related_name="required_permissions")
    group = models.ForeignKey("auth.Group")

class EndpointQuery(models.Model):
    query = models.ForeignKey(Query, related_name="endpoint_queries")
    endpoint = models.ForeignKey(Endpoint, related_name="endpoint_queries")
    key = models.CharField(max_length=50)

    return_one = models.BooleanField(default=False)

    cache_timeout_seconds = models.IntegerField(null=True, blank=True, default=None)

    def __unicode__(self):
        return "'%s' as '%s' for %s" % (self.query, self.key, self.endpoint)

    class Meta:
        unique_together = (("query", "endpoint", "key"),)

    def run(self, params={}):
        if self.cache_timeout_seconds is None:
            return self.query.run(return_one=self.return_one, params=params)

        cache = get_cache(getattr(settings, 'APIHANGAR_CACHE', "default"))
        args = md5_constructor(json_dumps(params)).hexdigest()
        cache_key = "apihangar.endpoint_query.%s.%s" % (self.id, args)
        result = cache.get(cache_key)
        if result is not None:
            return result

        result = self.query.run(return_one=self.return_one, params=params)
        cache.set(cache_key, result, self.cache_timeout_seconds)
        return result

class PrebuiltView(models.Model):
    endpoint = models.ForeignKey(Endpoint, related_name="prebuilt_views")
    url = models.CharField(max_length=250, unique=True)
    response_type = models.CharField(max_length=15, default="json")
    template = models.CharField(max_length=250, null=True, blank=True)
    params = models.TextField(null=True, blank=True)

    def load_params(self):
        try:
            return json_loads(self.params)
        except (KeyError, ValueError):
            return {}
    
class PrebuiltViewPermission(models.Model):
    view = models.ForeignKey(PrebuiltView, related_name="required_permissions")
    group = models.ForeignKey("auth.Group")
