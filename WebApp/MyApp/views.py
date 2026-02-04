from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import SanPham, CuaHang, Kho, HangTonKho, KhachHang, DonHang, GiaoHang, NhanVien, YeuCauNhapKho

# ==================== MIXINS & HELPERS ====================
class SidebarContextMixin:
    sidebar_active = ""
    page_title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_active'] = self.sidebar_active
        context['page_title'] = self.page_title
        return context

# ==================== HOME & GIS ====================
def home(request):
    """
    Dashboard chính - Sử dụng ORM để lấy dữ liệu thống kê
    """
    total_stores = CuaHang.objects.count()
    total_warehouses = Kho.objects.count()
    total_products = SanPham.objects.count()
    total_inventory = HangTonKho.objects.aggregate(total=Sum('SoLuong'))['total'] or 0
    total_customers = KhachHang.objects.count()
    total_orders = DonHang.objects.count()

    stores_qs = CuaHang.objects.all().order_by('MaCH')
    
    inventory_by_warehouse_qs = HangTonKho.objects.values('MaKho__Ten')\
        .annotate(total=Sum('SoLuong'))\
        .order_by('MaKho__Ten')
    
    stores_list = []
    for store in stores_qs:
        stores_list.append({
            'MaCH': store.MaCH,
            'Ten': store.Ten,
            'DiaChi': store.DiaChi,
            'TrangThai': store.TrangThai,
            'lon': store.geom.x if store.geom else 0,
            'lat': store.geom.y if store.geom else 0,
        })

    inventory_by_warehouse = [
        (item['MaKho__Ten'], item['total']) for item in inventory_by_warehouse_qs
    ]

    context = {
        'total_stores': total_stores,
        'total_warehouses': total_warehouses,
        'total_products': total_products,
        'total_inventory': total_inventory,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'stores_list': stores_list,
        'inventory_by_warehouse': inventory_by_warehouse,
        'sidebar_active': 'dashboard'
    }
    
    return render(request, 'MyApp/home.html', context)

# GIS APIs keep as is (same logic)
def store_geojson(request):
    stores = CuaHang.objects.all()
    features = []
    for store in stores:
        if store.geom:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": store.MaCH,
                    "name": store.Ten,
                    "address": store.DiaChi,
                    "phone": store.SDT or 'N/A',
                    "status": store.TrangThai,
                    "type": store.Loai
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [store.geom.x, store.geom.y]
                }
            })
    return JsonResponse({"type": "FeatureCollection", "features": features})

def store_heatmap(request):
    stores = CuaHang.objects.filter(geom__isnull=False).values_list('geom', flat=True)
    warehouses = Kho.objects.filter(geom__isnull=False).values_list('geom', flat=True)
    data = [[p.y, p.x] for p in stores] + [[p.y, p.x] for p in warehouses]
    return JsonResponse(data, safe=False)

@require_GET
def service_area(request):
    try:
        center_lat = float(request.GET.get('lat'))
        center_lng = float(request.GET.get('lng'))
        radius_km = float(request.GET.get('radius', 2))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Tham số không hợp lệ'}, status=400)
    
    center_point = Point(center_lng, center_lat, srid=4326)
    nearby_stores = CuaHang.objects.filter(
        geom__distance_lte=(center_point, D(km=radius_km))
    ).annotate(distance=Distance('geom', center_point)).order_by('distance')
    
    features = []
    for store in nearby_stores:
        if store.geom:
            dist_val = store.distance.km if hasattr(store.distance, 'km') else 0
            features.append({
                "type": "Feature",
                "properties": {
                    "id": store.MaCH, "name": store.Ten, "address": store.DiaChi,
                    "phone": store.SDT or 'N/A', "distance_km": round(dist_val, 2)
                },
                "geometry": {"type": "Point", "coordinates": [store.geom.x, store.geom.y]}
            })
    return JsonResponse({'center': [center_lat, center_lng], 'radius_km': radius_km, 'stores': {"type": "FeatureCollection", "features": features}})

def kho_geojson(request):
    warehouses = Kho.objects.all()
    features = []
    for wh in warehouses:
        if wh.geom:
            features.append({
                "type": "Feature",
                "properties": {"id": wh.MaKho, "name": wh.Ten, "address": wh.DiaChi, "type": wh.Loai},
                "geometry": {"type": "Point", "coordinates": [wh.geom.x, wh.geom.y]}
            })
    return JsonResponse({"type": "FeatureCollection", "features": features})

def inventory_stats(request):
    data = HangTonKho.objects.select_related('MaSP', 'MaKho').order_by('-SoLuong').values('MaSP__Ten', 'MaKho__Ten', 'SoLuong')
    result = [{'product': item['MaSP__Ten'], 'warehouse': item['MaKho__Ten'], 'quantity': item['SoLuong']} for item in data]
    return JsonResponse({'inventory': result})

# ==================== CRUD VIEWS ====================

# --- CỬA HÀNG (STORES) ---
class CuaHangListView(SidebarContextMixin, ListView):
    model = CuaHang
    template_name = 'MyApp/store_list.html'
    context_object_name = 'stores'
    sidebar_active = 'stores'
    page_title = 'Quản lý Cửa hàng'

class CuaHangCreateView(SidebarContextMixin, CreateView):
    model = CuaHang
    fields = ['MaCH', 'Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai', 'geom']
    template_name = 'MyApp/store_form.html'
    success_url = reverse_lazy('store_list')
    sidebar_active = 'stores'
    page_title = 'Thêm Cửa hàng mới'

class CuaHangUpdateView(SidebarContextMixin, UpdateView):
    model = CuaHang
    fields = ['Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai', 'geom']
    template_name = 'MyApp/store_form.html'
    success_url = reverse_lazy('store_list')
    sidebar_active = 'stores'
    page_title = 'Cập nhật Cửa hàng'

class CuaHangDeleteView(DeleteView):
    model = CuaHang
    success_url = reverse_lazy('store_list')

# --- SẢN PHẨM (PRODUCTS) ---
class SanPhamListView(SidebarContextMixin, ListView):
    model = SanPham
    template_name = 'MyApp/product_list.html'
    context_object_name = 'products'
    sidebar_active = 'products'
    page_title = 'Quản lý Sản phẩm'

class SanPhamCreateView(SidebarContextMixin, CreateView):
    model = SanPham
    fields = ['MaSP', 'Ten', 'DanhMuc', 'MieuTa', 'TrangThai']
    template_name = 'MyApp/product_form.html'
    success_url = reverse_lazy('product_list')
    sidebar_active = 'products'

class SanPhamUpdateView(SidebarContextMixin, UpdateView):
    model = SanPham
    fields = ['Ten', 'DanhMuc', 'MieuTa', 'TrangThai']
    template_name = 'MyApp/product_form.html'
    success_url = reverse_lazy('product_list')
    sidebar_active = 'products'

class SanPhamDeleteView(DeleteView):
    model = SanPham
    success_url = reverse_lazy('product_list')

# --- KHÁCH HÀNG (CUSTOMERS) ---
class KhachHangListView(SidebarContextMixin, ListView):
    model = KhachHang
    template_name = 'MyApp/customer_list.html'
    context_object_name = 'customers'
    sidebar_active = 'customers'
    page_title = 'Quản lý Khách hàng'

class KhachHangCreateView(SidebarContextMixin, CreateView):
    model = KhachHang
    fields = ['MaKH', 'Ten', 'SDT', 'Email', 'DiaChi']
    template_name = 'MyApp/customer_form.html'
    success_url = reverse_lazy('customer_list')
    sidebar_active = 'customers'

class KhachHangUpdateView(SidebarContextMixin, UpdateView):
    model = KhachHang
    fields = ['Ten', 'SDT', 'Email', 'DiaChi']
    template_name = 'MyApp/customer_form.html'
    success_url = reverse_lazy('customer_list')
    sidebar_active = 'customers'

class KhachHangDeleteView(DeleteView):
    model = KhachHang
    success_url = reverse_lazy('customer_list')

# --- ĐƠN HÀNG (ORDERS) ---
class DonHangListView(SidebarContextMixin, ListView):
    model = DonHang
    template_name = 'MyApp/order_list.html'
    context_object_name = 'orders'
    sidebar_active = 'orders'
    page_title = 'Quản lý Đơn hàng'

class DonHangCreateView(SidebarContextMixin, CreateView):
    model = DonHang
    fields = ['MaDH', 'KhachHang', 'TongTien', 'TrangThai']
    template_name = 'MyApp/order_form.html'
    success_url = reverse_lazy('order_list')
    sidebar_active = 'orders'

class DonHangUpdateView(SidebarContextMixin, UpdateView):
    model = DonHang
    fields = ['KhachHang', 'TongTien', 'TrangThai']
    template_name = 'MyApp/order_form.html'
    success_url = reverse_lazy('order_list')
    sidebar_active = 'orders'

class DonHangDeleteView(DeleteView):
    model = DonHang
    success_url = reverse_lazy('order_list')

# --- GIAO HÀNG (DELIVERY) ---
class GiaoHangListView(SidebarContextMixin, ListView):
    model = GiaoHang
    template_name = 'MyApp/delivery_list.html'
    context_object_name = 'deliveries'
    sidebar_active = 'delivery'
    page_title = 'Quản lý Giao hàng'

class GiaoHangCreateView(SidebarContextMixin, CreateView):
    model = GiaoHang
    fields = ['MaGH', 'DonHang', 'NguoiGiao', 'SdtNguoiGiao', 'TrangThai']
    template_name = 'MyApp/delivery_form.html'
    success_url = reverse_lazy('delivery_list')
    sidebar_active = 'delivery'

class GiaoHangUpdateView(SidebarContextMixin, UpdateView):
    model = GiaoHang
    fields = ['NguoiGiao', 'SdtNguoiGiao', 'TrangThai', 'NgayGiao']
    template_name = 'MyApp/delivery_form.html'
    success_url = reverse_lazy('delivery_list')
    sidebar_active = 'delivery'

class GiaoHangDeleteView(DeleteView):
    model = GiaoHang
    success_url = reverse_lazy('delivery_list')

# --- KHO HÀNG (WAREHOUSES) ---
class KhoListView(SidebarContextMixin, ListView):
    model = Kho
    template_name = 'MyApp/kho_list.html'
    context_object_name = 'warehouses'
    sidebar_active = 'warehouses'
    page_title = 'Quản lý Kho hàng'

class KhoCreateView(SidebarContextMixin, CreateView):
    model = Kho
    fields = ['MaKho', 'Ten', 'Loai', 'DiaChi', 'geom']
    template_name = 'MyApp/kho_form.html'
    success_url = reverse_lazy('kho_list')
    sidebar_active = 'warehouses'

class KhoUpdateView(SidebarContextMixin, UpdateView):
    model = Kho
    fields = ['Ten', 'Loai', 'DiaChi', 'geom']
    template_name = 'MyApp/kho_form.html'
    success_url = reverse_lazy('kho_list')
    sidebar_active = 'warehouses'

class KhoDeleteView(DeleteView):
    model = Kho
    success_url = reverse_lazy('kho_list')

# --- NHÂN VIÊN (EMPLOYEES) ---
class NhanVienListView(SidebarContextMixin, ListView):
    model = NhanVien
    template_name = 'MyApp/nhanvien_list.html'
    context_object_name = 'employees'
    sidebar_active = 'employees'
    page_title = 'Quản lý Nhân viên'

class NhanVienCreateView(SidebarContextMixin, CreateView):
    model = NhanVien
    fields = ['MaNV', 'Ten', 'SDT', 'Role']
    template_name = 'MyApp/nhanvien_form.html'
    success_url = reverse_lazy('nhanvien_list')
    sidebar_active = 'employees'

class NhanVienUpdateView(SidebarContextMixin, UpdateView):
    model = NhanVien
    fields = ['Ten', 'SDT', 'Role']
    template_name = 'MyApp/nhanvien_form.html'
    success_url = reverse_lazy('nhanvien_list')
    sidebar_active = 'employees'

class NhanVienDeleteView(DeleteView):
    model = NhanVien
    success_url = reverse_lazy('nhanvien_list')

# --- NHẬP KHO (STOCK IN) ---
class StockInListView(SidebarContextMixin, ListView):
    model = YeuCauNhapKho
    template_name = 'MyApp/stock_in_list.html'
    context_object_name = 'requests'
    sidebar_active = 'stock_in'
    page_title = 'Yêu cầu Nhập kho'

class StockInCreateView(SidebarContextMixin, CreateView):
    model = YeuCauNhapKho
    fields = ['MaYC', 'Ngay', 'TrangThai', 'GhiChu', 'MaNV']
    template_name = 'MyApp/stock_in_form.html'
    success_url = reverse_lazy('stock_in_list')
    sidebar_active = 'stock_in'

class StockInUpdateView(SidebarContextMixin, UpdateView):
    model = YeuCauNhapKho
    fields = ['Ngay', 'TrangThai', 'GhiChu', 'MaNV']
    template_name = 'MyApp/stock_in_form.html'
    success_url = reverse_lazy('stock_in_list')
    sidebar_active = 'stock_in'

class StockInDeleteView(DeleteView):
    model = YeuCauNhapKho
    success_url = reverse_lazy('stock_in_list')
