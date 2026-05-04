# 📁 SQL Files Summary - WebApp E-commerce

## 📦 Tệp SQL Được Tạo

### ✅ 1. **database_schema.sql** (Main Schema)
**Kích thước**: ~15KB
**Nội dung**:
- ✓ Tạo PostgreSQL extensions (PostGIS)
- ✓ Tạo 20 bảng chính
- ✓ Tạo 15+ indexes
- ✓ Tạo 3 views (v_hangtonkho_detail, v_donhang_detail, v_danhgia_sanpham)
- ✓ Tạo 2 functions (auto-update inventory)
- ✓ Tạo 2 triggers (auto-update on stock in/out)
- ✓ Thêm dữ liệu mẫu cơ bản (5 danh mục, 5 nhân viên, 2 kho, 2 cửa hàng)

**Chạy**:
```bash
psql -U postgres -d webapp_gis -f database_schema.sql
```

---

### ✅ 2. **sample_data.sql** (Extended Sample Data)
**Kích thước**: ~12KB
**Nội dung**:
- ✓ 10 danh mục sản phẩm đầy đủ
- ✓ 30+ sản phẩm với giá realistic
- ✓ 5 nhân viên với các role khác nhau
- ✓ 4 kho hàng tại các tỉnh thành
- ✓ 5 cửa hàng với locations GIS
- ✓ 100+ bản ghi tồn kho
- ✓ 5 yêu cầu nhập kho
- ✓ 5 đơn hàng hoàn chỉnh
- ✓ Dữ liệu đánh giá sản phẩm & cửa hàng

**Chạy sau database_schema.sql**:
```bash
psql -U postgres -d webapp_gis -f sample_data.sql
```

---

### ✅ 3. **SQL_GUIDE.md** (Documentation)
**Hướng dẫn sử dụng chi tiết**:
- 🔍 Cách 1: Sử dụng psql (Command Line)
- 🔍 Cách 2: Sử dụng DBeaver/pgAdmin
- 🔍 Cách 3: Sử dụng Django
- 📊 Các truy vấn SQL hữu ích
- 🛠️ Bảo trì & Optimize
- ⚠️ Troubleshooting

---

## 🚀 Quick Start (3 Bước)

### Bước 1: Tạo Database
```bash
psql -U postgres

# Trong psql:
CREATE DATABASE webapp_gis;
\q
```

### Bước 2: Chạy Schema
```bash
psql -U postgres -d webapp_gis -f "e:\Python\GIS\WebApp\database_schema.sql"
```

### Bước 3: Thêm Sample Data
```bash
psql -U postgres -d webapp_gis -f "e:\Python\GIS\WebApp\sample_data.sql"
```

**Hoàn tất!** Database đã sẵn sàng ✅

---

## 📊 Dữ Liệu Được Tạo

| Bảng | Số Bản Ghi | Mô Tả |
|---|---|---|
| **danhmuc** | 10 | Danh mục sản phẩm |
| **sanpham** | 30+ | Sản phẩm (giá, mô tả, hình ảnh) |
| **nhanvien** | 5 | Nhân viên (roles: Admin, KT, NV, User) |
| **kho** | 4 | Kho hàng (kho tổng + chi nhánh) |
| **cuahang** | 5 | Cửa hàng (Hà Nội, TP.HCM, Đà Nẵng) |
| **hangtonkho** | 100+ | Tồn kho (các kho, sản phẩm) |
| **donhang** | 5 | Đơn hàng mẫu |
| **chitietdonhang** | 12 | Chi tiết các đơn hàng |
| **danhgia** | 8 | Đánh giá sản phẩm |
| **danhgiacuahang** | 5 | Đánh giá cửa hàng |
| **yeucaunhapkho** | 5 | Yêu cầu nhập kho |
| **yeucautrahang** | 2 | Yêu cầu trả hàng |

**Total**: 200+ records mẫu ✅

---

## 🎯 Tính Năng Database

### ✨ Tính Năng GIS
- ✓ Lưu trữ tọa độ kho (latitude/longitude)
- ✓ Lưu trữ tọa độ cửa hàng
- ✓ Tính toán khoảng cách giữa kho/cửa hàng
- ✓ Query địa lý (các cửa hàng gần nhất, kho gần nhất)

### ✨ Tính Năng Inventory
- ✓ Auto-update tồn kho khi nhập
- ✓ Auto-update tồn kho khi xuất
- ✓ Triggers tự động

### ✨ Tính Năng Views
- ✓ View chi tiết tồn kho (với tên sản phẩm, kho)
- ✓ View chi tiết đơn hàng (với tổng tiền)
- ✓ View đánh giá sản phẩm (rating trung bình)

### ✨ Tính Năng Index
- ✓ Index trên tất cả các fields thường dùng
- ✓ Index GIS cho spatial queries
- ✓ Index composite cho joins

---

## 🔗 Kết Nối Với Django

### Django Settings (WebApp/settings.py)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'webapp_gis',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Chạy Migrations
```bash
python manage.py migrate
```

### Verify Kết Nối
```bash
python manage.py shell
>>> from MyApp.models import SanPham
>>> print(SanPham.objects.count())
30  # Hoặc số sản phẩm tương tự
```

---

## 📋 Các Truy Vấn Hữu Ích

### 1. Tồn Kho Chi Tiết
```sql
SELECT * FROM v_hangtonkho_detail;
```

### 2. Đơn Hàng Chi Tiết
```sql
SELECT * FROM v_donhang_detail;
```

### 3. Sản Phẩm Bán Chạy
```sql
SELECT sp.ten, SUM(ctdh.soluong) as so_luong_ban
FROM chitietdonhang ctdh
JOIN sanpham sp ON ctdh.masp = sp.masp
GROUP BY sp.masp, sp.ten
ORDER BY so_luong_ban DESC LIMIT 10;
```

### 4. Đơn Hàng Chưa Hoàn Thành
```sql
SELECT madh, tennguoinhan, trangthai, ngaytao
FROM donhang
WHERE trangthai IN ('Đang xử lý', 'Đang giao')
ORDER BY ngaytao;
```

### 5. Cửa Hàng Gần Nhất Từ Kho (GIS)
```sql
SELECT ch.ten, k.ten, 
       ST_Distance(ch.geom, k.geom) * 111000 as khoang_cach
FROM cuahang ch
CROSS JOIN kho k
ORDER BY khoang_cach LIMIT 5;
```

---

## 🛠️ Bảo Trì

### Backup
```bash
pg_dump -U postgres webapp_gis > backup_webapp.sql
```

### Restore
```bash
psql -U postgres webapp_gis < backup_webapp.sql
```

### Optimize
```bash
psql -U postgres -d webapp_gis -c "VACUUM ANALYZE;"
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **Backup trước khi chạy** (nếu database đã tồn tại)
   ```bash
   pg_dump -U postgres webapp_gis > backup_before.sql
   ```

2. **Kiểm tra phiên bản PostgreSQL** (cần ≥ 10)
   ```bash
   psql --version
   ```

3. **Kiểm tra PostGIS extension**
   ```bash
   psql -U postgres -d webapp_gis -c "SELECT PostGIS_version();"
   ```

4. **Nếu gặp lỗi connection**
   - Kiểm tra username/password
   - Kiểm tra port (mặc định 5432)
   - Kiểm tra PostgreSQL đang chạy

5. **Nếu gặp lỗi about duplicate key**
   - Dữ liệu đã tồn tại
   - Sử dụng `ON CONFLICT DO NOTHING` (đã có sẵn)

---

## 📞 Troubleshooting

### Lỗi: "FATAL: database webapp_gis does not exist"
```bash
# Tạo database trước
psql -U postgres -c "CREATE DATABASE webapp_gis;"
```

### Lỗi: "Unrecognized extension name postgis"
```bash
# Cài đặt PostGIS (Ubuntu/Debian)
sudo apt-get install postgresql-[version]-postgis

# macOS
brew install postgis

# Windows
# Chọn PostGIS khi cài PostgreSQL
```

### Lỗi: "Permission denied"
```bash
# Sử dụng postgres user
sudo -u postgres psql

# Hoặc set password
psql -U postgres -W
```

### Lỗi: "Foreign key violation"
- Đảm bảo chạy schema trước sample_data
- Đảm bảo tất cả foreign keys đã tồn tại

---

## 📚 File References

### Database Schema Files
- `database_schema.sql` - Main schema (run first!)
- `sample_data.sql` - Sample data (run second)

### Documentation
- `SQL_GUIDE.md` - Chi tiết guide
- `OPTIMIZATION_GUIDE.md` - Database optimization
- `EXCEL_FEATURES_README.md` - Excel features

### Django Files
- `WebApp/settings.py` - Database configuration
- `MyApp/models.py` - ORM models

---

## ✅ Success Checklist

- [ ] PostgreSQL + PostGIS installed
- [ ] Database `webapp_gis` created
- [ ] `database_schema.sql` executed successfully
- [ ] `sample_data.sql` executed successfully
- [ ] All tables created (\dt in psql)
- [ ] Sample data visible (SELECT COUNT(*))
- [ ] Django can connect (python manage.py shell)
- [ ] All views working (SELECT * FROM v_hangtonkho_detail)
- [ ] Excel import/export tested

---

## 🎉 Ready to Go!

Database của bạn đã sẵn sàng với:
- ✅ 20 bảng hoàn chỉnh
- ✅ GIS support (locations, distances)
- ✅ 200+ sample records
- ✅ Auto-update triggers
- ✅ Useful views & functions
- ✅ Production-ready indexes

**Bắt đầu phát triển! 🚀**

---

**Version**: 1.0
**Created**: 2024
**Database**: PostgreSQL + PostGIS
**Django ORM**: Supported ✅
