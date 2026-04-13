from django import forms
from django.forms import ClearableFileInput
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.conf import settings
import os
import random


from django.db.models import Count, Sum, Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import SanPham, CuaHang, Kho, HangTonKho, NhanVien, YeuCauNhapKho, DanhMuc, DanhGiaCuaHang
from .forms import DanhGiaForm 
from django.db.models import Avg


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class SidebarContextMixin:
    sidebar_active = ""
    page_title = ""
    required_roles = [] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_active'] = self.sidebar_active
        context['page_title'] = self.page_title
        context['user_name'] = self.request.session.get('user_name', 'Khách')
        context['user_role'] = self.request.session.get('user_role', '')
        context['current_user_id'] = self.request.session.get('user_id', '')
        context['is_admin_view'] = self.request.session.get('is_admin_view', False)
        return context

    def dispatch(self, request, *args, **kwargs):
        # 1. Kiểm tra đăng nhập
        if 'user_id' not in request.session:
            return redirect('login')
        
        # 2. Lấy role và trạng thái view hiện tại
        user_role = request.session.get('user_role')
        is_admin_view = request.session.get('is_admin_view', False)

        # 3. Kiểm tra phân quyền (Role và View)
        if self.required_roles and 'Admin' in self.required_roles:
            # Nếu trang yêu cầu Admin, nhưng user không phải Admin HOẶC đang tắt view Admin
            if user_role != 'Admin' or (user_role == 'Admin' and not is_admin_view):
                return render(request, '403.html', {'message': 'Bạn không có quyền truy cập hoặc đang ở chế độ Nhân viên!'}, status=403)
        elif self.required_roles and user_role not in self.required_roles:
            return render(request, '403.html', {'message': 'Bạn không có quyền truy cập chức năng này!'}, status=403)
            
        return super().dispatch(request, *args, **kwargs)

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('login')
            user_role = request.session.get('user_role')
            if allowed_roles and user_role not in allowed_roles:
                return render(request, '403.html', {'message': 'Bạn không có quyền thực hiện hành động này!'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


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
            'Loai': store.Loai.strip() if store.Loai else "", 
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
        
        
        nv_list = list(NhanVien.objects.raw(
            "SELECT * FROM nhanvien WHERE sdt = %s AND matkhau = %s", 
            [sdt, matkhau]
        ))
        
        if nv_list:
            nv = nv_list[0]
            
            request.session['user_id'] = nv.MaNV
            request.session['user_name'] = nv.Ten
            request.session['user_role'] = nv.Role
            # Mặc định Admin đăng nhập vào sẽ thấy view Admin
            request.session['is_admin_view'] = (nv.Role == 'Admin')
            return redirect('home')
        else:
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

def forgot_password_view(request):
    """
    Yêu cầu reset mật khẩu: Tạo OTP 6 số và lưu vào Session
    """
    error = None
    success = None
    if request.method == 'POST':
        sdt = request.POST.get('sdt')
        email_input = request.POST.get('email')
        try:
            nv = NhanVien.objects.get(SDT=sdt)
            
            # Kiểm tra Email nhập vào có khớp với Database không
            db_email = getattr(nv, 'Email', None)
            if not db_email or db_email.lower() != email_input.lower():
                error = "Email không khớp với thông tin đã đăng ký cho số điện thoại này."
            else:
                # Tạo mã OTP 6 số ngẫu nhiên
                otp = str(random.randint(100000, 999999))
                
                # Lưu OTP và MaNV vào Session
                request.session['reset_otp'] = otp
                request.session['reset_manv'] = nv.MaNV
                request.session.set_expiry(600)
                
                # Gửi mã OTP
                send_mail(
                    'Mã xác thực đặt lại mật khẩu - SMART MART',
                    f'Chào {nv.Ten},\n\nMã xác thực (OTP) của bạn là: {otp}\n\nMã này có hiệu lực trong 10 phút.',
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@smartmart.com'),
                    [db_email],
                    fail_silently=False,
                )
                return redirect('verify_otp')
        except NhanVien.DoesNotExist:
            error = "Số điện thoại không tồn tại trong hệ thống."
        except Exception as e:
            error = f"Có lỗi xảy ra: {str(e)}"
            
    return render(request, 'MyApp/forgot_password.html', {'error': error, 'success': success})


def verify_otp_view(request):
    """
    Trang nhập mã OTP từ email
    """
    error = None
    if request.method == 'POST':
        # Ghép các ô nhập otp lại (nếu dùng giao diện nhiều ô)
        otp_input = request.POST.get('otp') 
        if not otp_input:
            # Hỗ trợ trường hợp giao diện tách từng ô
            otp_input = "".join([request.POST.get(f'digit{i}', '') for i in range(1, 7)])

        otp_session = request.session.get('reset_otp')
        
        if otp_session and otp_input == otp_session:
            # Xác thực thành công, cho phép đổi mật khẩu
            request.session['otp_verified'] = True
            return redirect('reset_password')
        else:
            error = "Mã OTP không chính xác hoặc đã hết hạn."
            
    return render(request, 'MyApp/verify_otp.html', {'error': error})


def reset_password_view(request):
    """
    Trang đặt mật khẩu mới (Chỉ cho phép sau khi đã Verify OTP thành công)
    """
    if not request.session.get('otp_verified'):
        return redirect('forgot_password')
        
    ma_nv = request.session.get('reset_manv')
    nv = get_object_or_404(NhanVien, MaNV=ma_nv)
    error = None
    
    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        
        if new_pass != confirm_pass:
            error = "Mật khẩu xác nhận không khớp."
        else:
            # Cập nhật thành công
            nv.MatKhau = new_pass
            nv.save()
            # Xóa session reset
            del request.session['reset_otp']
            del request.session['reset_manv']
            del request.session['otp_verified']
            return render(request, 'MyApp/reset_password.html', {'success': 'Mật khẩu đã được đổi thành công.'})

    return render(request, 'MyApp/reset_password.html', {'error': error})


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
        
        
        if action == 'update_profile':
            user.Ten = request.POST.get('ten')
            user.SDT = request.POST.get('sdt')
            user.save()
            request.session['user_name'] = user.Ten 
            success_msg = "Cập nhật thông tin thành công!"
            
        
        elif action == 'change_password':
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            
            from django.db import connection
            is_correct = False
            with connection.cursor() as cursor:
                cursor.execute("SELECT (matkhau = %s) FROM nhanvien WHERE manv = %s", [old_pass, user.MaNV])
                row = cursor.fetchone()
                if row:
                    is_correct = row[0]

            if not is_correct:
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
        'user_role': request.session.get('user_role', ''),
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




def inventory_stats(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    data = HangTonKho.objects.select_related('MaSP', 'MaKho').order_by('-SoLuong').values('MaSP__Ten', 'MaKho__Ten', 'SoLuong')
    result = [{'product': item['MaSP__Ten'], 'warehouse': item['MaKho__Ten'], 'quantity': item['SoLuong']} for item in data]
    return JsonResponse({'inventory': result})



#  CỬA HÀNG  
class CuaHangListView(SidebarContextMixin, ListView):
    model = CuaHang
    template_name = 'MyApp/store_list.html'
    context_object_name = 'stores'
    sidebar_active = 'stores'
    page_title = 'Quản lý Cửa hàng'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        loai = self.request.GET.get('loai')
        trang_thai = self.request.GET.get('trang_thai')

        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(DiaChi__icontains=q) | Q(MaCH__icontains=q)
            )
        if loai:
            queryset = queryset.filter(Loai=loai)
        if trang_thai:
            queryset = queryset.filter(TrangThai=trang_thai)
        return queryset.order_by('MaCH')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loai_choices'] = CuaHang.objects.values_list('Loai', flat=True).distinct()
        context['trang_thai_choices'] = CuaHang.objects.values_list('TrangThai', flat=True).distinct()
        return context

class CuaHangCreateView(SidebarContextMixin, CreateView):
    model = CuaHang
    fields = ['MaCH', 'Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai', 'geom', 'MoTa']
    template_name = 'MyApp/store_form.html'
    success_url = reverse_lazy('store_list')
    sidebar_active = 'stores'
    page_title = 'Thêm Cửa hàng mới'

    def get_form(self, form_class=None):
        return super().get_form(form_class)

    def form_valid(self, form):
        files = self.request.FILES.getlist('hinhanh_upload')
        fs = FileSystemStorage(location=os.path.join('media', 'store'))
        
        instance = form.save(commit=False)
        # Keep existing images, standardize them, and add new ones
        existing_paths = instance.hinhanh if instance.hinhanh else []
        new_paths = []
        for p in existing_paths:
            if p and not p.startswith('http'):
                # Đảm bảo đường dẫn luôn bắt đầu bằng 'store/'
                p_clean = p.replace('store/', '').replace('warehouse/', '')
                new_paths.append(f'store/{p_clean}')
            else:
                new_paths.append(p)
        
        for f in files:
            filename = fs.save(f.name, f)
            new_paths.append(f'store/{filename}')
            
        # Deduplicate while keeping order
        instance.hinhanh = list(dict.fromkeys(new_paths))
        instance.save()
        self.object = instance
        return redirect(self.get_success_url())

class CuaHangUpdateView(SidebarContextMixin, UpdateView):
    model = CuaHang
    fields = ['Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai', 'geom', 'MoTa']
    template_name = 'MyApp/store_form.html'
    success_url = reverse_lazy('store_list')
    sidebar_active = 'stores'
    page_title = 'Cập nhật Cửa hàng'

    def get_form(self, form_class=None):
        return super().get_form(form_class)

    def form_valid(self, form):
        files = self.request.FILES.getlist('hinhanh_upload')
        fs = FileSystemStorage(location=os.path.join('media', 'store'))
        
        instance = form.save(commit=False)
        # Keep existing images, standardize them, and add new ones
        existing_paths = instance.hinhanh if instance.hinhanh else []
        new_paths = []
        for p in existing_paths:
            if p and not p.startswith('http'):
                # Đảm bảo đường dẫn luôn bắt đầu bằng 'store/'
                p_clean = p.replace('store/', '').replace('warehouse/', '')
                new_paths.append(f'store/{p_clean}')
            else:
                new_paths.append(p)
        
        for f in files:
            filename = fs.save(f.name, f)
            new_paths.append(f'store/{filename}')
            
        # Deduplicate while keeping order
        instance.hinhanh = list(dict.fromkeys(new_paths))
        instance.save()
        self.object = instance
        return redirect(self.get_success_url())

def store_detail_view(request, pk):
    if 'user_id' not in request.session: return redirect('login')
    store = get_object_or_404(CuaHang, MaCH=pk)
    
    # Lấy danh sách đánh giá
    reviews = store.danh_gia.all()
    
    # --- LOGIC TÍNH ĐIỂM TRUNG BÌNH ---
    total_reviews = reviews.count()
    # Tính trung bình, nếu chưa có ai đánh giá thì mặc định là 0
    avg_rating = reviews.aggregate(Avg('SoSao'))['SoSao__avg'] or 0
    avg_rating = round(avg_rating, 1) # Làm tròn 1 chữ số thập phân (VD: 4.7)
    # Tính phần trăm để hiển thị thanh sao màu xanh (VD: 4.7 sao = 94%)
    avg_percent = (avg_rating / 5) * 100 if total_reviews > 0 else 0
    
    # Xử lý khi gửi form
    if request.method == 'POST':
        form = DanhGiaForm(request.POST)
        if form.is_valid():
            danh_gia = form.save(commit=False)
            danh_gia.CuaHang = store
            danh_gia.NhanVien = get_object_or_404(NhanVien, MaNV=request.session['user_id'])
            danh_gia.save()
            return redirect('store_detail', pk=pk)
    else:
        form = DanhGiaForm()

    return render(request, 'MyApp/store_detail.html', {
        'store': store,
        'reviews': reviews,
        'form': form,
        'avg_rating': avg_rating,       # Truyền điểm trung bình ra giao diện
        'total_reviews': total_reviews, # Truyền tổng số lượt ra giao diện
        'avg_percent': avg_percent,     # Truyền % để vẽ sao
        'sidebar_active': 'stores',
        'page_title': 'Chi tiết Cửa hàng',
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    })

def store_image_check_view(request, pk):
    if 'user_id' not in request.session: return redirect('login')
    store = get_object_or_404(CuaHang, MaCH=pk)
    return render(request, 'MyApp/store_image_check.html', {
        'store': store,
        'sidebar_active': 'stores'
    })

class CuaHangDeleteView(SidebarContextMixin, DeleteView):
    model = CuaHang
    success_url = reverse_lazy('store_list')

#  SẢN PHẨM 
class SanPhamListView(SidebarContextMixin, ListView):
    model = SanPham
    template_name = 'MyApp/product_list.html'
    context_object_name = 'products'
    sidebar_active = 'products'
    page_title = 'Quản lý Sản phẩm'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        dm = self.request.GET.get('danhmuc')
        
        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(MieuTa__icontains=q) | Q(MaSP__icontains=q)
            )
        if dm:
            queryset = queryset.filter(DanhMuc_id=dm)
        return queryset.order_by('MaSP')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['danhmuc_choices'] = DanhMuc.objects.all()
        return context

class SanPhamDetailView(SidebarContextMixin, DetailView):
    model = SanPham
    template_name = 'MyApp/product_detail.html'
    context_object_name = 'product'
    sidebar_active = 'products'
    page_title = 'Chi tiết sản phẩm'

class SanPhamCreateView(SidebarContextMixin, CreateView):
    model = SanPham
    fields = ['MaSP', 'Ten', 'Image', 'DanhMuc', 'MieuTa', 'TrangThai']
    template_name = 'MyApp/product_form.html'
    success_url = reverse_lazy('product_list')
    sidebar_active = 'products'

class SanPhamUpdateView(SidebarContextMixin, UpdateView):
    model = SanPham
    fields = ['Ten', 'Image', 'DanhMuc', 'MieuTa', 'TrangThai']
    template_name = 'MyApp/product_form.html'
    success_url = reverse_lazy('product_list')
    sidebar_active = 'products'

class SanPhamDeleteView(SidebarContextMixin, DeleteView):
    model = SanPham
    success_url = reverse_lazy('product_list')

#  DANH MỤC 
class DanhMucListView(SidebarContextMixin, ListView):
    model = DanhMuc
    template_name = 'MyApp/danhmuc_list.html'
    context_object_name = 'categories'
    sidebar_active = 'categories'
    page_title = 'Quản lý Danh mục'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(MaDM__icontains=q)
            )
        return queryset.order_by('MaDM')

class DanhMucCreateView(SidebarContextMixin, CreateView):
    model = DanhMuc
    fields = ['MaDM', 'Ten']
    template_name = 'MyApp/danhmuc_form.html'
    success_url = reverse_lazy('danhmuc_list')
    sidebar_active = 'categories'
    page_title = 'Thêm Danh mục mới'

class DanhMucUpdateView(SidebarContextMixin, UpdateView):
    model = DanhMuc
    fields = ['Ten']
    template_name = 'MyApp/danhmuc_form.html'
    success_url = reverse_lazy('danhmuc_list')
    sidebar_active = 'categories'
    page_title = 'Cập nhật Danh mục'

class DanhMucDeleteView(SidebarContextMixin, DeleteView):
    model = DanhMuc
    success_url = reverse_lazy('danhmuc_list')

#  TỒN KHO
class HangTonKhoListView(SidebarContextMixin, ListView):
    model = HangTonKho
    template_name = 'MyApp/inventory_list.html'
    context_object_name = 'inventory'
    sidebar_active = 'inventory'
    page_title = 'Quản lý Tồn kho'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        kho = self.request.GET.get('kho')
        
        if q:
            queryset = queryset.filter(
                Q(MaSP__Ten__icontains=q) | Q(MaSP__MaSP__icontains=q)
            )
        if kho:
            queryset = queryset.filter(MaKho_id=kho)
        return queryset.select_related('MaSP', 'MaKho').order_by('MaKho', 'MaSP')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kho_choices'] = Kho.objects.all()
        return context

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


#  KHO HÀNG
#  KHO HÀNG
class KhoListView(SidebarContextMixin, ListView):
    model = Kho
    template_name = 'MyApp/kho_list.html'
    context_object_name = 'warehouses'
    sidebar_active = 'warehouses'
    page_title = 'Quản lý Kho hàng'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        loai = self.request.GET.get('loai')

        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(DiaChi__icontains=q) | Q(MaKho__icontains=q)
            )
        if loai:
            queryset = queryset.filter(Loai=loai)
        return queryset.order_by('MaKho')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loai_choices'] = Kho.objects.values_list('Loai', flat=True).distinct()
        return context

class KhoCreateView(SidebarContextMixin, CreateView):
    model = Kho
    fields = ['MaKho', 'Ten', 'Loai', 'DiaChi', 'geom', 'MoTa']
    template_name = 'MyApp/kho_form.html'
    success_url = reverse_lazy('kho_list')
    sidebar_active = 'warehouses'
    page_title = 'Thêm Kho mới'

    def get_form(self, form_class=None):
        return super().get_form(form_class)

    def form_valid(self, form):
        files = self.request.FILES.getlist('hinhanh_upload')
        fs = FileSystemStorage(location=os.path.join('media', 'warehouse'))
        
        instance = form.save(commit=False)
        # Keep existing images, standardize them, and add new ones
        existing_paths = instance.hinhanh if instance.hinhanh else []
        new_paths = []
        for p in existing_paths:
            if p and not p.startswith('http'):
                p_clean = p.replace('store/', '').replace('warehouse/', '')
                new_paths.append(f'warehouse/{p_clean}')
            else:
                new_paths.append(p)
        
        for f in files:
            filename = fs.save(f.name, f)
            new_paths.append(f'warehouse/{filename}')
        instance.hinhanh = list(dict.fromkeys(new_paths))
        instance.save()
        self.object = instance
        return redirect(self.get_success_url())

class KhoUpdateView(SidebarContextMixin, UpdateView):
    model = Kho
    fields = ['Ten', 'Loai', 'DiaChi', 'geom', 'MoTa']
    template_name = 'MyApp/kho_form.html'
    success_url = reverse_lazy('kho_list')
    sidebar_active = 'warehouses'
    page_title = 'Cập nhật Kho'

    def get_form(self, form_class=None):
        return super().get_form(form_class)

    def form_valid(self, form):
        files = self.request.FILES.getlist('hinhanh_upload')
        fs = FileSystemStorage(location=os.path.join('media', 'warehouse'))
        
        instance = form.save(commit=False)
        # Keep existing images, standardize them, and add new ones
        existing_paths = instance.hinhanh if instance.hinhanh else []
        new_paths = []
        for p in existing_paths:
            if p and not p.startswith('http'):
                p_clean = p.replace('store/', '').replace('warehouse/', '')
                new_paths.append(f'warehouse/{p_clean}')
            else:
                new_paths.append(p)
        
        for f in files:
            filename = fs.save(f.name, f)
            new_paths.append(f'warehouse/{filename}')
        instance.hinhanh = list(dict.fromkeys(new_paths))
        instance.save()
        self.object = instance
        return redirect(self.get_success_url())

def kho_detail_view(request, pk):
    if 'user_id' not in request.session: return redirect('login')
    wh = get_object_or_404(Kho, MaKho=pk)
    return render(request, 'MyApp/kho_detail.html', {
        'wh': wh,
        'sidebar_active': 'warehouses',
        'page_title': 'Chi tiết Kho hàng',
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    })

class KhoDeleteView(SidebarContextMixin, DeleteView):
    model = Kho
    success_url = reverse_lazy('kho_list')

#  NHÂN VIÊN 
class NhanVienListView(SidebarContextMixin, ListView):
    model = NhanVien
    template_name = 'MyApp/nhanvien_list.html'
    context_object_name = 'employees'
    sidebar_active = 'employees'
    page_title = 'Quản lý Nhân viên'
    paginate_by = 5
    required_roles = ['Admin']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        role = self.request.GET.get('role')
        
        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(MaNV__icontains=q) | Q(SDT__icontains=q)
            )
        if role:
            queryset = queryset.filter(Role=role)
        return queryset.order_by('MaNV')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = NhanVien.objects.values_list('Role', flat=True).distinct()
        return context

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

#  NHẬP KHO 
class StockInListView(SidebarContextMixin, ListView):
    model = YeuCauNhapKho
    template_name = 'MyApp/stock_in_list.html'
    context_object_name = 'requests'
    sidebar_active = 'stock_in'
    page_title = 'Yêu cầu Nhập kho'
    paginate_by = 5
    required_roles = ['Admin', 'Kế Toán']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        
        if q:
            queryset = queryset.filter(
                Q(MaYC__icontains=q) | Q(GhiChu__icontains=q) | Q(MaNV__Ten__icontains=q)
            )
        if status:
            queryset = queryset.filter(TrangThai=status)
        return queryset.select_related('MaNV').order_by('-Ngay')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = YeuCauNhapKho.objects.values_list('TrangThai', flat=True).distinct()
        return context

class StockInDetailView(SidebarContextMixin, DetailView):
    model = YeuCauNhapKho
    template_name = 'MyApp/stock_in_detail.html'
    context_object_name = 'request_obj'
    sidebar_active = 'stock_in'
    page_title = 'Chi tiết Yêu cầu Nhập kho'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Lấy danh sách sản phẩm chi tiết của phiếu này
        from .models import NhapKhoChiTiet
        context['details'] = NhapKhoChiTiet.objects.filter(MaYC=self.object).select_related('MaSP', 'MaKho')
        return context

from django.forms import inlineformset_factory
from .models import YeuCauNhapKho, NhapKhoChiTiet

# Tạo FormSet để quản lý danh sách sản phẩm bên trong phiếu nhập
StockInDetailFormSet = inlineformset_factory(
    YeuCauNhapKho, 
    NhapKhoChiTiet,
    fields=['MaSP', 'MaKho', 'SoLuong'],
    extra=1, # Hiển thị 1 dòng trống để nhập
    can_delete=True
)

from .forms import YeuCauNhapKhoForm

class StockInCreateView(SidebarContextMixin, CreateView):
    model = YeuCauNhapKho
    form_class = YeuCauNhapKhoForm
    template_name = 'MyApp/stock_in_form.html'
    success_url = reverse_lazy('stock_in_list')
    sidebar_active = 'stock_in'
    required_roles = ['Admin', 'Kế Toán']
    page_title = 'Tạo mới Phiếu nhập kho'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['product_formset'] = StockInDetailFormSet(self.request.POST)
        else:
            data['product_formset'] = StockInDetailFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        product_formset = context['product_formset']
        
        if product_formset.is_valid():
            self.object = form.save()
            product_formset.instance = self.object
            product_formset.save()
            
            # CẬP NHẬT TỒN KHO KHI TẠO MỚI PHIẾU ĐÃ DUYỆT LUÔN
            if self.object.TrangThai == 'Đã duyệt':
                from .models import HangTonKho, NhapKhoChiTiet
                items = NhapKhoChiTiet.objects.filter(MaYC=self.object)
                for item in items:
                    inventory, created = HangTonKho.objects.get_or_create(
                        MaKho=item.MaKho, MaSP=item.MaSP, defaults={'SoLuong': 0}
                    )
                    inventory.SoLuong += item.SoLuong
                    inventory.save()
                    
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class StockInUpdateView(SidebarContextMixin, UpdateView):
    model = YeuCauNhapKho
    form_class = YeuCauNhapKhoForm
    template_name = 'MyApp/stock_in_form.html'
    success_url = reverse_lazy('stock_in_list')
    sidebar_active = 'stock_in'
    required_roles = ['Admin', 'Kế Toán']
    page_title = 'Chỉnh sửa Phiếu nhập kho'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['product_formset'] = StockInDetailFormSet(self.request.POST, instance=self.object)
        else:
            data['product_formset'] = StockInDetailFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        product_formset = context['product_formset']
        
        # Lưu trạng thái cũ trước khi update
        old_status = self.get_object().TrangThai
        
        if product_formset.is_valid():
            self.object = form.save()
            product_formset.instance = self.object
            product_formset.save()
            
            # LOGIC CẬP NHẬT TỒN KHO KHI CHUYỂN SANG ĐÃ DUYỆT
            new_status = self.object.TrangThai
            if old_status != 'Đã duyệt' and new_status == 'Đã duyệt':
                from .models import HangTonKho, NhapKhoChiTiet
                items = NhapKhoChiTiet.objects.filter(MaYC=self.object)
                for item in items:
                    inventory, created = HangTonKho.objects.get_or_create(
                        MaKho=item.MaKho, MaSP=item.MaSP, defaults={'SoLuong': 0}
                    )
                    inventory.SoLuong += item.SoLuong
                    inventory.save()
                    
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class StockInDeleteView(SidebarContextMixin, DeleteView):
    model = YeuCauNhapKho
    success_url = reverse_lazy('stock_in_list')
    required_roles = ['Admin', 'Kế Toán']

@csrf_exempt
def upload_gis_images(request):
    if request.method == 'POST':
        target_id = request.POST.get('id')
        target_type = request.POST.get('type') # 'store' hoặc 'warehouse'
        files = request.FILES.getlist('images')
        
        if not target_id or not target_type:
            return JsonResponse({'success': False, 'message': 'Thiếu ID hoặc Type'}, status=400)
            
        instance = None
        upload_path = 'store/' if target_type == 'store' else 'warehouse/'
        
        if target_type == 'store':
            instance = get_object_or_404(CuaHang, MaCH=target_id)
        else:
            instance = get_object_or_404(Kho, MaKho=target_id)
            
        fs = FileSystemStorage(location=os.path.join('media', upload_path))
        
        if instance.hinhanh is None:
            instance.hinhanh = []
            
        new_paths = list(instance.hinhanh) # Clone array
        
        for f in files:
            filename = fs.save(f.name, f)
            # Lưu đường dẫn tương đối để frontend dễ truy cập
            new_paths.append(f'{upload_path}{filename}')
            
        instance.hinhanh = new_paths
        instance.save()
        
        return JsonResponse({'success': True, 'paths': new_paths})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_gis_image(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        target_id = data.get('id')
        target_type = data.get('type')
        image_path = data.get('path')
        
        if not all([target_id, target_type, image_path]):
            return JsonResponse({'success': False, 'message': 'Thiếu dữ liệu'}, status=400)
            
        if target_type == 'store':
            instance = get_object_or_404(CuaHang, MaCH=target_id)
        else:
            instance = get_object_or_404(Kho, MaKho=target_id)
            
        if instance.hinhanh and image_path in instance.hinhanh:
            new_paths = list(instance.hinhanh)
            new_paths.remove(image_path)
            instance.hinhanh = new_paths
            instance.save()
            return JsonResponse({'success': True})
            
        return JsonResponse({'success': False, 'message': 'Ảnh không tồn tại'}, status=404)
        
    return JsonResponse({'success': False}, status=405)

def custom_404_view(request, custom_path=None):
    return render(request, '404.html', status=404)

@role_required(['Admin'])
def switch_view_role(request):
    """
    Hàm đổi góc nhìn cho Admin (Admin <-> Nhân Viên)
    """
    if request.method == 'POST':
        current_status = request.session.get('is_admin_view', True)
        request.session['is_admin_view'] = not current_status
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# HÀM XÓA ĐÁNH GIÁ
def delete_review(request, pk):
    if 'user_id' not in request.session: return redirect('login')
    
    review = get_object_or_404(DanhGiaCuaHang, id=pk)
    store_id = review.CuaHang.MaCH

    # CHỐT CHẶN BẢO MẬT: Chỉ chủ nhân mới được xóa
    if review.NhanVien.MaNV == request.session['user_id']:
        review.delete()

    return redirect('store_detail', pk=store_id)


# HÀM SỬA ĐÁNH GIÁ
def edit_review(request, pk):
    if 'user_id' not in request.session: return redirect('login')
    
    review = get_object_or_404(DanhGiaCuaHang, id=pk)
    store_id = review.CuaHang.MaCH

    # CHỐT CHẶN BẢO MẬT: Chặn nếu người khác cố tình truy cập link để sửa
    if review.NhanVien.MaNV != request.session['user_id']:
        return redirect('store_detail', pk=store_id)

    if request.method == 'POST':
        form = DanhGiaForm(request.POST, instance=review) # instance=review để load dữ liệu cũ lên
        if form.is_valid():
            form.save()
            return redirect('store_detail', pk=store_id)
    else:
        form = DanhGiaForm(instance=review)

    return render(request, 'MyApp/edit_review.html', {
        'form': form,
        'review': review,
        'store': review.CuaHang,
        'page_title': 'Sửa đánh giá',
        'sidebar_active': 'stores',
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    })