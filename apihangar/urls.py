from django.conf.urls import url

import apihangar.views

urlpatterns = [
    url(r'^form/html/(?P<api_url>.*)/$', apihangar.views.retrieve_endpoint_form,
        {'response_type': "html"}, name='retrieve_endpoint_form_html'),
    url(r'^form/json/(?P<api_url>.*)/$', apihangar.views.retrieve_endpoint_form,
        {'response_type': "json"}, name='retrieve_endpoint_form_json'),

    url(r'^json/(?P<api_url>.*)/$', apihangar.views.execute_endpoint,
        {'response_type': "json"},
        name='execute_endpoint_json'),
    url(r'^html/(?P<api_url>.*)/$', apihangar.views.execute_endpoint,
        {'response_type': "html"},
        name='execute_endpoint_html'),

    url('^view/(?P<view_url>.*)/$', apihangar.views.execute_view, 
        name='execute_view'),
    
]
