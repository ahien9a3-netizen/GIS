from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cuahang/', views.cuahang, name='cuahang'),
    path('kho/', views.kho, name='kho'),
    path('sanpham/', views.sanpham, name='sanpham'),
    path('nhapkho/', views.nhapkho, name='nhapkho'),
]

from myapp.views.tool_map import map_cuahang
from myapp.views.tool_density import density_map
from myapp.views.tool_service_area import service_area

urlpatterns = [
    path('tool/map/', map_cuahang, name='tool_map'),
    path('tool/density/', density_map, name='tool_density'),
    path('tool/service-area/', service_area, name='tool_service_area'),
]
