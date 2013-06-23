from django.contrib import admin
from apihangar.models import (EndpointQuery,
                              EndpointPermission,
                              PrebuiltViewPermission,
                              Query,
                              Endpoint,
                              PrebuiltView)

class EndpointQueryInline(admin.StackedInline):
    model = EndpointQuery

class EndpointPermissionInline(admin.StackedInline):
    model = EndpointPermission

class EndpointAdmin(admin.ModelAdmin):
    inlines = [
        EndpointQueryInline,
        EndpointPermissionInline,
        ]

class PrebuiltViewPermissionInline(admin.StackedInline):
    model = PrebuiltViewPermission

class PrebuiltViewAdmin(admin.ModelAdmin):
    inlines = [
        PrebuiltViewPermissionInline,
        ]
admin.site.register(Query)
admin.site.register(Endpoint, EndpointAdmin)
admin.site.register(PrebuiltView, PrebuiltViewAdmin)
