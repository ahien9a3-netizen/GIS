"""
Enhanced Django Admin with Excel Export
Add this to your admin.py to enable Excel export from Django admin
"""

from django.contrib import admin
from django.http import HttpResponse
from .models import SanPham, CuaHang, Kho, HangTonKho, NhanVien, DanhMuc, DonHang, YeuCauNhapKho
from .excel_utils import ExcelExporter
from .optimization import QueryOptimizer


class ExcelExportMixin(admin.ModelAdmin):
    """Mixin to add Excel export action to admin"""
    
    excel_export_fields = None
    
    def get_excel_export_fields(self):
        """Get fields to export to Excel"""
        if self.excel_export_fields:
            return self.excel_export_fields
        
        return [f.name for f in self.model._meta.get_fields() if f.name != 'id']
    
    def export_to_excel(self, request, queryset):
        """Action to export selected items to Excel"""
        fields = self.get_excel_export_fields()
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    export_to_excel.short_description = "Export selected items to Excel"
    
    def get_actions(self, request):
        """Add export action"""
        actions = super().get_actions(request)
        actions['export_to_excel'] = (self.export_to_excel, 'export_to_excel', self.export_to_excel.short_description)
        return actions


class SanPhamAdmin(ExcelExportMixin):
    """Admin for SanPham with Excel export"""
    list_display = ['MaSP', 'Ten', 'DanhMuc', 'Gia', 'TrangThai']
    list_filter = ['TrangThai', 'DanhMuc']
    search_fields = ['MaSP', 'Ten']
    excel_export_fields = ['MaSP', 'Ten', 'DanhMuc__Ten', 'Gia', 'TrangThai']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return QueryOptimizer.optimize_sanpham_queries(queryset)


class CuaHangAdmin(ExcelExportMixin):
    """Admin for CuaHang with Excel export"""
    list_display = ['MaCH', 'Ten', 'Loai', 'SDT', 'TrangThai']
    list_filter = ['Loai', 'TrangThai']
    search_fields = ['MaCH', 'Ten', 'DiaChi']
    excel_export_fields = ['MaCH', 'Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return QueryOptimizer.optimize_cuahang_queries(queryset)


class KhoAdmin(ExcelExportMixin):
    """Admin for Kho with Excel export"""
    list_display = ['MaKho', 'Ten', 'Loai', 'DiaChi']
    list_filter = ['Loai']
    search_fields = ['MaKho', 'Ten', 'DiaChi']
    excel_export_fields = ['MaKho', 'Ten', 'Loai', 'DiaChi']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return QueryOptimizer.optimize_kho_queries(queryset)


class HangTonKhoAdmin(ExcelExportMixin):
    """Admin for HangTonKho with Excel export"""
    list_display = ['MaKho', 'MaSP', 'SoLuong']
    list_filter = ['MaKho']
    search_fields = ['MaKho__Ten', 'MaSP__Ten']
    excel_export_fields = ['MaKho__MaKho', 'MaKho__Ten', 'MaSP__MaSP', 'MaSP__Ten', 'SoLuong']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return QueryOptimizer.optimize_hangtonkho_queries(queryset)


class DonHangAdmin(ExcelExportMixin):
    """Admin for DonHang with Excel export"""
    list_display = ['MaDH', 'TenNguoiNhan', 'TrangThai', 'PhuongThucTT', 'NgayTao']
    list_filter = ['TrangThai', 'PhuongThucTT', 'NgayTao']
    search_fields = ['MaDH', 'TenNguoiNhan', 'SDT_Nhan']
    excel_export_fields = ['MaDH', 'TenNguoiNhan', 'SDT_Nhan', 'DiaChi_Nhan', 'TrangThai', 'PhuongThucTT', 'NgayTao']
    readonly_fields = ['NgayTao']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return QueryOptimizer.optimize_donhang_queries(queryset)


class YeuCauNhapKhoAdmin(ExcelExportMixin):
    """Admin for YeuCauNhapKho with Excel export"""
    list_display = ['MaYC', 'Ngay', 'TrangThai', 'MaNV']
    list_filter = ['TrangThai', 'Ngay']
    search_fields = ['MaYC']
    excel_export_fields = ['MaYC', 'Ngay', 'TrangThai', 'MaNV__Ten']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return QueryOptimizer.optimize_yeucaunhapkho_queries(queryset)


class DanhMucAdmin(admin.ModelAdmin):
    """Admin for DanhMuc"""
    list_display = ['MaDM', 'Ten']
    search_fields = ['MaDM', 'Ten']


class NhanVienAdmin(admin.ModelAdmin):
    """Admin for NhanVien"""
    list_display = ['MaNV', 'Ten', 'Email', 'Role']
    list_filter = ['Role']
    search_fields = ['MaNV', 'Ten', 'Email']


# Register all models with enhanced admin
admin.site.register(SanPham, SanPhamAdmin)
admin.site.register(CuaHang, CuaHangAdmin)
admin.site.register(Kho, KhoAdmin)
admin.site.register(HangTonKho, HangTonKhoAdmin)
admin.site.register(DonHang, DonHangAdmin)
admin.site.register(YeuCauNhapKho, YeuCauNhapKhoAdmin)
admin.site.register(DanhMuc, DanhMucAdmin)
admin.site.register(NhanVien, NhanVienAdmin)
