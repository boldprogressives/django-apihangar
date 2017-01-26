import re

from htmlentitydefs import name2codepoint
# for some reason, python 2.5.2 doesn't have this one (apostrophe)
name2codepoint['#39'] = 39

def unescape(s):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)


# We need simplejson for object_pairs_hook before Python 2.7:
#  http://stackoverflow.com/a/6921842/689985
import sys
if sys.version_info[:2] < (2, 7):
    import simplejson as json
else:
    import json

from django.core.serializers.json import DjangoJSONEncoder
from collections import OrderedDict

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        SortedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

def sorteddict_with_tuples(pairs):
    return SortedDict((k, v) if not isinstance(v, list)
                      else (k, tuple(v))
                      for k, v in pairs)

def json_dumps(*args, **kw):
    kw.setdefault('indent', 2)
    kw.setdefault('cls', DjangoJSONEncoder)
    return json.dumps(*args, **kw)

def json_loads(*args, **kw):
    """
    Load list-like objects from JSON as Python tuples, not lists.
    """
    kw.setdefault('object_pairs_hooks', sorteddict_with_tuples)
    return json.loads(*args, **kw)

from django.http import HttpResponse
from djangohelpers.lib import rendered_with

def render_response(request, response_type, ctx):

    if response_type == "json":
        json = json_dumps(ctx)
        jsonp = request.GET.get("jsonp") or request.GET.get("callback")
        if jsonp:
            return HttpResponse("%s(%s);" % (jsonp, json), 
                                content_type="text/javascript")
        else:
            return HttpResponse(json, content_type="application/json")
    elif response_type == "html":
        template = request.GET.get("template", "apihangar/default_template.html")
        @rendered_with(template)
        def inner(_request, ctx):
            return ctx
        return inner(request, ctx)

def check_permission(request, object):
    groups = list(request.user.groups.all().values_list("name", flat=True))
    for permission in object.get_required_permissions():
        if permission not in groups:
            return permission.group.name
