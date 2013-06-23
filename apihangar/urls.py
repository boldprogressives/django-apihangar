from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns(
    'apihangar.views',

    url(r'^form/html/(?P<api_url>.*)/$', 'retrieve_endpoint_form',
        {'response_type': "html"}, name='retrieve_endpoint_form_html'),
    url(r'^form/json/(?P<api_url>.*)/$', 'retrieve_endpoint_form',
        {'response_type': "json"}, name='retrieve_endpoint_form_json'),

    url(r'^json/(?P<api_url>.*)/$', 'execute_endpoint',
        {'response_type': "json"},
        name='execute_endpoint_json'),
    url(r'^html/(?P<api_url>.*)/$', 'execute_endpoint',
        {'response_type': "html"},
        name='execute_endpoint_html'),

    url('^view/(?P<view_url>.*)/$', 'execute_view', 
        name='execute_view'),

    )
