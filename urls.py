from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path("PVApp/", include("PVApp.urls")),
    path("admin/", admin.site.urls),
    path('plotly/', views.plotly_view, name='plotly'),
]
