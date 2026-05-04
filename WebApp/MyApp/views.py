from django import forms
from django.utils import timezone
from django.forms import ClearableFileInput
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.conf import settings
import os
import random
from django.core.paginator import Paginator


from django.db.models import Count, Sum, Q, Avg, Avg as models_Avg
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import SanPham, CuaHang, Kho, HangTonKho, NhanVien, KhachHang, YeuCauNhapKho, NhapKhoChiTiet, YeuCauXuatKho, XuatKhoChiTiet, DanhMuc, DanhGiaCuaHang, PhanBoCungCap, GioHang, ChiTietGioHang, DonHang, ChiTietDonHang, YeuCauTraHang
from .forms import (
    YeuCauNhapKhoForm, YeuCauXuatKhoForm,
    CuaHangForm, KhoForm, NhanVienForm,
    SanPhamForm, DanhMucForm, HangTonKhoForm
)

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
        return context

    def dispatch(self, request, *args, **kwargs):
        # 1. Kiểm tra đăng nhập
        if 'user_id' not in request.session:
            return redirect('login')
        
        # 2. Kiểm tra phân quyền (Role)
        user_role = request.session.get('user_role')
        
        # Ngăn chặn hoàn toàn tài khoản Khách hàng truy cập vào các class-based view của trang quản trị
        if user_role == 'Khách Hàng':
            return render(request, '403.html', {'message': 'Tài khoản khách hàng không có quyền truy cập trang quản trị!'}, status=403)
            
        if self.required_roles and user_role not in self.required_roles:
            return render(request, '403.html', {'message': 'Bạn không có quyền truy cập chức năng này!'}, status=403)
            
        return super().dispatch(request, *args, **kwargs)



def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('login')
            user_role = request.session.get('user_role')
            
            # Ngăn chặn hoàn toàn tài khoản Khách hàng truy cập vào các function-based view của trang quản trị
            if user_role == 'Khách Hàng':
                return render(request, '403.html', {'message': 'Tài khoản khách hàng không có quyền thực hiện hành động này!'}, status=403)
                
            if allowed_roles and user_role not in allowed_roles:
                return render(request, '403.html', {'message': 'Bạn không có quyền thực hiện hành động này!'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


from django.shortcuts import render, redirect, get_object_or_404

def _get_cart_context(request):
    """
    Helper để lấy số lượng sản phẩm trong giỏ hàng hiện tại + Thông tin User
    """
    user_id = request.session.get('user_id')
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        request.session['init'] = True # Bắt buộc Django gửi Cookie sessionid về Browser
        session_id = request.session.session_key
    
    cart = None
    user_obj = None
    if user_id:
        # Nếu đã đăng nhập, ưu tiên lấy KhachHang, nếu không có thì lấy NhanVien
        from .models import KhachHang
        if request.session.get('user_role') == 'Khách Hàng':
            user_obj = KhachHang.objects.filter(MaKH=user_id).first()
            if user_obj:
                cart, _ = GioHang.objects.get_or_create(KhachHang=user_obj)
        else:
            user_obj = NhanVien.objects.filter(MaNV=user_id).first()
            if user_obj:
                cart, _ = GioHang.objects.get_or_create(NguoiDung=user_obj)
    
    if not cart:
        # Nếu chưa đăng nhập hoặc không tìm thấy user, dùng SessionID
        cart, _ = GioHang.objects.get_or_create(SessionID=session_id)
    
    count = 0
    if cart:
        count = cart.items.aggregate(total=Sum('SoLuong'))['total'] or 0
        
    return {
        'cart_count': count, 
        'cart_obj': cart,
        'customer_name': user_obj.Ten if user_obj else None,
        'customer_email': user_obj.Email if user_obj else None,
        'user_role': request.session.get('user_role'),
    }

def public_home(request):
    """
    Trang cửa hàng người dùng công khai (Public Storefront).
    Không yêu cầu đăng nhập. Hiển thị bản đồ GIS, danh sách cửa hàng, sản phẩm nổi bật.
    Hỗ trợ tìm kiếm qua GET param ?q=
    """
    total_stores = CuaHang.objects.count()
    stores_qs = CuaHang.objects.filter(TrangThai='Hoạt động').order_by('MaCH')
    
    # Xử lý tìm kiếm
    search_query = request.GET.get('q', '').strip()
    
    # Lấy tất cả sản phẩm đang bán và danh mục để làm Tab lọc
    products = SanPham.objects.filter(TrangThai__iexact='đang bán').select_related('DanhMuc')
    categories = DanhMuc.objects.all()
    
    if search_query:
        products = products.filter(
            Q(Ten__icontains=search_query) | Q(MieuTa__icontains=search_query) | Q(DanhMuc__Ten__icontains=search_query)
        )
        stores_qs = stores_qs.filter(
            Q(Ten__icontains=search_query) | Q(DiaChi__icontains=search_query) | Q(Loai__icontains=search_query)
        )

    context = {
        'total_stores': total_stores,
        'stores_list': stores_qs,
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'page_title': 'Trang Chủ - SMART MART',
        'customer_name': request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None),
        'user_role': request.session.get('user_role'),
        'active_nav': 'home',
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_storefront.html', context)

def public_product_list(request):
    """
    Trang danh sách sản phẩm đầy đủ cho khách hàng.
    Hỗ trợ lọc theo danh mục và tìm kiếm.
    """
    selected_cat = request.GET.get('cat', '')
    search_q = request.GET.get('q', '').strip()
    
    products = SanPham.objects.filter(TrangThai__iexact='đang bán').select_related('DanhMuc')
    categories = DanhMuc.objects.all()
    
    if selected_cat:
        products = products.filter(DanhMuc__MaDM=selected_cat)
        
    if search_q:
        products = products.filter(
            Q(Ten__icontains=search_q) | Q(MieuTa__icontains=search_q)
        )
        
    products_list = products.order_by('Ten')
    paginator = Paginator(products_list, 9)  # 9 sản phẩm mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,  # Thay thế queryset bằng page_obj
        'categories': categories,
        'selected_cat': selected_cat,
        'search_q': search_q,
        'page_title': 'Tất cả sản phẩm - SMART MART',
        'active_nav': 'products',
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_product_list.html', context)

def public_store_list(request):
    """
    Trang danh sách toàn bộ cửa hàng cho khách hàng.
    """
    search_q = request.GET.get('q', '').strip()
    stores = CuaHang.objects.filter(TrangThai='Hoạt động').order_by('MaCH')
    
    if search_q:
        stores = stores.filter(
            Q(Ten__icontains=search_q) | Q(DiaChi__icontains=search_q) | Q(Loai__icontains=search_q)
        )
    
    stores_ordered = stores.order_by('MaCH')
    paginator = Paginator(stores_ordered, 8)  # 8 cửa hàng mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'stores_list': page_obj,  # Thay thế queryset bằng page_obj
        'search_q': search_q,
        'page_title': 'Hệ Thống Cửa Hàng - SMART MART',
        'active_nav': 'stores',
        'customer_name': request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None),
        'customer_email': request.session.get('user_email'),
        'user_role': request.session.get('user_role'),
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_store_list.html', context)

def public_about(request):
    """
    Trang Giới Thiệu (About Us)
    """
    context = {
        'page_title': 'Giới Thiệu - SMART MART',
        'customer_name': request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None),
        'user_role': request.session.get('user_role'),
        'active_nav': 'about',
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_about.html', context)

def public_product_detail(request, pk):
    """
    Trang Chi Tiết Sản Phẩm dành cho Khách Hàng (có thể gửi đánh giá)
    Hỗ trợ: filter theo số sao (?star=1..5) + phân trang (5 review/trang)
    """
    from .models import DanhGia
    from django.core.paginator import Paginator
    product = get_object_or_404(SanPham, pk=pk)
    nguoi_dung_name = request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None)
    
    if request.method == 'POST':
        # Đồng bộ field names với HTML form
        nguoi_dung = request.session.get('user_name') or request.POST.get('name') or 'Khách hàng ẩn danh'
        diem = request.POST.get('rating')  # form HTML dùng name='rating'
        binh_luan = request.POST.get('comment')  # form HTML dùng name='comment'
        
        if diem and binh_luan:
            # Kiểm tra chống spam: Mỗi người dùng chỉ đánh giá 1 lần cho 1 sản phẩm
            exists = DanhGia.objects.filter(SanPham=product, NguoiDung=nguoi_dung).exists()
            if not exists:
                DanhGia.objects.create(
                    SanPham=product,
                    NguoiDung=nguoi_dung,
                    Diem=int(diem),
                    BinhLuan=binh_luan
                )
            return redirect('public_product_detail', pk=pk)
            
    # ── Tất cả review (để tính thống kê) ──
    all_reviews = DanhGia.objects.filter(SanPham=product).order_by('-NgayTao')
    total_reviews = all_reviews.count()
    
    # Tính trung bình sao
    avg_rating = 0
    if total_reviews > 0:
        avg_rating = sum(r.Diem for r in all_reviews) / total_reviews
        avg_rating = round(avg_rating, 1)

    # Thống kê phân bổ theo số sao (cho filter bar)
    rating_dist = {i: all_reviews.filter(Diem=i).count() for i in range(1, 6)}
    rating_percentages = {i: (count / total_reviews * 100 if total_reviews > 0 else 0) for i, count in rating_dist.items()}

    # ── Filter theo số sao (nếu có) ──
    star_filter = request.GET.get('star', '')
    if star_filter and star_filter.isdigit() and 1 <= int(star_filter) <= 5:
        star_filter = int(star_filter)
        filtered_reviews = all_reviews.filter(Diem=star_filter)
    else:
        star_filter = ''
        filtered_reviews = all_reviews

    # ── Phân trang: 5 review / trang ──
    paginator = Paginator(filtered_reviews, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'product': product,
        'reviews': page_obj,           # page object (hỗ trợ .has_next, .paginator, ...)
        'page_obj': page_obj,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'rating_dist': rating_dist,
        'rating_percentages': rating_percentages,
        'star_filter': star_filter,    # số sao đang lọc ('' = tất cả)
        'page_title': f'{product.Ten} - SMART MART',
        'customer_name': request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None),
        'user_role': request.session.get('user_role'),
        'has_reviewed': DanhGia.objects.filter(SanPham=product, NguoiDung=nguoi_dung_name).exists() if nguoi_dung_name else False,
        'active_nav': 'products',
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_product_detail.html', context)


def public_store_detail(request, pk):
    """
    Trang chi tiết cửa hàng công khai cho người dùng.
    Hiển thị thông tin cửa hàng và vị trí trên bản đồ nhỏ.
    Cho phép đánh giá và bình luận.
    """
    store = get_object_or_404(CuaHang, MaCH=pk)
    user_session_name_check = request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None)
    
    if request.method == 'POST':
        user_session_name = request.session.get('user_name')
        if not user_session_name and request.user.is_authenticated:
            user_session_name = request.user.username
            
        user_name = user_session_name or request.POST.get('name') or "Khách ẩn danh"
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')
        
        if comment:
            # Kiểm tra chống spam: 1 người dùng - 1 cửa hàng - 1 đánh giá
            exists = DanhGiaCuaHang.objects.filter(CuaHang=store, NguoiDung=user_name).exists()
            if not exists:
                DanhGiaCuaHang.objects.create(
                    CuaHang=store,
                    NguoiDung=user_name,
                    Diem=int(rating),
                    BinhLuan=comment
                )
            return redirect('public_store_detail', pk=pk)

    all_reviews = store.danh_gias.all().order_by('-NgayTao')
    avg_rating = all_reviews.aggregate(Avg('Diem'))['Diem__avg'] or 0
    total_reviews = all_reviews.count()
    
    # Phân phối đánh giá (Rating distribution)
    rating_dist = {i: all_reviews.filter(Diem=i).count() for i in range(1, 6)}
    rating_percentages = {i: (count / total_reviews * 100 if total_reviews > 0 else 0) for i, count in rating_dist.items()}

    # Filter theo số sao
    star_filter = request.GET.get('star', '')
    if star_filter and star_filter.isdigit() and 1 <= int(star_filter) <= 5:
        star_filter = int(star_filter)
        filtered_reviews = all_reviews.filter(Diem=star_filter)
    else:
        star_filter = ''
        filtered_reviews = all_reviews

    # Phân trang: 5 review / trang
    from django.core.paginator import Paginator
    paginator = Paginator(filtered_reviews, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Lấy danh sách sản phẩm tại cửa hàng (thông qua Kho cung cấp)
    warehouse_ids = PhanBoCungCap.objects.filter(cua_hang=store).values_list('kho', flat=True)
    product_ids = HangTonKho.objects.filter(MaKho__in=warehouse_ids).values_list('MaSP', flat=True).distinct()
    store_products = SanPham.objects.filter(MaSP__in=product_ids, TrangThai='Đang bán')[:8]
    
    # Tính trạng thái mở/đóng cửa dựa trên giờ thực tế
    from datetime import datetime
    now_time = datetime.now().time()
    is_open = False
    if store.GioMoCua and store.GioDongCua:
        is_open = store.GioMoCua <= now_time <= store.GioDongCua
    elif store.TrangThai == 'Hoạt động':
        is_open = True  # Mặc định mở nếu cửa hàng đang hoạt động và không khai báo giờ
    
    context = {
        'store': store,
        'reviews': page_obj,
        'page_obj': page_obj,
        'rating_dist': rating_dist,
        'rating_percentages': rating_percentages,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'star_filter': star_filter,
        'store_products': store_products,
        'is_open': is_open,
        'page_title': f'{store.Ten} - SMART MART',
        'customer_name': request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None),
        'user_role': request.session.get('user_role'),
        'has_reviewed': store.danh_gias.filter(NguoiDung=user_session_name_check).exists() if user_session_name_check else False,
        'active_nav': 'stores',
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_store_detail.html', context)

def public_kho_detail(request, pk):
    """
    Trang chi tiết kho hàng công khai cho người dùng.
    """
    wh = get_object_or_404(Kho, MaKho=pk)
    
    # Lấy danh sách sản phẩm đang có tại kho này
    inventory = HangTonKho.objects.filter(MaKho=wh).select_related('MaSP')
    # Lọc các sản phẩm 'Đang bán'
    inventory = [item for item in inventory if item.MaSP.TrangThai == 'Đang bán']
    
    context = {
        'wh': wh,
        'inventory': inventory,
        'page_title': f'{wh.Ten} - SMART MART',
        'customer_name': request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None),
        'user_role': request.session.get('user_role'),
        'active_nav': 'warehouses',
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_kho_detail.html', context)

def public_login(request, next_url=None):
    """
    [DEPRECATED] Chuyển hướng về trang login thống nhất.
    Giữ lại để các link cũ không bị đứt.
    """
    # Nếu đã đăng nhập rồi thì redirect luôn
    if request.session.get('user_id'):
        role = request.session.get('user_role', '')
        if role in ['Admin', 'Nhân Viên', 'Kế Toán']:
            return redirect('home')
        return redirect('public_home')
    # Chưa đăng nhập → về trang login thống nhất
    next_param = request.GET.get('next', next_url or '')
    if next_param:
        return redirect(f"{{% url 'login' %}}?next={next_param}")
    return redirect('login')

def public_register(request):
    """
    Đăng ký tài khoản mặc định role là User
    """
    error = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        from .models import KhachHang
        import re
        
        if KhachHang.objects.filter(Email=email).exists():
            error = "Email này đã tồn tại trên hệ thống!"
        elif phone and not re.match(r'^0\d{9,10}$', phone.strip()):
            error = "Số điện thoại không hợp lệ (phải bắt đầu bằng 0, 10-11 chữ số)."
        else:
            # Tạo mã định danh MaKH cho người dùng mới
            makh = f"KH{random.randint(10000, 99999)}"
            while KhachHang.objects.filter(MaKH=makh).exists():
                makh = f"KH{random.randint(10000, 99999)}"
            
            KhachHang.objects.create(
                MaKH=makh,
                Ten=name,
                Email=email,
                SDT=phone,
                MatKhau=password
            )
            return redirect('public_login')
            
    return render(request, 'MyApp/public_register.html', {'error': error, 'page_title': 'Đăng Ký - SMART MART'})

def public_logout(request):
    """
    Đăng xuất thống nhất – dùng chung logic với logout_view.
    """
    request.session.flush()
    return redirect('login')

def view_cart(request):
    """
    Trang chi tiết giỏ hàng
    """
    if not request.session.get('user_id') and not request.user.is_authenticated:
        from django.contrib import messages
        messages.warning(request, 'Vui lòng Đăng nhập để sử dụng tính năng Giỏ hàng.')
        return redirect('public_login')
        
    cart_context = _get_cart_context(request)
    cart = cart_context['cart_obj']
    items = list(cart.items.all().select_related('SanPham')) if cart else []
    
    total_price = 0
    for item in items:
        item.total_price = item.SanPham.Gia * item.SoLuong
        total_price += item.total_price
        
    context = {
        'items': items,
        'total_price': total_price,
        'page_title': 'Giỏ hàng của bạn - SMART MART',
        'customer_name': request.session.get('user_name'),
        'user_role': request.session.get('user_role'),
        'active_nav': 'cart',
    }
    context.update(cart_context)
    return render(request, 'MyApp/public_cart.html', context)

@csrf_exempt
def ajax_add_to_cart(request, pk):
    """
    API thêm sản phẩm vào giỏ hàng (AJAX)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
        
    if not request.session.get('user_id') and not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng.', 'require_login': True})
        
    product = get_object_or_404(SanPham, pk=pk)
    cart_data = _get_cart_context(request)
    cart = cart_data['cart_obj']
    
    item, created = ChiTietGioHang.objects.get_or_create(GioHang=cart, SanPham=product)
    if not created:
        item.SoLuong += 1
        item.save()
        
    # Tính lại tổng số lượng
    new_count = cart.items.aggregate(total=Sum('SoLuong'))['total'] or 0
    
    return JsonResponse({
        'success': True, 
        'message': f'Đã thêm {product.Ten} vào giỏ hàng!',
        'cart_count': new_count
    })

@csrf_exempt
def ajax_update_cart(request):
    """
    API cập nhật số lượng (tăng/giảm/xóa)
    """
    import json
    data = json.loads(request.body)
    item_id = data.get('item_id')
    action = data.get('action') # 'plus', 'minus', 'remove'
    
    item = get_object_or_404(ChiTietGioHang, id=item_id)
    
    if action == 'plus':
        item.SoLuong += 1
        item.save()
    elif action == 'minus':
        if item.SoLuong > 1:
            item.SoLuong -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()
        
    cart_data = _get_cart_context(request)
    return JsonResponse({
        'success': True,
        'cart_count': cart_data['cart_count']
    })

def public_checkout(request):
    """
    Trang thanh toán - Nhập thông tin nhận hàng
    """
    if not request.session.get('user_id') and not request.user.is_authenticated:
        from django.contrib import messages
        messages.warning(request, 'Vui lòng Đăng nhập để Thanh toán.')
        return redirect('public_login')

    cart_context = _get_cart_context(request)
    cart = cart_context['cart_obj']
    
    if not cart or cart.items.count() == 0:
        return redirect('view_cart')
        
    items = cart.items.all().select_related('SanPham')
    total_price = sum(item.SanPham.Gia * item.SoLuong for item in items)
    
    # Nếu đã đăng nhập, lấy thông tin mặc định
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    user = None
    if user_id:
        from .models import KhachHang
        if user_role == 'Khách Hàng':
            user = KhachHang.objects.filter(MaKH=user_id).first()
        else:
            user = NhanVien.objects.filter(MaNV=user_id).first()
    
    context = {
        'items': items,
        'total_price': total_price,
        'user': user,
        'page_title': 'Thanh Toán - SMART MART',
        'customer_name': request.session.get('user_name'),
        'user_role': request.session.get('user_role'),
        'active_nav': 'cart',
    }
    context.update(cart_context)
    return render(request, 'MyApp/public_checkout.html', context)

@csrf_exempt
def create_order(request):
    """
    Xử lý tạo đơn hàng thực tế
    """
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
        
    import json
    data = json.loads(request.body)
    
    ten = data.get('name')
    sdt = data.get('phone')
    diachi = data.get('address')
    ghichu = data.get('note', '')
    pt_thanhtoan = data.get('payment_method', 'COD')
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not all([ten, sdt, diachi]):
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin nhận hàng.'})
        
    if not lat or not lng:
        return JsonResponse({'success': False, 'message': 'Hệ thống cần tọa độ để tìm Kho hàng gần nhất.'})
        
    cart_data = _get_cart_context(request)
    cart = cart_data['cart_obj']
    items = cart.items.all()
    
    if items.count() == 0:
        return JsonResponse({'success': False, 'message': 'Giỏ hàng đang trống.'})
        
    # --- LOGIC GIS TÌM KHO VÀ TRỪ TỒN KHO ---
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance
    from .models import Kho, HangTonKho, KhachHang, NhanVien, DonHang, ChiTietDonHang
    import random
    from django.db import transaction
    
    user_location = Point(float(lng), float(lat), srid=4326)
    
    # Tìm các kho có đủ số lượng cho TẤT CẢ sản phẩm trong giỏ
    available_khos = Kho.objects.all()
    for item in items:
        # Lọc ra những kho có đủ hàng cho item này
        khos_with_item = HangTonKho.objects.filter(
            MaSP=item.SanPham,
            SoLuong__gte=item.SoLuong
        ).values_list('MaKho', flat=True)
        available_khos = available_khos.filter(MaKho__in=khos_with_item)
        
    if not available_khos.exists():
        return JsonResponse({'success': False, 'message': 'Không có Cửa hàng/Kho nào đủ hàng cho tất cả sản phẩm trong giỏ. Vui lòng giảm số lượng!'})
        
    # Lấy Kho gần nhất
    nearest_kho = available_khos.annotate(distance=Distance('geom', user_location)).order_by('distance').first()
    
    # Tính tổng tiền
    total = sum(i.SanPham.Gia * i.SoLuong for i in items)
    
    # Tạo mã đơn hàng ngẫu nhiên
    madh = f"DH{random.randint(100000, 999999)}"
    while DonHang.objects.filter(MaDH=madh).exists():
        madh = f"DH{random.randint(100000, 999999)}"
        
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    
    khachhang = None
    nhanvien = None
    if user_id:
        if user_role == 'Khách Hàng':
            khachhang = KhachHang.objects.filter(MaKH=user_id).first()
        else:
            nhanvien = NhanVien.objects.filter(MaNV=user_id).first()
    
    # Ghi chú thêm Kho xuất hàng
    ghichu_final = f"{ghichu} | Xuất từ: {nearest_kho.Ten}" if ghichu else f"Xuất từ: {nearest_kho.Ten}"
    
    try:
        with transaction.atomic():
            # 1. Tạo đơn hàng
            order = DonHang.objects.create(
                MaDH=madh,
                NguoiDung=nhanvien,
                KhachHang=khachhang,
                TenNguoiNhan=ten,
                SDT_Nhan=sdt,
                DiaChi_Nhan=diachi,
                TongTien=total,
                GhiChu=ghichu_final,
                PhuongThucThanhToan=pt_thanhtoan,
                TrangThai='Đang xử lý'
            )
            
            # 2. Tạo chi tiết đơn hàng & Trừ Tồn Kho
            for item in items:
                ChiTietDonHang.objects.create(
                    DonHang=order,
                    SanPham=item.SanPham,
                    SoLuong=item.SoLuong,
                    GiaBan=item.SanPham.Gia
                )
                
                # Trừ tồn kho
                htk = HangTonKho.objects.get(MaKho=nearest_kho, MaSP=item.SanPham)
                htk.SoLuong -= item.SoLuong
                htk.save()
                
            # 3. Xóa giỏ hàng
            items.delete()
            
            return JsonResponse({
                'success': True, 
                'message': 'Đặt hàng thành công!',
                'order_id': madh
            })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'})

def home(request):
    """
    dashboard chính - Sử dụng ORM để lấy dữ liệu thống kê
    """
    if 'user_id' not in request.session:
        return redirect('login')
        
    if request.session.get('user_role') not in ['Admin', 'Nhân Viên', 'Kế Toán']:
        return render(request, '403.html', {'message': 'Tài khoản khách hàng không có quyền truy cập trang quản trị!'}, status=403)

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
    
    # --- CÁC THỐNG KÊ CŨ ---
    # 1. Thống kê sản phẩm theo danh mục
    category_stats = DanhMuc.objects.annotate(total_products=Count('sanpham')).values('Ten', 'total_products')
    
    # 2. Thống kê tồn kho theo kho hàng
    inventory_stats = HangTonKho.objects.values('MaKho__Ten').annotate(total_qty=Sum('SoLuong')).order_by('-total_qty')
    
    # 3. Thống kê trạng thái cửa hàng
    store_status = CuaHang.objects.values('TrangThai').annotate(count=Count('MaCH'))
    
    # 4. Thống kê nhân viên theo vai trò
    employee_roles = NhanVien.objects.values('Role').annotate(count=Count('MaNV'))

    # --- THỐNG KÊ ĐỊA LÝ MỚI ---
    # 5. Tổng số cửa hàng và kho
    total_stores = CuaHang.objects.count()
    total_warehouses = Kho.objects.count()
    
    # 6. Thống kê cửa hàng theo loại
    stores_by_type = CuaHang.objects.values('Loai').annotate(count=Count('MaCH'))
    
    # 7. Thống kê kho theo loại
    warehouses_by_type = Kho.objects.values('Loai').annotate(count=Count('MaKho'))
    
    # 8. Tìm các cặp tọa độ gần nhau (để cảnh báo) - kiểm tra 2m
    min_dist = 0.00002
    nearby_pairs = []
    
    # Kiểm tra giữa các cửa hàng
    stores = list(CuaHang.objects.all())
    for i in range(len(stores)):
        for j in range(i+1, len(stores)):
            if stores[i].geom and stores[j].geom and stores[i].geom.distance(stores[j].geom) < min_dist:
                nearby_pairs.append({
                    'type': 'Cửa hàng - Cửa hàng',
                    'name1': stores[i].Ten,
                    'name2': stores[j].Ten,
                    'distance': round(stores[i].geom.distance(stores[j].geom) * 111000, 2)
                })
    
    # Kiểm tra giữa các kho
    warehouses = list(Kho.objects.all())
    for i in range(len(warehouses)):
        for j in range(i+1, len(warehouses)):
            if warehouses[i].geom and warehouses[j].geom and warehouses[i].geom.distance(warehouses[j].geom) < min_dist:
                nearby_pairs.append({
                    'type': 'Kho - Kho',
                    'name1': warehouses[i].Ten,
                    'name2': warehouses[j].Ten,
                    'distance': round(warehouses[i].geom.distance(warehouses[j].geom) * 111000, 2)
                })
    
    # Kiểm tra giữa cửa hàng và kho
    for store in stores:
        for wh in warehouses:
            if store.geom and wh.geom and store.geom.distance(wh.geom) < min_dist:
                nearby_pairs.append({
                    'type': 'Cửa hàng - Kho',
                    'name1': store.Ten,
                    'name2': wh.Ten,
                    'distance': round(store.geom.distance(wh.geom) * 111000, 2)
                })

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
    stores_type_json = {
        'labels': [item['Loai'] for item in stores_by_type],
        'values': [int(item['count']) for item in stores_by_type]
    }
    warehouses_type_json = {
        'labels': [item['Loai'] for item in warehouses_by_type],
        'values': [int(item['count']) for item in warehouses_by_type]
    }

    context = {
        'sidebar_active': 'reports',
        'page_title': 'Báo cáo Thống kê',
        'cat_json': json.dumps(cat_json),
        'inv_json': json.dumps(inv_json),
        'st_json': json.dumps(st_json),
        'em_json': json.dumps(em_json),
        'stores_type_json': json.dumps(stores_type_json),
        'warehouses_type_json': json.dumps(warehouses_type_json),
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', ''),
        'total_stores': total_stores,
        'total_warehouses': total_warehouses,
        'stores_by_type': stores_by_type,
        'warehouses_by_type': warehouses_by_type,
        'nearby_pairs': nearby_pairs
    }
    return render(request, 'MyApp/reports.html', context)

def login_view(request):
    """
    LOGIN THỐNG NHẤT – Dùng chung cho Nhân viên & Khách hàng.
    Nhận: SDT hoặc Email + Mật khẩu.
    Redirect: Admin/NV/KeToan → /dashboard/ | Khách Hàng → trang chủ storefront.
    """
    # Nếu đã đăng nhập rồi thì redirect luôn
    if request.session.get('user_id'):
        role = request.session.get('user_role', '')
        if role in ['Admin', 'Nhân Viên', 'Kế Toán']:
            return redirect('home')
        return redirect('public_home')

    error = None
    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()   # SDT hoặc Email
        matkhau  = request.POST.get('matkhau', '').strip()
        next_url = request.POST.get('next', '')

        from .models import KhachHang, GioHang

        # ── 1. Kiểm tra Nhân viên (SDT hoặc Email) ──────────────────
        nv = NhanVien.objects.filter(
            Q(SDT=login_id) | Q(Email__iexact=login_id)
        ).first()

        if nv and nv.MatKhau == matkhau:
            request.session['user_id']   = nv.MaNV
            request.session['user_name'] = nv.Ten
            request.session['user_role'] = nv.Role
            # Nhân viên/Admin → trang quản trị
            if nv.Role in ['Admin', 'Nhân Viên', 'Kế Toán']:
                return redirect(next_url or 'home')
            # NV có role khác (ví dụ Khách Hàng được lưu trong NhanVien) → storefront
            return redirect(next_url or 'public_home')

        # ── 2. Kiểm tra Khách hàng (Email hoặc SDT) ─────────────────
        kh = KhachHang.objects.filter(
            Q(Email__iexact=login_id) | Q(SDT=login_id)
        ).first()

        if kh and kh.MatKhau == matkhau:
            request.session['user_id']   = kh.MaKH
            request.session['user_name'] = kh.Ten
            request.session['user_role'] = 'Khách Hàng'

            # Gộp giỏ hàng session → tài khoản
            session_key = request.session.session_key
            if session_key:
                session_cart = GioHang.objects.filter(SessionID=session_key).first()
                user_cart, _ = GioHang.objects.get_or_create(KhachHang=kh)
                if session_cart and session_cart != user_cart:
                    for item in session_cart.items.all():
                        existing = user_cart.items.filter(SanPham=item.SanPham).first()
                        if existing:
                            existing.SoLuong += item.SoLuong
                            existing.save()
                        else:
                            item.GioHang = user_cart
                            item.save()
                    session_cart.delete()

            return redirect(next_url or 'public_home')

        # ── 3. Sai thông tin ────────────────────────────────────────
        error = "Số điện thoại / Email hoặc mật khẩu không chính xác!"

    next_url = request.GET.get('next', '')
    return render(request, 'MyApp/login.html', {
        'error': error,
        'next': next_url,
        'page_title': 'Đăng nhập – SMART MART',
    })

def logout_view(request):
    """
    ĐĂNG XUẤT THỐNG NHẤT – Xóa session, redirect về trang login chung.
    """
    request.session.flush()
    messages.success(request, "Đã đăng xuất thành công!")
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
            user = None
            user_type = None
            
            # 1. Tìm trong KhachHang trước
            from .models import KhachHang
            kh = KhachHang.objects.filter(SDT=sdt).first()
            if kh:
                user = kh
                user_type = 'khachhang'
            else:
                # 2. Tìm trong NhanVien
                nv = NhanVien.objects.filter(SDT=sdt).first()
                if nv:
                    user = nv
                    user_type = 'nhanvien'
                    
            if not user:
                error = "Số điện thoại không tồn tại trong hệ thống."
            else:
                # Kiểm tra Email nhập vào có khớp với Database không
                db_email = getattr(user, 'Email', None)
                if not db_email or db_email.lower() != email_input.lower():
                    error = "Email không khớp với thông tin đã đăng ký cho số điện thoại này."
                else:
                    # Tạo mã OTP 6 số ngẫu nhiên
                    otp = str(random.randint(100000, 999999))
                    
                    # Lưu OTP và user ID vào Session
                    request.session['reset_otp'] = otp
                    request.session['reset_user_type'] = user_type
                    if user_type == 'nhanvien':
                        request.session['reset_user_id'] = user.MaNV
                    else:
                        request.session['reset_user_id'] = user.MaKH
                        
                    request.session.set_expiry(600)
                    
                    # Gửi mã OTP
                    send_mail(
                        'Mã xác thực đặt lại mật khẩu - SMART MART',
                        f'Chào {user.Ten},\n\nMã xác thực (OTP) của bạn là: {otp}\n\nMã này có hiệu lực trong 10 phút.',
                        getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@smartmart.com'),
                        [db_email],
                        fail_silently=False,
                    )
                    return redirect('verify_otp')
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
        
    user_type = request.session.get('reset_user_type')
    user_id = request.session.get('reset_user_id')
    user = None
    
    if user_type == 'nhanvien':
        user = get_object_or_404(NhanVien, MaNV=user_id)
    elif user_type == 'khachhang':
        from .models import KhachHang
        user = get_object_or_404(KhachHang, MaKH=user_id)
    else:
        return redirect('forgot_password')
        
    error = None
    
    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        
        if new_pass != confirm_pass:
            error = "Mật khẩu xác nhận không khớp."
        else:
            # Cập nhật thành công
            user.MatKhau = new_pass
            user.save()
            # Xóa session reset
            if 'reset_otp' in request.session: del request.session['reset_otp']
            if 'reset_user_id' in request.session: del request.session['reset_user_id']
            if 'reset_user_type' in request.session: del request.session['reset_user_type']
            if 'otp_verified' in request.session: del request.session['otp_verified']
            return render(request, 'MyApp/reset_password.html', {'success': 'Mật khẩu đã được đổi thành công.', 'is_customer': user_type == 'khachhang'})

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

            if user.MatKhau != old_pass:
                error_msg = "Mật khẩu hiện tại không chính xác!"
            elif len(new_pass) < 6:
                error_msg = "Mật khẩu mới phải có ít nhất 6 ký tự!"
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
    Trang bản đồ GIS chuyên dụng (Full screen) - Dành cho nhân viên
    """
    if 'user_id' not in request.session:
        return redirect('login')
        
    if request.session.get('user_role') == 'Khách Hàng':
        return redirect('public_gis_map')

    context = {
        'sidebar_active': 'gis_map',
        'page_title': 'Bản đồ GIS Chuyên sâu',
        'user_name': request.session.get('user_name', 'Khách'),
        'user_role': request.session.get('user_role', '')
    }
    return render(request, 'MyApp/gis_map.html', context)

def public_gis_map(request):
    """
    Trang bản đồ GIS công khai cho người dùng và khách hàng
    """
    customer_name = request.session.get('user_name') or (request.user.username if request.user.is_authenticated else None)
    customer_email = request.session.get('user_email')
    if not customer_email and request.user.is_authenticated:
        customer_email = request.user.email

    context = {
        'page_title': 'Bản đồ SMART MART - Công nghệ GIS',
        'active_nav': 'map',
        'customer_name': customer_name,
        'customer_email': customer_email,
        'user_role': request.session.get('user_role'),
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_gis_map.html', context)




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
    form_class = CuaHangForm
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
    form_class = CuaHangForm
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
    return render(request, 'MyApp/store_detail.html', {
        'store': store,
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
    required_roles = ['Admin']

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
    form_class = SanPhamForm  # Dùng form có validation đầy đủ
    template_name = 'MyApp/product_form.html'
    success_url = reverse_lazy('product_list')
    sidebar_active = 'products'

class SanPhamUpdateView(SidebarContextMixin, UpdateView):
    model = SanPham
    form_class = SanPhamForm  # MaSP sẽ bị disabled khi edit
    template_name = 'MyApp/product_form.html'
    success_url = reverse_lazy('product_list')
    sidebar_active = 'products'

class SanPhamDeleteView(SidebarContextMixin, DeleteView):
    model = SanPham
    success_url = reverse_lazy('product_list')
    required_roles = ['Admin']

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
    form_class = DanhMucForm  # Dùng form có validation đầy đủ
    template_name = 'MyApp/danhmuc_form.html'
    success_url = reverse_lazy('danhmuc_list')
    sidebar_active = 'categories'
    page_title = 'Thêm Danh mục mới'

class DanhMucUpdateView(SidebarContextMixin, UpdateView):
    model = DanhMuc
    form_class = DanhMucForm  # MaDM sẽ bị disabled khi edit
    template_name = 'MyApp/danhmuc_form.html'
    success_url = reverse_lazy('danhmuc_list')
    sidebar_active = 'categories'
    page_title = 'Cập nhật Danh mục'

class DanhMucDeleteView(SidebarContextMixin, DeleteView):
    model = DanhMuc
    success_url = reverse_lazy('danhmuc_list')
    required_roles = ['Admin']

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
    form_class = HangTonKhoForm  # Dùng form có validation: không trùng, không âm
    template_name = 'MyApp/inventory_form.html'
    success_url = reverse_lazy('inventory_list')
    sidebar_active = 'inventory'
    page_title = 'Thêm mới Tồn kho'

class HangTonKhoUpdateView(SidebarContextMixin, UpdateView):
    model = HangTonKho
    form_class = HangTonKhoForm  # Dùng form có validation: SoLuong không âm
    template_name = 'MyApp/inventory_form.html'
    success_url = reverse_lazy('inventory_list')
    sidebar_active = 'inventory'
    page_title = 'Điều chỉnh Tồn kho'

    def get_object(self, queryset=None):
        return get_object_or_404(HangTonKho, MaKho=self.kwargs['makho'], MaSP=self.kwargs['masp'])

class HangTonKhoDeleteView(SidebarContextMixin, DeleteView):
    model = HangTonKho
    success_url = reverse_lazy('inventory_list')
    required_roles = ['Admin', 'Kế Toán']

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
    form_class = KhoForm
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
    form_class = KhoForm
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
    required_roles = ['Admin']

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
    form_class = NhanVienForm
    template_name = 'MyApp/nhanvien_form.html'
    success_url = reverse_lazy('nhanvien_list')
    sidebar_active = 'employees'
    required_roles = ['Admin']

class NhanVienUpdateView(SidebarContextMixin, UpdateView):
    model = NhanVien
    form_class = NhanVienForm
    template_name = 'MyApp/nhanvien_form.html'
    success_url = reverse_lazy('nhanvien_list')
    sidebar_active = 'employees'
    required_roles = ['Admin']

class NhanVienDeleteView(SidebarContextMixin, DeleteView):
    model = NhanVien
    success_url = reverse_lazy('nhanvien_list')
    required_roles = ['Admin']


# --- Export Excel ---
def export_nhapkho_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Border, Side, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from datetime import datetime
    from django.http import HttpResponse
    import time

    # Start time logging
    start_time = time.time()

    # Get all YeuCauNhapKho and their items
    nhapkho_list = YeuCauNhapKho.objects.all().order_by('Ngay')
    
    if not nhapkho_list.exists():
        messages.warning(request, "Không có dữ liệu để xuất Excel!")
        return redirect('stock_in_list')
    
    # Create a workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Phiếu nhập kho"

    # Setup styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")  # Blue for stock in
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

    # Write header row
    headers = [
        "STT",
        "Mã phiếu",
        "Ngày nhập",
        "Nhà cung cấp",
        "Danh sách sản phẩm",
        "Tổng số lượng",
        "Tổng thành tiền",
        "Trạng thái"
    ]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center_alignment

    # Step 1: Group items by MaYC (Mã yêu cầu nhập kho) and log raw count
    grouped_data = {}
    raw_row_count = 0
    
    for yeucau in nhapkho_list:
        chitiet_list = NhapKhoChiTiet.objects.filter(MaYC=yeucau.MaYC)
        items_info = []
        total_soluong = 0
        total_thanhtien = 0
        
        for chitiet in chitiet_list:
            raw_row_count +=1
            sanpham = chitiet.MaSP
            gia = sanpham.Gia
            soluong = chitiet.SoLuong
            thanhtien = soluong * gia
            total_soluong += soluong
            total_thanhtien += thanhtien
            items_info.append({
                "masp": sanpham.MaSP,
                "tensp": sanpham.Ten,
                "soluong": soluong,
                "gia": gia,
                "thanhtien": thanhtien
            })
        
        grouped_data[yeucau.MaYC] = {
            "yeucau": yeucau,
            "items": items_info,
            "total_soluong": total_soluong,
            "total_thanhtien": total_thanhtien
        }

    # Step 2: Write data to Excel
    current_row = 2
    stt = 0

    for mayc, data in grouped_data.items():
        stt +=1
        yeucau = data["yeucau"]
        items = data["items"]
        total_soluong = data["total_soluong"]
        total_thanhtien = data["total_thanhtien"]
        num_items = len(items)
        
        # Get NCC (placeholder)
        ncc = ""
        
        # Build products string
        products_str = ""
        for idx, item in enumerate(items):
            products_str += f"{item['tensp']} ({item['masp']})\n"
            products_str += f"Số lượng: {item['soluong']} - Đơn giá: {item['gia']:,} - Thành tiền: {item['thanhtien']:,}"
            if idx < num_items - 1:
                products_str += "\n\n"
        
        # Determine number of rows needed
        merge_end_row = current_row + num_items -1
        
        # Write STT
        cell = ws.cell(row=current_row, column=1, value=stt)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items > 1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=1, end_column=1)
        
        # Write Mã phiếu
        cell = ws.cell(row=current_row, column=2, value=mayc)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=2, end_column=2)
        
        # Write Ngày nhập
        cell = ws.cell(row=current_row, column=3, value=yeucau.Ngay.strftime('%d/%m/%Y'))
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=3, end_column=3)
        
        # Write Nhà cung cấp
        cell = ws.cell(row=current_row, column=4, value=ncc)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=4, end_column=4)
        
        # Write Danh sách sản phẩm
        cell = ws.cell(row=current_row, column=5, value=products_str)
        cell.border = thin_border
        cell.alignment = left_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=5, end_column=5)
        
        # Write Tổng số lượng
        cell = ws.cell(row=current_row, column=6, value=total_soluong)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=6, end_column=6)
        
        # Write Tổng thành tiền
        cell = ws.cell(row=current_row, column=7, value=total_thanhtien)
        cell.border = thin_border
        cell.alignment = center_alignment
        cell.number_format = '#,##0'
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=7, end_column=7)
        
        # Write Trạng thái
        cell = ws.cell(row=current_row, column=8, value=yeucau.TrangThai)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=8, end_column=8)
        
        # Set row heights
        for row in range(current_row, merge_end_row + 1):
            ws.row_dimensions[row].height = 20
        
        current_row = merge_end_row + 1

    # Auto adjust column widths
    ws.column_dimensions[get_column_letter(1)].width = 8  # STT
    ws.column_dimensions[get_column_letter(2)].width = 15 # Mã phiếu
    ws.column_dimensions[get_column_letter(3)].width = 15 # Ngày
    ws.column_dimensions[get_column_letter(4)].width = 20 # NCC
    ws.column_dimensions[get_column_letter(5)].width = 60 # Sản phẩm
    ws.column_dimensions[get_column_letter(6)].width = 18 # Tổng SL
    ws.column_dimensions[get_column_letter(7)].width = 20 # Tổng tiền
    ws.column_dimensions[get_column_letter(8)].width = 15 # Trạng thái

    # End time logging
    end_time = time.time()
    export_duration = round(end_time - start_time, 2)
    merged_row_count = len(grouped_data)
    print(f"[EXPORT NHAP KHO] Raw rows: {raw_row_count}, Merged rows: {merged_row_count}, Duration: {export_duration}s")

    # Create response
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PhieuNhapKho_{timestamp}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


# --- Export Stock Out ---
def export_stockout_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Border, Side, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from datetime import datetime
    from django.http import HttpResponse
    import time

    # Start time logging
    start_time = time.time()

    # Get all YeuCauXuatKho and their items
    stockout_list = YeuCauXuatKho.objects.all().order_by('Ngay')
    
    if not stockout_list.exists():
        messages.warning(request, "Không có dữ liệu để xuất Excel!")
        return redirect('stock_out_list')
    
    # Create a workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Phiếu xuất kho"

    # Setup styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="EF4444", end_color="EF4444", fill_type="solid")  # Red for stock out (without #)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    top_alignment = Alignment(horizontal='center', vertical='top')
    left_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

    # Write header row
    headers = [
        "STT",
        "Mã phiếu",
        "Ngày xuất",
        "Lý do xuất",
        "Khách hàng (nếu có)",
        "Danh sách sản phẩm",
        "Trạng thái"
    ]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center_alignment

    # Step 1: Group items by MaPX (Mã yêu cầu xuất kho) and log raw count
    grouped_data = {}
    raw_row_count = 0
    
    for phieuxuat in stockout_list:
        chitiet_list = XuatKhoChiTiet.objects.filter(PhieuXuat=phieuxuat.MaPX)
        items_info = []
        
        for chitiet in chitiet_list:
            raw_row_count +=1
            sanpham = chitiet.MaSP
            gia = sanpham.Gia
            soluong = chitiet.SoLuong
            thanhtien = soluong * gia
            items_info.append({
                "masp": sanpham.MaSP,
                "tensp": sanpham.Ten,
                "soluong": soluong,
                "gia": gia,
                "thanhtien": thanhtien
            })
        
        grouped_data[phieuxuat.MaPX] = {
            "phieuxuat": phieuxuat,
            "items": items_info
        }

    # Step 2: Write data to Excel
    current_row = 2
    stt = 0

    for mapx, data in grouped_data.items():
        stt +=1
        phieuxuat = data["phieuxuat"]
        items = data["items"]
        num_items = len(items)
        
        # Get customer name
        khach_hang = ""
        if phieuxuat.DonHang and phieuxuat.DonHang.TenNguoiNhan:
            khach_hang = phieuxuat.DonHang.TenNguoiNhan
        
        # Build products string
        products_str = ""
        for idx, item in enumerate(items):
            products_str += f"{item['tensp']} ({item['masp']})\n"
            products_str += f"Số lượng: {item['soluong']} - Đơn giá: {item['gia']:,} - Thành tiền: {item['thanhtien']:,}"
            if idx < num_items - 1:
                products_str += "\n\n"
        
        # Determine number of rows needed
        merge_end_row = current_row + num_items -1
        
        # Write STT
        cell = ws.cell(row=current_row, column=1, value=stt)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items > 1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=1, end_column=1)
        
        # Write Mã phiếu
        cell = ws.cell(row=current_row, column=2, value=mapx)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=2, end_column=2)
        
        # Write Ngày xuất
        cell = ws.cell(row=current_row, column=3, value=phieuxuat.Ngay.strftime('%d/%m/%Y'))
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=3, end_column=3)
        
        # Write Lý do xuất
        cell = ws.cell(row=current_row, column=4, value=phieuxuat.LyDo)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=4, end_column=4)
        
        # Write Khách hàng
        cell = ws.cell(row=current_row, column=5, value=khach_hang)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=5, end_column=5)
        
        # Write Danh sách sản phẩm
        cell = ws.cell(row=current_row, column=6, value=products_str)
        cell.border = thin_border
        cell.alignment = left_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=6, end_column=6)
        
        # Write Trạng thái
        cell = ws.cell(row=current_row, column=7, value=phieuxuat.TrangThai)
        cell.border = thin_border
        cell.alignment = center_alignment
        if num_items >1:
            ws.merge_cells(start_row=current_row, end_row=merge_end_row, start_column=7, end_column=7)
        
        # Set row heights (optional, adjust as needed)
        for row in range(current_row, merge_end_row + 1):
            ws.row_dimensions[row].height = 20
        
        current_row = merge_end_row + 1

    # Auto adjust column widths
    ws.column_dimensions[get_column_letter(1)].width = 8  # STT
    ws.column_dimensions[get_column_letter(2)].width = 15 # Mã phiếu
    ws.column_dimensions[get_column_letter(3)].width = 15 # Ngày
    ws.column_dimensions[get_column_letter(4)].width = 20 # Lý do
    ws.column_dimensions[get_column_letter(5)].width = 25 # Khách hàng
    ws.column_dimensions[get_column_letter(6)].width = 60 # Sản phẩm
    ws.column_dimensions[get_column_letter(7)].width = 15 # Trạng thái

    # End time logging
    end_time = time.time()
    export_duration = round(end_time - start_time, 2)
    merged_row_count = len(grouped_data)
    print(f"[EXPORT XUAT KHO] Raw rows: {raw_row_count}, Merged rows: {merged_row_count}, Duration: {export_duration}s")

    # Create response
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PhieuXuatKho_{timestamp}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


# --- API Endpoints ---
@csrf_exempt
def check_coordinates(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        exclude_id = data.get('exclude_id')
        exclude_type = data.get('exclude_type')
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    
    from django.contrib.gis.geos import Point
    point = Point(lng, lat, srid=4326)
    
    # ±0.0001 degrees tolerance (~11 meters)
    min_dist = 0.0001
    nearby = []
    
    # Check warehouses
    kho_query = Kho.objects.filter(geom__dwithin=(point, min_dist))
    if exclude_id and exclude_type == 'kho':
        kho_query = kho_query.exclude(MaKho=exclude_id)
    for k in kho_query:
        nearby.append({
            'type': 'kho',
            'id': k.MaKho,
            'name': k.Ten,
            'address': k.DiaChi,
            'lat': k.geom.y,
            'lng': k.geom.x
        })
    
    # Check stores
    cuahang_query = CuaHang.objects.filter(geom__dwithin=(point, min_dist))
    if exclude_id and exclude_type == 'cuahang':
        cuahang_query = cuahang_query.exclude(MaCH=exclude_id)
    for c in cuahang_query:
        nearby.append({
            'type': 'cuahang',
            'id': c.MaCH,
            'name': c.Ten,
            'address': c.DiaChi,
            'lat': c.geom.y,
            'lng': c.geom.x
        })
    
    return JsonResponse({
        'has_duplicate': len(nearby) > 0,
        'nearby': nearby
    })

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
            # --- VALIDATE: Formset phải có ít nhất 1 dòng sản phẩm hợp lệ ---
            filled_forms = [
                f for f in product_formset
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            ]
            if not filled_forms:
                messages.error(self.request, "Phiếu nhập kho phải có ít nhất 1 sản phẩm. Vui lòng thêm dòng sản phẩm trước khi lưu.")
                return self.render_to_response(self.get_context_data(form=form))

            # --- VALIDATE: SoLuong > 0 từng dòng ---
            invalid_qty = False
            for f in filled_forms:
                sl = f.cleaned_data.get('SoLuong')
                if sl is not None and sl <= 0:
                    messages.error(self.request, "Số lượng mỗi sản phẩm trong phiếu nhập phải lớn hơn 0.")
                    invalid_qty = True
                    break
            if invalid_qty:
                return self.render_to_response(self.get_context_data(form=form))

            # Tự động gán nhân viên đang đăng nhập làm người tạo phiếu
            user_id = self.request.session.get('user_id')
            if user_id:
                from .models import NhanVien
                try:
                    nv = NhanVien.objects.get(MaNV=user_id)
                    form.instance.MaNV = nv
                except NhanVien.DoesNotExist:
                    pass

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

            messages.success(self.request, f"Đã tạo phiếu nhập kho {self.object.MaYC} thành công!")
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

    def dispatch(self, request, *args, **kwargs):
        """Khóa phiếu khi đã ở trạng thái 'Đã duyệt' — không cho sửa nữa."""
        response = super().dispatch(request, *args, **kwargs)
        obj = self.get_object()
        if obj.TrangThai == 'Đã duyệt':
            messages.error(
                request,
                f"Phiếu nhập '{obj.MaYC}' đã ở trạng thái 'Đã duyệt'. Không thể chỉnh sửa!"
            )
            return redirect(self.success_url)
        return response

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
            
            new_status = self.object.TrangThai
            
            # CỘNG tồn kho khi chuyển sang Đã duyệt
            if old_status != 'Đã duyệt' and new_status == 'Đã duyệt':
                from .models import HangTonKho, NhapKhoChiTiet
                items = NhapKhoChiTiet.objects.filter(MaYC=self.object)
                for item in items:
                    inventory, created = HangTonKho.objects.get_or_create(
                        MaKho=item.MaKho, MaSP=item.MaSP, defaults={'SoLuong': 0}
                    )
                    inventory.SoLuong += item.SoLuong
                    inventory.save()
            
            # TRỪ lại tồn kho khi chuyển ngược từ Đã duyệt về Chờ duyệt
            elif old_status == 'Đã duyệt' and new_status != 'Đã duyệt':
                from .models import HangTonKho, NhapKhoChiTiet
                items = NhapKhoChiTiet.objects.filter(MaYC=self.object)
                for item in items:
                    try:
                        inventory = HangTonKho.objects.get(MaKho=item.MaKho, MaSP=item.MaSP)
                        inventory.SoLuong -= item.SoLuong
                        if inventory.SoLuong <= 0:
                            inventory.delete()
                        else:
                            inventory.save()
                    except HangTonKho.DoesNotExist:
                        pass
                    
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

def public_order_invoice(request, order_id):
    """
    Trang in hóa đơn cho Đơn hàng
    """
    order = get_object_or_404(DonHang.objects.prefetch_related('return_requests'), MaDH=order_id)
    
    # Bảo mật: Kiểm tra quyền truy cập
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    
    user_obj = None
    if user_id:
        if user_role == 'Khách Hàng':
            user_obj = KhachHang.objects.filter(MaKH=user_id).first()
        else:
            user_obj = NhanVien.objects.filter(MaNV=user_id).first()

    is_staff = user_role in ['Admin', 'Nhân Viên', 'Kế Toán']
    
    # Check ownership
    is_owner = False
    if user_role == 'Khách Hàng' and order.KhachHang == user_obj:
        is_owner = True
    elif user_role != 'Khách Hàng' and order.NguoiDung == user_obj:
        is_owner = True
        
    if not is_staff and not is_owner:
        return render(request, '403.html', {'message': 'Bạn không có quyền xem hóa đơn này!'}, status=403)

    # Sử dụng related_name='items' từ model ChiTietDonHang
    items = order.items.all().select_related('SanPham')
    
    # Lấy thông tin giỏ hàng và người dùng cho Header
    cart_data = _get_cart_context(request)
    customer_email = user_obj.Email if user_obj else None
    
    context = {
        'order': order,
        'items': items,
        'page_title': f'Hóa Đơn {order.MaDH} - SMART MART',
        'customer_name': user_obj.Ten if user_obj else None,
        'customer_email': customer_email,
        'user_role': user_role,
        'cart_count': cart_data.get('cart_count', 0),
        'active_nav': 'orders',
    }
    return render(request, 'MyApp/public_order_invoice.html', context)

def public_return_request(request, order_id):
    """
    Trang gửi yêu cầu trả hàng chi tiết (Dedicated Return Page)
    """
    if not request.session.get('user_id'):
        return redirect('public_login')
        
    order = get_object_or_404(DonHang.objects.prefetch_related('return_requests'), MaDH=order_id)
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    
    user_obj = None
    if user_id:
        if user_role == 'Khách Hàng':
            user_obj = KhachHang.objects.filter(MaKH=user_id).first()
        else:
            user_obj = NhanVien.objects.filter(MaNV=user_id).first()
    
    # Kiểm tra quyền (chỉ chủ đơn hàng mới được yêu cầu trả)
    is_owner = False
    if user_role == 'Khách Hàng' and order.KhachHang == user_obj:
        is_owner = True
    elif user_role != 'Khách Hàng' and order.NguoiDung == user_obj:
        is_owner = True

    if not is_owner and user_role not in ['Admin', 'Nhân Viên', 'Kế Toán']:
        return render(request, '403.html', status=403)

    # Nếu đã có yêu cầu xử lý rồi thì không cho tạo thêm
    if order.return_requests.exists():
        messages.warning(request, "Đơn hàng này đã có yêu cầu trả hàng đang được xử lý.")
        return redirect('public_order_invoice', order_id=order_id)

    if request.method == 'POST':
        sdt = request.POST.get('sdt')
        email = request.POST.get('email')
        stk_nh = request.POST.get('stk_nh')
        stk_momo = request.POST.get('stk_momo')
        ly_do = request.POST.get('ly_do')
        
        anh_hd = request.FILES.get('anh_hoa_don')
        anh_mc = request.FILES.get('anh_minh_chung')

        import random
        request_id = f"TH{random.randint(100000, 999999)}"
        
        YeuCauTraHang.objects.create(
            MaYCTH=request_id,
            DonHang=order,
            SdtLienHe=sdt,
            EmailLienHe=email,
            SoTaiKhoanNH=stk_nh,
            SoTaiKhoanMoMo=stk_momo,
            LyDo=ly_do,
            AnhHoaDon=anh_hd,
            AnhMinhChung=anh_mc,
            SoTienHoan=order.TongTien,
            TrangThai='Đang xử lý'
        )
        messages.success(request, "Gửi yêu cầu trả hàng thành công. Smart Mart sẽ kiểm tra và phản hồi sớm nhất!")
        return redirect('public_order_history')

    cart_data = _get_cart_context(request)
    context = {
        'order': order,
        'page_title': f'Trả hàng / Hoàn tiền {order.MaDH} - SMART MART',
        'customer_name': user_obj.Ten if user_obj else None,
        'customer_email': user_obj.Email if user_obj else None,
        'customer_phone': user_obj.SDT if user_obj else None,
        'cart_count': cart_data.get('cart_count', 0),
        'user_role': request.session.get('user_role'),
    }
    return render(request, 'MyApp/public_return_request.html', context)

def public_order_history(request):
    """
    Trang danh sách đơn hàng của khách hàng (Lịch sử mua hàng)
    """
    if not request.session.get('user_id') and not request.user.is_authenticated:
        return redirect('public_login')
        
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    user_obj = None
    if user_id:
        if user_role == 'Khách Hàng':
            user_obj = KhachHang.objects.filter(MaKH=user_id).first()
        else:
            user_obj = NhanVien.objects.filter(MaNV=user_id).first()
    
    orders = []
    if user_obj:
        if user_role == 'Khách Hàng':
            orders = DonHang.objects.filter(KhachHang=user_obj).prefetch_related('return_requests').order_by('-NgayTao')
        else:
            orders = DonHang.objects.filter(NguoiDung=user_obj).prefetch_related('return_requests').order_by('-NgayTao')
        
    # Lấy thông tin giỏ hàng cho Header
    cart_data = _get_cart_context(request)
    
    context = {
        'orders': orders,
        'page_title': 'Lịch sử mua hàng - SMART MART',
        'customer_name': user_obj.Ten if user_obj else None,
        'customer_email': user_obj.Email if user_obj else None,
        'user_role': request.session.get('user_role'),
        'cart_count': cart_data.get('cart_count', 0),
    }
    return render(request, 'MyApp/public_order_history.html', context)

def public_profile(request):
    """
    Trang cá nhân của khách hàng (Storefront Profile)
    """
    if not request.session.get('user_id'):
        return redirect('public_login')
        
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if user_role == 'Khách Hàng':
        user = get_object_or_404(KhachHang, MaKH=user_id)
    else:
        user = get_object_or_404(NhanVien, MaNV=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_info':
            user.Ten = request.POST.get('ten')
            user.Email = request.POST.get('email')
            user.SDT = request.POST.get('sdt')
            user.save()
            request.session['user_name'] = user.Ten 
            messages.success(request, "Cập nhật thông tin thành công!")
            
        elif action == 'change_password':
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            if user.MatKhau == old_pass:
                if new_pass == confirm_pass:
                    user.MatKhau = new_pass
                    user.save()
                    messages.success(request, "Đổi mật khẩu thành công!")
                else:
                    messages.error(request, "Mật khẩu mới không khớp!")
            else:
                messages.error(request, "Mật khẩu cũ không chính xác!")
        
        return redirect('public_profile')

    cart_data = _get_cart_context(request)
    
    # Lấy thống kê đơn hàng
    if request.session.get('user_role') == 'Khách Hàng':
        orders_query = DonHang.objects.filter(KhachHang=user)
    else:
        orders_query = DonHang.objects.filter(NguoiDung=user)
    total_orders = orders_query.count()
    pending_orders = orders_query.filter(TrangThai='Đang xử lý').count()
    completed_orders = orders_query.filter(TrangThai='Hoàn thành').count()
    recent_orders = orders_query.order_by('-NgayTao')[:3]

    context = {
        'user': user,
        'customer_name': user.Ten,
        'customer_email': user.Email,
        'user_role': request.session.get('user_role'),
        'page_title': 'Tài khoản của tôi - SMART MART',
        'active_nav': 'profile',
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'recent_orders': recent_orders,
    }
    context.update(cart_data)
    return render(request, 'MyApp/public_profile.html', context)

def public_settings(request):
    """
    Trang cài đặt của khách hàng (Storefront Settings)
    """
    if not request.session.get('user_id'):
        return redirect('public_login')
    
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if user_role == 'Khách Hàng':
        user = get_object_or_404(KhachHang, MaKH=user_id)
    else:
        user = get_object_or_404(NhanVien, MaNV=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_password':
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            if user.MatKhau == old_pass:
                if new_pass == confirm_pass:
                    user.MatKhau = new_pass
                    user.save()
                    messages.success(request, "Đổi mật khẩu thành công!")
                else:
                    messages.error(request, "Mật khẩu xác nhận không khớp!")
            else:
                messages.error(request, "Mật khẩu cũ không chính xác!")
            
            return redirect('public_settings')

    context = {
        'page_title': 'Cài đặt tài khoản - SMART MART',
        'user': user,
        'customer_name': user.Ten,
        'customer_email': user.Email,
        'user_role': request.session.get('user_role'),
    }
    context.update(_get_cart_context(request))
    return render(request, 'MyApp/public_settings.html', context)

def submit_return_request(request, order_id):
    """
    Gửi yêu cầu trả hàng từ phía khách hàng
    """
    if not request.session.get('user_id'):
        return redirect('public_login')
        
    order = get_object_or_404(DonHang, MaDH=order_id)
    
    if request.method == 'POST':
        ly_do = request.POST.get('ly_do')
        if not ly_do:
            messages.error(request, "Vui lòng nhập lý do trả hàng.")
            return redirect('public_order_history')
            
        # Tạo mã yêu cầu ngẫu nhiên
        import random
        request_id = f"TH{random.randint(100000, 999999)}"
        
        YeuCauTraHang.objects.create(
            MaYCTH=request_id,
            DonHang=order,
            LyDo=ly_do,
            SoTienHoan=order.TongTien, # Mặc định hoàn toàn bộ
            TrangThai='Đang xử lý'
        )
        messages.success(request, f"Đã gửi yêu cầu trả hàng cho đơn {order_id}. Chúng tôi sẽ xử lý sớm nhất!")
        
    return redirect('public_order_history')

# --- QUẢN TRỊ ĐƠN HÀNG (DÀNH CHO ADMIN/NHÂN VIÊN) ---

class OrderListView(SidebarContextMixin, ListView):
    model = DonHang
    template_name = 'MyApp/order_list.html'
    context_object_name = 'orders'
    sidebar_active = 'orders'
    page_title = 'Quản lý Đơn hàng'
    required_roles = ['Admin', 'Nhân Viên', 'Kế Toán']
    paginate_by = 15

    def get_queryset(self):
        queryset = DonHang.objects.all().order_by('-NgayTao')
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            queryset = queryset.filter(
                Q(MaDH__icontains=q) | 
                Q(TenNguoiNhan__icontains=q) | 
                Q(SDT_Nhan__icontains=q)
            )
        if status:
            queryset = queryset.filter(TrangThai=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = DonHang.TRANG_THAI_DH
        return context

class OrderDetailView(SidebarContextMixin, DetailView):
    model = DonHang
    template_name = 'MyApp/order_detail.html'
    context_object_name = 'order'
    sidebar_active = 'orders'
    page_title = 'Chi tiết Đơn hàng'
    required_roles = ['Admin', 'Nhân Viên', 'Kế Toán']
    pk_url_kwarg = 'order_id'

    def get_object(self):
        return get_object_or_404(DonHang, MaDH=self.kwargs.get('order_id'))

@role_required(allowed_roles=['Admin', 'Nhân Viên'])
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(DonHang, MaDH=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(DonHang.TRANG_THAI_DH):
            order.TrangThai = new_status
            order.save()
            messages.success(request, f"Đã cập nhật trạng thái đơn hàng {order_id} thành {new_status}")
        else:
            messages.error(request, "Trạng thái không hợp lệ.")
    return redirect('order_detail', order_id=order_id)

# --- QUẢN TRỊ TRẢ HÀNG & HOÀN TIỀN ---
from .emails import send_refund_notification

class ReturnListView(SidebarContextMixin, ListView):
    model = YeuCauTraHang
    template_name = 'MyApp/return_list.html'
    context_object_name = 'returns'
    sidebar_active = 'returns'
    page_title = 'Quản lý Trả hàng'
    required_roles = ['Admin', 'Nhân Viên', 'Kế Toán']
    paginate_by = 15

    def get_queryset(self):
        queryset = YeuCauTraHang.objects.all().order_by('-NgayTao')
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            queryset = queryset.filter(
                Q(MaYCTH__icontains=q) | 
                Q(DonHang__MaDH__icontains=q)
            )
        if status:
            queryset = queryset.filter(TrangThai=status)
        return queryset

class ReturnDetailView(SidebarContextMixin, DetailView):
    model = YeuCauTraHang
    template_name = 'MyApp/return_detail.html'
    context_object_name = 'ret'
    sidebar_active = 'returns'
    page_title = 'Chi tiết Yêu cầu Trả hàng'
    required_roles = ['Admin', 'Nhân Viên', 'Kế Toán']
    pk_url_kwarg = 'request_id'

    def get_object(self):
        return get_object_or_404(YeuCauTraHang, MaYCTH=self.kwargs.get('request_id'))

@role_required(allowed_roles=['Admin', 'Kế Toán'])
def update_return_status(request, request_id):
    if request.method == 'POST':
        ret = get_object_or_404(YeuCauTraHang, MaYCTH=request_id)
        new_status = request.POST.get('status')
        note = request.POST.get('note')
        amount = request.POST.get('amount')

        if new_status in dict(YeuCauTraHang.TRANG_THAI_CHOICES):
            ret.TrangThai = new_status
            ret.GhiChuAdmin = note
            if amount:
                ret.SoTienHoan = amount
            
            if new_status == 'Đã hoàn tiền':
                ret.NgayXuLy = timezone.now()
                # Gửi Email thông báo qua Mailtrap
                send_refund_notification(ret)
                
                # Cập nhật trạng thái Đơn hàng thành 'Đã trả hàng'
                order = ret.DonHang
                order.TrangThai = 'Đã trả hàng'
                order.save()
                
            ret.save()
            messages.success(request, f"Đã cập nhật trạng thái yêu cầu {request_id}")
        else:
            messages.error(request, "Trạng thái không hợp lệ.")
            
    return redirect('return_detail', request_id=request_id)


# --- QUẢN LÝ XUẤT KHO ---
from .models import YeuCauXuatKho, XuatKhoChiTiet
from .forms import YeuCauXuatKhoForm

class StockOutListView(SidebarContextMixin, ListView):
    model = YeuCauXuatKho
    template_name = 'MyApp/stock_out_list.html'
    context_object_name = 'requests'
    sidebar_active = 'stock_out'
    page_title = 'Yêu cầu Xuất kho'
    paginate_by = 10
    required_roles = ['Admin', 'Kế Toán']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            queryset = queryset.filter(Q(MaPX__icontains=q) | Q(GhiChu__icontains=q))
        if status:
            queryset = queryset.filter(TrangThai=status)
        return queryset.order_by('-Ngay')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = YeuCauXuatKho.objects.values_list('TrangThai', flat=True).distinct()
        return context

class StockOutDetailView(SidebarContextMixin, DetailView):
    model = YeuCauXuatKho
    template_name = 'MyApp/stock_out_detail.html'
    context_object_name = 'px'
    sidebar_active = 'stock_out'
    page_title = 'Chi tiết Phiếu xuất kho'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details'] = XuatKhoChiTiet.objects.filter(PhieuXuat=self.object).select_related('MaSP', 'MaKho')
        return context

StockOutDetailFormSet = inlineformset_factory(
    YeuCauXuatKho, 
    XuatKhoChiTiet,
    fields=['MaKho', 'MaSP', 'SoLuong'],
    extra=1,
    can_delete=True
)

class StockOutCreateView(SidebarContextMixin, CreateView):
    model = YeuCauXuatKho
    form_class = YeuCauXuatKhoForm
    template_name = 'MyApp/stock_out_form.html'
    success_url = reverse_lazy('stock_out_list')
    sidebar_active = 'stock_out'
    required_roles = ['Admin', 'Kế Toán']
    page_title = 'Tạo mới Phiếu xuất kho'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['product_formset'] = StockOutDetailFormSet(self.request.POST)
        else:
            data['product_formset'] = StockOutDetailFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        product_formset = context['product_formset']

        if product_formset.is_valid():
            # --- VALIDATE: Formset phải có ít nhất 1 dòng sản phẩm hợp lệ ---
            filled_forms = [
                f for f in product_formset
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            ]
            if not filled_forms:
                messages.error(self.request, "Phiếu xuất kho phải có ít nhất 1 sản phẩm. Vui lòng thêm dòng sản phẩm trước khi lưu.")
                return self.render_to_response(self.get_context_data(form=form))

            # --- VALIDATE: SoLuong > 0 từng dòng ---
            for f in filled_forms:
                sl = f.cleaned_data.get('SoLuong')
                if sl is not None and sl <= 0:
                    messages.error(self.request, "Số lượng mỗi sản phẩm trong phiếu xuất phải lớn hơn 0.")
                    return self.render_to_response(self.get_context_data(form=form))

            # --- VALIDATE TRƯỚC: Kiểm tra tồn kho đủ nếu trạng thái là Đã xuất ---
            from .models import HangTonKho
            if form.cleaned_data.get('TrangThai') == 'Đã xuất':
                for f in filled_forms:
                    makho = f.cleaned_data.get('MaKho')
                    masp = f.cleaned_data.get('MaSP')
                    sl = f.cleaned_data.get('SoLuong')
                    if makho and masp and sl:
                        htk = HangTonKho.objects.filter(MaKho=makho, MaSP=masp).first()
                        if not htk:
                            messages.error(self.request, f"Không có tồn kho cho '{masp}' tại kho '{makho}'. Phiếu không thể xuất.")
                            return self.render_to_response(self.get_context_data(form=form))
                        if htk.SoLuong < sl:
                            messages.error(
                                self.request,
                                f"Không đủ tồn kho cho '{masp.Ten}' tại kho '{makho.Ten}'. "
                                f"Tồn hiện tại: {htk.SoLuong}, Yêu cầu xuất: {sl}."
                            )
                            return self.render_to_response(self.get_context_data(form=form))

            # Tự động gán nhân viên đang đăng nhập làm người tạo phiếu xuất
            user_id = self.request.session.get('user_id')
            if user_id:
                from .models import NhanVien
                try:
                    nv = NhanVien.objects.get(MaNV=user_id)
                    form.instance.MaNV = nv
                except NhanVien.DoesNotExist:
                    pass

            self.object = form.save()
            product_formset.instance = self.object
            product_formset.save()

            # GIẢM TỒN KHO KHI XUẤT
            if self.object.TrangThai == 'Đã xuất':
                items = self.object.items.all()
                for item in items:
                    inventory = HangTonKho.objects.get(MaKho=item.MaKho, MaSP=item.MaSP)
                    inventory.SoLuong -= item.SoLuong
                    inventory.save()

            messages.success(self.request, f"Đã tạo phiếu xuất {self.object.MaPX} thành công!")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class StockOutUpdateView(SidebarContextMixin, UpdateView):
    model = YeuCauXuatKho
    form_class = YeuCauXuatKhoForm
    template_name = 'MyApp/stock_out_form.html'
    success_url = reverse_lazy('stock_out_list')
    sidebar_active = 'stock_out'
    required_roles = ['Admin', 'Kế Toán']
    page_title = 'Chỉnh sửa Phiếu xuất kho'

    def dispatch(self, request, *args, **kwargs):
        """Khóa phiếu khi đã ở trạng thái 'Đã xuất' — không cho sửa nữa."""
        response = super().dispatch(request, *args, **kwargs)
        obj = self.get_object()
        if obj.TrangThai == 'Đã xuất':
            messages.error(
                request,
                f"Phiếu xuất '{obj.MaPX}' đã ở trạng thái 'Đã xuất'. Không thể chỉnh sửa!"
            )
            return redirect(self.success_url)
        return response

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['product_formset'] = StockOutDetailFormSet(self.request.POST, instance=self.object)
        else:
            data['product_formset'] = StockOutDetailFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        # Lưu trạng thái cũ trước khi update
        old_status = YeuCauXuatKho.objects.get(pk=self.object.pk).TrangThai
        context = self.get_context_data()
        product_formset = context['product_formset']
        
        if product_formset.is_valid():
            self.object = form.save()
            product_formset.save()
            
            # Nếu chuyển sang 'Đã xuất' từ trạng thái khác
            if self.object.TrangThai == 'Đã xuất' and old_status != 'Đã xuất':
                from .models import HangTonKho
                items = self.object.items.all()
                # Kiểm tra tồn kho đủ trước khi xuất
                for item in items:
                    try:
                        inventory = HangTonKho.objects.get(MaKho=item.MaKho, MaSP=item.MaSP)
                        if inventory.SoLuong < item.SoLuong:
                            messages.error(self.request, f"Không đủ tồn kho cho '{item.MaSP.Ten}' tại kho '{item.MaKho.Ten}'. Tồn: {inventory.SoLuong}, Yêu cầu: {item.SoLuong}")
                            self.object.TrangThai = old_status
                            self.object.save()
                            return redirect(self.success_url)
                    except HangTonKho.DoesNotExist:
                        messages.error(self.request, f"Không có tồn kho cho '{item.MaSP.Ten}' tại kho '{item.MaKho.Ten}'.")
                        self.object.TrangThai = old_status
                        self.object.save()
                        return redirect(self.success_url)
                
                # Nếu đủ hàng, thực hiện trừ
                for item in items:
                    inventory = HangTonKho.objects.get(MaKho=item.MaKho, MaSP=item.MaSP)
                    inventory.SoLuong -= item.SoLuong
                    inventory.save()
            
            messages.success(self.request, f"Đã cập nhật phiếu xuất {self.object.MaPX}")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class StockOutDeleteView(SidebarContextMixin, DeleteView):
    model = YeuCauXuatKho
    success_url = reverse_lazy('stock_out_list')
    required_roles = ['Admin']

import openpyxl
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

def download_stockin_template(request):
    """
    Tải file mẫu Excel nhập kho.
    Sheet 1: File mẫu để điền dữ liệu.
    Sheet 2 & 3: Danh sách Mã SP và Mã Kho hợp lệ trong hệ thống để tham khảo.
    """
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()

    # ===== SHEET 1: Mẫu nhập liệu =====
    ws = wb.active
    ws.title = "Nhap_Kho_Mau"
    headers = ["Mã Sản Phẩm (*)", "Mã Kho (*)", "Số Lượng (*)", "Ghi Chú"]
    ws.append(headers)
    header_font  = Font(bold=True, color="FFFFFF")
    header_fill  = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font       = header_font
        cell.fill       = header_fill
        cell.alignment  = center_align
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 22
    # Dữ liệu mẫu minh hoạ
    ws.append(["SP001", "KHO01", 50, "Nhập lô hàng mới"])
    ws.append(["SP002", "KHO01", 100, ""])

    # ===== SHEET 2: Danh sách Sản phẩm tham khảo =====
    ws2 = wb.create_sheet("DS_San_Pham_Tham_Khao")
    ws2.append(["Mã SP", "Tên sản phẩm", "Trạng thái"])
    for col, w in zip([1, 2, 3], [15, 40, 15]):
        cell = ws2.cell(row=1, column=col)
        cell.font  = Font(bold=True, color="FFFFFF")
        cell.fill  = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
        ws2.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w
    for sp in SanPham.objects.all().order_by('MaSP'):
        ws2.append([sp.MaSP, sp.Ten, sp.TrangThai])

    # ===== SHEET 3: Danh sách Kho tham khảo =====
    ws3 = wb.create_sheet("DS_Kho_Tham_Khao")
    ws3.append(["Mã Kho", "Tên kho", "Loại", "Địa chỉ"])
    for col, w in zip([1, 2, 3, 4], [15, 35, 15, 40]):
        cell = ws3.cell(row=1, column=col)
        cell.font  = Font(bold=True, color="FFFFFF")
        cell.fill  = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")
        ws3.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w
    for kho in Kho.objects.all().order_by('MaKho'):
        ws3.append([kho.MaKho, kho.Ten, kho.Loai, kho.DiaChi or ''])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Mau_Nhap_Kho.xlsx"'
    wb.save(response)
    return response

@csrf_exempt
def parse_stockin_excel(request):
    """
    Parse file Excel nhập kho, validate từng dòng, trả về JSON.
    Logic: chỉ đưa dòng vào data khi KHÔNG có lỗi nào.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            ws = wb.active

            data = []
            errors = []

            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                # Bỏ qua dòng trống hoàn toàn
                if not any(row):
                    continue

                ma_sp = str(row[0]).strip() if row[0] is not None else None
                ma_kho = str(row[1]).strip() if row[1] is not None else None
                so_luong_raw = row[2]
                ghi_chu = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ''

                row_has_error = False

                # Kiểm tra trường bắt buộc
                if not ma_sp or not ma_kho or so_luong_raw is None:
                    errors.append(f"Dòng {row_idx}: Thiếu thông tin bắt buộc (Mã SP, Mã Kho, Số lượng).")
                    continue

                # Kiểm tra số lượng hợp lệ
                try:
                    so_luong = int(so_luong_raw)
                    if so_luong <= 0:
                        errors.append(f"Dòng {row_idx}: Số lượng phải lớn hơn 0.")
                        row_has_error = True
                except (ValueError, TypeError):
                    errors.append(f"Dòng {row_idx}: Số lượng '{so_luong_raw}' không hợp lệ, phải là số nguyên.")
                    continue

                # Kiểm tra Sản phẩm tồn tại trong DB
                ten_sp = ma_sp
                sp_obj = SanPham.objects.filter(MaSP=ma_sp).first()
                if not sp_obj:
                    errors.append(f"Dòng {row_idx}: Không tìm thấy Sản phẩm mã '{ma_sp}'.")
                    row_has_error = True
                else:
                    ten_sp = sp_obj.Ten

                # Kiểm tra Kho tồn tại trong DB
                ten_kho = ma_kho
                kho_obj = Kho.objects.filter(MaKho=ma_kho).first()
                if not kho_obj:
                    errors.append(f"Dòng {row_idx}: Không tìm thấy Kho mã '{ma_kho}'.")
                    row_has_error = True
                else:
                    ten_kho = kho_obj.Ten

                # Chỉ thêm vào data nếu dòng này KHÔNG có lỗi nào
                if not row_has_error:
                    data.append({
                        'masp': ma_sp,
                        'ten_sp': ten_sp,
                        'makho': ma_kho,
                        'ten_kho': ten_kho,
                        'soluong': so_luong,
                        'ghichu': ghi_chu,
                    })

            if errors:
                return JsonResponse({'success': False, 'errors': errors})

            if not data:
                return JsonResponse({'success': False, 'errors': ["File Excel không có dữ liệu hợp lệ nào."]})

            return JsonResponse({'success': True, 'data': data, 'total': len(data)})

        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f"Lỗi định dạng file Excel: {str(e)}"]})

    return JsonResponse({'success': False, 'errors': ["Không tìm thấy file tải lên hợp lệ."]})
