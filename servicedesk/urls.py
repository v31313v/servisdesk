from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tickets/', include('tickets.urls')),
    path('reports/', include('reports.urls')),
    path('', include('tickets.urls')),
]