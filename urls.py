from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path("PVApp/", include("PVApp.urls")),
    path("admin/", admin.site.urls),
    # path('map/', views.load_tiff_data, name='map'),
    path('map/', views.map_view, name='map'),
    path('map200/', views.connsql, name='map200'),
    path('Render/', views.render_view, name='Render'),
    path('plotly/', views.plotly_view, name='plotly'),
    path('testing/', views.testing_view, name='testing'),
    #path('copy/', views.copy_map, name='copy'),
]
