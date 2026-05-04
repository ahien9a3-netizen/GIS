# SQL Database Guide - WebApp E-commerce

## 📋 Tập Tin SQL Được Cung Cấp

### 1. **database_schema.sql**
- Tạo toàn bộ cấu trúc database
- Tạo tất cả các bảng
- Tạo indexes
- Tạo views và functions
- Tạo triggers (tự động cập nhật tồn kho)
- Thêm dữ liệu mẫu cơ bản

### 2. **sample_data.sql**
- Thêm dữ liệu mẫu chi tiết
- 10+ danh mục sản phẩm
- 30+ sản phẩm mẫu
- 5 nhân viên
- 4 kho hàng
- 5 cửa hàng
- 5 đơn hàng hoàn chỉnh
- Các đánh giá mẫu

---

## 🚀 Cách Sử Dụng

### Cách 1: Sử dụng psql (Recommended)

#### 1.1 Tạo Database
```bash
# Bằng psql (Windows/Linux/Mac)
psql -U postgres

# Hoặc với password
psql -U postgres -W

# Tạo database
CREATE DATABASE webapp_gis;
\q
```

#### 1.2 Tạo Schema
```bash
# Chạy file schema từ cmd/terminal
psql -U postgres -d webapp_gis -f "e:\Python\GIS\WebApp\database_schema.sql"

# Hoặc từ Git Bash
psql -U postgres -d webapp_gis -f /e/Python/GIS/WebApp/database_schema.sql
```

#### 1.3 Thêm Dữ Liệu Mẫu
```bash
# Chạy file sample data
psql -U postgres -d webapp_gis -f "e:\Python\GIS\WebApp\sample_data.sql"
```

#### 1.4 Xác Minh Dữ Liệu
```bash
# Kết nối tới database
psql -U postgres -d webapp_gis

# Kiểm tra bảng
\dt

# Kiểm tra số bản ghi
SELECT COUNT(*) FROM sanpham;
SELECT COUNT(*) FROM cuahang;
SELECT COUNT(*) FROM donhang;

# Thoát
\q
```

---

### Cách 2: Sử dụng DBeaver / pgAdmin

#### 2.1 Mở DBeaver
- Mở DBeaver
- Kết nối tới PostgreSQL server
- Tạo database mới (webapp_gis)

#### 2.2 Chạy SQL Script
- Mở file `database_schema.sql`
- Ctrl+A để chọn tất cả
- Ctrl+Enter để chạy
- Chờ hoàn tất

#### 2.3 Thêm Dữ Liệu
- Mở file `sample_data.sql`
- Ctrl+A để chọn tất cả
- Ctrl+Enter để chạy

#### 2.4 Kiểm Tra
- Xem danh sách bảng ở sidebar
- Click vào bảng để xem dữ liệu

---

### Cách 3: Sử dụng Django (Recommended cho development)

#### 3.1 Tạo Migrations từ Models
```bash
cd e:\Python\GIS\WebApp

# Tạo migrations từ models Django
python manage.py makemigrations

# Xem migrations sẽ tạo gì
python manage.py sqlmigrate MyApp 0001
```

#### 3.2 Chạy Migrations
```bash
# Áp dụng migrations
python manage.py migrate
```

#### 3.3 Thêm Dữ Liệu Mẫu
```bash
# Chạy SQL directly
psql -U postgres -d webapp_gis -f "e:\Python\GIS\WebApp\sample_data.sql"

# Hoặc từ Django shell
python manage.py shell

# Trong shell, chạy:
>>> from MyApp.models import SanPham, CuaHang, DanhMuc
>>> from django.contrib.gis.geos import Point
>>> 
>>> # Tạo danh mục
>>> dm = DanhMuc.objects.create(MaDM='DM001', Ten='Điện Tử')
>>> 
>>> # Tạo sản phẩm
>>> sp = SanPham.objects.create(
...     MaSP='SP001',
...     Ten='iPhone 15 Pro',
...     DanhMuc=dm,
...     Gia=30000000,
...     TrangThai='Đang bán'
... )
>>> 
>>> # Kiểm tra
>>> SanPham.objects.count()
1
>>> exit()
```

---

## 📊 Cấu Trúc Database

### Các Bảng Chính

#### 1. **danhmuc** (Danh Mục)
```sql
madm (VARCHAR 20) PRIMARY KEY
tendm (VARCHAR 255) - Tên danh mục
```

#### 2. **sanpham** (Sản Phẩm)
```sql
masp (VARCHAR 20) PRIMARY KEY
ten (VARCHAR 255) - Tên sản phẩm
danhmuc (FK) - Liên kết danh mục
gia (DECIMAL) - Giá bán
trangthai (VARCHAR 50) - Trạng thái
```

#### 3. **kho** (Kho Hàng)
```sql
makho (VARCHAR 20) PRIMARY KEY
ten (VARCHAR 255) - Tên kho
loai (VARCHAR 50) - Loại kho
diachi (TEXT) - Địa chỉ
geom (GEOMETRY) - Tọa độ GIS
```

#### 4. **cuahang** (Cửa Hàng)
```sql
mach (VARCHAR 20) PRIMARY KEY
ten (VARCHAR 255) - Tên cửa hàng
loai (VARCHAR 50) - Loại cửa hàng
diachi (TEXT) - Địa chỉ
sdt (VARCHAR 20) - Số điện thoại
geom (GEOMETRY) - Tọa độ GIS
```

#### 5. **hangtonkho** (Tồn Kho)
```sql
makho (FK) - Liên kết kho
masp (FK) - Liên kết sản phẩm
soluong (INTEGER) - Số lượng tồn
```

#### 6. **donhang** (Đơn Hàng)
```sql
madh (VARCHAR 20) PRIMARY KEY
manv (FK) - Liên kết nhân viên
tennguoinhan (VARCHAR 255) - Tên người nhận
trangthai (VARCHAR 50) - Trạng thái đơn
```

#### 7. **chitietdonhang** (Chi Tiết Đơn Hàng)
```sql
madh (FK) - Liên kết đơn hàng
masp (FK) - Liên kết sản phẩm
soluong (INTEGER) - Số lượng
giatrongdh (DECIMAL) - Giá trong đơn
```

---

## 🔍 Các Views Hữu Ích

### View: v_hangtonkho_detail
Xem thông tin tồn kho chi tiết với tên sản phẩm, kho, giá trị:
```sql
SELECT * FROM v_hangtonkho_detail;
```

### View: v_donhang_detail
Xem thông tin đơn hàng chi tiết:
```sql
SELECT * FROM v_donhang_detail;
```

### View: v_danhgia_sanpham
Xem đánh giá sản phẩm:
```sql
SELECT * FROM v_danhgia_sanpham;
```

---

## 🛠️ Các Truy Vấn Thường Dùng

### 1. Kiểm Tra Tồn Kho
```sql
-- Tồn kho theo kho
SELECT k.ten as kho, sp.ten as sanpham, htk.soluong
FROM hangtonkho htk
JOIN kho k ON htk.makho = k.makho
JOIN sanpham sp ON htk.masp = sp.masp
ORDER BY k.ten, sp.ten;

-- Tồn kho theo sản phẩm
SELECT sp.ten, SUM(htk.soluong) as tongton
FROM hangtonkho htk
JOIN sanpham sp ON htk.masp = sp.masp
GROUP BY sp.masp, sp.ten
HAVING SUM(htk.soluong) < 10;
```

### 2. Doanh Thu Bán Hàng
```sql
-- Doanh thu theo ngày
SELECT DATE(dh.ngaytao) as ngay, COUNT(*) as so_don, SUM(ctdh.soluong * ctdh.giatrongdh) as doanhthu
FROM donhang dh
JOIN chitietdonhang ctdh ON dh.madh = ctdh.madh
GROUP BY DATE(dh.ngaytao)
ORDER BY ngay DESC;

-- Doanh thu theo sản phẩm
SELECT sp.ten, SUM(ctdh.soluong) as soluongban, SUM(ctdh.soluong * ctdh.giatrongdh) as doanhthu
FROM chitietdonhang ctdh
JOIN sanpham sp ON ctdh.masp = sp.masp
GROUP BY sp.masp, sp.ten
ORDER BY doanhthu DESC;
```

### 3. Đơn Hàng Chưa Hoàn Thành
```sql
-- Đơn hàng đang xử lý
SELECT madh, tennguoinhan, sdt_nhan, trangthai, ngaytao
FROM donhang
WHERE trangthai IN ('Đang xử lý', 'Đang giao')
ORDER BY ngaytao;

-- Số ngày chưa giao
SELECT madh, tennguoinhan, CURRENT_DATE - DATE(ngaytao) as ngay_cho
FROM donhang
WHERE trangthai = 'Đang giao'
ORDER BY ngaytao;
```

### 4. Cửa Hàng và Kho Gần Nhất
```sql
-- Kho gần cửa hàng (sử dụng GIS)
SELECT ch.ten as cuahang, k.ten as kho, 
       ST_Distance(ch.geom, k.geom) * 111000 as khoangcach_meter
FROM cuahang ch
CROSS JOIN kho k
ORDER BY ch.mach, ST_Distance(ch.geom, k.geom)
LIMIT 10;
```

### 5. Đánh Giá Và Rating
```sql
-- Sản phẩm được đánh giá cao nhất
SELECT sp.ten, ROUND(AVG(dg.diem), 2) as diem_trungbinh, COUNT(dg.id) as sodanhgia
FROM sanpham sp
LEFT JOIN danhgia dg ON sp.masp = dg.masp
GROUP BY sp.masp, sp.ten
HAVING COUNT(dg.id) > 0
ORDER BY diem_trungbinh DESC;
```

---

## 🔧 Bảo Trì Database

### 1. Backup Database
```bash
# Backup toàn bộ database
pg_dump -U postgres webapp_gis > backup_2024.sql

# Backup chỉ dữ liệu
pg_dump -U postgres --data-only webapp_gis > backup_data_2024.sql

# Backup chỉ schema
pg_dump -U postgres --schema-only webapp_gis > backup_schema_2024.sql
```

### 2. Restore Database
```bash
# Restore toàn bộ
psql -U postgres webapp_gis < backup_2024.sql

# Restore chỉ dữ liệu (nếu schema đã tồn tại)
psql -U postgres webapp_gis < backup_data_2024.sql
```

### 3. Optimize Database
```sql
-- Analyze tables
ANALYZE;

-- Vacuum
VACUUM ANALYZE;

-- Kiểm tra kích thước database
SELECT pg_database.datname, 
       pg_size_pretty(pg_database_size(pg_database.datname))
FROM pg_database
WHERE datname = 'webapp_gis';

-- Kiểm tra kích thước bảng
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## ⚠️ Chú Ý Quan Trọng

### 1. **Backup Trước Khi Chạy**
```bash
# Tạo backup trước
pg_dump -U postgres webapp_gis > backup_before.sql
```

### 2. **Kiểm Tra Phiên Bản PostgreSQL**
```bash
psql --version
# Cần phiên bản 10+
```

### 3. **Kiểm Tra PostGIS**
```bash
psql -U postgres -d webapp_gis

# Trong psql:
SELECT PostGIS_version();
```

### 4. **Nếu Gặp Lỗi**
```bash
# Kiểm tra lỗi
psql -U postgres -d webapp_gis -f database_schema.sql 2>&1 | tee error.log

# Xem file error.log để tìm vấn đề
cat error.log
```

---

## 📞 Support

### Các Lệnh Hữu Ích

```bash
# Kết nối database
psql -U postgres -d webapp_gis

# Từ psql:
\dt                    # Liệt kê tất cả bảng
\dv                    # Liệt kê tất cả views
\df                    # Liệt kê tất cả functions
\di                    # Liệt kê tất cả indexes
\d tablename           # Xem cấu trúc bảng
SELECT * FROM table LIMIT 5;  # Xem 5 bản ghi đầu
\q                     # Thoát

# Count bản ghi
SELECT COUNT(*) FROM sanpham;
SELECT COUNT(*) FROM donhang;

# Xem schema
\dn                    # Liệt kê schemas
```

---

## 🎯 Workflow Khuyến Nghị

1. **Development**
   ```bash
   psql -U postgres -d webapp_gis -f database_schema.sql
   psql -U postgres -d webapp_gis -f sample_data.sql
   python manage.py runserver
   ```

2. **Testing**
   ```bash
   # Test dữ liệu mẫu
   python manage.py shell
   >>> from MyApp.models import *
   >>> print(SanPham.objects.count())
   ```

3. **Production**
   ```bash
   # Backup trước
   pg_dump -U postgres webapp_gis > backup_prod.sql
   
   # Chạy schema
   psql -U postgres -d webapp_prod -f database_schema.sql
   
   # Chạy migrations
   python manage.py migrate
   ```

---

## ✅ Checklist

- [ ] PostgreSQL + PostGIS cài đặt
- [ ] Database `webapp_gis` được tạo
- [ ] File `database_schema.sql` chạy thành công
- [ ] File `sample_data.sql` chạy thành công
- [ ] Kiểm tra tất cả bảng được tạo (\dt)
- [ ] Kiểm tra dữ liệu mẫu (SELECT COUNT)
- [ ] Django models kết nối tới database
- [ ] Chạy `python manage.py migrate` thành công
- [ ] Test Excel import/export

---

**Version**: 1.0
**Last Updated**: 2024
**Status**: Production Ready ✅
