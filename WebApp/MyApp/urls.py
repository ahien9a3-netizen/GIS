from django.urls import path
from .views import (
    home, report_view, login_view, logout_view, settings_view, gis_map, store_geojson, store_heatmap, service_area, kho_geojson, inventory_stats,
    CuaHangListView, CuaHangCreateView, CuaHangUpdateView, CuaHangDeleteView,
    SanPhamListView, SanPhamCreateView, SanPhamUpdateView, SanPhamDeleteView,
    DanhMucListView, DanhMucCreateView, DanhMucUpdateView, DanhMucDeleteView,
    KhoListView, KhoCreateView, KhoUpdateView, KhoDeleteView,
    NhanVienListView, NhanVienCreateView, NhanVienUpdateView, NhanVienDeleteView,
    StockInListView, StockInCreateView, StockInUpdateView, StockInDeleteView,
    HangTonKhoListView, HangTonKhoCreateView, HangTonKhoUpdateView, HangTonKhoDeleteView
)

urlpatterns = [
    path('', home, name='home'),
    path('gis-map/', gis_map, name='gis_map'),
    path('reports/', report_view, name='reports'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('settings/', settings_view, name='settings'),
    path('api/stores-geojson/', store_geojson, name='store_geojson'),
    path('api/stores-heatmap/', store_heatmap, name='store_heatmap'),
    path('api/service-area/', service_area, name='service_area'),
    path('api/kho-geojson/', kho_geojson, name='kho_geojson'),
    path('api/inventory-stats/', inventory_stats, name='inventory_stats'),

    # Cửa hàng
    path('stores/', CuaHangListView.as_view(), name='store_list'),
    path('stores/add/', CuaHangCreateView.as_view(), name='store_add'),
    path('stores/<str:pk>/edit/', CuaHangUpdateView.as_view(), name='store_edit'),
    path('stores/<str:pk>/delete/', CuaHangDeleteView.as_view(), name='store_delete'),

    # Sản phẩm
    path('products/', SanPhamListView.as_view(), name='product_list'),
    path('products/add/', SanPhamCreateView.as_view(), name='product_add'),
    path('products/<str:pk>/edit/', SanPhamUpdateView.as_view(), name='product_edit'),
    path('products/<str:pk>/delete/', SanPhamDeleteView.as_view(), name='product_delete'),

    # Danh mục
    path('categories/', DanhMucListView.as_view(), name='danhmuc_list'),
    path('categories/add/', DanhMucCreateView.as_view(), name='danhmuc_add'),
    path('categories/<str:pk>/edit/', DanhMucUpdateView.as_view(), name='danhmuc_edit'),
    path('categories/<str:pk>/delete/', DanhMucDeleteView.as_view(), name='danhmuc_delete'),


    # Kho hàng
    path('warehouses/', KhoListView.as_view(), name='kho_list'),
    path('warehouses/add/', KhoCreateView.as_view(), name='kho_add'),
    path('warehouses/<str:pk>/edit/', KhoUpdateView.as_view(), name='kho_edit'),
    path('warehouses/<str:pk>/delete/', KhoDeleteView.as_view(), name='kho_delete'),

    # Nhân viên
    path('employees/', NhanVienListView.as_view(), name='nhanvien_list'),
    path('employees/add/', NhanVienCreateView.as_view(), name='nhanvien_add'),
    path('employees/<str:pk>/edit/', NhanVienUpdateView.as_view(), name='nhanvien_edit'),
    path('employees/<str:pk>/delete/', NhanVienDeleteView.as_view(), name='nhanvien_delete'),

    # Nhập kho
    path('stock-in/', StockInListView.as_view(), name='stock_in_list'),
    path('stock-in/add/', StockInCreateView.as_view(), name='stock_in_add'),
    path('stock-in/<str:pk>/edit/', StockInUpdateView.as_view(), name='stock_in_edit'),
    path('stock-in/<str:pk>/delete/', StockInDeleteView.as_view(), name='stock_in_delete'),

    # Tồn kho
    path('inventory/', HangTonKhoListView.as_view(), name='inventory_list'),
    path('inventory/add/', HangTonKhoCreateView.as_view(), name='inventory_add'),
    path('inventory/<str:makho>/<str:masp>/edit/', HangTonKhoUpdateView.as_view(), name='inventory_edit'),
    path('inventory/<str:makho>/<str:masp>/delete/', HangTonKhoDeleteView.as_view(), name='inventory_delete'),
]
