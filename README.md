# 🗺️ SMART MART — Hệ Thống Quản Lý Chuỗi Cửa Hàng Tiện Lợi, Gia Dụng và Điện Tử

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Django](https://img.shields.io/badge/Django-6.0-green?logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)
![PostGIS](https://img.shields.io/badge/PostGIS-Enabled-orange)

> Đồ án môn học GIS — Nhóm 13

---

## 📋 Giới Thiệu

**SMART MART** là hệ thống quản lý chuỗi cửa hàng tiện lợi tích hợp công nghệ GIS (Geographic Information System), cho phép:

- 🗺️ Hiển thị vị trí cửa hàng trên bản đồ tương tác (Leaflet + OpenStreetMap)
- 📍 Tìm cửa hàng gần nhất, tìm đường đi
- 🛒 Mua hàng online với giỏ hàng và thanh toán
- ⭐ Đánh giá, bình luận sản phẩm và cửa hàng (chống spam, phân trang, lọc sao)
- 📦 Quản lý kho hàng, nhập kho (hỗ trợ import Excel)
- 👥 Quản lý nhân viên, khách hàng, đơn hàng

---

## 🛠️ Yêu Cầu Hệ Thống

| Phần mềm | Phiên bản |
|----------|-----------|
| Python | 3.10 trở lên |
| PostgreSQL | 15 trở lên |
| PostGIS | 3.x (extension cho PostgreSQL) |
| Git | (tùy chọn) |

---

## 🚀 Hướng Dẫn Cài Đặt

### Bước 1: Cài đặt PostgreSQL + PostGIS

1. Tải PostgreSQL: https://www.postgresql.org/download/
2. Trong quá trình cài, mở **Stack Builder** → chọn cài **PostGIS**
3. Hoặc cài PostGIS riêng: https://postgis.net/install/

### Bước 2: Restore Database

**Cách 1 — Dùng pgAdmin:**
1. Mở pgAdmin 4
2. Click phải vào **Databases** → **Create** → **Database...**
3. Đặt tên: `webapp1` → Click **Save**
4. Click phải vào database vừa tạo → **Query Tool**
5. Chạy lệnh: `CREATE EXTENSION postgis;`
6. Click phải vào database → **Restore...** → Chọn file `backup_GIS.sql`

**Cách 2 — Dùng Terminal:**
```bash
# Tạo database
psql -U postgres -c "CREATE DATABASE webapp1;"

# Bật PostGIS extension
psql -U postgres -d webapp1 -c "CREATE EXTENSION postgis;"

# Restore dữ liệu
psql -U postgres -d webapp1 -f backup_GIS.sql
```

### Bước 3: Cài đặt Python và thư viện

```bash
# Clone repository
git clone https://github.com/<username>/GIS-SmartMart.git
cd GIS-SmartMart

# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### Bước 4: Cấu hình Database

Mở file `WebApp/WebApp/settings.py`, chỉnh sửa phần `DATABASES`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'webapp1',        # Tên database đã tạo ở Bước 2
        'USER': 'postgres',       # User PostgreSQL
        'PASSWORD': '123',        # Mật khẩu PostgreSQL của bạn
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Bước 5: Chạy ứng dụng

```bash
cd WebApp
python manage.py migrate    # Đồng bộ database (nếu cần)
python manage.py runserver  # Khởi chạy server
```

Mở trình duyệt tại: **http://127.0.0.1:8000/**

---

## 🔑 Tài Khoản Mẫu

| Vai trò | SĐT / Email | Mật khẩu |
|---------|-------------|----------|
| Admin / Nhân viên | `0123456789` | `123456` |
| Khách hàng | Tạo mới qua trang Đăng ký | — |

---

## 📁 Cấu Trúc Thư Mục

```
GIS/
├── WebApp/
│   ├── MyApp/                  # App chính
│   │   ├── models.py           # Models (SanPham, CuaHang, DanhGia, Kho, ...)
│   │   ├── views.py            # Views xử lý logic
│   │   ├── urls.py             # URL routing
│   │   ├── templates/MyApp/    # HTML templates
│   │   └── static/             # CSS, JS, Images
│   ├── WebApp/
│   │   ├── settings.py         # Cấu hình Django
│   │   └── urls.py             # URL gốc
│   └── manage.py
├── requirements.txt            # Danh sách thư viện Python
└── README.md                   # File này
```

---

## ✨ Tính Năng Chính

### 🗺️ GIS & Bản Đồ
- Hiển thị cửa hàng trên bản đồ Leaflet
- Tìm đường đi (routing)
- Tìm cửa hàng gần nhất
- Chọn địa chỉ giao hàng bằng click bản đồ (có nút xác nhận)

### 🛒 Thương Mại Điện Tử
- Danh sách sản phẩm với tìm kiếm, lọc danh mục
- Giỏ hàng, đặt hàng, lịch sử đơn hàng
- Checkout với chọn vị trí giao hàng trên bản đồ

### ⭐ Đánh Giá & Bình Luận
- Đánh giá sao (1-5) cho sản phẩm và cửa hàng
- Chống spam: mỗi người chỉ đánh giá 1 lần
- Bộ lọc theo số sao (filter chips)
- Phân trang bình luận (5 comment/trang)

### 📦 Quản Lý Kho
- Nhập kho từ file Excel
- Thêm dòng sản phẩm thủ công
- Theo dõi tồn kho theo cửa hàng

### 👤 Quản Lý Người Dùng
- Đăng nhập hợp nhất (Nhân viên + Khách hàng chung 1 trang)
- Phân quyền: Admin, Nhân viên, Kế toán, Khách hàng
- Quản lý profile, đổi mật khẩu

---

## 🔧 Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|-----------|-----------|
| Backend | Django 6.0, Django REST Framework |
| Database | PostgreSQL 15 + PostGIS |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Bản đồ | Leaflet.js, OpenStreetMap, Nominatim |
| Icons | Font Awesome 6 |
| Fonts | Google Fonts (Inter, Outfit) |
| Animation | AOS (Animate On Scroll) |

---

## 👥 Nhóm 13

> Đồ án môn học Hệ Thống Thông Tin Địa Lý (GIS)

---

## 📄 License

Project này được phát triển cho mục đích học tập.
