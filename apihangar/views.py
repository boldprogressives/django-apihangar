from django.http import HttpResponseForbidden
from django.utils.html import escape
from djangohelpers import allow_http
import urllib

from apihangar.models import Endpoint, PrebuiltView
from apihangar.utils import json_dumps, unescape, render_response, check_permission

@allow_http("GET")
def retrieve_endpoint_form(request, api_url, response_type="json"):
    endpoint = Endpoint.objects.get(url=api_url)

    if check_permission(request, endpoint) is not None:
        return HttpResponseForbidden()

    variables = set()
    for apiquery in endpoint.endpoint_queries.all().select_related():
        variables.update(apiquery.query.get_variables())

    return render_response(request, response_type, {'variables': variables})

@allow_http("GET")
def execute_view(request, view_url):
    view = PrebuiltView.objects.select_related("endpoint").get(url=view_url)

    if check_permission(request, view) is not None:
        return HttpResponseForbidden()

    json = view.endpoint.run(params=view.load_params())

    return render_response(request, response_type, json)
    
@allow_http("GET")
def execute_endpoint(request, api_url, response_type="json"):
    endpoint = Endpoint.objects.get(url=api_url)

    if check_permission(request, endpoint) is not None:
        return HttpResponseForbidden()

    params = {}
    for key in request.GET.keys():
        value = unescape(urllib.unquote(request.GET[key]))
        key = unescape(urllib.unquote(key))

        if key.startswith("list:"):
            key = key[5:]
            if key.startswith("int:"):
                params[key[4:]] = tuple(
                    [int(i.strip()) for i in value.split(",") if i])
            else:
                params[key] = tuple(
                    [str(i.strip()) for i in value.split(",") if i])
                    
        else:
            if key.startswith("int:"):
                try:
                    params[key[4:]] = int(value)
                except ValueError:
                    continue
            else:
                params[key] = str(value.strip())
    
    json = endpoint.run(params=params)

    return render_response(request, response_type, json)
