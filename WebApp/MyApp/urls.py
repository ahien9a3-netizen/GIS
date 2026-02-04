from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cuahang/', views.cuahang, name='cuahang'),
    path('kho/', views.kho, name='kho'),
    path('sanpham/', views.sanpham, name='sanpham'),
    path('nhapkho/', views.nhapkho, name='nhapkho'),
]

