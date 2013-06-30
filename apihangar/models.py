from django.conf import settings
from django.core.cache import get_cache
from django.db import connections
from django.db import models
from django.utils.hashcompat import md5_constructor

from apihangar.core import get_variables, render_sql, run
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

    def get_variables(self):
        return get_variables(self)
    
    def render_sql(self, params):
        return render_sql(self, params)

    def run(self, return_one=False, return_list=False, params={}):
        return run(self, return_one=return_one, return_list=return_list, params=params)

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

    def get_required_permissions(self):
        return self.required_permissions.select_related("group").all().values_list(
            "group__name", flat=True)

class EndpointPermission(models.Model):
    endpoint = models.ForeignKey(Endpoint, related_name="required_permissions")
    group = models.ForeignKey("auth.Group")

class EndpointQuery(models.Model):
    query = models.ForeignKey(Query, related_name="endpoint_queries")
    endpoint = models.ForeignKey(Endpoint, related_name="endpoint_queries")
    key = models.CharField(max_length=50)

    return_one = models.BooleanField(default=False)
    return_list = models.BooleanField(default=False)

    cache_timeout_seconds = models.IntegerField(null=True, blank=True, default=None)

    def __unicode__(self):
        return "'%s' as '%s' for %s" % (self.query, self.key, self.endpoint)

    class Meta:
        unique_together = (("query", "endpoint", "key"),)

    def run(self, params={}):
        if self.cache_timeout_seconds is None:
            return self.query.run(return_one=self.return_one, return_list=self.return_list,
                                  params=params)

        cache = get_cache(getattr(settings, 'APIHANGAR_CACHE', "default"))
        args = md5_constructor(json_dumps(params)).hexdigest()
        cache_key = "apihangar.endpoint_query.%s.%s" % (self.id, args)
        result = cache.get(cache_key)
        if result is not None:
            return result

        result = self.query.run(return_one=self.return_one, return_list=self.return_list,
                                params=params)
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
