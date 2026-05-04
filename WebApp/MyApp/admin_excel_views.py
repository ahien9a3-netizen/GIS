"""
Admin views for Excel import/export functionality
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import openpyxl
from decimal import Decimal
from datetime import datetime

from MyApp.models import (
    DanhMuc, SanPham, DanhGia, Kho, CuaHang, NhanVien, 
    YeuCauNhapKho, HangTonKho, NhapKhoChiTiet,
    YeuCauXuatKho, XuatKhoChiTiet, GioHang, ChiTietGioHang,
    DonHang, ChiTietDonHang, YeuCauTraHang, DanhGiaCuaHang, PhanBoCungCap
)

# Model mapping cho import
MODEL_MAPPING = {
    'danhmuc': DanhMuc,
    'sanpham': SanPham,
    'danhgia': DanhGia,
    'kho': Kho,
    'cuahang': CuaHang,
    'nhanvien': NhanVien,
    'yeucaunhapkho': YeuCauNhapKho,
    'hangtonkho': HangTonKho,
    'nhapkhochitiet': NhapKhoChiTiet,
    'yeucauxuatkho': YeuCauXuatKho,
    'xuatkhochitiet': XuatKhoChiTiet,
    'giohang': GioHang,
    'chitietgiohang': ChiTietGioHang,
    'donhang': DonHang,
    'chitietdonhang': ChiTietDonHang,
    'yeucautrahang': YeuCauTraHang,
    'danhgiacuahang': DanhGiaCuaHang,
    'phanbocungcap': PhanBoCungCap,
}

@staff_member_required
@require_http_methods(["POST"])
def admin_excel_import(request):
    """
    Handle Excel import for admin
    Expected POST parameters:
    - excel_file: File object
    - model_name: Model name (lowercase)
    - skip_errors: Boolean to skip rows with errors
    """
    
    if 'excel_file' not in request.FILES:
        messages.error(request, 'No file uploaded')
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    
    excel_file = request.FILES['excel_file']
    model_name = request.GET.get('model_name', '').lower()
    skip_errors = request.POST.get('skip_errors') == 'true'
    
    if not excel_file.name.endswith('.xlsx'):
        messages.error(request, 'Only .xlsx files are supported')
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    
    if model_name not in MODEL_MAPPING:
        messages.error(request, f'Invalid model: {model_name}')
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    
    model_class = MODEL_MAPPING[model_name]
    
    try:
        # Load workbook
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # Get headers (first row)
        headers = []
        for cell in ws[1]:
            if cell.value:
                headers.append(cell.value)
        
        if not headers:
            messages.error(request, 'Excel file is empty or has no headers')
            return redirect(request.META.get('HTTP_REFERER', '/admin/'))
        
        # Process data rows
        imported_count = 0
        error_rows = []
        
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            try:
                # Extract row data
                row_data = {}
                for col_num, cell in enumerate(row):
                    if col_num < len(headers):
                        field_name = headers[col_num]
                        value = cell.value
                        
                        if value is not None:
                            # Try to convert value to appropriate type
                            try:
                                field = model_class._meta.get_field(field_name)
                                
                                # Handle different field types
                                if hasattr(field, 'choices') and field.choices:
                                    row_data[field_name] = value
                                elif field.get_internal_type() == 'DecimalField':
                                    row_data[field_name] = Decimal(str(value))
                                elif field.get_internal_type() == 'IntegerField':
                                    row_data[field_name] = int(value) if value else None
                                elif field.get_internal_type() == 'BooleanField':
                                    row_data[field_name] = bool(value)
                                elif field.get_internal_type() == 'DateTimeField':
                                    if isinstance(value, str):
                                        row_data[field_name] = datetime.fromisoformat(value)
                                    else:
                                        row_data[field_name] = value
                                elif field.get_internal_type() == 'DateField':
                                    if isinstance(value, str):
                                        row_data[field_name] = datetime.strptime(value, '%Y-%m-%d').date()
                                    else:
                                        row_data[field_name] = value
                                else:
                                    row_data[field_name] = value
                            except:
                                row_data[field_name] = value
                
                if row_data:
                    # Try to create or update object
                    pk_field = model_class._meta.pk.name
                    if pk_field in row_data:
                        obj, created = model_class.objects.update_or_create(
                            **{pk_field: row_data[pk_field]},
                            defaults={k: v for k, v in row_data.items() if k != pk_field}
                        )
                    else:
                        obj = model_class.objects.create(**row_data)
                    
                    imported_count += 1
            
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                if skip_errors:
                    error_rows.append(error_msg)
                else:
                    messages.error(request, error_msg)
                    return redirect(request.META.get('HTTP_REFERER', '/admin/'))
        
        # Success message
        msg = f'✅ Successfully imported {imported_count} records'
        if error_rows:
            msg += f' ({len(error_rows)} rows skipped with errors)'
            for err in error_rows[:5]:  # Show first 5 errors
                messages.warning(request, err)
        
        messages.success(request, msg)
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
    
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


def generate_excel_template(model_name):
    """
    Generate Excel template for import
    """
    if model_name not in MODEL_MAPPING:
        raise ValueError(f'Invalid model: {model_name}')
    
    model_class = MODEL_MAPPING[model_name]
    
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = model_class.__name__
    
    # Get fields (exclude auto-generated)
    fields = [
        f for f in model_class._meta.get_fields()
        if not (f.auto_created and f.many_to_one)
        and f.name not in ['id']
        and hasattr(f, 'get_internal_type')
    ]
    
    # Write headers
    for col_num, field in enumerate(fields, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = field.name
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Add data type hint in second row
        hint_cell = ws.cell(row=2, column=col_num)
        hint_cell.value = field.get_internal_type()
        hint_cell.font = Font(italic=True, size=9, color="666666")
    
    # Set column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    return wb


@staff_member_required
def admin_download_template(request):
    """
    Download Excel template for specific model
    """
    model_name = request.GET.get('model', '').lower()
    
    if not model_name:
        messages.error(request, 'Model name not specified')
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    
    try:
        wb = generate_excel_template(model_name)
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{model_name}_template_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        wb.save(response)
        return response
    
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    except Exception as e:
        messages.error(request, f'Error generating template: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
