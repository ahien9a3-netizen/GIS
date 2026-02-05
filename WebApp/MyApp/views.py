from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import SanPham, CuaHang, Kho, HangTonKho, NhanVien, YeuCauNhapKho, DanhMuc

# ==================== MIXINS & HELPERS ====================
class SidebarContextMixin:
    sidebar_active = ""
    page_title = ""
    required_roles = [] # Danh sách các role được phép truy cập (trống = tất cả)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_active'] = self.sidebar_active
        context['page_title'] = self.page_title
        context['user_name'] = self.request.session.get('user_name', 'Khách')
        context['user_role'] = self.request.session.get('user_role', '')
        context['current_user_id'] = self.request.session.get('user_id', '')
        return context

    def dispatch(self, request, *args, **kwargs):
        # 1. Kiểm tra đăng nhập
        if 'user_id' not in request.session:
            return redirect('login')
        
        # 2. Kiểm tra phân quyền (Role)
        user_role = request.session.get('user_role')
        if self.required_roles and user_role not in self.required_roles:
            return render(request, 'MyApp/403.html', {'message': 'Bạn không có quyền truy cập chức năng này!'}, status=403)
            
        return super().dispatch(request, *args, **kwargs)

# Decorator cho Function-Based Views
def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('login')
            user_role = request.session.get('user_role')
            if allowed_roles and user_role not in allowed_roles:
                return render(request, 'MyApp/403.html', {'message': 'Bạn không có quyền thực hiện hành động này!'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# ==================== HOME & GIS ====================
def home(request):
    """
    dashboard chính - Sử dụng ORM để lấy dữ liệu thống kê
    """
    if 'user_id' not in request.session:
        return redirect('login')

    total_stores = CuaHang.objects.count()
    total_warehouses = Kho.objects.count()
    total_products = SanPham.objects.count()
    total_inventory = HangTonKho.objects.aggregate(total=Sum('SoLuong'))['total'] or 0

    stores_qs = CuaHang.objects.all().order_by('MaCH')
    
    inventory_by_warehouse_qs = HangTonKho.objects.values('MaKho__Ten')\
        .annotate(total=Sum('SoLuong'))\
        .order_by('MaKho__Ten')
    
    stores_list = []
    for store in stores_qs:
        stores_list.append({
            'MaCH': store.MaCH,
            'Ten': store.Ten,
            'Loai': store.Loai.strip() if store.Loai else "", # Đảm bảo không có khoảng trắng thừa
            'DiaChi': store.DiaChi,
            'TrangThai': store.TrangThai,
            'lon': store.geom.x if store.geom else 0,
            'lat': store.geom.y if store.geom else 0,
        })

    warehouses_qs = Kho.objects.all().order_by('MaKho')
    warehouses_list = []
    for wh in warehouses_qs:
        warehouses_list.append({
            'MaKho': wh.MaKho,
            'Ten': wh.Ten,
            'DiaChi': wh.DiaChi,
            'lon': wh.geom.x if wh.geom else 0,
            'lat': wh.geom.y if wh.geom else 0,
        })

    inventory_by_warehouse = [
        (item['MaKho__Ten'], item['total']) for item in inventory_by_warehouse_qs
    ]

    context = {
        'total_stores': total_stores,
        'total_warehouses': total_warehouses,
        'total_products': total_products,
        'total_inventory': total_inventory,
        'stores_list': stores_list,
        'warehouses_list': warehouses_list,
        'inventory_by_warehouse': inventory_by_warehouse,
        'sidebar_active': 'dashboard',
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    }
    
    return render(request, 'MyApp/home.html', context)

@role_required(['Admin', 'Kế Toán'])
def report_view(request):
    """
    Trang báo cáo thống kê - Tổng hợp dữ liệu biểu đồ
    """
    if 'user_id' not in request.session:
        return redirect('login')
    # 1. Thống kê sản phẩm theo danh mục
    category_stats = DanhMuc.objects.annotate(total_products=Count('sanpham')).values('Ten', 'total_products')
    
    # 2. Thống kê tồn kho theo kho hàng
    inventory_stats = HangTonKho.objects.values('MaKho__Ten').annotate(total_qty=Sum('SoLuong')).order_by('-total_qty')
    
    # 3. Thống kê trạng thái cửa hàng
    store_status = CuaHang.objects.values('TrangThai').annotate(count=Count('MaCH'))
    
    # 4. Thống kê nhân viên theo vai trò
    employee_roles = NhanVien.objects.values('Role').annotate(count=Count('MaNV'))

    import json
    
    # Chuẩn bị dữ liệu JSON cho biểu đồ
    cat_json = {
        'labels': [item['Ten'] for item in category_stats],
        'values': [int(item['total_products']) for item in category_stats]
    }
    inv_json = {
        'labels': [item['MaKho__Ten'] for item in inventory_stats],
        'values': [int(item['total_qty']) for item in inventory_stats]
    }
    st_json = {
        'labels': [item['TrangThai'] for item in store_status],
        'values': [int(item['count']) for item in store_status]
    }
    em_json = {
        'labels': [item['Role'] for item in employee_roles],
        'values': [int(item['count']) for item in employee_roles]
    }

    context = {
        'sidebar_active': 'reports',
        'page_title': 'Báo cáo Thống kê',
        'cat_json': json.dumps(cat_json),
        'inv_json': json.dumps(inv_json),
        'st_json': json.dumps(st_json),
        'em_json': json.dumps(em_json),
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    }
    return render(request, 'MyApp/reports.html', context)

def login_view(request):
    """
    Xử lý đăng nhập thủ công từ bảng NhanVien sử dụng SDT
    """
    error = None
    if request.method == 'POST':
        sdt = request.POST.get('sdt')
        matkhau = request.POST.get('matkhau')
        
        try:
            nv = NhanVien.objects.get(SDT=sdt, MatKhau=matkhau)
            # Lưu vào session
            request.session['user_id'] = nv.MaNV
            request.session['user_name'] = nv.Ten
            request.session['user_role'] = nv.Role
            return redirect('home')
        except NhanVien.DoesNotExist:
            error = "Số điện thoại hoặc mật khẩu không đúng!"
            
    return render(request, 'MyApp/login.html', {'error': error})

def logout_view(request):
    """
    Đăng xuất - Xóa session
    """
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'user_name' in request.session:
        del request.session['user_name']
    return redirect('login')

def settings_view(request):
    """
    Trang cài đặt và quản lý thông tin cá nhân/mật khẩu
    """
    if 'user_id' not in request.session:
        return redirect('login')
    
    user_id = request.session.get('user_id')
    try:
        user = NhanVien.objects.get(MaNV=user_id)
    except NhanVien.DoesNotExist:
        return redirect('logout')

    success_msg = None
    error_msg = None

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. Cập nhật thông tin cơ bản
        if action == 'update_profile':
            user.Ten = request.POST.get('ten')
            user.SDT = request.POST.get('sdt')
            user.save()
            request.session['user_name'] = user.Ten # Cập nhật lại tên trên header
            success_msg = "Cập nhật thông tin thành công!"
            
        # 2. Đổi mật khẩu
        elif action == 'change_password':
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            if old_pass != user.MatKhau:
                error_msg = "Mật khẩu hiện tại không chính xác!"
            elif new_pass != confirm_pass:
                error_msg = "Mật khẩu mới không khớp nhau!"
            else:
                user.MatKhau = new_pass
                user.save()
                success_msg = "Đổi mật khẩu thành công!"

    context = {
        'sidebar_active': 'settings',
        'page_title': 'Cài đặt tài khoản',
        'user': user,
        'user_name': user.Ten,
        'success_msg': success_msg,
        'error_msg': error_msg
    }
    return render(request, 'MyApp/settings.html', context)

def gis_map(request):
    """
    Trang bản đồ GIS chuyên dụng (Full screen)
    """
    if 'user_id' not in request.session:
        return redirect('login')
    context = {
        'sidebar_active': 'gis_map',
        'page_title': 'Bản đồ GIS Chuyên sâu',
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    }
    return render(request, 'MyApp/gis_map.html', context)

# GIS APIs keep as is (same logic)
def store_geojson(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
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
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    stores = CuaHang.objects.filter(geom__isnull=False).values_list('geom', flat=True)
    warehouses = Kho.objects.filter(geom__isnull=False).values_list('geom', flat=True)
    data = [[p.y, p.x] for p in stores] + [[p.y, p.x] for p in warehouses]
    return JsonResponse(data, safe=False)

@require_GET
def service_area(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
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
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    kho_list = Kho.objects.all()
    features = []
    for wh in kho_list:
        if wh.geom:
            features.append({
                "type": "Feature",
                "properties": {"id": wh.MaKho, "name": wh.Ten, "address": wh.DiaChi, "type": wh.Loai},
                "geometry": {"type": "Point", "coordinates": [wh.geom.x, wh.geom.y]}
            })
    return JsonResponse({"type": "FeatureCollection", "features": features})

def inventory_stats(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
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

class CuaHangDeleteView(SidebarContextMixin, DeleteView):
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

class SanPhamDeleteView(SidebarContextMixin, DeleteView):
    model = SanPham
    success_url = reverse_lazy('product_list')

# --- DANH MỤC (CATEGORIES) ---
class DanhMucListView(SidebarContextMixin, ListView):
    model = DanhMuc
    template_name = 'MyApp/danhmuc_list.html'
    context_object_name = 'categories'
    sidebar_active = 'categories'
    page_title = 'Quản lý Danh mục'

class DanhMucCreateView(SidebarContextMixin, CreateView):
    model = DanhMuc
    fields = ['MaDM', 'Ten', 'MoTa']
    template_name = 'MyApp/danhmuc_form.html'
    success_url = reverse_lazy('danhmuc_list')
    sidebar_active = 'categories'
    page_title = 'Thêm Danh mục mới'

class DanhMucUpdateView(SidebarContextMixin, UpdateView):
    model = DanhMuc
    fields = ['Ten', 'MoTa']
    template_name = 'MyApp/danhmuc_form.html'
    success_url = reverse_lazy('danhmuc_list')
    sidebar_active = 'categories'
    page_title = 'Cập nhật Danh mục'

class DanhMucDeleteView(SidebarContextMixin, DeleteView):
    model = DanhMuc
    success_url = reverse_lazy('danhmuc_list')

# --- TỒN KHO (INVENTORY) ---
class HangTonKhoListView(SidebarContextMixin, ListView):
    model = HangTonKho
    template_name = 'MyApp/inventory_list.html'
    context_object_name = 'inventory'
    sidebar_active = 'inventory'
    page_title = 'Quản lý Tồn kho'

class HangTonKhoCreateView(SidebarContextMixin, CreateView):
    model = HangTonKho
    fields = ['MaKho', 'MaSP', 'SoLuong']
    template_name = 'MyApp/inventory_form.html'
    success_url = reverse_lazy('inventory_list')
    sidebar_active = 'inventory'
    page_title = 'Thêm mới Tồn kho'

class HangTonKhoUpdateView(SidebarContextMixin, UpdateView):
    model = HangTonKho
    fields = ['SoLuong']
    template_name = 'MyApp/inventory_form.html'
    success_url = reverse_lazy('inventory_list')
    sidebar_active = 'inventory'
    page_title = 'Điều chỉnh Tồn kho'

    def get_object(self, queryset=None):
        return get_object_or_404(HangTonKho, MaKho=self.kwargs['makho'], MaSP=self.kwargs['masp'])

class HangTonKhoDeleteView(SidebarContextMixin, DeleteView):
    model = HangTonKho
    success_url = reverse_lazy('inventory_list')

    def get_object(self, queryset=None):
        return get_object_or_404(HangTonKho, MaKho=self.kwargs['makho'], MaSP=self.kwargs['masp'])


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

class KhoDeleteView(SidebarContextMixin, DeleteView):
    model = Kho
    success_url = reverse_lazy('kho_list')

# --- NHÂN VIÊN (EMPLOYEES) ---
class NhanVienListView(SidebarContextMixin, ListView):
    model = NhanVien
    template_name = 'MyApp/nhanvien_list.html'
    context_object_name = 'employees'
    sidebar_active = 'employees'
    page_title = 'Quản lý Nhân viên'
    required_roles = ['Admin']

class NhanVienCreateView(SidebarContextMixin, CreateView):
    model = NhanVien
    fields = ['MaNV', 'Ten', 'SDT', 'Role', 'MatKhau']
    template_name = 'MyApp/nhanvien_form.html'
    success_url = reverse_lazy('nhanvien_list')
    sidebar_active = 'employees'
    required_roles = ['Admin']

class NhanVienUpdateView(SidebarContextMixin, UpdateView):
    model = NhanVien
    fields = ['Ten', 'SDT', 'Role', 'MatKhau']
    template_name = 'MyApp/nhanvien_form.html'
    success_url = reverse_lazy('nhanvien_list')
    sidebar_active = 'employees'
    required_roles = ['Admin']

class NhanVienDeleteView(SidebarContextMixin, DeleteView):
    model = NhanVien
    success_url = reverse_lazy('nhanvien_list')
    required_roles = ['Admin']

# --- NHẬP KHO (STOCK IN) ---
class StockInListView(SidebarContextMixin, ListView):
    model = YeuCauNhapKho
    template_name = 'MyApp/stock_in_list.html'
    context_object_name = 'requests'
    sidebar_active = 'stock_in'
    page_title = 'Yêu cầu Nhập kho'
    required_roles = ['Admin', 'Kế Toán']

class StockInCreateView(SidebarContextMixin, CreateView):
    model = YeuCauNhapKho
    fields = ['MaYC', 'Ngay', 'TrangThai', 'GhiChu', 'MaNV']
    template_name = 'MyApp/stock_in_form.html'
    success_url = reverse_lazy('stock_in_list')
    sidebar_active = 'stock_in'
    required_roles = ['Admin', 'Kế Toán']

class StockInUpdateView(SidebarContextMixin, UpdateView):
    model = YeuCauNhapKho
    fields = ['Ngay', 'TrangThai', 'GhiChu', 'MaNV']
    template_name = 'MyApp/stock_in_form.html'
    success_url = reverse_lazy('stock_in_list')
    sidebar_active = 'stock_in'
    required_roles = ['Admin', 'Kế Toán']

class StockInDeleteView(SidebarContextMixin, DeleteView):
    model = YeuCauNhapKho
    success_url = reverse_lazy('stock_in_list')
    required_roles = ['Admin', 'Kế Toán']
