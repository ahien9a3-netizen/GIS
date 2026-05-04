"""
Excel Import/Export Views
Views for handling Excel import/export operations
"""

from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect
import json
from .excel_utils import ExcelExporter, ExcelImporter, ExcelTemplateGenerator, BulkExcelImporter
from .models import SanPham, CuaHang, Kho, HangTonKho, NhanVien, DanhMuc, DonHang, YeuCauNhapKho, YeuCauXuatKho


class ExcelExportMixin:
    """Mixin to add Excel export functionality to list views"""
    
    export_fields = []
    export_model = None
    
    def get_export_filename(self):
        """Override to customize filename"""
        model_name = self.export_model._meta.verbose_name_plural or self.export_model.__name__
        return f"{model_name.lower()}_export.xlsx"
    
    def export_to_excel(self):
        """Export queryset to Excel"""
        queryset = self.get_queryset()
        fields = self.export_fields or [f.name for f in self.export_model._meta.get_fields()]
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.get_export_filename()}"'
        return response


class SanPhamExportView(View):
    """Export Sản phẩm to Excel"""
    
    def get(self, request):
        queryset = SanPham.objects.select_related('DanhMuc')
        fields = ['MaSP', 'Ten', 'DanhMuc__Ten', 'Gia', 'TrangThai']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="sanpham_export.xlsx"'
        return response


class SanPhamImportView(View):
    """Import Sản phẩm from Excel"""
    
    def get(self, request):
        # Generate and download template
        fields = ['MaSP', 'Ten', 'DanhMuc', 'Gia', 'TrangThai']
        output, filename = ExcelTemplateGenerator.generate_template(fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="sanpham_template.xlsx"'
        return response
    
    def post(self, request):
        try:
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'Không tìm thấy file'}, status=400)
            
            file_obj = request.FILES['file']
            
            # Field mapping
            field_mapping = {
                'MaSP': 'MaSP',
                'Ten': 'Ten',
                'DanhMuc': 'DanhMuc_id',
                'Gia': 'Gia',
                'TrangThai': 'TrangThai'
            }
            
            # Validate headers
            df = __import__('pandas').read_excel(file_obj)
            is_valid, missing = ExcelImporter.validate_headers(df.columns.tolist(), list(field_mapping.keys()))
            
            if not is_valid:
                return JsonResponse({'error': f"Thiếu cột: {', '.join(missing)}"}, status=400)
            
            # Import data
            file_obj.seek(0)
            success, error_count, errors = ExcelImporter.import_data(
                file_obj, 
                SanPham, 
                field_mapping, 
                skip_errors=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Nhập thành công {success} sản phẩm',
                'errors': errors[:10]  # Return first 10 errors
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class KhoExportView(View):
    """Export Kho to Excel"""
    
    def get(self, request):
        queryset = Kho.objects.all()
        fields = ['MaKho', 'Ten', 'Loai', 'DiaChi']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="kho_export.xlsx"'
        return response


class CuaHangExportView(View):
    """Export Cửa hàng to Excel"""
    
    def get(self, request):
        queryset = CuaHang.objects.all()
        fields = ['MaCH', 'Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="cuahang_export.xlsx"'
        return response


class HangTonKhoExportView(View):
    """Export Hàng tồn kho to Excel"""
    
    def get(self, request):
        queryset = HangTonKho.objects.select_related('MaKho', 'MaSP')
        fields = ['MaKho', 'MaKho__Ten', 'MaSP', 'MaSP__Ten', 'SoLuong']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="hangtonkho_export.xlsx"'
        return response


class DonHangExportView(View):
    """Export Đơn hàng to Excel"""
    
    def get(self, request):
        queryset = DonHang.objects.select_related('NguoiDung')
        fields = ['MaDH', 'NguoiDung__Ten', 'TenNguoiNhan', 'SDT_Nhan', 'DiaChi_Nhan', 'TrangThai', 'PhuongThucThanhToan', 'NgayTao']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="donhang_export.xlsx"'
        return response


class NhanVienExportView(View):
    """Export Nhân viên to Excel"""
    
    def get(self, request):
        queryset = NhanVien.objects.all()
        fields = ['MaNV', 'Ten', 'SDT', 'Email', 'Role']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="nhanvien_export.xlsx"'
        return response


class YeuCauNhapKhoExportView(View):
    """Export Yêu cầu nhập kho to Excel"""
    
    def get(self, request):
        queryset = YeuCauNhapKho.objects.select_related('MaNV')
        fields = ['MaYC', 'MaNV__Ten', 'Ngay', 'TrangThai']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="yeucaunhapkho_export.xlsx"'
        return response


class YeuCauXuatKhoExportView(View):
    """Export Yêu cầu xuất kho to Excel"""
    
    def get(self, request):
        queryset = YeuCauXuatKho.objects.select_related('MaNV', 'DonHang')
        fields = ['MaPX', 'MaNV__Ten', 'DonHang__MaDH', 'LyDo', 'TrangThai', 'Ngay']
        
        output, filename = ExcelExporter.export_queryset(queryset, fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="yeucauxuatkho_export.xlsx"'
        return response


class BulkImportView(View):
    """Generic bulk import view"""
    
    model_map = {
        'sanpham': (SanPham, {
            'MaSP': 'MaSP',
            'Ten': 'Ten',
            'DanhMuc': 'DanhMuc_id',
            'Gia': 'Gia',
            'TrangThai': 'TrangThai'
        }),
        'kho': (Kho, {
            'MaKho': 'MaKho',
            'Ten': 'Ten',
            'Loai': 'Loai',
            'DiaChi': 'DiaChi'
        }),
        'cuahang': (CuaHang, {
            'MaCH': 'MaCH',
            'Ten': 'Ten',
            'Loai': 'Loai',
            'DiaChi': 'DiaChi',
            'SDT': 'SDT'
        }),
        'yeucaunhapkho': (YeuCauNhapKho, {
            'MaYC': 'MaYC',
            'MaNV': 'MaNV_id',
            'Ngay': 'Ngay',
            'TrangThai': 'TrangThai'
        }),
        'yeucauxuatkho': (YeuCauXuatKho, {
            'MaPX': 'MaPX',
            'MaNV': 'MaNV_id',
            'DonHang': 'DonHang_id',
            'LyDo': 'LyDo',
            'TrangThai': 'TrangThai'
        }),
        'nhanvien': (NhanVien, {
            'MaNV': 'MaNV',
            'Ten': 'Ten',
            'SDT': 'SDT',
            'Email': 'Email',
            'Role': 'Role'
        }),
    }
    
    def post(self, request, model_name):
        try:
            if model_name not in self.model_map:
                return JsonResponse({'error': 'Model không hỗ trợ'}, status=400)
            
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'Không tìm thấy file'}, status=400)
            
            model_class, field_mapping = self.model_map[model_name]
            file_obj = request.FILES['file']
            
            # Use bulk import for better performance
            total, errors = BulkExcelImporter.bulk_create_from_excel(
                file_obj, 
                model_class, 
                field_mapping,
                batch_size=1000
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Nhập thành công {total} bản ghi',
                'errors': errors[:10]
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ExportTemplateView(View):
    """Download Excel template for import"""
    
    templates = {
        'sanpham': ['MaSP', 'Ten', 'DanhMuc', 'Gia', 'TrangThai'],
        'kho': ['MaKho', 'Ten', 'Loai', 'DiaChi'],
        'cuahang': ['MaCH', 'Ten', 'Loai', 'DiaChi', 'SDT', 'TrangThai'],
        'hangtonkho': ['MaKho', 'MaSP', 'SoLuong'],
        'yeucaunhapkho': ['MaYC', 'MaNV', 'Ngay', 'TrangThai'],
        'yeucauxuatkho': ['MaPX', 'MaNV', 'DonHang', 'LyDo', 'TrangThai'],
        'nhanvien': ['MaNV', 'Ten', 'SDT', 'Email', 'Role'],
    }
    
    def get(self, request, model_name):
        if model_name not in self.templates:
            return JsonResponse({'error': 'Template không tồn tại'}, status=404)
        
        fields = self.templates[model_name]
        output, filename = ExcelTemplateGenerator.generate_template(fields)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{model_name}_template.xlsx"'
        return response
