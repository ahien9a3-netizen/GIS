# 📊 Excel Import/Export Guide for Django Admin

## ✨ Features

Your Django Admin now has **Excel import/export functionality** for the following models:

### Models with Excel Support:
- ✅ **Cửa Hàng** (Stores)
- ✅ **Kho Hàng** (Warehouses)
- ✅ **Sản Phẩm** (Products)
- ✅ **Nhân Viên** (Employees)
- ✅ **Yêu Cầu Nhập Kho** (Stock In Requests)
- ✅ **Yêu Cầu Xuất Kho** (Stock Out Requests)
- ✅ **Hàng Tồn Kho** (Inventory)
- Plus 12 other models!

---

## 🎯 How to Use

### 1️⃣ **Export to Excel**

**From any admin change_list page:**

1. ✓ Check the checkboxes next to records you want to export (or leave unchecked to export all)
2. ✓ Click the **📥 Export to Excel** button (light blue, top of the list)
3. ✓ Select the records from dropdown menu "Export Selected to Excel"
4. ✓ Excel file downloads automatically

**What you get:**
- ✅ All columns with data formatted nicely
- ✅ Headers with blue background and white text
- ✅ Numbers formatted with decimals
- ✅ Dates formatted as YYYY-MM-DD HH:MM:SS
- ✅ Columns auto-sized for readability

---

### 2️⃣ **Import from Excel**

**From any admin change_list page:**

1. ✓ Click **📤 Import from Excel** button (green, top of the list)
2. ✓ Modal dialog opens
3. ✓ Click "Select Excel File" and choose your .xlsx file
4. ✓ (Optional) Check "Skip rows with errors" to continue importing if some rows fail
5. ✓ Click "Import Now"
6. ✓ Success message shows how many records were imported

**Important:**
- ⚠️ Only `.xlsx` files are supported (not `.xls` or `.csv`)
- ⚠️ First row must contain field names (headers)
- ⚠️ Field names must match model field names (exact match, case-sensitive)
- ⚠️ Primary key field must be present if updating existing records

---

### 3️⃣ **Download Template**

**To get a pre-made template for import:**

1. ✓ Click **📋 Download Template** button (gray, top of the list)
2. ✓ Excel file downloads with:
   - Headers in blue (row 1)
   - Field type hints in gray (row 2)
   - Proper column widths
3. ✓ Edit the template and fill in your data
4. ✓ Save as `.xlsx`
5. ✓ Use "Import from Excel" to upload it

---

## 📋 Template Example (Sản Phẩm)

When you download the **Product template**, you get:

```
MaSP (CharField)       | Ten (CharField)        | DanhMuc (ForeignKey)  | Gia (DecimalField)
SP001                  | iPhone 15 Pro          | Điện Tử               | 25000000
SP002                  | Samsung Galaxy S24     | Điện Tử               | 22000000
```

---

## ✅ Import Guidelines

### Field Types and Expected Formats:

| Field Type | Excel Format | Example |
|---|---|---|
| **CharField** | Text | "iPhone 15" |
| **IntegerField** | Number | 100 |
| **DecimalField** | Number (with decimals) | 25000000.00 |
| **DateField** | YYYY-MM-DD | 2024-01-15 |
| **DateTimeField** | YYYY-MM-DD HH:MM:SS | 2024-01-15 14:30:00 |
| **BooleanField** | TRUE/FALSE or 1/0 | TRUE |
| **ForeignKey** | Primary key value | CH001 |
| **Choices** | Choice value | "Đang bán" |

---

## 🛡️ Error Handling

### If import fails:

1. ✅ Error message tells you which row failed and why
2. ✅ Check field names match exactly
3. ✅ Verify data types (numbers, dates, etc.)
4. ✅ Check foreign key values exist
5. ✅ Remove special characters if needed

### Skip Errors:

- If you check **"Skip rows with errors"**, the import will:
  - ✓ Continue importing valid rows
  - ✓ Show warning messages for failed rows (first 5 shown)
  - ✓ Display success count + number of skipped rows

---

## 💡 Tips & Tricks

### 1. **Bulk Update**
Export data → Edit in Excel → Import back with same primary keys = Update all records

### 2. **Data Migration**
Download template → Fill with data from other system → Import

### 3. **Backup**
Regularly export critical data (Products, Orders, Employees) as backup

### 4. **Validation**
Check imported data in admin immediately after upload to verify it's correct

### 5. **Large Files**
- Files with 10,000+ rows work fine
- Rows are imported in batches of 1000
- Importing takes a few seconds

---

## 🔐 Permissions

- ✅ Only **staff members** can access import/export
- ✅ Only **superusers** can import/export if permission restrictions are set
- ✅ No extra permissions needed (uses Django's default staff permission)

---

## 📂 File Locations

- **Admin Import/Export Code**: `MyApp/admin.py`
- **Admin Excel Views**: `MyApp/admin_excel_views.py`
- **Admin Template**: `MyApp/templates/admin/MyApp/change_list.html`
- **URLs**: `MyApp/urls.py` (routes `/admin-api/excel/*`)

---

## 🚨 Common Issues & Solutions

### Issue: "Only .xlsx files are supported"
**Solution:** Save file as Excel Workbook (.xlsx), not Excel 2003 (.xls)

### Issue: Field name not found
**Solution:** Use exact field name from template, must match database column name

### Issue: Import hangs or takes too long
**Solution:** Check file size (too many rows?), try importing smaller batches

### Issue: Data looks wrong after import
**Solution:** Verify field types in template match actual data (numbers vs text)

### Issue: Foreign key reference not found
**Solution:** Make sure the related object exists (e.g., product category exists before importing product)

---

## 📞 Support

For issues or questions:
1. Check the error message carefully
2. Download the template for correct field names
3. Verify data types match the template hints
4. Test with small dataset first (few rows)
5. Check admin logs for detailed error info

---

**Version**: 1.0
**Created**: 2024
**Supported Models**: 19 models
**File Format**: .xlsx (Excel 2007+)
**Status**: ✅ Production Ready
