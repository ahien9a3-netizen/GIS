from django.urls import path
from django.views.generic import TemplateView
from .tool import store_geojson, store_heatmap, service_area, kho_geojson
from .views import (
    home, report_view, login_view, logout_view, settings_view, gis_map, inventory_stats, upload_gis_images, delete_gis_image,
    forgot_password_view, reset_password_view, verify_otp_view, switch_view_role, delete_review, edit_review,
    CuaHangListView, CuaHangCreateView, CuaHangUpdateView, CuaHangDeleteView, store_detail_view,
    SanPhamListView, SanPhamCreateView, SanPhamUpdateView, SanPhamDeleteView, SanPhamDetailView,
    DanhMucListView, DanhMucCreateView, DanhMucUpdateView, DanhMucDeleteView,
    KhoListView, KhoCreateView, KhoUpdateView, KhoDeleteView, kho_detail_view,
    NhanVienListView, NhanVienCreateView, NhanVienUpdateView, NhanVienDeleteView,
    StockInListView, StockInCreateView, StockInUpdateView, StockInDeleteView, StockInDetailView,
    HangTonKhoListView, HangTonKhoCreateView, HangTonKhoUpdateView, HangTonKhoDeleteView,
    public_home, public_about, public_product_list, public_product_detail, public_store_detail, public_kho_detail, public_login, public_register, public_logout, public_gis_map,
    customer_forgot_password_view, customer_verify_otp_view, customer_reset_password_view,
    view_cart, ajax_add_to_cart, ajax_update_cart, public_checkout, create_order, public_order_invoice, public_return_request, public_order_history, public_profile, submit_return_request,
    public_store_list,
    OrderListView, OrderDetailView, update_order_status,
    ReturnListView, ReturnDetailView, update_return_status,
    StockOutListView, StockOutCreateView, StockOutUpdateView, StockOutDetailView, StockOutDeleteView
)

urlpatterns = [
    path('', public_home, name='public_home'),
    path('about/', public_about, name='public_about'),
    path('products-all/', public_product_list, name='public_product_list'),
    path('stores-all/', public_store_list, name='public_store_list'),
    path('map/', public_gis_map, name='public_gis_map'),
    path('product/<str:pk>/', public_product_detail, name='public_product_detail'),
    path('store/detail/<str:pk>/', public_store_detail, name='public_store_detail'),
    path('warehouses/public/<str:pk>/', public_kho_detail, name='public_kho_detail'),
    path('customer/login/', public_login, name='public_login'),
    path('customer/forgot-password/', customer_forgot_password_view, name='customer_forgot_password'),
    path('customer/verify-otp/', customer_verify_otp_view, name='customer_verify_otp'),
    path('customer/reset-password/', customer_reset_password_view, name='customer_reset_password'),
    path('customer/register/', public_register, name='public_register'),
    path('customer/logout/', public_logout, name='public_logout'),
    path('cart/', view_cart, name='view_cart'),
    path('checkout/', public_checkout, name='public_checkout'),
    path('api/cart/add/<str:pk>/', ajax_add_to_cart, name='ajax_add_to_cart'),
    path('api/cart/update/', ajax_update_cart, name='ajax_update_cart'),
    path('api/order/create/', create_order, name='create_order'),

    # --- GIS API ENDPOINTS ---
    path('api/stores-geojson/', store_geojson, name='store_geojson'),
    path('api/store-heatmap/', store_heatmap, name='store_heatmap'),
    path('api/service-area/', service_area, name='service_area'),
    path('api/kho-geojson/', kho_geojson, name='kho_geojson'),
    path('dashboard/', home, name='home'),
    path('gis-map/', gis_map, name='gis_map'),
    path('reports/', report_view, name='reports'),
    path('login/', login_view, name='login'),  # Admin/Staff login - riêng biệt với public login
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('reset-password/', reset_password_view, name='reset_password'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('logout/', logout_view, name='logout'),
    path('settings/', settings_view, name='settings'),
    path('switch-view/', switch_view_role, name='switch_view'),
    path('api/stores-geojson/', store_geojson, name='store_geojson'),
    path('api/stores-heatmap/', store_heatmap, name='store_heatmap'),
    path('api/service-area/', service_area, name='service_area'),
    path('api/kho-geojson/', kho_geojson, name='kho_geojson'),
    path('api/inventory-stats/', inventory_stats, name='inventory_stats'),
    path('api/upload-gis-images/', upload_gis_images, name='upload_gis_images'),
    path('api/delete-gis-image/', delete_gis_image, name='delete_gis_image'),

    # Cửa hàng
    path('stores/', CuaHangListView.as_view(), name='store_list'),
    path('stores/add/', CuaHangCreateView.as_view(), name='store_add'),
    path('stores/<str:pk>/', store_detail_view, name='store_detail'),
    path('stores/<str:pk>/edit/', CuaHangUpdateView.as_view(), name='store_edit'),
    path('stores/<str:pk>/delete/', CuaHangDeleteView.as_view(), name='store_delete'),
    path('review/edit/<int:pk>/', edit_review, name='edit_review'),
    path('review/delete/<int:pk>/', delete_review, name='delete_review'),

    # Sản phẩm
    path('products/', SanPhamListView.as_view(), name='product_list'),
    path('products/add/', SanPhamCreateView.as_view(), name='product_add'),
    path('products/<str:pk>/', SanPhamDetailView.as_view(), name='product_detail'),
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
    path('warehouses/<str:pk>/', kho_detail_view, name='kho_detail'),
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
    path('stock-in/<str:pk>/', StockInDetailView.as_view(), name='stock_in_detail'),
    path('stock-in/<str:pk>/edit/', StockInUpdateView.as_view(), name='stock_in_edit'),
    path('stock-in/<str:pk>/delete/', StockInDeleteView.as_view(), name='stock_in_delete'),

    # Tồn kho
    path('inventory/', HangTonKhoListView.as_view(), name='inventory_list'),
    path('inventory/add/', HangTonKhoCreateView.as_view(), name='inventory_add'),
    path('inventory/<str:makho>/<str:masp>/edit/', HangTonKhoUpdateView.as_view(), name='inventory_edit'),
    path('inventory/<str:makho>/<str:masp>/delete/', HangTonKhoDeleteView.as_view(), name='inventory_delete'),

    # Test error pages (temporary)
    path('test-404/', TemplateView.as_view(template_name='404.html')),
    path('test-403/', TemplateView.as_view(template_name='403.html')),
    
    # Public Invoice & History
    path('order/invoice/<str:order_id>/', public_order_invoice, name='public_order_invoice'),
    path('order/<str:order_id>/return-request/', public_return_request, name='public_return_request'),
    path('customer/order-history/', public_order_history, name='public_order_history'),
    path('customer/profile/', public_profile, name='public_profile'),
    path('customer/submit-return/<str:order_id>/', submit_return_request, name='submit_return_request'),

    # --- ADMIN ORDER MANAGEMENT ---
    path('management/orders/', OrderListView.as_view(), name='order_list'),
    path('management/orders/<str:order_id>/', OrderDetailView.as_view(), name='order_detail'),
    path('management/orders/update-status/<str:order_id>/', update_order_status, name='update_order_status'),
    # --- ADMIN RETURNS MANAGEMENT ---
    path('management/returns/', ReturnListView.as_view(), name='return_list'),
    path('management/returns/<str:request_id>/', ReturnDetailView.as_view(), name='return_detail'),
    path('management/returns/update-status/<str:request_id>/', update_return_status, name='update_return_status'),
    
    # --- ADMIN STOCK OUT MANAGEMENT ---
    path('stock-out/', StockOutListView.as_view(), name='stock_out_list'),
    path('stock-out/add/', StockOutCreateView.as_view(), name='stock_out_add'),
    path('stock-out/<str:pk>/', StockOutDetailView.as_view(), name='stock_out_detail'),
    path('stock-out/<str:pk>/edit/', StockOutUpdateView.as_view(), name='stock_out_edit'),
    path('stock-out/<str:pk>/delete/', StockOutDeleteView.as_view(), name='stock_out_delete'),
]
