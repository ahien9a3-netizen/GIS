"""
Excel Import/Export Utilities
Utilities for importing and exporting data to/from Excel files
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
from decimal import Decimal


class ExcelExporter:
    """Export Django models to Excel files"""
    
    HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF")
    BORDER = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    @staticmethod
    def export_queryset(queryset, fields, filename=None):
        """
        Export a queryset to Excel
        
        Args:
            queryset: Django queryset
            fields: List of field names to export
            filename: Optional filename for the Excel file
        
        Returns:
            BytesIO object containing Excel file
        """
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Data"
        
        # Write headers
        for col_idx, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = field
            cell.fill = ExcelExporter.HEADER_FILL
            cell.font = ExcelExporter.HEADER_FONT
            cell.border = ExcelExporter.BORDER
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Write data
        for row_idx, obj in enumerate(queryset, 2):
            for col_idx, field in enumerate(fields, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                
                # Handle nested fields (e.g., 'relation__field')
                value = obj
                for attr in field.split('__'):
                    if hasattr(value, attr):
                        value = getattr(value, attr)
                    else:
                        value = None
                        break
                
                # Format value
                if isinstance(value, Decimal):
                    cell.value = float(value)
                    cell.number_format = '#,##0.00'
                elif isinstance(value, datetime):
                    cell.value = value
                    cell.number_format = 'yyyy-mm-dd hh:mm:ss'
                else:
                    cell.value = value
                
                cell.border = ExcelExporter.BORDER
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        
        # Auto-adjust column widths
        for col_idx, field in enumerate(fields, 1):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = max(len(str(field)), 15)
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output, filename
    
    @staticmethod
    def export_to_file(queryset, fields, filepath):
        """Export queryset directly to file"""
        output, _ = ExcelExporter.export_queryset(queryset, fields)
        with open(filepath, 'wb') as f:
            f.write(output.getvalue())


class ExcelImporter:
    """Import data from Excel files to Django models"""
    
    @staticmethod
    def read_excel_file(file_obj):
        """
        Read Excel file and return data as list of dictionaries
        
        Args:
            file_obj: File object or file path
        
        Returns:
            List of dictionaries representing rows
        """
        try:
            df = pd.read_excel(file_obj)
            # Replace NaN with None
            df = df.where(pd.notna(df), None)
            return df.to_dict('records')
        except Exception as e:
            raise ValueError(f"Lỗi đọc file Excel: {str(e)}")
    
    @staticmethod
    def validate_headers(excel_headers, required_headers):
        """
        Validate if Excel file has required headers
        
        Args:
            excel_headers: Headers from Excel file
            required_headers: List of required headers
        
        Returns:
            Tuple (is_valid, missing_headers)
        """
        missing = [h for h in required_headers if h not in excel_headers]
        return len(missing) == 0, missing
    
    @staticmethod
    def import_data(file_obj, model_class, field_mapping, skip_errors=True):
        """
        Import data from Excel to Django model
        
        Args:
            file_obj: Excel file object
            model_class: Django model class
            field_mapping: Dict mapping Excel columns to model fields
            skip_errors: If True, skip rows with errors; if False, raise exception
        
        Returns:
            Tuple (success_count, error_count, error_messages)
        """
        data = ExcelImporter.read_excel_file(file_obj)
        success_count = 0
        error_count = 0
        error_messages = []
        
        for row_idx, row in enumerate(data, 2):  # Start from 2 (skip header)
            try:
                # Map Excel columns to model fields
                obj_data = {}
                for excel_col, model_field in field_mapping.items():
                    if excel_col in row and row[excel_col] is not None:
                        obj_data[model_field] = row[excel_col]
                
                # Create and save object
                obj = model_class(**obj_data)
                obj.full_clean()  # Validate
                obj.save()
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"Hàng {row_idx}: {str(e)}"
                error_messages.append(error_msg)
                
                if not skip_errors:
                    raise Exception(error_msg)
        
        return success_count, error_count, error_messages


class BulkExcelImporter:
    """Bulk import for better performance"""
    
    @staticmethod
    def bulk_create_from_excel(file_obj, model_class, field_mapping, batch_size=1000):
        """
        Bulk create objects from Excel for better performance
        
        Args:
            file_obj: Excel file object
            model_class: Django model class
            field_mapping: Dict mapping Excel columns to model fields
            batch_size: Number of objects to create per batch
        
        Returns:
            Tuple (total_created, errors)
        """
        data = ExcelImporter.read_excel_file(file_obj)
        objects = []
        errors = []
        
        for row_idx, row in enumerate(data, 2):
            try:
                obj_data = {}
                for excel_col, model_field in field_mapping.items():
                    if excel_col in row and row[excel_col] is not None:
                        obj_data[model_field] = row[excel_col]
                
                obj = model_class(**obj_data)
                obj.full_clean()
                objects.append(obj)
                
                # Bulk create when batch size reached
                if len(objects) >= batch_size:
                    model_class.objects.bulk_create(objects)
                    objects = []
                    
            except Exception as e:
                errors.append(f"Hàng {row_idx}: {str(e)}")
        
        # Create remaining objects
        if objects:
            model_class.objects.bulk_create(objects)
        
        return len(data) - len(errors), errors


class ExcelTemplateGenerator:
    """Generate Excel templates for import"""
    
    @staticmethod
    def generate_template(fields, filename=None):
        """
        Generate an Excel template with headers
        
        Args:
            fields: List of field names
            filename: Optional filename
        
        Returns:
            BytesIO object containing template
        """
        if not filename:
            filename = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Template"
        
        # Write headers
        for col_idx, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = field
            cell.fill = ExcelExporter.HEADER_FILL
            cell.font = ExcelExporter.HEADER_FONT
            cell.border = ExcelExporter.BORDER
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Freeze header row
        ws.freeze_panes = 'A2'
        
        # Auto-adjust column widths
        for col_idx, field in enumerate(fields, 1):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = max(len(str(field)), 15)
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output, filename
