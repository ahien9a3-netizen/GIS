"""
Optimized View Classes and Mixins
Enhanced views with better query performance and caching
"""

from django.views.generic import ListView
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from .optimization import QueryOptimizer, CacheMixin
from .models import SanPham, CuaHang, Kho, HangTonKho, DonHang, YeuCauNhapKho


class OptimizedListViewMixin(CacheMixin):
    """Mixin to optimize ListView queries"""
    
    query_optimizer = None
    cache_timeout = 300
    
    def get_queryset(self):
        """Get and optimize queryset"""
        queryset = super().get_queryset()
        
        # Apply query optimizer if available
        if self.query_optimizer:
            queryset = self.query_optimizer(queryset)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add cache information to context"""
        context = super().get_context_data(**kwargs)
        context['cache_enabled'] = True
        return context


class OptimizedSanPhamListView(OptimizedListViewMixin, ListView):
    """Optimized SanPham list view"""
    model = SanPham
    query_optimizer = QueryOptimizer.optimize_sanpham_queries
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters
        q = self.request.GET.get('q')
        dm = self.request.GET.get('danhmuc')
        
        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(MieuTa__icontains=q) | Q(MaSP__icontains=q)
            )
        if dm:
            queryset = queryset.filter(DanhMuc__MaDM=dm)
        
        return queryset.order_by('-MaSP')


class OptimizedCuaHangListView(OptimizedListViewMixin, ListView):
    """Optimized CuaHang list view"""
    model = CuaHang
    query_optimizer = QueryOptimizer.optimize_cuahang_queries
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters
        q = self.request.GET.get('q')
        loai = self.request.GET.get('loai')
        
        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(DiaChi__icontains=q) | Q(MaCH__icontains=q)
            )
        if loai:
            queryset = queryset.filter(Loai=loai)
        
        return queryset.order_by('Ten')


class OptimizedKhoListView(OptimizedListViewMixin, ListView):
    """Optimized Kho list view"""
    model = Kho
    query_optimizer = QueryOptimizer.optimize_kho_queries
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters
        q = self.request.GET.get('q')
        loai = self.request.GET.get('loai')
        
        if q:
            queryset = queryset.filter(
                Q(Ten__icontains=q) | Q(DiaChi__icontains=q) | Q(MaKho__icontains=q)
            )
        if loai:
            queryset = queryset.filter(Loai=loai)
        
        return queryset.order_by('Ten')


class OptimizedHangTonKhoListView(OptimizedListViewMixin, ListView):
    """Optimized HangTonKho list view"""
    model = HangTonKho
    query_optimizer = QueryOptimizer.optimize_hangtonkho_queries
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters
        kho = self.request.GET.get('kho')
        sanpham = self.request.GET.get('sanpham')
        
        if kho:
            queryset = queryset.filter(MaKho__MaKho=kho)
        if sanpham:
            queryset = queryset.filter(MaSP__MaSP=sanpham)
        
        return queryset.order_by('MaKho', 'MaSP')


class OptimizedDonHangListView(OptimizedListViewMixin, ListView):
    """Optimized DonHang list view"""
    model = DonHang
    query_optimizer = QueryOptimizer.optimize_donhang_queries
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters
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
        
        return queryset.order_by('-NgayTao')


class OptimizedYeuCauNhapKhoListView(OptimizedListViewMixin, ListView):
    """Optimized YeuCauNhapKho list view"""
    model = YeuCauNhapKho
    query_optimizer = QueryOptimizer.optimize_yeucaunhapkho_queries
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        
        if q:
            queryset = queryset.filter(MaYC__icontains=q)
        if status:
            queryset = queryset.filter(TrangThai=status)
        
        return queryset.order_by('-Ngay')


# Export optimization query tools
__all__ = [
    'OptimizedListViewMixin',
    'OptimizedSanPhamListView',
    'OptimizedCuaHangListView',
    'OptimizedKhoListView',
    'OptimizedHangTonKhoListView',
    'OptimizedDonHangListView',
    'OptimizedYeuCauNhapKhoListView',
]
