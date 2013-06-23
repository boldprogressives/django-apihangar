from apihangar.utils import dictfetchall
from django.db import connections
from django.template import Template, Context
import djtemplateinspector as inspector
import re

__all__ = ["get_variables", "render_sql", "run"]

def _template_get_variables(query):
    """
    Returns an ordered list of variable names in this query's SQL,
    by monkeypatching Django template internals to maintain a list
    of all variables that it attempted to resolve in the template.
    """
    tmpl = Template(query.sql.replace("int:", "").replace("list:", ""))
    variables = inspector.get_variables(tmpl)

    restored_variables = []
    for v in variables:
        if "list:int:%s" % v in query.sql:
            restored_variables.append("list:int:%s" % v)
        elif "int:%s" % v in query.sql:
            restored_variables.append("int:%s" % v)
        elif "list:%s" % v in query.sql:
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

def _string_get_variables(query):
    """
    Returns an ordered list of variable names in this query's SQL,
    by extracting %(var_name)s patterns from the raw string.
    """
    extraction = re.findall(
        r"%\((?P<var_name>[\w\d\-_]+)\)(?P<var_type>[sdla])", query.sql)
    restored_variables = []
    for var, type in extraction:
        restored_variables.append("%s%s" % (query._format_char_to_type[type], var))
    return restored_variables

def get_variables(query):
    if query.use_templates:
        return _template_get_variables(query)
    return _string_get_variables(query)

def _template_render_sql(query, params):
    ## Parameters have already been type-cast as needed,
    ## so swallow all the ad-hoc type prefixes which will
    ## otherwise trip up the Django template machinery.
    sql = query.sql.replace("int:", "").replace("list:", "")

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
            
def _string_render_sql(query, params):
    sql = query.sql.replace(")l", ")r").replace(")a", ")r")
    return sql % params

def render_sql(query, params):
    if query.use_templates:
        return _template_render_sql(query, params)
    return _string_render_sql(query, params)

def run(query, return_one=False, params={}):
    cursor = connections[query.database].cursor()

    sql = render_sql(query, params)
    sql = ' '.join(line.strip() for line in sql.splitlines() 
                   if line and line.strip())
    ## Python's tuple repr() will result in 1-tuples like ("foo",)
    ## but MySQL needs them to look like ("foo") instead.
    sql = sql.replace(",)", ")").replace(", )", " )")

    cursor.execute(sql)
    result = dictfetchall(cursor)

    if return_one:
        result = result[0]

    return (connections[query.database].queries.pop(0),
            result)
